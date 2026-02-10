# NANOBOT: Quick Reference Guide

## At a Glance

**Type**: Ultra-lightweight AI assistant framework (~3,400 LOC)  
**Language**: Python 3.11+ (core) + Node.js (WhatsApp bridge)  
**Architecture**: Async event-driven with message bus pattern  
**Channels**: Telegram, Discord, WhatsApp, Feishu, DingTalk  
**LLM Support**: 12+ providers (OpenRouter, Claude, GPT, DeepSeek, etc.)  
**License**: MIT

---

## Architecture Layers

```
┌────────────────────────────────────────┐
│    Chat Platforms (5 channels)         │
│  Telegram | Discord | WhatsApp | etc.  │
└─────────────┬────────────────────────┘
              │ JSON messages
              ▼
┌────────────────────────────────────────┐
│    Message Bus (AsyncQueue)            │
│  Inbound Queue | Outbound Queue        │
└─────────────┬────────────────────────┘
              │ 
              ▼
┌────────────────────────────────────────┐
│    Agent Loop (Core Engine)            │
│  LLM ↔ Tool Execution ↔ Context        │
└─────────────┬────────────────────────┘
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐
│ Tools  │ │ LLM  │ │Session │
└────────┘ └──────┘ └────────┘
```

---

## File Organization

