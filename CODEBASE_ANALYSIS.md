# NANOBOT: Comprehensive Codebase Analysis

## Executive Summary

**Nanobot** is an ultra-lightweight personal AI assistant framework (~4,000 lines of core code) that integrates with multiple chat platforms (Telegram, Discord, WhatsApp, Feishu, DingTalk) and supports various LLM providers. The architecture is modular, event-driven, and designed for easy extension.

### Key Statistics
- **Total Core Lines**: ~3,448 (verified via `bash core_agent_lines.sh`)
- **Version**: 0.1.3.post5
- **Python Version**: ≥3.11
- **Main Dependencies**: litellm, pydantic, websockets, python-telegram-bot
- **Architecture**: Async event-driven with message bus pattern

---

## 1. CURRENT ARCHITECTURE & MAIN COMPONENTS

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CHAT CHANNELS                              │
│  ┌──────────┬──────────┬─────────┬────────┬────────┐         │
│  │Telegram  │ Discord  │WhatsApp │Feishu  │DingTalk│         │
│  └──────────┴──────────┴─────────┴────────┴────────┘         │
└────────────────────┬────────────────────────────────────────┘
                     │ (WebSocket/HTTP)
┌────────────────────▼────────────────────────────────────────┐
│                    MESSAGE BUS                               │
│  ┌──────────────────┬──────────────────┐                    │
│  │ Inbound Queue    │ Outbound Queue   │                    │
│  └──────────────────┴──────────────────┘                    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 AGENT LOOP (Core Engine)                     │
│  ┌──────────────────────────────────────────┐               │
│  │ 1. Receive message from bus              │               │
│  │ 2. Build context (history + memory)      │               │
│  │ 3. Call LLM provider                     │               │
│  │ 4. Execute tool calls                    │               │
│  │ 5. Send response back to bus             │               │
│  └──────────────────────────────────────────┘               │
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼──┐ ┌────────▼──────┐ ┌─────▼───┐
│ Tools │ │ LLM Providers │ │ Sessions│
│       │ │               │ │         │
└───────┘ └────────────────┘ └─────────┘
```

### 1.2 Core Components

#### **nanobot/agent/loop.py** (377 lines)
The central processing engine:
- Receives inbound messages from the bus
- Manages conversation sessions and context
- Coordinates tool execution with LLM
- Sends outbound responses back through channels
- Implements up to 20 iterations of LLM-tool-execute loops

Key Methods:
```python
class AgentLoop:
    async def process_message(msg: InboundMessage) -> OutboundMessage
    async def _llm_call(context, tools) -> LLMResponse
    async def _execute_tool(tool_name, params) -> str
    async def _on_tool_result(result) -> None
```

#### **nanobot/bus/** (Message Queue)
Async message broker decoupling channels from the agent:
```python
class MessageBus:
    inbound: asyncio.Queue[InboundMessage]
    outbound: asyncio.Queue[OutboundMessage]
    
    async def publish_inbound(msg)
    async def consume_inbound() -> msg
    async def publish_outbound(msg)
    async def consume_outbound() -> msg
