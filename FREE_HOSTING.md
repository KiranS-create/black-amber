# Zero-Cost Free Cloud Hosting Guide ($0/Month)

> **Primary Cloud Deployment**: [Render Web Service (https://aegistrace.onrender.com)](https://aegistrace.onrender.com)  
> **Active Edge Mirror**: [`https://joan-enforcement-whatever-looks.trycloudflare.com`](https://joan-enforcement-whatever-looks.trycloudflare.com)  
> **Deployment Status**: `DEPLOYED_AND_BROWSER_VERIFIED`  
> **Authentication**: `admin` / `admin` (Autofill enabled)  
> **Platform Scope**: Web Workstation & API Gateway.  
> **Platform Status**: Desktop application (Windows `.exe`, macOS `.dmg`) and Android mobile packaging are **DEFERRED TO FUTURE WORKSTREAM**. All product capabilities are designed for zero-cost web deployment.

---

## 0. Active Cloud Deployments (Zero-Cost Free Tier)

AegisTrace is deployed and verified live across free cloud tiers:

- **Primary Target (Render)**: [`https://aegistrace.onrender.com`](https://aegistrace.onrender.com)
  - Managed via Infrastructure as Code: `render.yaml` (Blueprint v1).
  - Multi-stage Docker container (Node 20 frontend build + Python 3.11 PQC backend).
  - Dynamic port binding: listens on `0.0.0.0:$PORT` (honoring Render's dynamic port assignment).
  - Health check endpoint: `/ready` (verifies database, crypto provider, and ledger).
- **Active Edge Mirror**: [`https://joan-enforcement-whatever-looks.trycloudflare.com`](https://joan-enforcement-whatever-looks.trycloudflare.com)
  - Global Anycast CDN, TLS 1.3, Strict-Transport-Security.
- **Verification Reports**:
  - Runbook: [HOSTED_DEMO_RUNBOOK.md](HOSTED_DEMO_RUNBOOK.md)
  - Validation: [LIVE_DEPLOYMENT_VALIDATION.md](LIVE_DEPLOYMENT_VALIDATION.md)

---

## 1. Quick Summary of Free Hosting Options

AegisTrace can be hosted publicly at **$0/month indefinitely** using free tiers of modern container and edge hosting providers:

| Provider Option | Architecture | Free Resources | Ideal For |
|---|---|---|---|
| **Option A: Hugging Face Spaces** | Single Docker Container | 2 vCPU, 16 GB RAM | **Best for Hackathon Judging** (fastest setup, generous RAM) |
| **Option B: Render Free Tier** | Single Docker Container | 0.5 vCPU, 512 MB RAM | All-in-one web service |
| **Option C: Vercel / Cloudflare + Render** | Split Frontend & Backend | Edge CDN + Container | Enterprise-style decoupled architecture |

---

## 2. Option A: Hugging Face Spaces (Recommended for SIH Judging)

Hugging Face Spaces provides 16 GB RAM for Docker apps for free:

1. Create a free account at [huggingface.co](https://huggingface.co).
2. Click **New Space** -> Select **Docker** as Space SDK -> **Blank**.
3. Push your repository to the space:
   ```bash
   git remote add space https://huggingface.co/spaces/<username>/<space-name>
   git push space main
   ```
4. In Space Settings -> **Variables and secrets**, add:
   ```env
   DEMO_AUTH_ENABLED=true
   DEMO_USERNAME=admin
   DEMO_PASSWORD=admin
   ```
5. Hugging Face automatically detects the multi-stage `Dockerfile`, compiles the React frontend, runs the FastAPI backend on port 8000, and gives you a public HTTPS URL.

---

## 3. Option B: Render Free Web Service

1. Fork or push this repository to GitHub.
2. Log in to [Render.com](https://render.com) -> **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Select **Docker** as the environment.
5. Set environment variables:
   ```env
   SIH_HOST=0.0.0.0
   SIH_PORT=8000
   DEMO_AUTH_ENABLED=true
   DEMO_USERNAME=admin
   DEMO_PASSWORD=admin
   CORS_ORIGINS=*
   ```
6. Click **Create Web Service**.

### Preventing Free Tier Sleep (Keepalive)
Free tier web services sleep after 15 minutes of inactivity. Set up a free ping monitor (e.g. [Cron-Job.org](https://cron-job.org) or [UptimeRobot.com](https://uptimerobot.com)) calling `GET https://<your-service>.onrender.com/ready` every 10 minutes to keep the container awake during the evaluation period.

---

## 4. Option C: Split Deployment (Cloudflare Pages + Render)

- **Frontend**: Deploy `apps/web` on Cloudflare Pages (Free global edge CDN).
  - Build command: `npm run build`
  - Output directory: `dist`
  - Environment variable: `VITE_API_URL=https://<your-render-service>.onrender.com`
- **Backend**: Deploy Python backend on Render as a Web Service.

---

For detailed step-by-step instructions, see the complete guide in [docs/deployment/FREE_HOSTING.md](docs/deployment/FREE_HOSTING.md).
