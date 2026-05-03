from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import sqlite3

app = Flask(__name__)
CORS(app)

events = []
sessions = {}

DB_PATH = "instance/honeypot.db"

# ───────── EVENTS (GET FROM DB) ─────────
@app.route("/events", methods=["GET"])
def get_events():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT ip, command, type, severity, session_id, pattern, phase, score, attack_label, timestamp
        FROM event
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "ip": r[0],
            "command": r[1],
            "type": r[2],
            "severity": r[3],
            "session_id": r[4],
            "pattern": r[5],
            "phase": r[6],
            "score": r[7],
            "attack_label": r[8],
            "timestamp": r[9]
        })

    return jsonify(result)

# ───────── EVENTS (STORE TO DB) ─────────
@app.route("/events", methods=["POST"])
def add_event():
    data = request.json

    ip = data.get("ip", "Unknown")
    cmd = data.get("command", "")
    etype = data.get("type", "unknown")
    severity = data.get("severity", 1)
    session_id = data.get("session_id")
    pattern = data.get("pattern", "normal")
    phase = data.get("phase", "reconnaissance")
    score = data.get("score", 0)
    attack_label = data.get("attack_label", "")

    timestamp = datetime.now().isoformat()

    # 🔥 SAVE TO SQLITE
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO event (ip, command, type, severity, session_id, pattern, phase, score, attack_label, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ip, cmd, etype, severity, session_id, pattern, phase, score, attack_label, timestamp))

    conn.commit()
    conn.close()

    # ───────── ALSO KEEP SESSION LOGIC (unchanged) ─────────
    if session_id:
        if session_id not in sessions:
            sessions[session_id] = {
                "ip": ip,
                "commands": [],
                "timeline": [],
                "score": 0,
                "phase": phase,
                "attack_label": attack_label
            }

        sessions[session_id]["commands"].append(cmd)
        sessions[session_id]["score"] += severity
        sessions[session_id]["phase"] = phase
        sessions[session_id]["attack_label"] = attack_label

        sessions[session_id]["timeline"].append({
            "time": timestamp[11:19],
            "cmd": cmd
        })

    return {"status": "ok"}

# ───────── SESSIONS ─────────
@app.route("/sessions", methods=["GET"])
def get_sessions():
    return jsonify(sessions)

# ───────── STATS ─────────
@app.route("/stats", methods=["GET"])
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM event")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM event WHERE type='recon'")
    recon = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM event WHERE type='sensitive'")
    sensitive = cur.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "recon": recon,
        "sensitive": sensitive
    }

if __name__ == "__main__":
    app.run(port=5000)