```

#### **nanobot/channels/** (Chat Integration)
Platform-specific implementations using a unified interface:

| Channel | Protocol | Features |
|---------|----------|----------|
| **Telegram** | Long Polling | Media download, voice transcription (Groq), typing indicator |
| **Discord** | Gateway WebSocket | Message reactions, guild support, attachment download |
| **WhatsApp** | WebSocket Bridge | QR-based auth, linked devices, group support |
| **Feishu** | WebSocket (Long Connection) | No IP needed, message reactions, encrypted events |
| **DingTalk** | Stream Mode | No IP needed, private/group chat |

---

## 2. WHERE WHATSAPP, TELEGRAM, AND OTHER PROVIDERS ARE IMPLEMENTED

### 2.1 WhatsApp Integration

**Files**: 
- `/nanobot/channels/whatsapp.py` - Python WebSocket client
- `/bridge/src/whatsapp.ts` - Node.js Baileys wrapper
- `/bridge/src/server.ts` - WebSocket bridge server

**Architecture**:
```
User's Phone (WhatsApp Web) 
       ↓ (Baileys library via Web API)
   Node.js Bridge Server (ws://localhost:3001)
       ↓ (JSON messages via WebSocket)
Python nanobot.channels.WhatsAppChannel
```

**Key Implementation Details**:

1. **QR Code Authentication** (`whatsapp.ts`):
```typescript
sock.ev.on('connection.update', (update) => {
  if (qr) {
    qrcode.generate(qr, { small: true });  // Display in terminal
    bridge.broadcast({ type: 'qr', qr });
  }
});
```

2. **Message Handling** (`whatsapp.py`):
```python
async def _handle_bridge_message(self, raw: str):
    data = json.loads(raw)
    if data.get("type") == "message":
        sender = data.get("sender", "")  # New LID format
        content = data.get("content", "")
        # Extract phone number from LID (e.g., "1234567890@s.whatsapp.net")
        sender_id = sender.split("@")[0]
```

3. **Bridge Protocol** (JSON WebSocket):
```json
// Python → Node.js (send message)
{"type": "send", "to": "1234567890@s.whatsapp.net", "text": "Hello"}

// Node.js → Python (received message)
{"type": "message", "sender": "1234567890@s.whatsapp.net", "content": "Hi", "id": "msg123", "isGroup": false}

// QR Code
{"type": "qr", "qr": "[QR_DATA_STRING]"}

// Status updates
{"type": "status", "status": "connected"}
```

**File Structure**:
```
~/.nanobot/
├── config.json                  # WhatsApp config + allowFrom list
├── whatsapp-auth/              # Authentication state (auth.json, device list, etc.)
└── sessions/                   # Conversation history (JSONL)
```

### 2.2 Telegram Integration

**File**: `/nanobot/channels/telegram.py`

**Features**:
- Long polling (no webhook needed)
- Media support: photos, voice, audio, documents
- Voice transcription via Groq Whisper
- Typing indicator
- Commands: `/start`, `/reset`, `/help`

**Key Implementation**:
```python
class TelegramChannel(BaseChannel):
    async def _on_message(self, update: Update, context):
        # Download media if present
        if media_file:
            file = await bot.get_file(media_file.file_id)
            await file.download_to_drive(f"~/.nanobot/media/{file_id}")
            
            # Transcribe if voice
            if media_type == "voice":
                transcriber = GroqTranscriptionProvider(api_key=groq_key)
                text = await transcriber.transcribe(file_path)
```

**Security Features**:
- User ID based `allowFrom` (integer or username)
- Markdown to HTML conversion for safe formatting
- Access control at base channel level

### 2.3 Discord Integration

**File**: `/nanobot/channels/discord.py`

**Architecture**:
- Direct Discord Gateway WebSocket (not using discord.py)
- Heartbeat mechanism
- Rate limiting aware
- HTTP API for message sending

**Protocol Flow**:
```python
# 1. Connect to gateway
async with websockets.connect(gateway_url) as ws:

# 2. Send IDENTIFY payload (op=2)
identify = {
    "op": 2,
    "d": {
        "token": config.token,
        "intents": 37377,  # GUILDS | GUILD_MESSAGES | MESSAGE_CONTENT
        "properties": {"os": "nanobot", "browser": "nanobot"}
    }
}

# 3. Receive HELLO (op=10) with heartbeat interval
# 4. Send heartbeat (op=1) every interval
# 5. Handle MESSAGE_CREATE (op=0, t=MESSAGE_CREATE)
```

### 2.4 Feishu Integration

**File**: `/nanobot/channels/feishu.py`

**Architecture**:
- Uses `lark-oapi` SDK
- WebSocket long connection (no webhook/IP needed)
- Stream mode event subscription
- Message reactions support

**Implementation**:
```python
async def start(self):
    # Use SDK's request/response for bidirectional communication
    self._client = lark.Client.builder()\
        .app_id(self.config.app_id)\
        .app_secret(self.config.app_secret)\
        .build()
    
    # Connect and register event handlers
    self._ws_client = self._client.ws()
    
    # Deduplicate messages using OrderedDict (Feishu re-sends same events)
    self._processed_message_ids = OrderedDict()
```

### 2.5 DingTalk Integration

**File**: `/nanobot/channels/dingtalk.py`

**Architecture**:
- Uses `dingtalk_stream` SDK
- Stream mode (no webhook needed)
- Callback handler pattern

---

## 3. AUTHENTICATION & SECURITY MECHANISMS

### 3.1 API Key Management

**Storage**: `~/.nanobot/config.json` (JSON)

```json
{
  "providers": {
    "openrouter": {
      "api_key": "sk-or-v1-xxx",
      "api_base": null,
      "extra_headers": null
    },
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allow_from": ["123456789", "username"]
    }
  }
}
```

**Security Measures**:
- File permissions: `chmod 600` recommended
- Plain text storage (not encrypted) - users advised to use OS keyring
- Environment variable fallback via Pydantic BaseSettings
- Separate keys for development/production

### 3.2 Access Control

**Allow-list Based**:
```python
class BaseChannel:
    def is_allowed(self, sender_id: str) -> bool:
        allow_list = self.config.allow_from  # []
        
        if not allow_list:
            return True  # Allow all if list is empty
        
        # Check exact match or compound IDs (e.g., "123|username")
        return sender_id in allow_list
