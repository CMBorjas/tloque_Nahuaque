# Tloque Nahuaque: Zero-Knowledge Private Cloud Orchestrator

## Overview

Tloque Nahuaque is an open-source, local-first orchestration platform designed to bridge the gap between high-security self-hosting and non-technical business operations. It provides a streamlined interface for deploying a pre-configured stack of privacy-centric services—including document management, credential vaulting, and local LLMs—via a single command.

The project addresses the growing need for small enterprises (legal, medical, and financial) to maintain data sovereignty without the overhead of a dedicated IT department or the security risks of public SaaS providers.

## Core Features

* **One-Touch Deployment:** Automated Docker orchestration that handles container lifecycle, networking, and volume persistence.
* **Conversational SysAdmin:** A natural language interface that allows users to manage their server environment (updates, backups, and logs) without using a terminal.
* **Air-Gapped Design:** Engineered to run entirely on a local network with optional encrypted tunneling for remote access.
* **Resource Monitoring:** Real-time visualization of CPU, RAM, and storage health tailored for consumer-grade hardware.
* **Smart Inventory Tracking:** Tracks dynamic business inventories and automatically generates customized procurement tasks when supplies fall below defined thresholds, tailored to the specific needs of the business.
* **Centralized Identity Management (SSO):** Single Sign-On capabilities allowing administrators to provision and revoke employee access across all services from one unified portal.
* **Automated Disaster Recovery:** Scheduled, encrypted snapshots of all system data and configurations, ensuring rapid recovery from localized failures or data corruption.
* **Integrated Booking & CRM:** Built-in scheduling and lightweight client management capabilities, keeping all customer data and appointments strictly on-premises.
* **Secure Internal Comms & Ticketing:** On-premise team chat and internal helpdesk to securely discuss sensitive client details and track IT requests.
* **Compliance & Audit Logging:** Aggregated, exportable system logs across all applications to simplify regulatory compliance (e.g., HIPAA/GDPR) reporting.

## Long-Term Sustainability

To guarantee that Tloque Nahuaque remains a sustainable, future-proof solution for small businesses, the architecture natively ensures:
* **Zero Vendor Lock-In:** All configurations and backups are stored in standard formats (e.g., JSON, YAML, SQL dumps). If a business chooses to migrate away, their data remains fully accessible and portable.
* **Automated Lifecycle Management:** The Orchestrator Engine handles both updates and rollbacks, removing the burden of manual version control from the user.
* **Hardware Agnostic Migration:** The entire environment is containerized. Moving the system to a new, more powerful server in the future simply requires migrating the encrypted Docker volumes and re-running the setup script.
* **Modular Ecosystem:** Users can disable any service they do not need, minimizing CPU/RAM footprint and ensuring the platform scales accurately with the operational growth of the business.

## Architecture

The system is built on a modular microservices architecture to ensure stability and ease of updates:

* **Orchestrator Engine:** A Python-based backend utilizing the Docker SDK to manage container states and network configurations.
* **Management UI:** A responsive React-based dashboard focused on accessibility and clear status reporting.
* **Service Mesh:** Pre-configured Traefik or Nginx Proxy Manager instance for handling internal routing and automated SSL via Let's Encrypt or local CA.

## Orchestrator Inventory

The **Orchestrator Engine** is composed of several key components and modules that work together to manage the self-hosted environment:

* **`core/docker_client.py`:** Interacts safely with the Docker SDK to handle container lifecycle, volumes, and persistent storage.
* **`core/network_manager.py`:** Manages isolated Docker networks and proxy configurations for the Service Mesh.
* **`api/server.py`:** A lightweight API server (e.g., FastAPI) exposing endpoints for the Management UI.
* **`services/catalog.yml`:** The default service registry defining the configurations and environment requirements for the core stack.
* **`business/inventory_manager.py`:** Tracks physical or resource inventories and hooks into the task generation pipeline to alert or create workflows when stock drops below thresholds.
* **`ai/nlp_agent.py`:** The Conversational SysAdmin interface that interprets user prompts via the local LLM to execute management tasks.
* **`monitor/telemetry.py`:** Gathers real-time resource usage statistics (CPU, RAM, Disks) for the dashboard.
* **`security/sso_bridge.py`:** Synchronizes unified authentication and role-based access control policies across all running containers.
* **`backup/snapshot_manager.py`:** Orchestrates routine, off-site encrypted data backups and manages emergency recovery procedures.
* **`compliance/audit_logger.py`:** Aggregates container and access logs to provide tamper-evident reports for compliance reviews.

## Included Service Stack

The default "Ghost-Host" deployment includes the following enterprise-grade tools:

1.  **Nextcloud:** Collaborative file storage and document editing.
2.  **Vaultwarden:** Bitwarden-compatible credential and secret management.
3.  **Ollama:** Localized Large Language Models for private data analysis.
4.  **Uptime Kuma:** Service monitoring and notification system.
5.  **Authentik:** Centralized identity proxy and single sign-on (SSO) provider.
6.  **Cal.com:** Self-hosted infrastructure for privacy-first appointment scheduling and bookings.
7.  **ERPNext (Core):** Lightweight open-source CRM and internal invoicing.
8.  **Mattermost:** Secure, local-first team communication platform.

## Prerequisites

* Linux-based OS (Ubuntu 22.04 LTS or Garuda Linux recommended)
* Docker Engine 24.0+
* Docker Compose V2
* Minimum 8GB RAM (16GB recommended for LLM usage)

## Installation

1. Clone the repository:
   `git clone https://github.com/CMBORJAS/tloque_Nahuaque.git`

2. Navigate to the directory:
   `cd tloque_Nahuaque`

3. Initialize the setup script:
   `./setup.sh`

4. Access the dashboard:
   Open `http://localhost:8080` in your browser.

## Security Model

Tloque Nahuaque follows the principle of least privilege. All containers are networked in isolation, and the management API is bound to the local loopback interface by default. Data is stored in encrypted volumes, ensuring that even if the hardware is compromised, the business data remains protected.

## License

Distributed under the MIT License. See LICENSE for more information.