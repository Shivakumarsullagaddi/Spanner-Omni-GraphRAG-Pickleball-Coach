# Google Cloud Spanner Omni Guide

Google Cloud Spanner Omni brings Google Spanner's distributed ACID transaction engine to edge, on-premises, and local container environments. This guide explains how Spanner Omni operates within the Pickleball Coach application.

---

## 1. Container Architecture & Ports

The container image `us-docker.pkg.dev/spanner-omni/images/spanner-omni:2026.r2.1-beta` runs in single-server development mode:

- **Internal gRPC Client Port**: `15000`
- **Internal Admin Web Console**: `15026`
- **Published Host Ports**: `9010` and `9020`

Because the container was started with `-p 9010:9010 -p 9020:9020`, an internal proxy bridges port 9010 to the internal listener on 15000:

```bash
docker exec -d spanner-omni nc -L -p 9010 nc 127.0.0.1 15000
```

---

## 2. Default Hierarchy

In Spanner Omni single-server mode:
- Project identifier: `default`
- Instance identifier: `default`
- System Database: `spanner-info` (created automatically on startup)
- Application Database: `pickleball-db`

The application configuration seamlessly detects and resolves both `default/default` and user-defined emulator instance paths.

---

## 3. Database Schema Overview

The database contains 8 core tables:

1. `Courts`: Court locations, surface types, hourly rates, and lighting metadata.
2. `Players`: Player profiles, skill levels (DUPR), and contact information.
3. `Bookings`: Reservations enforced with transactional conflict checks.
4. `MatchRequests`: Public matchmaking requests with open spot counts.
5. `CourtZones`: Physical zones including Non-Volley Zone (NVZ Kitchen) boundaries.
6. `Shots`: Graph shot nodes recording shot type, speed (mph), spin, and court coordinates.
7. `ShotTransitions`: Graph directed edges connecting sequential shots across rally depth.
8. `GameSessions`: Point-by-point summaries, match scores, faults, and AI coaching summaries.

---

## 4. Spanner CLI Operations

Inspect databases inside the running container:

```bash
docker exec spanner-omni /google/spanner/bin/spanner databases list
```

Describe a specific database:

```bash
docker exec spanner-omni /google/spanner/bin/spanner databases describe pickleball-db
```

Execute SQL queries directly:

```bash
docker exec spanner-omni /google/spanner/bin/spanner databases execute-sql pickleball-db --sql "SELECT COUNT(*) FROM Courts"
```

---

## 5. Schema Initialization and Seeding

Database initialization occurs automatically when the application starts or via the HTTP endpoint:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/spanner/init" -Method Post
```

This ensures the database `pickleball-db` exists, executes missing DDL statements, and inserts initial seed data for courts, players, and match requests.
