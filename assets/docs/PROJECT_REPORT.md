# Cloud Computing Masters Project: Sentinel

**Team Members:** Kushagra Bainsla, Yash, Tejas
**Date:** November 21, 2024
**Repository:** [GitHub - Sentinel](https://github.com/Kushagrabainsla/sentinel)

---

## 1. Executive Summary

**Sentinel** is a cloud-native, serverless email marketing and analytics platform designed for high scalability and cost-efficiency. Unlike traditional email services that charge high monthly fees regardless of usage, Sentinel utilizes a pay-per-use serverless architecture on AWS, making it ideal for startups and developers who need powerful email capabilities without the overhead.

The platform integrates **Generative AI (Google Gemini)** to assist users in creating compelling email content, solving the "writer's block" problem in marketing campaigns.

---

## 2. Concept, Use Case & Motivation

### Problem Statement
Small businesses and developers often struggle with existing email marketing tools because they are:
1.  **Expensive:** Fixed monthly subscriptions even for low volumes (e.g., Mailchimp starts at ~$13/mo even for small lists).
2.  **Complex:** Bloated interfaces with steep learning curves.
3.  **Disconnected:** Hard to integrate programmatically into custom applications.
4.  **Content Heavy:** Creating engaging email copy is time-consuming and difficult.

### Proposed Solution
Sentinel provides a **Serverless Email Marketing SaaS** that offers:
*   **Usage-based pricing:** Built on AWS Lambda and DynamoDB, incurring near-zero costs when idle.
*   **Developer-first API:** Full programmatic control over campaigns, segments, and tracking.
*   **AI-Powered Content:** Integrated GenAI to instantly generate professional email copy.
*   **Real-time Analytics:** Granular tracking of opens, clicks, and engagement.

### Competitive Analysis
| Feature | Sentinel (Our Solution) | [Mailchimp](https://mailchimp.com) | [SendGrid](https://sendgrid.com) |
| :--- | :--- | :--- | :--- |
| **Pricing Model** | Pay-per-use (Serverless) | Monthly Subscription | Monthly / CPM |
| **AI Content Gen** | Native (Gemini Pro) | Add-on / Basic | Basic |
| **Architecture** | Serverless (Lambda) | Monolithic / Microservices | Legacy Infrastructure |
| **Scalability** | Auto-scaling (Zero to Infinity) | Tier-based limits | Tier-based limits |
| **Developer Focus** | High (API First) | Low (UI First) | High |

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
*   **AI Integration:** **Google Gemini API** is integrated via secure Lambda functions for content generation and campaign analytics insights.

### Architecture Diagram
![Architecture Diagram](/assets/images/sentinel-architecture-diagram.png?q=1)

### Public Cloud Applicability
*   **Scalability:** The system uses AWS Lambda and DynamoDB, which automatically scale up to handle traffic spikes (e.g., sending 10k emails in a minute) and scale down to zero when idle.
*   **Security:**
    *   **IAM Roles:** Least privilege access policies for all Lambda functions.
    *   **Secrets Manager:** Secure storage for API keys (Gemini) and database credentials.
    *   **Encryption:** DynamoDB encryption at rest (KMS) and TLS 1.3 in transit.
*   **Reliability:**
    *   **Multi-AZ:** All serverless components (Lambda, DynamoDB, SQS) are inherently distributed across multiple Availability Zones.
    *   **DLQ (Dead Letter Queues):** Failed email jobs are captured in SQS DLQs for replay and analysis.

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
*   **Enhanced Authentication Guard:** Client-side route protection with automatic redirects, preventing unauthorized access to protected routes and seamlessly redirecting authenticated users away from login/register pages.
*   **Campaign Management:** Create, update, delete, and schedule email campaigns.
*   **Audience Segmentation:** Manage contact lists and segments.
*   **AI Content Generation:** Generate email subjects and bodies using Gemini AI based on tone and goal.
*   **AI-Powered Analytics Insights:** Automated campaign performance analysis with actionable recommendations using Gemini AI.
*   **Email Sending:** High-volume sending via SES with rate limiting.
*   **Tracking:** Invisible pixel tracking for opens and redirect tracking for link clicks.
*   **Advanced Analytics Dashboard:** Comprehensive real-time analytics with:
    *   **Temporal Analysis:** Hourly and daily engagement patterns with peak time identification
    *   **User Segmentation:** Engagement-based recipient categorization (highly engaged, moderately engaged, low engagement)
    *   **Multi-dimensional Metrics:** Device, browser, OS, and geographic distribution analysis
    *   **Link Performance:** Top clicked links tracking with detailed click counts
    *   **Response Time Analytics:** Average time-to-open and time-to-click metrics
    *   **Interactive Visualizations:** Area charts, pie charts, and bar charts with custom tooltips using Recharts
*   **Dashboard:** Next.js UI for managing all aspects of the platform with real-time analytics.

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

### Resource Estimation for Productization
To take Sentinel from a prototype to a production-ready SaaS product, the following resources would be required:

*   **Engineering Team:**
    *   2 Full-stack Developers (Feature development)
    *   1 DevOps Engineer (Security, Compliance, Multi-region rollout)
*   **Infrastructure:**
    *   Production AWS Account (Separate from Dev/Staging)
    *   Dedicated IP Addresses for SES (to ensure high sender reputation) - ~$25/month/IP
*   **Compliance:**
    *   GDPR/CCPA Compliance audit
    *   SOC 2 Type II certification (for enterprise clients)

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

1.  **SMS & Push Notifications:** Expand beyond email to omni-channel marketing.
2.  **Visual Email Builder:** Drag-and-drop editor for HTML emails.
3.  **Advanced Analytics Enhancements:** Heatmaps for click tracking and enhanced user geography reports.
4.  **Email Templates Library:** Pre-built, customizable templates for faster campaign creation.
5.  **Smart Segments:** Dynamic audience segmentation based on engagement patterns and behavior.

---

## 8. AI/ML Relevance

Sentinel leverages **Google's Gemini AI** (Gemini 2.5 Flash) in two critical areas to enhance the email marketing workflow. The AI integration was a collaborative effort: Yash and Tejas developed the initial Python scripts for AI content generation and analytics, while Kushagra refactored these into production-ready, scalable Lambda functions with proper error handling, API integration, and security controls.

### 8.1 AI-Powered Content Generation (`generate_email`)
*   **Development:** Initial scripts developed by Yash and Tejas, then migrated to production Lambda by Kushagra.
*   **Integration:** A dedicated Lambda function securely calls the Gemini API with proper error handling and retry logic.
*   **Prompt Engineering:** Custom system prompts ensure the AI generates HTML-ready, spam-compliant content tailored to specific audience segments, tone (professional, casual, urgent), and campaign goals.
*   **Security:** API keys stored in AWS Secrets Manager with IAM-based access control.
*   **Value:** Reduces campaign creation time from hours to minutes, democratizing professional copywriting for all users regardless of marketing expertise.

### 8.2 AI-Powered Campaign Analytics (`generate_insights`)
*   **Development:** Analytics engine co-developed by Yash and Tejas, productionized as a Lambda microservice by Kushagra.
*   **Integration:** A dedicated Lambda function that processes campaign performance data and generates intelligent insights via Gemini API.
*   **Intelligent Analysis:** The AI examines comprehensive campaign metrics including:
    *   **Engagement Metrics:** Open rates, unique opens, click-through rates, unique clicks
    *   **Timing Analysis:** Average time to open, average time to click, temporal patterns
    *   **Event Distribution:** Breakdown of sent, delivered, opened, clicked, bounced, and unsubscribed events
    *   **Comparative Benchmarks:** Performance relative to industry standards and historical campaigns
*   **Structured Output:** Returns a comprehensive JSON report with:
    *   **Executive Summary:** High-level campaign performance overview with key takeaways
    *   **Key Strengths:** Identifies what worked well (e.g., subject line effectiveness, optimal send time)
    *   **Areas for Improvement:** Data-driven identification of weaknesses and missed opportunities
    *   **Actionable Recommendations:** 3 specific, concrete, and implementable suggestions with examples for optimizing the next campaign
*   **API Integration:** Exposed via API Gateway endpoint, allowing both dashboard and programmatic access to insights.
*   **Value:** Transforms raw analytics data into strategic, actionable insights, enabling data-driven decision-making without requiring deep marketing expertise or data analysis skills. Essentially provides every user with an AI marketing analyst.
