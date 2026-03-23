# Production Readiness Checklist

This document tracks what is required before calling this app production-ready.

## Current Assessment

Status: partially ready (good foundation, still needs hardening).

What is already in place:
- Background document processing for heavy PDF/image ingestion
- MongoDB persistence for documents, quizzes, attempts, and chat history
- Auth integration via Clerk
- Basic PWA assets and service worker registration path
- Upload storage support for local + optional Supabase

What still needs completion for production:
- CI pipeline with automated backend + frontend tests
- Structured logging/metrics/alerts (Sentry, OpenTelemetry, or equivalent)
- Rate limits and abuse protection on chat/upload endpoints
- Strong secrets management and environment segregation (dev/stage/prod)
- Load testing and capacity targets for large concurrent uploads
- Database backup/restore runbook and retention policy
- Security scan and dependency update policy

## Required Environment Variables

Backend:
- GROQ_API_KEY
- HF_TOKEN
- MONGODB_URI
- MONGODB_DATABASE
- FRONTEND_ORIGINS or FRONTEND_ORIGIN_REGEX

Optional but recommended:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_BUCKET
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

Frontend:
- NEXT_PUBLIC_API_URL
- Clerk publishable key variables used by your auth setup

## Release Checklist

1. Backend
- Run backend tests and smoke checks
- Validate upload -> processing -> chat -> quiz flow on real sample PDFs
- Verify document status timeout behavior and failure messaging

2. Frontend
- Run lint/build
- Validate login/logout and protected routes
- Validate chat disabled state for non-ready documents

3. Data
- Confirm vector index exists and query performance is acceptable
- Confirm metadata fields pages/tables_count/chunks_count populate correctly

4. Infra
- HTTPS enabled on all public endpoints
- CORS restricted to expected origins only
- Observability dashboard and alert rules enabled

5. Operations
- Incident response owner assigned
- Deployment rollback procedure documented
- On-call and runtime logs access tested

## Suggested Go-Live Gates

- P95 chat response latency under target (define SLA)
- Upload success rate > 99% on representative files
- No blocker/high security findings
- Backup restore drill validated
