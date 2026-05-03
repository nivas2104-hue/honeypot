import subprocess
import re
import requests
import time

API_URL = "http://127.0.0.1:5000/events"

TOKEN = "8515805563:AAGwypFakr6EXpy0l6tYetsD5lyudoQLvTw"   # ⚠️ replace
CHAT_ID = "8342220910"

def send_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📲 TELEGRAM:", res.text)
    except Exception as e:
        print("⚠️ Telegram failed:", e)

# ───────── SESSION SYSTEM ─────────
sessions = {}
SESSION_TIMEOUT = 60
ALERT_COOLDOWN = 30

def get_session(ip):
    now = time.time()

    if ip in sessions:
        if now - sessions[ip]["last_seen"] < SESSION_TIMEOUT:
            sessions[ip]["last_seen"] = now
            return sessions[ip]

    session_id = f"{ip}_{int(now)}"
    sessions[ip] = {
        "id": session_id,
        "last_seen": now,
        "score": 0,
        "commands": [],
        "timeline": [],
        "phase": "reconnaissance",
        "last_alert": 0,
        "last_alert_score": 0
    }
    return sessions[ip]

# ───────── 🔥 REGEX CLASSIFICATION (UPGRADED) ─────────
def classify_command(cmd):
    cmd = cmd.lower()

    # Recon
    if re.search(r"\b(ls|pwd|whoami|uname)\b", cmd):
        return "recon", 2

    # Sensitive files (handles typos)
    if re.search(r"passwd|shadow", cmd):
        return "sensitive", 9

    # Process inspection
    if re.search(r"ps\s+aux", cmd):
        return "sensitive", 7

    # File operations
    if re.search(r"\b(touch|rm|cd)\b", cmd):
        return "file", 4

    # Downloads (handles wget, wgett, curl, etc.)
    if re.search(r"(wget|curl)", cmd):
        return "download", 7

    return "unknown", 1

# ───────── PHASE ─────────
def update_phase(session):
    cmds = session["commands"]

    if any("wget" in c or "curl" in c for c in cmds):
        return "exploitation"

    if any("passwd" in c for c in cmds):
        return "enumeration"

    if len(cmds) > 5:
        return "reconnaissance"

    return session["phase"]

# ───────── PATTERN ─────────
def detect_pattern(session):
    cmds = session["commands"]

    if any("passwd" in c for c in cmds) and any("wget" in c for c in cmds):
        return "multi-stage attack"

    if len(cmds) > 8:
        return "aggressive exploration"

    return "normal"

# ───────── ATTACK LABEL ─────────
def get_attack_label(session):
    cmds = session["commands"]

    if any("passwd" in c for c in cmds) and any("wget" in c for c in cmds):
        return "Credential Enumeration + Payload Download"

    if any("passwd" in c for c in cmds):
        return "Credential Enumeration"

    if any("wget" in c or "curl" in c for c in cmds):
        return "Payload Download Attempt"

    if len(cmds) > 5:
        return "Aggressive Reconnaissance"

    return "Low Activity"

# ───────── DOCKER ─────────
def get_container_id():
    result = subprocess.run(
        ["docker", "ps", "-q", "--filter", "ancestor=cowrie/cowrie"],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()

print("🔍 Advanced monitoring started...\n")

seen_lines = []
MAX_LINES = 100

while True:
    container_id = get_container_id()

    if not container_id:
        print("❌ Cowrie not running...")
        time.sleep(3)
        continue

    process = subprocess.Popen(
        ["docker", "logs", "-f", container_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    current_ip = "Unknown"

    for line in process.stdout:

        if line in seen_lines:
            continue

        seen_lines.append(line)
        if len(seen_lines) > MAX_LINES:
            seen_lines.pop(0)

        ip_match = re.search(r'\[(?:HoneyPotSSHTransport,0,)(.*?)\]', line)
        if ip_match:
            current_ip = ip_match.group(1)

        if "CMD:" in line:
            cmd = line.split("CMD:")[1].strip()

            session = get_session(current_ip)

            etype, severity = classify_command(cmd)

            # ───── UPDATE SESSION ─────
            session["commands"].append(cmd)
            session["score"] += severity

            now_str = time.strftime("%H:%M:%S")
            session["timeline"].append({
                "time": now_str,
                "cmd": cmd
            })

            session["phase"] = update_phase(session)
            pattern = detect_pattern(session)
            label = get_attack_label(session)

            # ───── SMART ALERT ─────
            now = time.time()
            score_jump = session["score"] - session["last_alert_score"]

            if (
                session["phase"] == "exploitation" and
                (
                    session["last_alert_score"] == 0
                    or score_jump >= 15
                )
                and now - session["last_alert"] > ALERT_COOLDOWN
            ):
                msg = f"""🔥 ACTIVE ATTACK

IP: {current_ip}
Session: {session['id']}

Phase: {session['phase']}
Pattern: {pattern}
Score: {session['score']}

Attack Type: {label}

Recent Command:
{cmd}
"""
                send_alert(msg)

                session["last_alert"] = now
                session["last_alert_score"] = session["score"]

            # ───── EVENT ─────
            event = {
                "ip": current_ip,
                "command": cmd,
                "type": etype,
                "severity": severity,
                "session_id": session["id"],
                "pattern": pattern,
                "phase": session["phase"],
                "score": session["score"],
                "attack_label": label,
                "timeline": session["timeline"][-10:],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }

            print(f"\nCommand: {cmd}")
            print(f"IP: {current_ip} | Score: {session['score']} | {label}")

            try:
                requests.post(API_URL, json=event)
            except:
                print("⚠️ Backend not running")

    time.sleep(2)
