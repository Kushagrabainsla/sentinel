<img src="/assets/images/sentinel-logo.png" alt="Sentinel Logo" width="60" height="60" align="left" style="margin-right: 15px; border: 2px solid #e1e5e9; border-radius: 8px; padding: 4px;">

# Sentinel

### A Cloud-Native Email Marketing & Analytics SaaS Platform

[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB%20%7C%20SES-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](.github/LICENSE.md)

> **Serverless email marketing platform built on AWS with real-time analytics, AI-powered content generation, and multi-region deployment.**

[API Documentation](assets/docs/API_USAGE_GUIDE.md) • [Project Details](https://docs.google.com/document/d/1O5GahoZqVnzIXXUuxENSTFhnbGMnF5W2S_Fg0H7R8Ik/edit?usp=sharing)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#️-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Deployment](#deployment)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## ✨ Features

### Core Functionality
- 🔐 **Custom API Authentication** - Secure API key-based access with user management
- 🛡️ **Enhanced Authentication Guard** - Client-side route protection with automatic redirects for authenticated and unauthenticated users
- 📧 **Email Campaign Management** - Create, schedule, and track email campaigns
- 📊 **Advanced Real-time Analytics** - Comprehensive analytics dashboard with temporal patterns, user segmentation, device/browser/OS distribution, geographic insights, and link performance tracking
- 🎯 **Proxy Open Detection** - Intelligent classification of email client prefetch opens vs. actual human opens for accurate engagement metrics
- 👥 **Segment Management** - Organize recipients into targeted segments
- 🤖 **AI-Powered Content Generation** - Generate email content using Google Gemini AI
- 📈 **AI Campaign Insights** - AI-generated analytics and actionable performance recommendations

### Security & Performance
- 🔒 **HTML Content Sanitization** - Automatic XSS and phishing link prevention with whitelist-based filtering
- 📊 **Comprehensive Monitoring** - 30+ CloudWatch alarms for Lambda, DynamoDB, API Gateway, and SQS
- 📊 **Queue Depth Monitoring** - CloudWatch alarms for proactive SQS queue management
- ⚡ **Optimized Concurrency** - Batch processing with controlled concurrency (14 emails/sec via 2×7 batches)
- 🔍 **URL Validation** - Blocks dangerous schemes (javascript:, data:) and obfuscated URLs
- 🚨 **Dead Letter Queue Alerts** - Immediate notifications for failed email deliveries
- 🔄 **Exponential Backoff Retry** - Intelligent retry logic for transient errors with jitter
- 🛡️ **Error Classification** - Automatic distinction between permanent and transient failures
- 🚦 **API Throttling** - Rate limiting at 1000 req/sec with 2000 burst capacity


### Technical Features
- ⚡ **Scalable Architecture** - Auto-scaling serverless infrastructure with reserved concurrency
- 🌍 **Multi-region Support** - Global DynamoDB tables across 3 regions (us-east-1, eu-west-1, ap-southeast-1)
- 🔄 **Event-Driven Processing** - SQS-based asynchronous email delivery with batch size optimization
- 📱 **Modern Web UI** - Next.js 16 frontend with real-time dashboards and interactive charts
- 🎯 **Advanced Link Tracking** - Automatic link tracking with top clicked links analysis and click-to-open rate metrics
- 🔔 **Comprehensive Event Processing** - Track delivery, opens, clicks, bounces, and unsubscribes with temporal and engagement analysis
- 📈 **Interactive Visualizations** - Area charts for temporal patterns, pie charts for distributions, and custom tooltips for detailed insights
- ⏱️ **Response Time Metrics** - Track average time-to-open and time-to-click for campaign optimization
- 🔍 **Observability** - CloudWatch Logs with 30-day retention and structured access logging
- 🛡️ **Fault Tolerance** - Automatic failover, retry logic, and circuit breaker patterns

---

## 🏗️ Architecture

![Sentinel System Architecture](/assets/images/sentinel-architecture-diagram.png?q=1)

### System Components

**Frontend Layer**
- Next.js 16 web application with TypeScript
- Deployed on AWS Amplify
- Real-time analytics dashboards with Recharts
- Rich text editor with TipTap

**API Layer**
- AWS API Gateway (REST API)
- Custom domain: `api.thesentinel.site`
- Lambda authorizer for API key validation
- Rate limiting and request validation

**Compute Layer**
- AWS Lambda (Python 3.12)
- Modular microservices architecture:
  - `auth_api` - User authentication and management
  - `campaigns_api` - Campaign CRUD operations
  - `segments_api` - Segment management
  - `tracking_api` - Email event tracking
  - `generate_email` - AI content generation
  - `generate_insights` - AI analytics insights
  - `send_worker` - Email delivery worker
  - `start_campaign` - Campaign scheduler

**Data Layer**
- DynamoDB Global Tables (multi-region replication)
  - Users, Campaigns, Segments, Events, Link Mappings
- S3 for static assets
- AWS Secrets Manager for API keys

**Messaging & Events**
- SQS for asynchronous email processing with DLQ
- EventBridge Scheduler for scheduled campaigns
- SES for email delivery with DKIM (rate-limited to 14 emails/sec via batch processing)

**Monitoring & Observability**
- CloudWatch Logs with 30-day retention
- 30+ CloudWatch alarms for proactive monitoring
- SNS notifications for critical alerts

---

## 🛠 Tech Stack

### Backend
- **Language**: Python 3.12
- **Cloud Provider**: AWS
- **Infrastructure as Code**: Terraform
- **Compute**: AWS Lambda
- **Database**: DynamoDB (Global Tables)
- **Email Service**: AWS SES
- **Queue**: AWS SQS
- **API Gateway**: AWS API Gateway
- **AI/ML**: Google Gemini AI

### Frontend
- **Framework**: Next.js 16
- **Language**: TypeScript
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4
- **Charts**: Recharts
- **Rich Text Editor**: TipTap
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form + Zod

### DevOps
- **IaC**: Terraform
- **CI/CD**: GitHub Actions
- **Deployment**: AWS Amplify (Frontend), Lambda (Backend)
- **State Management**: Terraform S3 Backend

---

## 🚀 Getting Started

### Prerequisites

- **AWS Account** with appropriate permissions
- **Terraform** >= 1.6
- **Python** 3.12
- **Node.js** >= 20
- **AWS CLI** configured with credentials
- **Domain** for SES (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   ```

2. **Install backend dependencies**
   ```bash
   # Each Lambda function has its own requirements
   cd services/auth_api
   pip install -r requirements.txt
   cd ../..
   ```

3. **Install frontend dependencies**
   ```bash
   cd ui
   npm install
   cd ..
   ```

### Configuration

1. **Set up Terraform variables**
   
   Create `infra/terraform.tfvars`:
   ```hcl
   region                = "us-east-1"
   enable_global_tables  = true
   global_table_regions  = ["us-east-1", "eu-west-1", "ap-southeast-1"]
   ses_from_address      = "hello@yourdomain.com"
   ```

2. **Configure AWS Secrets Manager**
   
   Store your Google Gemini API key:
   ```bash
   aws secretsmanager create-secret \
     --name sentinel/gemini-api-key \
     --secret-string "YOUR_GEMINI_API_KEY"
   ```

3. **Set up SES Domain**
   
   Verify your domain in AWS SES and update the domain in `infra/main.tf`:
   ```hcl
   module "ses" {
     source = "./modules/ses"
     domain = "yourdomain.com"
   }
   ```

### Deployment

1. **Initialize Terraform**
   ```bash
   cd infra
   terraform init
   ```

2. **Plan infrastructure changes**
   ```bash
   terraform plan
   ```

3. **Deploy infrastructure**
   ```bash
   terraform apply
   ```

4. **Deploy frontend**
   ```bash
   cd ../ui
   npm run build
   # Deploy to AWS Amplify or your preferred hosting
   ```

5. **Get API endpoint**
   ```bash
   cd ../infra
   terraform output api_endpoint
   ```

---

## 💻 Usage

### Quick Start

1. **Register a new user**
   ```bash
   curl -X POST https://api.thesentinel.site/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Your Name",
       "email": "your.email@example.com",
       "password": "SecurePassword123!"
     }'
   ```

2. **Create an email segment**
   ```bash
   curl -X POST https://api.thesentinel.site/v1/segments \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY" \
     -d '{
       "name": "Newsletter Subscribers",
       "emails": ["user1@example.com", "user2@example.com"]
     }'
   ```

3. **Create and send a campaign**
   ```bash
   curl -X POST https://api.thesentinel.site/v1/campaigns \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY" \
     -d '{
       "name": "Welcome Campaign",
       "type": "I",
       "delivery_type": "SEG",
       "subject": "Welcome!",
       "html_body": "<h1>Welcome to our platform!</h1>",
       "segment_id": "YOUR_SEGMENT_ID",
       "from_email": "hello@yourdomain.com",
       "from_name": "Your Company"
     }'
   ```

For detailed API usage, see the [API Usage Guide](assets/docs/API_USAGE_GUIDE.md).

---

## 📚 API Reference

### Base URL
```
https://api.thesentinel.site/v1
```

### Authentication
All authenticated endpoints require an API key in the header:
```
X-API-Key: YOUR_API_KEY
```

### Main Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `POST /auth/regenerate-key` - Regenerate API key
- `POST /auth/update` - Update user profile

#### Campaigns
- `GET /campaigns` - List all campaigns
- `POST /campaigns` - Create campaign
- `GET /campaigns/{id}` - Get campaign details
- `PUT /campaigns/{id}` - Update campaign
- `DELETE /campaigns/{id}` - Delete campaign
- `GET /campaigns/{id}/events` - Get campaign analytics

#### Segments
- `GET /segments` - List all segments
- `POST /segments` - Create segment
- `GET /segments/{id}` - Get segment details
- `PUT /segments/{id}` - Update segment
- `DELETE /segments/{id}` - Delete segment
- `POST /segments/{id}/emails` - Add emails to segment
- `DELETE /segments/{id}/emails` - Remove emails from segment

#### AI Services
- `POST /generate-email` - Generate email content with AI
- `POST /generate-insights` - Generate campaign insights with AI

#### Tracking (Public)
- `GET /track/open/{tracking_id}` - Track email opens
- `GET /track/click/{tracking_id}` - Track link clicks
- `GET /unsubscribe/{token}` - Unsubscribe handler

For complete API documentation with examples, see [API_USAGE_GUIDE.md](assets/docs/API_USAGE_GUIDE.md).

---

## 📁 Project Structure

```
sentinel/
├── assets/                    # Static assets and documentation
│   ├── docs/                  # Documentation files
│   └── images/                # Images and diagrams
├── infra/                     # Terraform infrastructure
│   ├── modules/               # Terraform modules
│   │   ├── alarms/           # CloudWatch alarms and monitoring
│   │   ├── api/              # API Gateway configuration
│   │   ├── dynamodb/         # DynamoDB tables
│   │   ├── iam/              # IAM roles and policies
│   │   ├── lambdas/          # Lambda functions with log retention
│   │   ├── network/          # VPC and networking
│   │   ├── queues/           # SQS queues with DLQ
│   │   ├── s3_assets/        # S3 buckets
│   │   └── ses/              # SES configuration
│   ├── main.tf               # Main Terraform configuration
│   ├── variables.tf          # Input variables
│   └── outputs.tf            # Output values
├── services/                  # Lambda function source code
│   ├── auth_api/             # Authentication service
│   ├── authorizer/           # API Gateway authorizer
│   ├── campaigns_api/        # Campaign management
│   ├── segments_api/         # Segment management
│   ├── tracking_api/         # Event tracking
│   ├── generate_email/       # AI email generation
│   ├── generate_insights/    # AI insights generation
│   ├── send_worker/          # Email delivery worker
│   ├── start_campaign/       # Campaign scheduler
│   └── common.py             # Shared utilities
├── ui/                        # Next.js frontend
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   ├── public/               # Static files
│   └── package.json          # Frontend dependencies
├── tools/                     # Utility scripts
├── .github/                   # GitHub Actions workflows
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

