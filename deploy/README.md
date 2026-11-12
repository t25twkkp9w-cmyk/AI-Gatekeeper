# Render cohort demo

Deploy the root Dockerfile as one paid Render web service with one instance.
Next.js and FastAPI bind only to loopback inside the container. Nginx exposes
Render's PORT and requires HTTP Basic authentication for the UI and API.
Render terminates HTTPS. Only /healthz is public and contains configuration
booleans, never keys or case data.

Attach a 1 GB persistent disk at /var/data. Set GATEKEEPER_DATA_DIR=/var/data.
The hosted service starts with synthetic seed cases. Local case databases are
not uploaded. Keep one instance because SQLite checkpoints share this disk.

Set OPENAI_API_KEY and LANGSMITH_API_KEY as Render secrets. Set DEMO_USERNAME
to cohort and enter a unique DEMO_PASSWORD of at least 16 characters.
The username permits letters, digits, underscores and hyphens only.
Set OPENAI_MODEL=gpt-4.1-mini and LANGSMITH_PROJECT=ai-gatekeeper-hosted.
Startup enforces live mode and LangSmith tracing and refuses missing secrets.
Do not use NEXT_PUBLIC variables for keys. Never commit .env or runtime data.

Use /healthz for the health check and disable automatic deploys initially.
render.yaml describes the same configuration for Blueprint deployment.
Review the displayed Render compute and disk charges before creating service.

This shared password protects a synthetic cohort demonstration. It does not
provide independent reviewer identities: the existing persona selector remains
a demo control. Anyone given the password can run billable model requests and
change demo cases. Do not add real patient or enterprise confidential data.

After deployment verify unauthenticated UI/API requests return 401, valid
credentials permit access, a synthetic case reaches human review, and LangSmith
receives nested model/tool spans. Restart and verify the case survives. Do not
approve a case merely to validate hosting. Docker image build and gateway
runtime checks must pass on Render before declaring this deployment ready.