```

**Per-Channel Configuration**:
```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "xxx",
      "allow_from": ["123456789", "my_username"]
    },
    "whatsapp": {
      "enabled": true,
      "allow_from": ["+1234567890", "+9876543210"]
    }
  }
}
```

### 3.3 Tool Execution Security

**Shell Command Protection** (`nanobot/agent/tools/shell.py`):
- Dangerous patterns blocked:
  - `rm -rf /` (root deletion)
  - Fork bombs
  - Filesystem formatting (`mkfs.*`)
  - Raw disk writes
- Execution timeout: 60 seconds (configurable)
- Output truncation: 10KB limit

**File Access Protection**:
```python
class ReadFileTool:
    def __init__(self, allowed_dir: Path | None = None):
        self.allowed_dir = allowed_dir  # Restrict to workspace if set
    
    async def execute(self, path: str):
        # Check if path is within allowed_dir
        if self.allowed_dir:
            resolved = Path(path).resolve()
            if not str(resolved).startswith(str(self.allowed_dir)):
                return "Error: Access denied (outside workspace)"
```

**Workspace Restriction**:
```
"tools": {
  "restrict_to_workspace": true  # ALL file operations confined to workspace
}
```

### 3.4 Input Validation

- URL validation (http/https only, no local file:// schemes)
- Parameter type checking against JSON schema
- Message length limits
- Redirect chain limits (5 max for web_fetch)

---

## 4. API ENDPOINTS & BOT COMMUNICATION

### 4.1 Communication Architecture

**No REST API** - Nanobot uses **event-driven async messaging**:

```
┌─────────────────────────────────────────┐
│       Chat Platforms (Channels)         │
│  Telegram / Discord / WhatsApp / etc.   │
└────────────────┬────────────────────────┘
                 │ (push messages via websocket/polling)
                 ▼
        ╔════════════════╗
        ║  Message Bus   ║
        ║  (AsyncQueue)  ║
        ╚════════════════╝
                 │ (consume)
                 ▼
        ╔════════════════╗
        ║  Agent Loop    ║
        ║  (process)     ║
        ╚════════════════╝
                 │ (publish response)
                 ▼
        ╔════════════════╗
        ║  Message Bus   ║
        ║  (Outbound)    ║
        ╚════════════════╝
                 │ (send)
                 ▼
┌────────────────────────────────────────┐
│    Chat Platforms (Send Messages)      │
└────────────────────────────────────────┘
```

### 4.2 Message Flow

**InboundMessage** (from channels):
```python
@dataclass
class InboundMessage:
    channel: str              # "telegram", "discord", "whatsapp"
    sender_id: str           # User ID from platform
    chat_id: str             # Chat/channel ID
    content: str             # Message text
    timestamp: datetime
    media: list[str]         # File paths of downloaded media
    metadata: dict           # Platform-specific data
    
    @property
    def session_key(self) -> str:
        return f"{self.channel}:{self.chat_id}"
