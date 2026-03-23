# AI Quiz Tutor Full Deployment Runbook

This guide is a start-to-finish checklist for:
- GitHub Actions backend auto-deploy to DigitalOcean
- DigitalOcean droplet setup
- Vercel frontend deployment
- Cloudflare DNS connection

Follow steps in order.

## 0) What not to use

Do not use GitHub Deploy Keys for this setup.
- Deploy keys are tied to a single repository and can be confusing for this flow.
- Your project already uses GitHub Actions with repository secrets.

Use GitHub Actions repository secrets instead.

## 1) Confirm local repo is pushed

From your local machine in the repo root:

    git status
    git push origin main

Expected:
- Working tree clean
- Branch up to date with origin/main

## 2) SSH key setup basics

You already created:
- Private key: C:\Users\Asus\.ssh\id_ed25519
- Public key: C:\Users\Asus\.ssh\id_ed25519.pub

Show public key (for DigitalOcean SSH key page):

    Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" -Raw

Show private key (for GitHub secret DO_SSH_KEY):

    Get-Content "$env:USERPROFILE\.ssh\id_ed25519" -Raw

Important:
- Public key goes to DigitalOcean
- Private key goes to GitHub Actions secret DO_SSH_KEY
- Never post private key in chat or screenshots

## 3) DigitalOcean droplet settings

Create a normal CPU droplet (not GPU):
- Region: closest to your users
- OS: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
- Size: 4 GB RAM / 2 vCPU
- Auth: SSH key selected
- Hostname: quiz-tutor-backend

After creation, note droplet IP.

## 4) GitHub repository secrets (this replaces Deploy Keys)

Go to GitHub:
Repository -> Settings -> Secrets and variables -> Actions -> New repository secret

Create/update these secrets exactly:
- DO_HOST = 165.22.98.154
- DO_USER = root
- DO_SSH_KEY = full private key content from id_ed25519
- GHCR_USERNAME = your GitHub username
- GHCR_PAT = GitHub Personal Access Token
- API_DOMAIN = api.quiztutor.sethna.me

Optional (only for deploy-hooks workflow):
- VERCEL_DEPLOY_HOOK_URL = Vercel deploy hook URL

Not needed in GitHub secrets:
- NEXT_PUBLIC_API_URL (this is set in Vercel project environment variables, not GitHub Actions secrets)

PAT requirements:
- Type: classic token is simplest for this setup
- Scopes: read:packages, write:packages

## 5) First-time server bootstrap on droplet

SSH from Windows:

    ssh root@YOUR_DROPLET_IP

Run on droplet:

    apt-get update && apt-get upgrade -y
    apt-get install -y git curl
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker --now
    docker --version
    docker compose version

Create app folder and clone repo:

    mkdir -p /opt/quiz-tutor
    cd /opt/quiz-tutor
    git clone https://github.com/YOUR_GITHUB_USERNAME/ai-quiz-tutor.git .

Create backend env file:

    cp deploy/server.example .env.backend
    nano .env.backend

Set real values in .env.backend:
- GROQ_API_KEY
- HF_TOKEN
- MONGODB_URI
- ANTHROPIC_API_KEY (optional)
- GHCR_OWNER (your GitHub username)
- IMAGE_TAG (latest)
- API_DOMAIN (api subdomain)

Save and exit nano.

## 6) First manual container run (sanity check)

On droplet:

    cd /opt/quiz-tutor
    docker compose -f deploy/docker-compose.prod.yml up -d
    docker compose -f deploy/docker-compose.prod.yml ps
    docker compose -f deploy/docker-compose.prod.yml logs backend --tail 100

Health check test:

    curl -I http://localhost:8000/health

Expected: HTTP 200 or success response.

## 7) Backend auto-deploy validation

Now trigger CI/CD by pushing any backend change to main:

    git add .
    git commit -m "chore: trigger backend deploy"
    git push origin main

Check GitHub Actions:
- Workflow: backend-digitalocean-cd
- Build and deploy jobs should pass

After workflow success, on droplet:

    cd /opt/quiz-tutor
    docker compose -f deploy/docker-compose.prod.yml ps
    docker compose -f deploy/docker-compose.prod.yml logs backend --tail 100

## 8) Vercel frontend deployment

In Vercel dashboard:
1. Add New Project
2. Import this GitHub repository
3. Root directory: apps/frontend
4. Framework: Next.js (auto-detected)
5. Add environment variable:
    NEXT_PUBLIC_API_URL = https://api.quiztutor.sethna.me
6. Add custom domain:
    quiztutor.sethna.me
6. Deploy

Vercel will auto-deploy on every push to main.

## 9) Cloudflare DNS wiring

In Cloudflare DNS for your domain:
- A record:
    - Name: api.quiztutor
    - IPv4: 165.22.98.154
    - Proxy status: DNS only (gray cloud for first setup)
    - TTL: Auto
- CNAME record (frontend):
    - Name: quiztutor
    - Target: cname.vercel-dns.com
    - Proxy status: DNS only (gray cloud for first setup)
    - TTL: Auto

Then in Vercel Domains page, verify quiztutor.sethna.me until status shows Valid Configuration.

Cloudflare SSL/TLS:
- Set mode to Full (strict)

## 10) Nginx domain update

Edit file in repo:
- deploy/nginx/quiz-tutor.conf

Replace server_name with your real API domain.

Commit and push:

    git add deploy/nginx/quiz-tutor.conf
    git commit -m "chore: set production api domain"
    git push origin main

On droplet, refresh compose if needed:

    cd /opt/quiz-tutor
    git pull
    docker compose -f deploy/docker-compose.prod.yml up -d

## 11) Quick troubleshooting

If SSH says host key changed:

    ssh-keygen -R YOUR_DROPLET_IP

If containers fail to start:

    docker compose -f deploy/docker-compose.prod.yml logs --tail 200

If backend is up but domain fails:
- Confirm Cloudflare A record points to droplet IP
- Confirm port 80 open in droplet firewall
- Confirm nginx container is running

## 12) Final live checks

Backend:
- https://api.quiztutor.sethna.me/health

Frontend:
- https://quiztutor.sethna.me

End-to-end:
- Upload a document in app
- Start chat and request quiz generation

Deployment complete when all three checks pass.
