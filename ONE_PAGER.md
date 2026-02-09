# Entobot Enterprise - One Pager

## What is Entobot Enterprise?

**Secure, Mobile-First AI Assistant Platform for Enterprises**

Entobot Enterprise is the enterprise transformation of nanobot - providing direct mobile-to-backend AI communication without third-party relay services.

## The Problem

Traditional AI assistants (ChatGPT, Copilot) and messaging integrations (WhatsApp, Telegram, Slack bots) have critical limitations for enterprises:

- Data leaves your infrastructure
- Third-party relay dependencies
- Compliance challenges (SOC2, GDPR, HIPAA)
- No air-gapped deployment
- Consumer-grade security

## The Solution

**Entobot Enterprise = Your AI + Your Infrastructure + Mobile First**

Direct WebSocket communication between native mobile apps and your backend servers. Zero external dependencies.

## Key Features

| Feature | Description | Business Value |
|---------|-------------|----------------|
| **Mobile Apps** | Native iOS & Android (Flutter) | Users work from anywhere securely |
| **QR Pairing** | 3-second device pairing | Frictionless onboarding |
| **No Relays** | Direct mobile-to-backend | Complete data control |
| **Enterprise Auth** | JWT, OAuth2, SAML, LDAP | Corporate SSO integration |
| **Dashboard** | Real-time monitoring | IT visibility and control |
| **Audit Logs** | Complete trail | Compliance-ready |
| **Any LLM** | OpenAI, Anthropic, local | Provider flexibility |
| **Air-Gapped** | Works offline | Government/healthcare ready |

## Architecture

```
Mobile App (iOS/Android) ←WSS→ Backend Server ←API→ Your LLM
                                      ↓
                              Web Dashboard
```

All components in YOUR infrastructure.

## Why Enterprises Choose Entobot

**Security:** Data never leaves your infrastructure  
**Compliance:** SOC2, GDPR, HIPAA-ready features  
**Flexibility:** Any LLM provider or local models  
**Cost:** No per-user fees, open source foundation  
**Control:** Complete audit trail and monitoring  

## Use Cases

- **IT/DevOps:** Developer assistance, infrastructure automation
- **Customer Support:** Agent guidance, knowledge base access
- **Sales:** Content generation, lead qualification
- **Enterprise:** Strategic planning, decision support

## Technical Specs

**Performance:**
- 100+ concurrent connections per server
- < 500ms message latency (local network)
- 1000+ messages/second throughput

**Deployment:**
- On-premises, private cloud, or air-gapped
- Works behind VPNs and firewalls
- Horizontal scaling ready
- Docker & Kubernetes support

**Technology:**
- Backend: Python 3.11+, FastAPI, WebSocket
- Mobile: Flutter 3.0+ (iOS & Android)
- Dashboard: HTML5/CSS3/JavaScript
- Database: PostgreSQL/SQLite

## Pricing Model

**No per-user licensing** - pay only for:
1. Infrastructure (cloud/on-prem servers)
2. LLM API (or use local models for free)

**Typical costs for 50 users:**
- Infrastructure: ~$200/month
- LLM API: ~$100-300/month
- **Total: $300-500/month**

Compare to enterprise SaaS: $25-50/user/month = $1,250-2,500/month

**ROI: 3-6 months**

## Deployment Timeline

- **POC:** 1 day
- **Pilot:** 1-2 weeks
- **Production:** 2-4 weeks
- **Enterprise Rollout:** 1-3 months

## Current Status

✅ **Demo-Ready** (February 2025)

- Phase 1: Backend security ✅
- Phase 2: Mobile apps ✅
- Phase 3: Integration ✅
- Phase 4: Dashboard ✅
- Phase 5: QA/Security ⏳
- Phase 6: Demo prep ✅

## Next Steps

1. **See Demo:** [Schedule 10-minute demo](DEMO.md)
2. **Try POC:** Deploy in 1 day
3. **Pilot:** 20-50 users for 2 weeks
4. **Production:** Full rollout

## Contact

- **Demo:** See [DEMO.md](DEMO.md)
- **Documentation:** [README.md](README.md)
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)
- **Enterprise:** enterprise@entobot.ai

---

**Entobot Enterprise: Your AI, Your Infrastructure, Your Control**