```

**OutboundMessage** (to channels):
```python
@dataclass
class OutboundMessage:
    channel: str
    chat_id: str
    content: str
    reply_to: str | None      # Message ID to reply to
    media: list[str]
    metadata: dict
```

### 4.3 Gateway Command Interface

While there's no HTTP API, the CLI provides commands:

```bash
# Chat interface
nanobot agent -m "question"            # Single message
nanobot agent                          # Interactive mode

# Gateway (multi-channel listening)
nanobot gateway                        # Start all enabled channels

# Channel management
nanobot channels login                 # WhatsApp QR login
nanobot channels status                # Channel status

# Configuration
nanobot status                         # Show provider/channel status
nanobot onboard                        # Initialize config
```

### 4.4 No Public Webhook/IP Required

**Key Advantage**: All channels use push (polling or websocket):

| Channel | Method | Public IP Needed? |
|---------|--------|-------------------|
| Telegram | Long Polling | No |
| Discord | WebSocket | No |
| WhatsApp | WebSocket (local bridge) | No |
| Feishu | WebSocket Long Connection | No |
| DingTalk | Stream Mode | No |

---

## 5. CONFIGURATION SYSTEM

### 5.1 Config File Location & Format

**Location**: `~/.nanobot/config.json`

**Type**: Pydantic BaseSettings (TOML/JSON/ENV)

### 5.2 Configuration Schema

```python
# Root config
class Config(BaseSettings):
    agents: AgentsConfig           # Agent defaults (model, workspace)
    channels: ChannelsConfig       # Chat platform configs
    providers: ProvidersConfig     # LLM provider configs
    gateway: GatewayConfig         # Server settings
    tools: ToolsConfig             # Tool behavior (timeouts, restrictions)
```

### 5.3 Provider Configuration

**Currently Supported** (12 providers):

```json
{
  "providers": {
    "openrouter": {"api_key": "sk-or-v1-...", "api_base": null},
    "anthropic": {"api_key": "sk-ant-..."},
    "openai": {"api_key": "sk-..."},
    "deepseek": {"api_key": "sk-..."},
    "groq": {"api_key": "gsk-..."},
    "zhipu": {"api_key": "...", "api_base": "https://open.bigmodel.cn/api/v4"},
    "dashscope": {"api_key": "..."},
    "vllm": {"api_key": "dummy", "api_base": "http://localhost:8000/v1"},
    "gemini": {"api_key": "..."},
    "moonshot": {"api_key": "..."},
    "aihubmix": {"api_key": "...", "api_base": "https://aihubmix.com/v1"}
  }
}
```

### 5.4 Channel Configuration

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allow_from": ["123456789"],
      "proxy": "socks5://127.0.0.1:1080"
    },
    "discord": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allow_from": ["987654321"],
      "gateway_url": "wss://gateway.discord.gg/?v=10&encoding=json",
      "intents": 37377
    },
    "whatsapp": {
      "enabled": true,
      "bridge_url": "ws://localhost:3001",
      "allow_from": ["+1234567890"]
    },
    "feishu": {
      "enabled": true,
      "app_id": "cli_xxx",
      "app_secret": "xxx",
      "encrypt_key": "",
      "verification_token": "",
      "allow_from": []
    },
    "dingtalk": {
      "enabled": true,
      "client_id": "YOUR_APP_KEY",
      "client_secret": "YOUR_APP_SECRET",
      "allow_from": []
    }
  }
}
```

### 5.5 Tool Configuration

```json
{
  "tools": {
    "web": {
      "search": {
        "api_key": "BRAVE_API_KEY",
        "max_results": 5
      }
    },
    "exec": {
      "timeout": 60
    },
    "restrict_to_workspace": false
  }
}
```

