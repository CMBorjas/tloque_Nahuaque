# Tloque Nahuaque: Zero-Knowledge Private Cloud Orchestrator

## Overview

Tloque Nahuaque is an open-source, local-first orchestration platform designed to bridge the gap between high-security self-hosting and non-technical business operations. It provides a streamlined interface for deploying a pre-configured stack of privacy-centric services—including document management, credential vaulting, and local LLMs—via a single command.

The project addresses the growing need for small enterprises (legal, medical, and financial) to maintain data sovereignty without the overhead of a dedicated IT department or the security risks of public SaaS providers.

## Core Features

* **One-Touch Deployment:** Automated Docker orchestration that handles container lifecycle, networking, and volume persistence.
* **Conversational SysAdmin:** A natural language interface (powered by Ollama) that allows users to manage their server environment — supports single and multi-intent commands in plain English.
* **Desktop Pet (Nahua):** A draggable desktop companion that floats on your screen, shows random chatter, receives Discord notifications, and lets you chat with the orchestrator from anywhere.
* **Discord Integration:** A bot bridge that forwards Discord DMs and mentions to the orchestrator backend, with notification bubbles on the desktop pet.
* **Air-Gapped Design:** Engineered to run entirely on a local network with optional encrypted tunneling for remote access.
* **Resource Monitoring:** Real-time visualization of CPU, RAM, and storage health tailored for consumer-grade hardware.
* **Smart Inventory Tracking:** Tracks dynamic business inventories and automatically generates customized procurement tasks when supplies fall below defined thresholds.
* **Automated Disaster Recovery:** Scheduled, encrypted snapshots of all system data and configurations, ensuring rapid recovery from failures.
* **Compliance & Audit Logging:** Aggregated, exportable system logs across all applications to simplify regulatory compliance (e.g., HIPAA/GDPR) reporting.

## Prerequisites

* **Python 3.10+**
* **Node.js 18+** and npm
* **Docker Engine 24.0+** and Docker Compose V2
* **Ollama** running locally (default port 11434)
* Minimum 8GB RAM (16GB recommended for LLM usage)

### Supported Platforms

| Platform | Status |
|----------|--------|
| macOS (Apple Silicon / Intel) | Fully supported |
| Windows 10/11 | Fully supported |
| Linux (Ubuntu 22.04+, etc.) | Fully supported |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/CMBORJAS/tloque_Nahuaque.git
cd tloque_Nahuaque
```

### 2. Pull an Ollama model

The SysAdmin AI requires a local LLM. Pull one before starting:

```bash
ollama pull qwen3.5:latest
```

### 3. Start everything

**macOS / Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

This single command starts:
- Backend API on `http://localhost:8000`
- Frontend UI on `http://localhost:5173`
- Nahua desktop pet on your screen

### 4. Stop everything

**macOS / Linux:**
```bash
./stop.sh
```

**Windows:**
```cmd
stop.bat
```

## Desktop Pet (Nahua)

Nahua is a pixel-art robot companion that lives on your desktop — not limited to the browser.

- **Drag** it anywhere on your screen
- **Click** to open a chat window (talks to the orchestrator backend)
- **Right-click** to quit
- Shows random idle chatter and system tips
- Displays Discord DM/mention notifications as purple bubbles

### Discord Notifications

To enable Discord notifications on the pet, create a `.env` file in the project root:

```
DISCORD_BOT_TOKEN=your_bot_token_here
```

The pet will connect to Discord and show incoming DMs and mentions as notification bubbles.

### Auto-Start on Login (macOS)

```bash
launchctl load ~/Library/LaunchAgents/com.nahua.desktoppet.plist
```

To disable:
```bash
launchctl unload ~/Library/LaunchAgents/com.nahua.desktoppet.plist
```

## Architecture

The system is built on a modular microservices architecture:

* **Orchestrator Engine:** A Python-based backend (FastAPI) utilizing the Docker SDK to manage container states and network configurations.
* **Management UI:** A responsive React + TypeScript dashboard (Vite) with pages for health/telemetry, orchestration, inventory, compliance, and SysAdmin AI chat.
* **Desktop Pet:** A PyQt6 native application that overlays on the desktop with chat and Discord integration.
* **Discord Bot:** An async bridge that forwards Discord messages to the orchestrator API.

## Orchestrator Modules

| Module | Description |
|--------|-------------|
| `core/docker_client.py` | Docker SDK wrapper for container lifecycle, volumes, and image pulls |
| `api/server.py` | FastAPI server exposing REST endpoints for the UI |
| `ai/nlp_agent.py` | Conversational SysAdmin — maps natural language to intents via Ollama (supports multi-intent) |
| `business/inventory_manager.py` | Inventory tracking with threshold-based procurement task generation |
| `monitor/telemetry.py` | Real-time CPU, RAM, and disk usage metrics |
| `backup/snapshot_manager.py` | Docker volume backup and disaster recovery |
| `compliance/audit_logger.py` | Tamper-evident audit logs for compliance |
| `discord_bot.py` | Discord bot bridge for remote orchestrator control |
| `desktop_pet.py` | Nahua — the desktop pet companion |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Backend health check |
| GET | `/api/inventory` | List all inventory items |
| POST | `/api/inventory` | Add/update an inventory item |
| POST | `/api/inventory/consume` | Consume stock |
| GET | `/api/inventory/tasks` | List procurement tasks |
| PATCH | `/api/inventory/tasks/{id}` | Update task status |
| POST | `/api/chat` | Send natural language command to SysAdmin AI |
| POST | `/api/orchestration/deploy` | Deploy the service stack |
| GET | `/api/orchestration/status` | List running containers |
| POST | `/api/orchestration/backup` | Backup a Docker volume |
| GET | `/api/system/telemetry` | System metrics (CPU, RAM, disk) |
| GET | `/api/compliance/audit` | Audit logs |

## Included Service Stack

The default deployment includes:

1. **Nextcloud:** Collaborative file storage and document editing.
2. **Vaultwarden:** Bitwarden-compatible credential management.
3. **Ollama:** Localized Large Language Models for private data analysis.
4. **Uptime Kuma:** Service monitoring and notification system.
5. **Authentik:** Centralized identity proxy and SSO provider.
6. **Cal.com:** Self-hosted appointment scheduling.
7. **ERPNext (Core):** Lightweight CRM and internal invoicing.
8. **Mattermost:** Secure team communication platform.

## Security Model

Tloque Nahuaque follows the principle of least privilege. All containers are networked in isolation, and the management API is bound to the local loopback interface by default. Data is stored in encrypted volumes, ensuring that even if the hardware is compromised, the business data remains protected.

## License

Distributed under the MIT License. See LICENSE for more information.
