# 🚀 Multi-Agent Productivity Assistant

A GCP-native, multi-agent assistant built with **LangGraph**, **FastAPI**, and **Vertex AI Gemini 1.5 Pro**. It uses a Supervisor-Worker architecture to coordinate Notes, Tasks, Scheduling, and Knowledge querying agents over a Cloud SQL PostgreSQL database.

## Prerequisites
- A Google Cloud Project with the **Vertex AI API** enabled.
- A **Cloud SQL PostgreSQL** database (or a local PostgreSQL instance for development).
- GCP Service Account credentials with access to Vertex AI.

## Local Development

1. **Set up the Environment:**
   Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   Fill in your `GCP_PROJECT_ID`, `DATABASE_URL`, and pointing `GOOGLE_APPLICATION_CREDENTIALS` to your service account JSON file.

2. **Run the Application locally:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```
   The API will be available at `http://localhost:8080`.
   OpenAPI Swagger docs are at `http://localhost:8080/docs`.

## Deployment to Google Cloud Run

This project is fully containerised and ready for Google Cloud Run deployment.

### Using Google Cloud SDK (`gcloud`):

1. **Build the container and submit it to Artifact Registry:**
   ```bash
   gcloud builds submit --tag gcr.io/your-gcp-project-id/productivity-agent
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy productivity-agent \
       --image gcr.io/your-gcp-project-id/productivity-agent \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --set-env-vars GCP_PROJECT_ID=your-gcp-project-id \
       --set-secrets=DATABASE_URL=your-secret-name:latest
   ```

### Architecture Highlights
- **Supervisor Agent:** Decomposes requests into a Graph execution plan.
- **MCP-Style Tools Layer:** Agent actions map cleanly to backend CRUD tools, making them extremely easy to migrate into full external MCP servers later.
- **Robust Exception Handling:** Gracefully handles LLM parsing issues and GCP Auth misses.