### 5.6 Agent Configuration

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "model": "anthropic/claude-opus-4-5",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 20
    }
  }
}
```

### 5.7 Gateway Configuration

```json
{
  "gateway": {
    "host": "0.0.0.0",
    "port": 18790
  }
}
```

---

## 6. EXISTING MOBILE OR WEB INTERFACES

### 6.1 Current Status

**No Native Mobile/Web UI**. Nanobot is designed as a **backend service** that interfaces with existing platforms.

### 6.2 Current Access Methods

1. **CLI** (Local)
   - `nanobot agent` - Interactive chat
   - `nanobot agent -m "msg"` - Single query
   - Direct terminal input

2. **Chat Platforms** (Remote)
   - Telegram Bot (web/mobile via Telegram app)
   - Discord Bot (web/mobile via Discord app)
   - WhatsApp (mobile via WhatsApp app)
   - Feishu/DingTalk (web/mobile via native apps)

3. **No HTTP REST API** - Architecture is event-driven only

### 6.3 Web/Mobile Architecture for Future App

To build a mobile app controlling nanobot:

**Option A: Direct REST API** (would need to add)
```
Mobile App (iOS/Android)
    ↓ (HTTPS REST)
    ↓
Nanobot REST API Gateway
    ↓
Agent Loop
```

**Option B: WebSocket API** (better for real-time)
```
Mobile App (iOS/Android)
    ↓ (WebSocket)
    ↓
Nanobot WebSocket Server
    ↓
Message Bus
    ↓
Agent Loop
```

**Option C: Leverage Existing Platforms** (current approach)
```
Mobile App (iOS/Android)
    ↓ (use Telegram SDK)
    ↓
Telegram Bot
    ↓
Nanobot
```

---

## 7. QR CODE & PAIRING MECHANISMS

### 7.1 WhatsApp QR Code Auth

**Flow**:
```
1. User runs: nanobot channels login
2. Bridge starts and displays QR code in terminal
3. User opens WhatsApp on phone → Settings → Linked Devices → Scan QR
4. Authentication state saved to ~/.nanobot/whatsapp-auth/
5. User runs: nanobot gateway to activate

# Two terminals:
Terminal 1: nanobot channels login     # Keep running for scanning
Terminal 2: nanobot gateway            # Process messages
```

**Implementation** (`bridge/src/whatsapp.ts`):
```typescript
sock.ev.on('connection.update', (update) => {
  if (qr) {
    qrcode.generate(qr, { small: true });  // Display in terminal
    onQR(qr);  // Send to Python
  }
});
```

**Python Side** (`whatsapp.py`):
```python
async def _handle_bridge_message(self, raw: str):
    data = json.loads(raw)
    if data.get("type") == "qr":
        logger.info("Scan QR code in the bridge terminal to connect WhatsApp")
