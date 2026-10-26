# Project Overview: Spanner Omni GraphRAG Pickleball Coach

## Executive Summary

The Spanner Omni GraphRAG Pickleball Coach is an interactive, full-stack application combining distributed relational database technology with generative AI agents. Built with Flask, Google Cloud Spanner Omni, and generative LLMs, the platform simulates a 2.5D visual pickleball court where human players compete against an adaptive AI opponent while receiving real-time tactical coaching grounded in ACID database records.

---

## Origin and Upstream Attribution

This project is an extended implementation based on the original Spanner Omni Pickleball Game authored by **Abirami Sukumaran** ([AbiramiSukumaran/pickleball](https://github.com/AbiramiSukumaran/pickleball)).

The upstream project introduced:
- The 2.5D visual court canvas and 60 FPS ball physics engine.
- Spanner Omni table designs and relational graph structures for shots and transitions.
- The foundational prompt engineering for AI tactical coaching.
- The single-page dashboard architecture.

This repository preserves the original work while providing substantial extensions for local execution, modular provider architecture, security auditing, and comprehensive documentation.

---

## Architectural Enhancements in this Repository

### 1. Modular AI Provider Architecture
The original application relied exclusively on hosted Google Gemini API calls. This project decouples AI inference into a provider-agnostic service ([`ai_service.py`](file:///D:/code_vipasana/pickleball/ai_service.py)) supporting:
- **Local Gemma 4** via a local Ollama Docker container (`gemma4:e2b`).
- **Google Gemini API** (`gemini-3.8-flash`) via the modern `google-genai` SDK.
- Single-variable runtime switching via `LLM_PROVIDER` in `.env`.

### 2. Local Container Integration & Port Bridge
The Spanner Omni container runs in single-server mode listening internally on port 15000 while published to host port 9010. A lightweight proxy bridge allows standard client libraries to connect without host networking constraints.

### 3. Reliability & Encoding Fixes
- Added UTF-8 stdout reconfiguration in Python to prevent Windows console `UnicodeEncodeError` when emitting game emojis.
- Corrected database creation DDL statement application to align with modern `google-cloud-spanner` v3.40+ library specifications.

### 4. Comprehensive Testing Suite
Introduced [`test_ai_service.py`](file:///D:/code_vipasana/pickleball/test_ai_service.py) with 20 automated tests validating provider selection, timeout enforcement, fallback prevention, credential sanitization, and API route responses.

---

## Core Components

| Component | Technology | Responsibility |
| :--- | :--- | :--- |
| Frontend Arena | HTML5 Canvas, Tailwind CSS, Web Audio API | 2.5D visual simulation, real-time telemetry display, concierge chat interface |
| Backend Server | Python 3.13, Flask 3.0 | API routes, transaction orchestration, AI service coordination |
| Database Engine | Google Cloud Spanner Omni | Distributed ACID transactions, court bookings, match history, graph telemetry |
| AI Inference Layer | Local Gemma 4 (Ollama) / Gemini API | Tactical shot advice, rally post-mortem analysis, rule concierge |

---

## Current Status

- Spanner Omni: Operational and verified on `localhost:9010`.
- Local Gemma 4: Operational and verified on `http://localhost:8080`.
- Google Gemini API: Verified via `google-genai` client.
- Test Suite: 20 passed unit and integration tests.
