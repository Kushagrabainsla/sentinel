# Issue: Next.js App on AWS Amplify Cannot Access Environment Variables at Runtime

When deploying a Next.js app on AWS Amplify, you may encounter the following problem:

- The app builds successfully and environment variables are available during build.
- At runtime (especially in SSR or API routes), environment variables such as API keys and secrets are missing.
- CloudWatch logs show errors like `process.env.MY_SECRET is undefined`.
- The app works locally, but fails to connect to backend or third-party services in production.

**Summary:**
Amplify environment variables are injected at build time, not at runtime. This causes runtime errors in Next.js SSR/API routes when trying to access secrets or API keys.