```

### 7.2 Telegram Bot Token

**No QR needed** - just get token from BotFather:
```
1. Search @BotFather in Telegram
2. Send /newbot
3. Follow prompts to get token
4. Add to config.json
5. nanobot gateway
```

### 7.3 Discord Bot Token

**No QR needed** - similar to Telegram:
```
1. Go to https://discord.com/developers/applications
2. Create app → Add Bot → Copy token
3. Configure intents (MESSAGE_CONTENT required)
4. Invite bot to server via OAuth2 URL
5. Add to config.json
```

### 7.4 Feishu/DingTalk App Credentials

**No QR needed** - direct credential setup:
```
1. Register app on platform
2. Get App ID + App Secret
3. Enable required permissions
4. Configure webhook or stream mode
5. Add to config.json
```

---

## 8. PROJECT STRUCTURE & TECH STACK

### 8.1 Complete Directory Tree

```
entobot/
├── nanobot/                          # Main Python package
│   ├── agent/                        # Core agent engine
│   │   ├── loop.py                   # Agent loop (LLM ↔ tool execution)
│   │   ├── context.py                # Prompt/context builder
│   │   ├── memory.py                 # Persistent memory
│   │   ├── skills.py                 # Skills loader
│   │   ├── subagent.py               # Background task execution
│   │   └── tools/                    # Built-in tools
│   │       ├── base.py               # Tool interface
│   │       ├── registry.py           # Tool registry
│   │       ├── filesystem.py         # read_file, write_file, edit_file, list_dir
│   │       ├── shell.py              # exec (with safety checks)
│   │       ├── web.py                # web_search, web_fetch
│   │       ├── message.py            # send_message (inter-agent)
│   │       ├── spawn.py              # spawn (background tasks)
│   │       └── cron.py               # cron (scheduled tasks)
│   │
│   ├── channels/                     # Chat platform integrations
│   │   ├── base.py                   # BaseChannel interface
│   │   ├── manager.py                # ChannelManager (coordinates all)
│   │   ├── telegram.py               # Telegram Bot API
│   │   ├── discord.py                # Discord Gateway WebSocket
│   │   ├── whatsapp.py               # WhatsApp Bridge WebSocket
│   │   ├── feishu.py                 # Feishu/Lark SDK
│   │   └── dingtalk.py               # DingTalk Stream Mode
│   │
│   ├── bus/                          # Message routing
│   │   ├── queue.py                  # AsyncQueue based MessageBus
│   │   └── events.py                 # InboundMessage, OutboundMessage
│   │
│   ├── providers/                    # LLM providers
│   │   ├── base.py                   # LLMProvider interface
│   │   ├── registry.py               # Provider registry (metadata)
│   │   ├── litellm_provider.py       # LiteLLM wrapper
│   │   └── transcription.py          # Groq Whisper transcription
│   │
│   ├── config/                       # Configuration
│   │   ├── schema.py                 # Pydantic config schema
│   │   └── loader.py                 # Config file loader
│   │
│   ├── session/                      # Session management
│   │   └── manager.py                # Session persistence (JSONL)
│   │
│   ├── cron/                         # Scheduled tasks
│   │   └── service.py                # Cron scheduler
│   │
│   ├── heartbeat/                    # Proactive wake-up
│   │   └── service.py                # Heartbeat scheduler
│   │
│   ├── skills/                       # Bundled skills
│   │   ├── github/                   # GitHub integration
│   │   ├── weather/                  # Weather API
│   │   ├── tmux/                     # Terminal multiplexer
│   │   ├── cron/                     # Cron skill
│   │   └── summarize/                # Text summarization
│   │
│   ├── cli/                          # Command-line interface
│   │   └── commands.py               # Typer CLI app
│   │
│   └── utils/                        # Utilities
│       └── helpers.py                # Helper functions
│
├── bridge/                           # WhatsApp Bridge (Node.js)
│   ├── src/
│   │   ├── index.ts                  # Entry point
│   │   ├── server.ts                 # WebSocket server
│   │   ├── whatsapp.ts               # Baileys wrapper
│   │   └── types.d.ts                # TypeScript definitions
│   ├── package.json                  # Node.js dependencies
│   └── tsconfig.json                 # TypeScript config
│
├── workspace/                        # Default workspace
│   ├── AGENTS.md                     # Agent documentation
│   ├── USER.md                       # User profile template
│   ├── SOUL.md                       # System instructions
│   ├── TOOLS.md                      # Tool descriptions
│   ├── HEARTBEAT.md                  # Heartbeat instructions
│   └── memory/                       # Long-term memory
│
├── tests/                            # Test suite
├── pyproject.toml                    # Python project config
├── README.md                         # Documentation
├── SECURITY.md                       # Security guidelines
├── COMMUNICATION.md                  # Community links
└── Dockerfile                        # Container image

# User data directory (created at runtime)
~/.nanobot/
├── config.json                       # User configuration
├── workspace/                        # User's workspace
├── sessions/                         # Conversation history (JSONL)
├── media/                            # Downloaded media files
├── whatsapp-auth/                    # WhatsApp auth state
├── history/                          # CLI history
└── logs/                             # Application logs
```

### 8.2 Tech Stack

#### **Backend (Python)**
```
Runtime:        Python 3.11+
Async:          asyncio
CLI:            Typer (argument parser + pretty output)
Config:         Pydantic 2.0+ with BaseSettings
Web Client:     httpx (async HTTP + SOCKS5)
Chat Libs:      python-telegram-bot, websockets
LLM:            LiteLLM (unified provider interface)
Logging:        Loguru
Markup:         Rich (terminal formatting)
Web Content:    readability-lxml (extract article content)
Cron:           croniter (schedule parsing)
```

#### **Bridge (Node.js)**
```
Runtime:        Node.js 18+
WhatsApp:       @whiskeysockets/baileys (7.0.0-rc.9)
WebSocket:      ws (8.17.1+) - DoS-fixed version
QR Terminal:    qrcode-terminal
Logging:        Pino
Language:       TypeScript 5.4+
```

#### **External Services**
```
LLM Providers:
  - OpenRouter (gateway)
  - Anthropic (Claude)
  - OpenAI (GPT)
  - DeepSeek
  - Groq (+ Whisper)
  - Google Gemini
  - Zhipu (GLM)
  - Dashscope (Qwen)
  - Moonshot (Kimi)
  - AiHubMix (gateway)
  - vLLM (local)

