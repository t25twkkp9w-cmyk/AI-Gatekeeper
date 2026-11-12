# Password-protected Render Free demo

Deploy the root Dockerfile on Free without a disk. Set GATEKEEPER_DATA_DIR=/tmp/gatekeeper-data and health check /healthz.
Set OPENAI_API_KEY, LANGSMITH_API_KEY and DEMO_PASSWORD in Render. Choose a unique password of at least 16 characters. DEMO_USERNAME=cohort. Live AI and tracing are enforced at startup. LANGSMITH_PROJECT=ai-gatekeeper-hosted.
Nginx protects the UI and API. Only health configuration is public. This shared password protects a synthetic demo, not independent reviewer identities. Authenticated users can trigger billable model calls. Cases may reset after restarts or redeploys. Verify the Docker build, authentication, synthetic workflow and LangSmith after deployment.
