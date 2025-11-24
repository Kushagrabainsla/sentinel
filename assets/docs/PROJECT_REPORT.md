# Cloud Computing Masters Project: Sentinel

**Team Members:** Kushagra Bainsla, Yash, Tejas
**Date:** November 21, 2024

---

## 1. Executive Summary

**Sentinel** is a cloud-native, serverless email marketing and analytics platform designed for high scalability and cost-efficiency. Unlike traditional email services that charge high monthly fees regardless of usage, Sentinel utilizes a pay-per-use serverless architecture on AWS, making it ideal for startups and developers who need powerful email capabilities without the overhead.

The platform integrates **Generative AI (Google Gemini)** to assist users in creating compelling email content, solving the "writer's block" problem in marketing campaigns.

---

## 2. Concept & Use Case

### Problem Statement
Small businesses and developers often struggle with existing email marketing tools because they are:
1.  **Expensive:** Fixed monthly subscriptions even for low volumes.
2.  **Complex:** Bloated interfaces with steep learning curves.
3.  **Disconnected:** Hard to integrate programmatically into custom applications.
4.  **Content Heavy:** Creating engaging email copy is time-consuming and difficult.

### Proposed Solution
Sentinel provides a **Serverless Email Marketing SaaS** that offers:
*   **Usage-based pricing:** Built on AWS Lambda and DynamoDB, incurring near-zero costs when idle.
*   **Developer-first API:** Full programmatic control over campaigns, segments, and tracking.
*   **AI-Powered Content:** Integrated GenAI to instantly generate professional email copy.
*   **Real-time Analytics:** Granular tracking of opens, clicks, and engagement.

### Target Users
*   **SaaS Developers:** Who need to embed email marketing into their apps.
*   **Startups:** Who need a cost-effective, scalable solution.
*   **Growth Hackers:** Who rely on data-driven campaigns and automation.

---

## 3. Cloud Architecture & Technical Design

### High-Level Architecture
Sentinel employs a fully **Serverless Microservices Architecture** on AWS.

*   **Frontend:** Next.js application hosted on **AWS Amplify** with global CDN distribution.
*   **API Layer:** **Amazon API Gateway (HTTP API)** serves as the unified entry point, routing requests to specific microservices.
*   **Compute:** **AWS Lambda** (Python) functions handle all business logic, ensuring automatic scaling from zero to thousands of concurrent requests.
*   **Data Persistence:** **Amazon DynamoDB Global Tables** provide multi-region active-active replication for high availability and low latency.
*   **Messaging & Queues:** **Amazon SQS** decouples the campaign initiation from the sending process, allowing for burst handling and rate limiting.
*   **Email Delivery:** **Amazon SES** (Simple Email Service) handles the actual email transmission with high deliverability, DKIM signing, and custom domains.
*   **Scheduling:** **Amazon EventBridge Scheduler** manages scheduled campaigns (e.g., "Send next Tuesday").
*   **AI Integration:** **Google Gemini API** is integrated via a secure Lambda function for content generation.

### Architecture Diagram
![Architecture Diagram](/assets/images/sentinel-architecture-diagram.png?q=1)

### Key Cloud Services Used
1.  **Compute:** AWS Lambda (Python 3.11)
2.  **Database:** Amazon DynamoDB (Global Tables)
3.  **API Management:** Amazon API Gateway
4.  **Storage:** Amazon S3 (Assets & Tracking Pixels)
5.  **Messaging:** Amazon SQS
6.  **Email:** Amazon SES
7.  **Scheduling:** Amazon EventBridge Scheduler
8.  **Hosting:** AWS Amplify
9.  **Security:** AWS IAM, AWS Secrets Manager

---

## 4. Prototype Implementation

### Features Implemented
*   **User Authentication:** Secure registration and login with API key generation.
*   **Campaign Management:** Create, update, delete, and schedule email campaigns.
*   **Audience Segmentation:** Manage contact lists and segments.
*   **AI Content Generation:** Generate email subjects and bodies using Gemini AI based on tone and goal.
*   **Email Sending:** High-volume sending via SES with rate limiting.
*   **Tracking:** Invisible pixel tracking for opens and redirect tracking for link clicks.
*   **Dashboard:** Next.js UI for managing all aspects of the platform.

### Infrastructure as Code (IaC)
The entire infrastructure is defined in **Terraform**, ensuring reproducibility and modularity.
*   **Modules:** `iam`, `network`, `lambdas`, `dynamodb`, `api`, `queues`, `s3_assets`, `ses`.
*   **State Management:** Remote state stored in S3 with locking.

### CI/CD
**GitHub Actions** pipelines handle:
1.  **Linting & Testing:** Python (flake8) and Terraform (fmt/validate).
2.  **Deployment:** Automatic deployment of Terraform infrastructure and Lambda code on push to `main`.

---

## 5. Cost & Resource Analysis

### Cloud Cost Estimation (Monthly)
*Based on 100,000 emails/month and 10,000 active users.*

| Service | Metric | Estimated Cost |
| :--- | :--- | :--- |
| **AWS Lambda** | 2M invocations, 128MB memory | ~$0.40 |
| **Amazon API Gateway** | 2M requests | ~$2.00 |
| **Amazon DynamoDB** | 5GB storage, 2M R/W units | ~$1.50 |
| **Amazon SES** | 100k emails | ~$10.00 |
| **Amazon S3** | 1GB storage, 100k GETs | ~$0.05 |
| **AWS Amplify** | Build minutes & hosting | ~$0.00 (Free Tier) |
| **Google Gemini** | AI API calls | ~$0.00 (Free Tier) |
| **Total** | | **~$13.95 / month** |

*Note: Many of these fall within the AWS Free Tier for the first 12 months.*

### Scalability Strategy
*   **Stateless Compute:** Lambda functions scale horizontally automatically.
*   **NoSQL Database:** DynamoDB handles massive scale without managing connections.
*   **Queue Buffering:** SQS prevents system overload during massive campaign blasts by smoothing out the load.

---

## 6. Challenges & Mitigations

| Challenge | Mitigation |
| :--- | :--- |
| **Cold Starts** | Used Python (lightweight runtime) and kept dependencies minimal. |
| **Email Deliverability** | Implemented DKIM, SPF, and DMARC. Used SES reputation dashboard. |
| **Distributed Tracing** | (Planned) Implement AWS X-Ray for end-to-end request tracking. |
| **SES Rate Limits** | Implemented SQS to buffer requests and respect SES sending limits. |

---

## 7. Roadmap & Future Work

1.  **A/B Testing:** Automatically split traffic between two email variations.
2.  **SMS & Push Notifications:** Expand beyond email to omni-channel marketing.
3.  **Visual Email Builder:** Drag-and-drop editor for HTML emails.
4.  **Advanced Analytics:** Heatmaps for click tracking and user geography.

---

## 8. AI/ML Relevance

Sentinel leverages **Google's Gemini Pro** model to democratize professional copywriting.
*   **Integration:** A dedicated Lambda function (`generate_email`) securely calls the Gemini API.
*   **Prompt Engineering:** Custom system prompts ensure the AI generates HTML-ready, spam-compliant content tailored to specific audience segments.
*   **Value:** Reduces campaign creation time from hours to minutes.
