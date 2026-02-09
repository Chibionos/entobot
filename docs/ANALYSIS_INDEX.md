# Nanobot Codebase Analysis - Document Index

## Generated Documentation

Three comprehensive documents have been created to help you understand the nanobot codebase:

### 1. EXPLORATION_SUMMARY.md (Executive Overview)
**Start here if you have 5 minutes**

Quick executive summary covering:
- What nanobot is and how it works
- Channel implementations (Telegram, Discord, WhatsApp, Feishu, DingTalk)
- Security & authentication
- LLM provider support
- Critical limitations (no REST API, no multi-user)
- What you'd need to build a mobile app
- Recommended reading order

**Best for**: Quick understanding, decision making, planning

---

### 2. QUICK_REFERENCE.md (Developer Cheat Sheet)
**Start here if you have 15 minutes**

Condensed reference guide with:
- Architecture diagram
- File organization
- CLI commands
- Configuration examples
- Security features checklist
- Tools available to the agent
- Docker deployment
- Performance characteristics
- Code statistics

**Best for**: Implementation, quick lookups, configuration help

---

### 3. CODEBASE_ANALYSIS.md (Deep Technical Dive)
**Start here if you have 30+ minutes**

Comprehensive 1,100+ line technical analysis covering:

**Section 1: Architecture & Components**
- High-level architecture diagram
- Core components (loop.py, bus, channels)
- Component responsibilities

**Section 2: Provider Implementation**
- WhatsApp (2-component bridge architecture)
- Telegram (polling-based)
- Discord (Gateway WebSocket)
- Feishu (long connection)
- DingTalk (stream mode)
- Each with code examples and protocol details

**Section 3: Authentication & Security**
- API key management
- Access control (allow-lists)
- Tool execution security
- Input validation
- Complete protection checklist

**Section 4: API & Communication**
- Message flow architecture
- InboundMessage & OutboundMessage types
- No REST API (limitations)
- Gateway command interface

**Section 5: Configuration System**
- File locations and formats
- Complete schema reference
- Provider configuration (12 providers)
- Channel configuration examples
- Tool configuration

**Section 6: Mobile/Web Interfaces**
- Current access methods
- Why no mobile app exists
- Architecture options for building one

**Section 7: QR & Pairing**
- WhatsApp QR auth flow
- Telegram/Discord token setup
- Feishu/DingTalk credentials

**Section 8: Project Structure & Tech Stack**
- Complete directory tree
- Dependencies breakdown
- Design patterns used
- Code metrics

**Section 9: Mobile App Integration**
- Architecture options
- REST API endpoint suggestions
- Authentication requirements
- Security considerations

**Section 10: Security & Operational Recommendations**
- Pre-production checklist
- Dangerous features to monitor
- Docker deployment

**Best for**: Understanding implementation details, extending the system, security review

---

## How to Use These Documents

### If you want to...

**Understand the overall architecture**
→ Read EXPLORATION_SUMMARY.md (5 min) + QUICK_REFERENCE.md (15 min)

**Set up nanobot for the first time**
→ Read QUICK_REFERENCE.md sections: Configuration, CLI Commands, Docker

**Add a new chat channel**
→ Read CODEBASE_ANALYSIS.md Section 2 + examine `nanobot/channels/base.py`

**Build a mobile app to control nanobot**
→ Read EXPLORATION_SUMMARY.md "For Building a Mobile App" + CODEBASE_ANALYSIS.md Section 9

**Understand WhatsApp integration**
→ Read CODEBASE_ANALYSIS.md Section 2.1 + examine:
- `nanobot/channels/whatsapp.py`
- `bridge/src/whatsapp.ts`
- `bridge/src/server.ts`

**Review security**
→ Read CODEBASE_ANALYSIS.md Section 3 + SECURITY.md in repo

**Deploy to production**
→ Read QUICK_REFERENCE.md Docker section + SECURITY.md + CODEBASE_ANALYSIS.md Section 10

**Extend with new tools**
→ Read CODEBASE_ANALYSIS.md Section 8.5 design patterns + examine `nanobot/agent/tools/`

**Add new LLM provider**
→ Read `nanobot/providers/registry.py` (registry pattern) + QUICK_REFERENCE.md LLM Providers section

---

## Key Numbers to Remember

- **3,448 lines** of core Python code
- **5 chat channels** supported
- **12 LLM providers** supported
- **10 built-in tools** available
- **~100-300 MB** memory usage
- **<2 seconds** startup time
- **60 seconds** default execution timeout
- **No REST API** currently (critical limitation for mobile apps)