Chat Platforms:
  - Telegram (Bot API)
  - Discord (Gateway v10)
  - WhatsApp (via Baileys)
  - Feishu/Lark (Open API)
  - DingTalk (Stream Mode)

Transcription:
  - Groq Whisper

Web Search:
  - Brave Search API
```

### 8.3 Dependency Graph

```python
# Core dependencies (required for all)
typer >= 0.9.0                    # CLI
litellm >= 1.0.0                  # LLM routing
pydantic >= 2.0.0                 # Config/validation
websockets >= 12.0                # Async WebSocket
httpx[socks] >= 0.25.0            # HTTP client + SOCKS5
loguru >= 0.7.0                   # Logging
readability-lxml >= 0.8.0         # Web content extraction
rich >= 13.0.0                    # Terminal rendering
croniter >= 2.0.0                 # Cron scheduling
python-telegram-bot >= 21.0       # Telegram Bot API
websocket-client >= 1.6.0         # WebSocket client
lark-oapi >= 1.0.0                # Feishu SDK
dingtalk-stream >= 0.4.0          # DingTalk Stream SDK
socksio >= 1.0.0                  # SOCKS protocol

# Optional/Bridge
@whiskeysockets/baileys           # WhatsApp (Node.js)
ws ^8.17.1                        # WebSocket server (Node.js)
```

### 8.4 Code Metrics

```
Lines of Code:
  agent/loop.py:              377 lines
  channels/telegram.py:       401 lines
  channels/discord.py:        262 lines
  channels/whatsapp.py:       146 lines
  channels/feishu.py:         ~200 lines
  providers/registry.py:      ~300 lines
  Total core:                 ~3,448 lines

File Count:
  Python files:               ~25
  TypeScript files:           4
  Configuration files:        3
  Documentation:              8
```

### 8.5 Design Patterns Used

1. **Observer Pattern** - Message Bus (pub/sub)
2. **Strategy Pattern** - Channel implementations (unified interface)
3. **Registry Pattern** - Tool and Provider registries
4. **Factory Pattern** - Channel manager creation
5. **Decorator Pattern** - Tool parameter validation
6. **Template Method** - BaseChannel with implement methods
7. **State Machine** - Channel connection states
8. **Builder Pattern** - Context building for LLM

---

## 9. MOBILE APP INTEGRATION STRATEGY

### 9.1 Current Gap

Nanobot has **no built-in mobile API**. To control it from a mobile app, you need to either:

1. **Add a REST/GraphQL API layer** (recommended)
2. **Use existing chat platform SDKs** (Telegram bot SDK, Discord SDK)
3. **Leverage WebSocket for bidirectional communication**

### 9.2 Recommended Architecture for Mobile App

```
┌────────────────────────────────┐
│     Mobile App (iOS/Android)   │
│  - React Native / Flutter      │
│  - HTTPS + JWT Auth            │
└────────────────┬───────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │  Nanobot REST API   │ ← NEW LAYER
        │  (FastAPI/aiohttp)  │
        │                     │
        │  POST /chat         │
        │  GET  /history      │
        │  POST /session/new  │
        │  DELETE /session    │
        │  WS /stream         │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  Agent Loop         │
        │  Message Bus        │
        │  Tool Registry      │
        └─────────────────────┘
