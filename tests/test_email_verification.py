import json
import importlib.util
import os
import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


SERVICE_ROOT = Path(__file__).resolve().parents[1] / "services"
sys.path.insert(0, str(SERVICE_ROOT))
sys.path.insert(0, str(SERVICE_ROOT / "auth_api"))

# AWS includes these modules in Lambda. Stub them for dependency-free local tests.
boto3 = types.ModuleType("boto3")
boto3.client = MagicMock()
boto3.resource = MagicMock()
botocore = types.ModuleType("botocore")
botocore_exceptions = types.ModuleType("botocore.exceptions")
botocore_exceptions.ClientError = type("ClientError", (Exception,), {})
boto3_dynamodb = types.ModuleType("boto3.dynamodb")
boto3_conditions = types.ModuleType("boto3.dynamodb.conditions")
boto3_conditions.Key = MagicMock()
boto3_conditions.Attr = MagicMock()
sys.modules.setdefault("boto3", boto3)
sys.modules.setdefault("boto3.dynamodb", boto3_dynamodb)
sys.modules.setdefault("boto3.dynamodb.conditions", boto3_conditions)
sys.modules.setdefault("botocore", botocore)
sys.modules.setdefault("botocore.exceptions", botocore_exceptions)

import handler as auth_handler

os.environ.setdefault("DYNAMODB_USERS_TABLE", "sentinel-users-test")
authorizer_path = SERVICE_ROOT / "authorizer" / "handler.py"
authorizer_spec = importlib.util.spec_from_file_location("sentinel_authorizer", authorizer_path)
authorizer_handler = importlib.util.module_from_spec(authorizer_spec)
authorizer_spec.loader.exec_module(authorizer_handler)


class FakeUsersTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[Item["id"]] = dict(Item)
        return {}

    def query(self, **_kwargs):
        return {"Items": list(self.items.values())}

    def get_item(self, Key, **_kwargs):
        item = self.items.get(Key["id"])
        return {"Item": item} if item else {}

    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues, **_kwargs):
        item = self.items[Key["id"]]
        values = ExpressionAttributeValues

        if "email_verification_sent_at" in UpdateExpression:
            item["email_verification_sent_at"] = values[":time"]
            item["email_verification_window_started_at"] = values.get(":window_start", values[":time"])
            item["email_verification_send_count"] = values.get(":send_count", values.get(":count", 1))
        if "email_verified = :verified" in UpdateExpression:
            item["email_verified"] = values[":verified"]
            item["email_verified_at"] = values[":time"]
            item["status"] = values[":active"]
            item["updated_at"] = values[":time"]
            item.pop("email_verification_token_hash", None)
            item.pop("email_verification_expires_at", None)
        if "email_verification_token_hash = :token_hash" in UpdateExpression:
            item["email_verification_token_hash"] = values[":token_hash"]
            item["email_verification_expires_at"] = values[":expires"]
            item["updated_at"] = values[":time"]
        return {}


def event(path, body):
    return {
        "rawPath": path,
        "requestContext": {"http": {"method": "POST"}, "requestId": "test-request"},
        "body": json.dumps(body),
    }


class EmailVerificationTests(unittest.TestCase):
    def setUp(self):
        self.table = FakeUsersTable()
        self.sent_token = None

        def capture_email(_email, _name, token):
            self.sent_token = token

        self.table_patch = patch.object(auth_handler, "get_users_table", return_value=self.table)
        self.email_patch = patch.object(auth_handler, "send_verification_email", side_effect=capture_email)
        self.table_patch.start()
        self.email_mock = self.email_patch.start()

    def tearDown(self):
        self.email_patch.stop()
        self.table_patch.stop()

    def test_registration_requires_verification_before_login(self):
        registration = auth_handler.lambda_handler(event("/v1/auth/register", {
            "email": "student@example.edu",
            "password": "correct-horse-battery-staple",
            "name": "Student User",
        }), None)
        registration_body = json.loads(registration["body"])

        self.assertEqual(registration["statusCode"], 201)
        self.assertNotIn("api_key", registration_body["user"])
        self.assertFalse(registration_body["user"]["email_verified"])
        self.assertIsNotNone(self.sent_token)

        blocked_login = auth_handler.lambda_handler(event("/v1/auth/login", {
            "email": "student@example.edu",
            "password": "correct-horse-battery-staple",
        }), None)
        self.assertEqual(blocked_login["statusCode"], 403)
        self.assertEqual(json.loads(blocked_login["body"])["code"], "EMAIL_NOT_VERIFIED")

        verification = auth_handler.lambda_handler(event("/v1/auth/verify-email", {
            "token": self.sent_token,
        }), None)
        self.assertEqual(verification["statusCode"], 200)

        successful_login = auth_handler.lambda_handler(event("/v1/auth/login", {
            "email": "student@example.edu",
            "password": "correct-horse-battery-staple",
        }), None)
        login_body = json.loads(successful_login["body"])
        self.assertEqual(successful_login["statusCode"], 200)
        self.assertTrue(login_body["user"]["email_verified"])
        self.assertIn("api_key", login_body["user"])

    def test_expired_token_is_rejected(self):
        user_id = "02a2b529-f26a-4958-ad69-f283efcaf923"
        token, token_hash = auth_handler.generate_verification_token(user_id)
        self.table.items[user_id] = {
            "id": user_id,
            "email": "expired@example.edu",
            "email_verified": False,
            "email_verification_token_hash": token_hash,
            "email_verification_expires_at": int(time.time()) - 1,
        }

        response = auth_handler.lambda_handler(event("/v1/auth/verify-email", {"token": token}), None)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response["body"])["code"], "TOKEN_EXPIRED")

    def test_resend_is_suppressed_during_cooldown(self):
        auth_handler.lambda_handler(event("/v1/auth/register", {
            "email": "cooldown@example.edu",
            "password": "correct-horse-battery-staple",
            "name": "Cooldown User",
        }), None)

        response = auth_handler.lambda_handler(event("/v1/auth/resend-verification", {
            "email": "cooldown@example.edu",
        }), None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(self.email_mock.call_count, 1)


class AuthorizerVerificationTests(unittest.TestCase):
    def authorize(self, email_verified):
        table = MagicMock()
        table.query.return_value = {"Items": [{
            "id": "user-1",
            "email": "student@example.edu",
            "status": auth_handler.UserStatus.ACTIVE.value,
            "email_verified": email_verified,
        }]}
        event_data = {
            "headers": {"x-api-key": "test-key"},
            "routeArn": "arn:aws:execute-api:us-east-1:123456789012:api/default/GET/resource",
        }

        with patch.object(authorizer_handler, "users_table", table):
            return authorizer_handler.lambda_handler(event_data, None)

    def test_unverified_user_is_denied(self):
        policy = self.authorize(False)
        self.assertEqual(policy["policyDocument"]["Statement"][0]["Effect"], "Deny")

    def test_verified_user_is_allowed(self):
        policy = self.authorize(True)
        self.assertEqual(policy["policyDocument"]["Statement"][0]["Effect"], "Allow")


if __name__ == "__main__":
    unittest.main()
