# Windows Local Setup Guide

This guide covers complete local deployment of Spanner Omni, Ollama Gemma 4, and the Flask application on Windows 11 using PowerShell.

---

## 1. Prerequisites

Ensure the following tools are installed and accessible in your system PATH:

- **Windows 11** (64-bit)
- **Docker Desktop** (WSL 2 backend enabled)
- **Python 3.13** or Python 3.11+
- **Git for Windows**
- **PowerShell 7+** or Windows PowerShell 5.1

Verify tool versions:

```powershell
docker --version
python --version
git --version
```

---

## 2. Directory Navigation

Open Windows PowerShell and navigate to the project directory:

```powershell
cd D:\code_vipasana\pickleball
```

---

## 3. Persistent Storage & Spanner Omni Setup

### Initial Volume Creation

```powershell
docker volume create spanner_omni_data
```

### Pulling Spanner Omni Image

```powershell
docker pull us-docker.pkg.dev/spanner-omni/images/spanner-omni:2026.r2.1-beta
```

### Launching Spanner Omni Container

```powershell
docker run -d --name spanner-omni -p 9010:9010 -p 9020:9020 -v spanner_omni_data:/spanner us-docker.pkg.dev/spanner-omni/images/spanner-omni:2026.r2.1-beta start-single-server
```

### Restarting an Existing Spanner Container

```powershell
docker start spanner-omni
```

### Enabling Port Forwarding Bridge

Spanner Omni single-server listens internally on port 15000. Start the port forwarder:

```powershell
docker exec -d spanner-omni nc -L -p 9010 nc 127.0.0.1 15000
```

### Verifying Spanner Readiness

```powershell
docker logs --tail 10 spanner-omni
docker exec spanner-omni /google/spanner/bin/spanner databases list
```

---

## 4. Local Gemma 4 via Ollama Setup (Optional)

Start the existing Gemma 4 Ollama container:

```powershell
docker start gemma4-ollama-instance
```

Verify available models:

```powershell
docker exec gemma4-ollama-instance ollama list
Invoke-RestMethod -Uri "http://localhost:8080/api/tags" -Method Get
```

---

## 5. Python Environment & Dependencies

### Virtual Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Dependency Installation

```powershell
pip install -r requirements.txt
```

---

## 6. Environment Configuration

Copy the example template to create your local `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` to configure your chosen provider (`LLM_PROVIDER=ollama` or `LLM_PROVIDER=gemini`).

---

## 7. Starting the Application

Ensure UTF-8 console output is active to avoid emoji rendering errors:

```powershell
$env:PYTHONUTF8="1"
python app.py
```

Open your browser and navigate to:

`http://localhost:5000`