---

## Critical Files in the Codebase

### Must-Read Files

1. **nanobot/agent/loop.py** (377 lines)
   - The heart of the system
   - Message processing pipeline
   - LLM call coordination

2. **nanobot/channels/base.py**
   - Channel interface definition
   - Access control implementation
   - Message bus integration

3. **nanobot/config/schema.py**
   - All configuration options
   - Provider registry mapping
   - Channel configurations

4. **nanobot/channels/whatsapp.py**
   - WebSocket client implementation
   - Bridge message protocol
   - QR handling

### Important Files

5. **bridge/src/whatsapp.ts** - Node.js bridge
6. **nanobot/bus/queue.py** - Message routing
7. **nanobot/session/manager.py** - Conversation storage
8. **nanobot/agent/tools/** - Tool implementations
9. **nanobot/providers/registry.py** - Provider system
10. **nanobot/cli/commands.py** - CLI interface

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────┐
│      Chat Platforms (5 channels)            │
│  Telegram | Discord | WhatsApp | etc.      │
└──────────────────┬──────────────────────────┘
                   │
          ┌────────▼────────┐
          │  Message Bus    │
          │  (AsyncQueue)   │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │   Agent Loop    │
          │   (Core Engine) │
          └────────┬────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼──┐    ┌─────▼────┐   ┌────▼───┐
│Tools │    │    LLM   │   │Session │
└──────┘    │ Providers│   └────────┘
            └──────────┘
```

---

## Quick Configuration Template

```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "workspace": "~/.nanobot/workspace"
    }
  },
  "providers": {
    "openrouter": {
      "api_key": "sk-or-v1-xxx"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allow_from": ["YOUR_USER_ID"]
    }
  }
}
```

---

## Common Questions Answered

**Q: Can multiple users access one instance?**
A: No, nanobot is designed for single-user operation. Each user needs their own instance.

**Q: Is there an HTTP REST API?**
A: No. All communication is via chat platforms or CLI. You'd need to add one for a mobile app.

**Q: How does WhatsApp authentication work?**
A: QR code based. User scans with WhatsApp → Linked Devices. State saved to ~/.nanobot/whatsapp-auth/

**Q: What's the recommended LLM provider?**
A: OpenRouter for multi-model access. Anthropic or OpenAI if you only need one provider.

**Q: Can the agent access any file?**
A: By default yes, but you can restrict to workspace with `restrict_to_workspace: true`

**Q: Is the shell execution safe?**
A: Medium safety. Dangerous patterns blocked but sophisticated attacks possible. Run in container.

**Q: How are conversations stored?**
A: JSONL files in ~/.nanobot/sessions/, one per conversation (channel:chat_id)

**Q: Can I run this on a phone?**
A: No native mobile app. Access via Telegram/Discord/WhatsApp app instead.

---

## Related Files in Repository

- **README.md** - Feature overview and quick start
- **SECURITY.md** - Security guidelines and best practices
- **COMMUNICATION.md** - Community links
- **pyproject.toml** - Python dependencies
- **Dockerfile** - Container image
- **bridge/package.json** - Node.js dependencies

---

## Exploration Metadata

**Date**: 2026-02-09
**Version Analyzed**: 0.1.3.post5
**Analysis Type**: Complete architecture, implementation, security, deployment
**Files Examined**: 40+ Python files, 4 TypeScript files
**Time Investment**: ~1.5 hours for complete exploration

---

## Next Steps

1. **Quick Start** (5 min)
   - Read EXPLORATION_SUMMARY.md

2. **Implementation Details** (30 min)
   - Read CODEBASE_ANALYSIS.md sections 1-3

3. **Local Setup** (15 min)
   - Follow README.md quick start
   - Use QUICK_REFERENCE.md for CLI commands

4. **Deep Dive** (ongoing)
   - Read full CODEBASE_ANALYSIS.md
   - Examine source code in nanobot/ directory

5. **Custom Integration** (varies)
   - Add REST API layer
   - Extend with new channels
   - Build mobile app integration

---

## Support Resources

- **GitHub Issues**: https://github.com/HKUDS/nanobot/issues
- **Discord Community**: https://discord.gg/MnCvHqpUGB
- **PyPI Package**: https://pypi.org/project/nanobot-ai/
- **Documentation**: README.md and SECURITY.md in repo

---

**Happy exploring! For questions, refer to the appropriate document above or check the source code.**

