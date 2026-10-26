# Contribution & Attribution Notice

## Upstream Project and Attribution

This project is an extended implementation based on the original **Spanner Omni Pickleball Game** created by **Abirami Sukumaran** ([AbiramiSukumaran](https://github.com/AbiramiSukumaran)), hosted at:

[https://github.com/AbiramiSukumaran/pickleball](https://github.com/AbiramiSukumaran/pickleball)

The upstream project provided the foundation for:
- 2.5D visual pickleball court simulation and canvas rendering.
- Ball trajectory physics and character animations.
- Spanner Omni database schema definitions (`Courts`, `Players`, `Bookings`, `MatchRequests`, `CourtZones`, `Shots`, `ShotTransitions`, `GameSessions`).
- Grounded RAG prompt templates for AI tactical coaching.
- Single-page dashboard UI using Tailwind CSS.

---

## License Compliance

The original work is licensed under the **Apache License, Version 2.0** ([`LICENSE`](file:///D:/code_vipasana/pickleball/LICENSE)).

In compliance with Section 4 of the Apache License:
1. A full copy of the original Apache License 2.0 is retained in the root directory.
2. Original copyright notices and authorship acknowledgements are preserved.
3. All local extensions, changes, and additions are prominently documented below.

---

## Record of Local Extensions and Enhancements

The following contributions were created and verified by **Shivakumar Sullagaddi** ([Shivakumarsullagaddi](https://github.com/Shivakumarsullagaddi)):

### 1. Modular AI Provider Interface ([`ai_service.py`](file:///D:/code_vipasana/pickleball/ai_service.py))
- Designed and implemented a provider-independent AI layer.
- Added [`OllamaProvider`](file:///D:/code_vipasana/pickleball/ai_service.py) connecting to local Gemma 4 (`gemma4:e2b`).
- Retained [`GeminiProvider`](file:///D:/code_vipasana/pickleball/ai_service.py) supporting hosted `gemini-3.8-flash` via the `google-genai` SDK.
- Implemented single-variable provider switching via `LLM_PROVIDER` in `.env`.
- Added automatic thinking tag sanitization (`<thought>...</thought>`) for local model outputs.
- Enforced strict failure isolation preventing silent cross-provider fallbacks.

### 2. Spanner Omni Container Integration & Stability
- Diagnosed single-server port architecture (internal port 15000 vs published port 9010) and established an automated bridge forwarder.
- Resolved Windows cp1252 console encoding crashes by enabling explicit UTF-8 reconfiguration for game emojis.
- Fixed Spanner database creation parameter syntax in [`app.py`](file:///D:/code_vipasana/pickleball/app.py) to match modern Google Cloud Spanner SDK standards.
- Supported automatic target resolution between `default/default` and emulator configurations.

### 3. Dynamic UI Status Reporting
- Updated [`templates/index.html`](file:///D:/code_vipasana/pickleball/templates/index.html) to dynamically display active AI provider badges, health states, and model versions via `/api/status`.
- Replaced hardcoded Gemini labels with dynamic provider indicators.

### 4. Comprehensive Testing & Verification ([`test_ai_service.py`](file:///D:/code_vipasana/pickleball/test_ai_service.py))
- Built a 20-test automated suite using `unittest` verifying provider selection, timeout enforcement, failure handling, route compatibility, and credential leak prevention.

### 5. Documentation Architecture
- Created a comprehensive 7-part documentation suite in [`docs/`](file:///D:/code_vipasana/pickleball/docs/README.md) covering deployment, configuration, Spanner Omni, AI providers, and testing.
