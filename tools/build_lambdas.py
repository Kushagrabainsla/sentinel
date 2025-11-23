#!/usr/bin/env python3
import os
import shutil
import subprocess
import zipfile
import sys

# Configuration
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SERVICES_DIR = os.path.join(PROJECT_ROOT, 'services')
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'infra', 'modules', 'lambdas', '.artifacts')
COMMON_FILE = os.path.join(SERVICES_DIR, 'common.py')

# List of lambdas to build (directory names in services/)
LAMBDAS = [
    'generate_email',
    'start_campaign',
    'send_worker',
    'tracking_api',
    'segments_api',
    'authorizer',
    'auth_api'
]

def build_lambda(lambda_name):
    print(f"Building {lambda_name}...")
    source_dir = os.path.join(SERVICES_DIR, lambda_name)
    build_dir = os.path.join(PROJECT_ROOT, 'build', lambda_name)
    zip_path = os.path.join(ARTIFACTS_DIR, f"{lambda_name}.zip")

    # Clean previous build
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # Copy source files
    for item in os.listdir(source_dir):
        s = os.path.join(source_dir, item)
        d = os.path.join(build_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # Copy common.py
    shutil.copy2(COMMON_FILE, os.path.join(build_dir, 'common.py'))

    # Install dependencies
    requirements_file = os.path.join(source_dir, 'requirements.txt')
    if os.path.exists(requirements_file):
        print(f"  Installing dependencies for {lambda_name}...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            '-r', requirements_file, 
            '-t', build_dir,
            '--quiet'
        ])

    # Zip artifacts
    print(f"  Zipping to {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arcname)

    # Cleanup build dir
    shutil.rmtree(build_dir)
    print(f"  Done: {lambda_name}")

def main():
    # Ensure artifacts directory exists
    if not os.path.exists(ARTIFACTS_DIR):
        os.makedirs(ARTIFACTS_DIR)

    for lambda_name in LAMBDAS:
        try:
            build_lambda(lambda_name)
        except Exception as e:
            print(f"Error building {lambda_name}: {e}")
            sys.exit(1)

    # Clean up build root
    build_root = os.path.join(PROJECT_ROOT, 'build')
    if os.path.exists(build_root):
        shutil.rmtree(build_root)

    print("\nAll lambdas built successfully!")

if __name__ == '__main__':
    main()
