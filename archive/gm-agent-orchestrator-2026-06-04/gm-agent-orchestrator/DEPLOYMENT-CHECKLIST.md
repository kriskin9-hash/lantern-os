# Phase 2 Deployment Checklist — 2026-05-25

## Pre-Deployment Verification

- [x] Docker installed (v29.4.2)
- [x] Docker Compose installed (v5.1.3)  
- [x] All scripts normalized to underscore naming convention
- [x] Dockerfile entry point corrected (lantern_orchestrator_main.py)
- [x] docker-compose.yml services wired correctly
- [x] Git repo clean, all changes committed and pushed

## Local Environment Setup

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] ~/.lantern/config.json configured (LLM providers, M5 attestation settings)
- [ ] ~/.lantern/sounds/ populated with audio library
- [ ] ~/lantern-rag-books/ created for knowledge base ingestion

## Docker Build & Launch

- [ ] Build Docker image: `docker-compose build`
- [ ] Launch services: `docker-compose up -d`
- [ ] Verify service health:
  - [ ] Lantern Desktop running on host (if applicable)
  - [ ] RAG server healthy on http://localhost:8767/health
  - [ ] Orchestrator logging to ~/.lantern/orchestrator.log
  - [ ] Payment system initialized with Family A/B/D ($600/mo baseline)

## Phase 2 Execution

- [ ] Execute first 10 warm referral messages (Family A/B/D networks)
- [ ] Track inbound responses (referral pipeline)
- [ ] Monitor NPS + churn for existing families
- [ ] Activate RAG knowledge base ingestion (local books → SQLite)
- [ ] Autopilot learning loop running (5-minute cycles)

## Success Criteria (June 25 COMET LEAP Checkpoint)

- [ ] 30+ days M5 attestation clean logs
- [ ] 6+ families using Lantern (A, B, D + 3 referrals)
- [ ] $600+/mo confirmed revenue (baseline) + new family subscriptions
- [ ] NPS ≥40
- [ ] Churn <5%
- [ ] 2+ unsolicited referrals
- [ ] $350/mo ARR (Year 1 target on track)

---

**Status**: Ready for Phase 2 launch ✓
**Date**: 2026-05-25
**Approval**: Pending founder sign-off
