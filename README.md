<div align="center">

<img src="docs/hero.svg" alt="RADNEX Cyber Engine" width="100%" />

# RADNEX

### Autonomous Terminal Cyber Shell & Next-Gen Multi-Gateway Intelligence Mesh

**Architect & Author:** [Chandan Pandey](https://github.com/thecnical) (`@thecnical`)

[![License: MIT](https://img.shields.io/badge/License-MIT-00ff41.svg?style=flat-square)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-00ff41.svg?style=flat-square&logo=python&logoColor=00ff41)](https://www.python.org/)
[![Platform: Linux / WSL2](https://img.shields.io/badge/Platform-Linux%20%2F%20WSL2-00ff41.svg?style=flat-square&logo=linux&logoColor=00ff41)](https://kernel.org/)
[![Architecture: Dual--Tier Hybrid](https://img.shields.io/badge/Architecture-Dual--Tier%20Hybrid-00ff41.svg?style=flat-square)](https://github.com/thecnical/Radnex)
[![Zero-Downtime Smart Routing](https://img.shields.io/badge/Zero--Downtime-Smart%20Routing%20(100%25%20Free)-00ff41.svg?style=flat-square)](https://github.com/thecnical/Radnex)

<br/>

<img src="docs/radnex-3d-arch.svg" alt="RADNEX 3D Multi-Tier Isometric Architecture" width="100%" />

<br/>

</div>

---

## ⚡ Overview

**RADNEX** is an ultra-fast, autonomous terminal cyber shell, offensive reconnaissance orchestrator, and AI-driven security engineering platform. Engineered from the ground up for elite security researchers, bug hunters, and DevOps engineers, RADNEX operates directly inside your Linux terminal with an uncompromising high-fps cyber-matrix interface, live streaming telemetry, and full-spectrum automation.

Unlike standard LLM interfaces that stall on single endpoints or rack up expensive API bills, RADNEX features an **Autonomous Cloud Gateway Mesh** that continuously balances and auto-failovers across **8 premier cloud gateways**—strictly prioritizing verified **100% Free AI models** with zero cost and zero downtime.

<div align="center">
  <img src="docs/terminal.svg" alt="RADNEX Interactive Cyber Terminal Session" width="100%" />
</div>

---

## 🛡️ Key Pillars & Breakthrough Features

### 1. 🔄 Zero-Downtime Smart Routing (100% Free AI Guarantee)
- **Zero Cost, Continuous Uptime:** Never get blocked by 429 rate limits or vendor maintenance. If one gateway hiccups, RADNEX instantly fails over to another live gateway in milliseconds.
- **Strict Free Pinning:** Automatically identifies and routes strictly to verified 0-cost / free-tier models (such as `deepseek-v4.1:free`, `gemini-2.0-flash`, `qwen4-72b:free`, `glm-4.5-flash`), eliminating unexpected credit depletion.

### 2. ⚡ Anthropic Ephemeral Prompt Caching (90% Cost & Latency Reduction)
- Full compatibility with prompt-caching headers on Anthropic-compatible endpoints.
- Re-sends system prompts, active doctrines (`AGENTS.md`), and workspace context without recomputing tokens on every turn.
- Measured latency cuts of up to **90%** on prolonged multi-turn autonomous hunts.

### 3. 🧠 Dual-Tier Hybrid Intelligence (Fast Scout + Heavy Architect)
- **Fast Scout Tier:** Low-latency, fast-response models (`gemini-2.0-flash`, `deepseek-flash`, `glm-4-air`) handle real-time reconnaissance, port scans, tool parameter extraction, and web crawling.
- **Heavy Architect Tier:** High-reasoning heavy engines (`deepseek-chat`, `qwen4-72b`, `llama-3.3-70b`) take over for threat modeling, complex code auditing, exploit synthesis, and final case reporting.

### 4. ⏪ Git Shadow Checkpoints & Instant Rollback (`/undo`)
- Automatic shadow git tree commits before any file modification, patch execution, or bash manipulation.
- Type `/undo` in the shell at any moment to atomically revert the workspace to its exact prior state.
- Inspect complete diffs before approving or reverting changes.

### 5. 📡 Headless Daemon & Background Webhooks (`/webhook`)
- Run long-running campaigns in the background with `--headless`.
- Real-time notification dispatch via Discord, Slack, and generic JSON webhooks upon milestone completion, critical vulnerability discovery, or hunt completion.

### 6. 🪟 Multi-Pane Matrix Orchestration (`/panes`)
- Native tmux integration (`ctrl+b h` / `ctrl+b v`) spawning dedicated Radnex instances in parallel panes.
- Inter-agent mailbox system (`agent_send`, `agent_peers`, `agent_inbox`) enabling cooperative red-team swarming without leaving the terminal.

---

## 🌐 Supported Cloud Gateway Matrix

RADNEX comes with pre-integrated support for 8 premier gateway providers:

| Gateway | Type | Free Models Available | Authentication / Setup |
| :--- | :--- | :--- | :--- |
| **APInex** | Cloud API | DeepSeek-V4.1, Gemini 2.5 Flash, GLM-4.5, Qwen Coder | `/apinex-api-setup` |
| **Radox AI** | Cloud API | DeepSeek V3, Gemini 2.0 Flash, Claude 3.5 Haiku, GPT-4o Mini | `/radox-api-setup` |
| **OpenRouter** | Multi-Provider | DeepSeek V4.1, Qwen4 72B, Llama 3.3 70B, GLM-6 Air | `/openrouter-api-setup` |
| **UnoRouter** | Anthropic Mesh | DeepSeek Chat, Qwen 2.5 Coder, Gemini Flash Exp | Integrated / Profile |
| **AIHubMix** | Unified Gateway | GLM-5.3 Flash, Qwen 3.8 Flash, Union Alpha | Integrated / Profile |
| **TokenHarbour** | High-Cap Mesh | DeepSeek Chat Free, Qwen 2.5 Coder Free, Gemini Flash | Integrated / Profile |
| **AntSeed** | P2P / Distributed | Distributed Free Peers & Mesh Nodes | Integrated / Profile |
| **Logfare** | Dedicated Proxy | DeepSeek V4.1 Flash, Qwen 3.8 27B | Integrated Default |

---

## 🚀 Quickstart & Installation

### Requirements
- **OS:** Linux (Ubuntu, Debian, Arch, Fedora) or WSL2 on Windows
- **Python:** 3.10, 3.11, 3.12, 3.13, or 3.14
- **Dependencies:** `git`, `curl`, `tmux` (optional, for `/panes`)

### Automated One-Line Install
```bash
curl -fsSL https://raw.githubusercontent.com/thecnical/Radnex/main/install.sh | bash
```

### Manual Developer Setup
```bash
# 1. Clone repository
git clone https://github.com/thecnical/Radnex.git
cd Radnex

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode
pip install -e .

# 4. Launch Radnex Cyber Shell
radnex
```

---

## 🎮 Operational Modes

Switch modes dynamically inside the session using `/mode <name>` or launch directly with `radnex --mode <name>`:

| Mode | Safety Gates | Description |
| :--- | :--- | :--- |
| **`default`** | Full Guardrails | Interactive coding, project maintenance, and safe analysis with human confirmations. |
| **`zim`** | Doctrine Enforced | Autonomous red-team reconnaissance governed strictly by `AGENTS.md` and target scope. |
| **`danger`** | Low-Impact Active | Active reconnaissance and low-impact probing permitted without confirmation halts. |
| **`uncensored`** | Unrestricted | Direct execution bypass for deep authorized vulnerability assessment and raw payload testing. |
| **`plan`** | Read-Only | Static analysis, architecture review, and playbook generation. All write/bash tools hidden. |
| **`edits`** | File Modification | File inspection and editing enabled; shell command execution disabled. |

---

## ⌨️ Command Reference

| Slash Command | Function |
| :--- | :--- |
| `/status` | Display active gateway, current model, token usage, and session health. |
| `/model [name]` | List available upstream models or switch to a specific model. |
| `/mode [name]` | Inspect or switch operational safety mode (`default`, `zim`, `danger`, etc.). |
| `/panes` | Relaunch into tmux multi-pane workspace with horizontal/vertical agent splits. |
| `/undo` | Rollback the most recent file change using git shadow checkpoints. |
| `/webhook <url>` | Configure destination URL for real-time notifications and milestone dispatches. |
| `/target <domain>` | Declare target in scope for autonomous reconnaissance. |
| `/osint <kind> <target>` | Trigger dedicated OSINT reconnaissance playbook (email, phone, domain, user). |
| `/think` | Toggle display of internal model reasoning / thinking stream. |
| `/compact` | Manually compress conversation history to optimize context window. |

---

## 📁 Repository Structure

```text
Radnex/
├── radnex/                  # Core engine package
│   ├── ui/                  # Textual cyber matrix TUI, widgets, boot splash
│   ├── routing.py           # Zero-Downtime Smart Failover & Free Model Registry
│   ├── shadow.py            # Git Shadow Checkpoints & Instant Rollback (/undo)
│   ├── webhook.py           # Background Dispatcher (Discord / Slack / Generic)
│   ├── apinex.py            # APInex gateway driver
│   ├── radox.py             # Radox AI gateway driver
│   ├── openrouter.py        # OpenRouter gateway driver
│   ├── unorouter.py         # UnoRouter gateway driver
│   ├── aihubmix.py          # AIHubMix gateway driver
│   ├── tokenharbour.py      # TokenHarbour gateway driver
│   ├── antseed.py           # AntSeed gateway driver
│   ├── logfare.py           # Logfare gateway driver
│   ├── agent.py             # ReAct loop, tool dispatch, and reasoning
│   ├── tools.py             # Full toolset (bash, files, web fetch, search)
│   └── panes.py             # tmux multi-pane orchestration & inter-agent IPC
├── docs/                    # Architectural diagrams & SVG assets
│   ├── hero.svg             # Cyber engine logo & author attribution
│   ├── radnex-3d-arch.svg   # 3D isometric multi-tier architecture diagram
│   └── terminal.svg         # Animated TUI session demonstration
├── tests/                   # Comprehensive test suites (500+ unit & integration tests)
├── install.sh               # One-line universal installer
├── pyproject.toml           # Project metadata & entrypoints
└── README.md                # Comprehensive documentation
```

---

## 👨‍💻 Author & Maintainer

**Chandan Pandey (`thecnical`)**  
- **GitHub:** [@thecnical](https://github.com/thecnical)  
- **Project Repository:** [https://github.com/thecnical/Radnex](https://github.com/thecnical/Radnex)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
