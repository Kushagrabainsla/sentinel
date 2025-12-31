<div align="center">
  <img src="/assets/images/sentinel-logo.png" alt="Sentinel Logo" width="120" height="120" style="border: 3px solid #e1e5e9; border-radius: 20px; padding: 8px; margin-bottom: 20px;">

  # Sentinel
  ### A Cloud-Native Email Marketing & Analytics SaaS Platform

  [![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB%20%7C%20SES-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com)
  [![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
  [![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
  [![Next.js](https://img.shields.io/badge/Next.js-16.0-000000?logo=next.js&logoColor=white)](https://nextjs.org/)

  **Serverless email marketing platform built on AWS with real-time analytics, AI-powered content generation, and multi-region deployment.**

  [API Documentation](assets/docs/API_USAGE_GUIDE.md) • [Project Details](https://docs.google.com/document/d/1O5GahoZqVnzIXXUuxENSTFhnbGMnF5W2S_Fg0H7R8Ik/edit?usp=sharing) • [Developer Guide](assets/docs/DEVELOPER_GUIDE.md)
</div>

---

## Table of Contents

- [Features](#features)
- [Platform Usage](#platform-usage)
- [API Reference](#api-reference)
- [License](#license)

---

## Features

- **Secure Authentication** — API key-based access with custom Lambda authorizers and route protection.
- **Campaign Management** — Seamlessly create, schedule, and track immediate or timed email campaigns.
- **Real-time Analytics** — Deep insights into opens (human vs. proxy), clicks, and behavioral distribution.
- **AI-Powered Insights** — Generate high-converting email content and performance recommendations via Gemini AI.
- **Global Scalability** — Built on multi-region DynamoDB Global Tables for sub-second latency worldwide.
- **Premium Dashboard** — A state-of-the-art Next.js 16 interface with interactive charts and real-time polling.

> For a technical deep-dive into security and performance metrics, see the [Project Report](assets/docs/PROJECT_REPORT.md).

---

## Platform Usage

Sentinel is designed for both high-productivity web usage and heavy-duty programmatic integration.

- **Web Experience**: Manage segments, design campaigns, and view live analytics at [dashboard.thesentinel.site](https://dashboard.thesentinel.site).
- **API First**: Every platform feature is exposed via our robust REST API. Reference the [API Usage Guide](assets/docs/API_USAGE_GUIDE.md) for endpoint details and `curl` examples.

---

## API Reference

The Sentinel API is organized around REST. All requests must be authenticated using the `X-API-Key` header.

| Category | Documentation Link |
| :--- | :--- |
| **Authentication** | [Auth & Key Mgmt](assets/docs/API_USAGE_GUIDE.md#1-create-a-user-account) |
| **Campaigns** | [Lifecycle & Stats](assets/docs/API_USAGE_GUIDE.md#campaign-management) |
| **Segments** | [Audience Mgmt](assets/docs/API_USAGE_GUIDE.md#segment-management) |
| **AI Services** | [GenAI Features](assets/docs/API_USAGE_GUIDE.md#generate-email-content-with-ai-gemini-lambda) |

---

## License

This project is licensed under the MIT License - see the [LICENSE](.github/LICENSE.md) file for details.

---

<div align="center">
  <p align="center">
    Built with precision by the <b>Sentinel Team</b>
    <br />
    <br />
    <a href="#sentinel">
      <img src="https://img.shields.io/badge/-Back%20to%20Top-eaecef?style=flat-square&logo=gitbook&logoColor=bcbcbc" alt="Back to Top">
    </a>
  </p>
</div>
