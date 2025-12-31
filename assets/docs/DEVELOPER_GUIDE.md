# Sentinel Developer Guide

Detailed information for developers contributing to or self-hosting the Sentinel platform.

---

## 🏗️ Architecture Deep Dive

Sentinel uses a fully serverless architecture built primarily on AWS. For a comprehensive breakdown of the system components, data flow diagrams, and scalability design, refer to the [Technical Project Report](PROJECT_REPORT.md).

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
└── README.md                 # Project overview
```

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

## 🚀 Getting Started (Local Setup)

### Prerequisites

- **AWS Account** with administrative permissions
- **Terraform** >= 1.6
- **Python** 3.12
- **Node.js** >= 20
- **AWS CLI** configured with active credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kushagrabainsla/sentinel.git
   cd sentinel
   ```

2. **Install Backend Dependencies** (Optional for local linting)
   ```bash
   # Each service can be managed individually
   cd services/auth_api
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**
   ```bash
   cd ui
   npm install
   ```

### Configuration

1. **Infrastructure Variables**: Create `infra/terraform.tfvars`:
   ```hcl
   region                = "us-east-1"
   enable_global_tables  = true
   ses_from_address      = "hello@yourdomain.com"
   ```

2. **AI Secrets**: Store your Gemini API key in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret --name sentinel/gemini-api-key --secret-string "YOUR_KEY"
   ```

---

## 🔧 Development Workflow

### Local UI Development
```bash
cd ui
npm run dev
```

### Linting & Formatting
```bash
cd ui
npm run lint
```

### Environment Variables

**Backend (Runtime)**
- `USERS_TABLE`, `CAMPAIGNS_TABLE`, `SEGMENTS_TABLE`, `EVENTS_TABLE`
- `GEMINI_API_KEY_SECRET`
- `SES_FROM_ADDRESS`
- `TRACKING_BASE_URL`

**Frontend (Build-time)**
- `NEXT_PUBLIC_API_URL`

---

## 🏗️ Deployment

### 1. Provision Infrastructure
```bash
cd infra
terraform init
terraform apply
```

### 2. Deploy Frontend
```bash
cd ui
npm run build
# Deploy output to Amplify or S3/CloudFront
```

---

## 🤝 Contributing Guidelines

1. **Branching**: Always branch off from `staging`.
2. **Commit Style**: Use descriptive, atomic commits.
3. **PR Process**: All changes to `main` must come via a PR from `staging`.
4. **Code Quality**: Ensure linting passes and infrastructure changes are planned via Terraform.