---

## 🔧 Development

### Local Development

1. **Run frontend locally**
   ```bash
   cd ui
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000)

2. **Lint frontend code**
   ```bash
   cd ui
   npm run lint
   ```

### Environment Variables

**Backend (Lambda)**
- `USERS_TABLE` - DynamoDB users table name
- `CAMPAIGNS_TABLE` - DynamoDB campaigns table name
- `SEGMENTS_TABLE` - DynamoDB segments table name
- `EVENTS_TABLE` - DynamoDB events table name
- `GEMINI_API_KEY_SECRET` - Secrets Manager secret name
- `SES_FROM_ADDRESS` - Default sender email
- `TRACKING_BASE_URL` - Base URL for tracking pixels

**Frontend**
- `NEXT_PUBLIC_API_URL` - API Gateway endpoint

---

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guidelines](.github/CONTRIBUTING.md) for details on how to submit changes.

### Quick Guidelines

- Always branch off from `staging`
- Never push directly to `main` or `staging`
- Keep commits atomic and messages meaningful
- Follow existing code style and conventions
- Update documentation as needed

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](.github/LICENSE.md) file for details.

---

## 🙏 Acknowledgments

- **AWS** for providing the serverless infrastructure
- **Google Gemini AI** for powering content generation
- **Terraform** for infrastructure as code
- **Next.js** team for the amazing frontend framework
- All contributors who have helped improve this project

---

## 📞 Support

- **Documentation**: [API Usage Guide](assets/docs/API_USAGE_GUIDE.md)
- **Project Details**: [Full Documentation](https://docs.google.com/document/d/1O5GahoZqVnzIXXUuxENSTFhnbGMnF5W2S_Fg0H7R8Ik/edit?usp=sharing)

---

<div align="center">


[⬆ Back to Top](#sentinel)

</div>