```

### 9.3 Required Authentication for Mobile App

```python
# Token-based authentication (JWT or API Key)
class MobileAuth:
    def __init__(self):
        self.api_keys = {}  # UUID -> encrypted key
        self.sessions = {}  # session_id -> {user_id, expires_at, allowed_tools}
    
    async def authenticate_request(token: str) -> User:
        # Verify JWT signature
        # Check expiration
        # Return user with allowed tools/constraints
        pass
```

### 9.4 Potential REST API Endpoints

```python
# Authentication
POST   /auth/register          # Create new user
POST   /auth/login             # Get JWT token
POST   /auth/refresh           # Refresh token
POST   /auth/logout            # Invalidate token

# Messaging
POST   /chat                   # Send message
GET    /history                # Get conversation history
GET    /history/{session_id}   # Get specific session

# Sessions
GET    /sessions               # List sessions
POST   /sessions               # Create new session
DELETE /sessions/{id}          # Delete session
PUT    /sessions/{id}/reset    # Reset history

# Agent Status
GET    /status                 # Agent/provider status
GET    /tools                  # Available tools
GET    /capabilities           # Agent capabilities

# Settings
GET    /config                 # User configuration
POST   /config                 # Update configuration
DELETE /data                   # Erase all user data

# Streaming
WS     /stream                 # WebSocket for real-time updates
```

### 9.5 Security for Mobile App

**Crucial Considerations**:

1. **Authentication & Authorization**
   ```python
   # JWT with short expiration + refresh tokens
   {
     "user_id": "uuid",
     "scope": ["read:chat", "write:chat"],
     "exp": 1704067200,
     "iss": "nanobot"
   }
   ```

2. **Rate Limiting**
   - Per user/API key
   - Tool execution limits
   - API call quotas

3. **Tool Access Control**
   ```python
   # Restrict certain tools per user
   user_config.allowed_tools = [
       "web_search",
       "web_fetch"
       # NOT: "shell exec", "file_write"
   ]
   ```

4. **Data Privacy**
   - Encrypt conversation history at rest
   - HTTPS only
   - No logging of sensitive data
   - User data deletion on request

5. **Rate Limiting & Timeouts**
   ```
   - 100 requests/hour per user
   - 5 minute timeout per message
   - 1000 concurrent users max
   ```

---

## 10. SECURITY & OPERATIONAL RECOMMENDATIONS

### 10.1 Pre-Production Checklist

- [x] API keys in config (not hardcoded)
- [x] Config file permissions: `chmod 600`
- [x] `allowFrom` lists configured
- [x] Run as non-root user
- [x] File permissions on workspace
- [x] Dependencies updated (`pip-audit`, `npm audit`)
- [x] Logs monitored for errors
- [x] Rate limits on providers
- [x] Backup strategy for sessions
- [x] Security review of custom skills

### 10.2 Dangerous Features to Monitor

1. **Shell Execution** - Tool can run arbitrary commands
   - Blocked patterns protect against major attacks
   - But sophisticated attacks possible
   - Recommendation: Run in isolated container

2. **File Write Access** - Can modify filesystem
   - Restricted to workspace if `restrict_to_workspace: true`
   - Without restriction, can write anywhere user has access

3. **Web Fetch** - Can download large files
   - Max 20MB attachment size (Discord)
   - No built-in rate limiting
   - Could exhaust disk space

### 10.3 Docker Deployment

```bash
# Build image
docker build -t nanobot .

# Initialize config
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot onboard

# Run gateway
docker run -v ~/.nanobot:/root/.nanobot -p 18790:18790 nanobot gateway

# Single command
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot agent -m "Hello"
```

---

## CONCLUSION

**Nanobot** is a lightweight, modular AI assistant framework designed for:
- Multiple chat platform integration
- LLM provider flexibility
- Tool extensibility
- Container deployment

**For a mobile app**, you would need to:
1. Add REST/WebSocket API layer
2. Implement JWT authentication
3. Add rate limiting & access control
4. Restrict tools available to mobile users
5. Ensure data encryption & privacy

The existing architecture supports this well due to its clean separation between channels, agent logic, and tools.