### Core Engine (agent/)
- **loop.py** (377 lines) - Main agent loop
- **tools/** - File, shell, web, message, spawn, cron tools
- **context.py** - Prompt building
- **memory.py** - Conversation memory
- **skills.py** - Skill loader

### Channel Integrations (channels/)
| File | Platform | Protocol | QR Auth? |
|------|----------|----------|----------|
| telegram.py | Telegram | Long Polling | No |
| discord.py | Discord | Gateway WS | No |
| whatsapp.py | WhatsApp | Bridge WS | Yes |
| feishu.py | Feishu | Long Connection | No |
| dingtalk.py | DingTalk | Stream Mode | No |

### Message System (bus/)
- **queue.py** - AsyncQueue-based MessageBus
- **events.py** - InboundMessage, OutboundMessage types

### LLM Routing (providers/)
- **registry.py** - Provider metadata (12+ providers)
- **litellm_provider.py** - LiteLLM wrapper
- **transcription.py** - Groq Whisper

### Configuration (config/)
- **schema.py** - Pydantic config schema
- **loader.py** - Config file loading

### WhatsApp Bridge (bridge/)
- **src/whatsapp.ts** - Baileys wrapper
- **src/server.ts** - WebSocket bridge
- **src/index.ts** - Entry point

---

## Configuration Locations

```
~/.nanobot/
├── config.json              ← Main config (API keys, channel tokens)
├── workspace/               ← User workspace (files, scripts)
├── sessions/                ← Conversation history (JSONL)
├── whatsapp-auth/           ← WhatsApp auth state
├── media/                   ← Downloaded media
├── history/                 ← CLI history
└── logs/                    ← Application logs
```

---

## Key Data Flows

### Incoming Message
```
Channel → InboundMessage
   ↓
Message Bus (inbound queue)
   ↓
Agent Loop:
   1. Load session history
   2. Build LLM prompt
   3. Call LLM
   4. Parse tool calls
   5. Execute tools
   6. Return response
   ↓
Message Bus (outbound queue)
   ↓
Channel → User
```

### WhatsApp Flow (Special)
```
Phone (WhatsApp Web)
   ↓ (Baileys)
Node.js Bridge (ws://localhost:3001)
   ↓ (JSON WebSocket)
Python WhatsAppChannel
   ↓
Agent Loop
```

---

## Security Features

### Built-in Protections
- ✅ Allow-list access control (per channel)
- ✅ Shell command pattern blocking (rm -rf /, mkfs, etc.)
- ✅ File path traversal prevention
- ✅ Workspace restriction option
- ✅ URL validation (http/https only)
- ✅ Execution timeout (60s default)
- ✅ Output truncation (10KB limit)

### Best Practices
- Store API keys in config.json (chmod 600)
- Use separate keys for dev/prod
- Configure allowFrom lists
- Run as non-root user
- Monitor logs for access attempts
- Keep dependencies updated (pip-audit, npm audit)

---

## LLM Providers (12 Total)

**Gateways** (can route any model):
- OpenRouter (sk-or-* keys)
- AiHubMix

**Direct Providers**:
- Anthropic (Claude)
- OpenAI (GPT)
- DeepSeek
- Groq (+ Whisper transcription)
- Google Gemini
- Zhipu (GLM)
- Dashscope (Qwen)
- Moonshot (Kimi)
- vLLM (local/self-hosted)

---

## CLI Commands

```bash
# Initialization
nanobot onboard                 # First-time setup

# Chat
nanobot agent -m "message"      # Single message
nanobot agent                   # Interactive mode

# Multi-channel
nanobot gateway                 # Start all enabled channels
nanobot channels login          # WhatsApp QR auth
nanobot channels status         # Channel status

# Status
nanobot status                  # Provider/channel status

# Scheduled tasks
nanobot cron add --name "daily" --cron "0 9 * * *" --message "msg"
nanobot cron list               # List scheduled tasks
nanobot cron remove <id>        # Remove task
```

---

## Authentication Methods

| Platform | Auth Type | Setup Time | Config |
|----------|-----------|-----------|--------|
| Telegram | Bot Token | 1 min | token from @BotFather |
| Discord | Bot Token | 2 min | token from Developer Portal |
| WhatsApp | QR Code | 5 min | Scan in Linked Devices |
| Feishu | App Creds | 5 min | App ID + Secret |
| DingTalk | App Creds | 5 min | Client ID + Secret |

---

## Tools Available to Agent

| Tool | Capability | Safety |
|------|-----------|--------|
| read_file | Read files | Path traversal blocked |
| write_file | Create/modify files | Workspace restriction option |
| edit_file | Edit files | Workspace restriction option |
| list_dir | List directories | Workspace restriction option |
| exec | Run shell commands | Dangerous patterns blocked |
| web_search | Brave Search API | Query only, no file access |
| web_fetch | Download + parse web pages | Max 20MB, 5 redirects |
| send_message | Inter-agent messaging | Internal only |
| spawn | Background tasks | Configurable timeout |
| cron | Schedule tasks | Requires skill setup |

---

## No REST API Currently

⚠️ **Important**: Nanobot has **no HTTP REST API** endpoint.

**Current communication model**:
- Chat platforms → WebSocket/polling → Agent
- No `/api/chat` endpoint
- All messaging is event-driven

**For mobile apps**, you would need to:
1. Add REST API layer (FastAPI recommended)
2. Implement JWT authentication
3. Add rate limiting
4. Restrict tool access
5. Ensure data encryption

---

## Docker Deployment

```bash
# Build
docker build -t nanobot .

# First run - initialize
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot onboard

# Edit config
vim ~/.nanobot/config.json

# Run gateway
docker run -v ~/.nanobot:/root/.nanobot -p 18790:18790 nanobot gateway

# Single command
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot agent -m "Hello"
```

---

## Performance Characteristics

- **Memory**: ~100-300MB at rest (varies by provider)
- **Startup**: <2 seconds
- **Message latency**: LLM dependent (10-60s typical)
- **Channel throughput**: Limited by LLM provider
- **Concurrent users**: 1 per instance (designed for single user)
- **Code size**: ~3,400 lines core Python

---

## Limitations & Known Issues

1. **No multi-user**: Designed for single user per instance
2. **No rate limiting**: Add your own if needed
3. **Plain text config**: API keys not encrypted
4. **Limited logging**: No audit trail by default
5. **Synchronous tool execution**: Tools run one at a time
6. **No persistent memory**: Only session history stored
7. **No paid content filtering**: Must manage yourself
8. **Shell access dangerous**: Even with protections

---

## Roadmap Features (Not Implemented)

- [ ] Multi-modal (images, voice, video)
- [ ] Long-term memory
- [ ] Better reasoning/planning
- [ ] More integrations (Slack, email)
- [ ] Self-improvement from feedback
- [ ] HTTP REST API

---

## Quick Setup Example

```bash
# 1. Install
pip install nanobot-ai

# 2. Initialize
nanobot onboard

# 3. Configure providers
cat ~/.nanobot/config.json
# Add your API keys

# 4. Enable channels
# Edit config.json:
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allow_from": ["YOUR_USER_ID"]
    }
  }
}

# 5. Run
nanobot gateway
```

---

## Code Stats

- **Total Python LOC**: ~3,448
- **Main components**: 8 (agent, channels, bus, providers, config, session, cli, skills)
- **Built-in tools**: 10
- **Supported channels**: 5
- **Supported LLM providers**: 12
- **Python files**: ~25
- **TypeScript files**: 4 (WhatsApp bridge)
- **Test coverage**: Basic

---

## Resources

- **GitHub**: https://github.com/HKUDS/nanobot
- **PyPI**: https://pypi.org/project/nanobot-ai/
- **Discord**: https://discord.gg/MnCvHqpUGB
- **Security**: See SECURITY.md in repository
- **Architecture**: See nanobot_arch.png in repository

