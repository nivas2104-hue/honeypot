import { useEffect, useState, useRef } from "react";

const API = "http://127.0.0.1:5000";

export default function App() {
  const [events, setEvents] = useState([]);
  const [sessions, setSessions] = useState({});
  const [connected, setConnected] = useState(false);
  const feedRef = useRef(null);

  // EVENTS (from backend / SQLite)
  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API}/events`)
        .then(res => res.json())
        .then(data => {
          setEvents(data);
          setConnected(true);
        })
        .catch(() => setConnected(false));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // SESSIONS
  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API}/sessions`)
        .then(res => res.json())
        .then(data => setSessions(data));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getColor = (score) => {
    if (score >= 25) return "#ff2d2d";
    if (score >= 15) return "#ff6a00";
    if (score >= 8) return "#f5c518";
    return "#00ff88";
  };

  // 🔥 regex-based detection (improved)
  const isDangerous = (cmd = "") => {
    return /passwd|wget|curl|ps aux/i.test(cmd);
  };

  return (
    <div style={{
      background: "#060610",
      color: "#c9d1d9",
      minHeight: "100vh",
      fontFamily: "monospace",
      padding: 20
    }}>

      {/* HEADER */}
      <h1 style={{ color: "#00ff88" }}>
        ◈ HONEYPOT · IDS
      </h1>

      <p style={{ color: "#555" }}>
        AUTOMATED INTRUSION DETECTION SYSTEM
      </p>

      <p>
        STREAM STATUS: {connected ? "🟢 LIVE" : "🔴 OFFLINE"}
      </p>

      {/* EVENTS */}
      <h3>📡 Live Events</h3>

      <div ref={feedRef} style={{
        maxHeight: 220,
        overflow: "auto",
        border: "1px solid #00ff8844",
        padding: 10
      }}>
        {events.length === 0 ? (
          <p style={{ color: "#444" }}>No events yet...</p>
        ) : (
          events.slice(0, 20).map((e, i) => {
            const danger = isDangerous(e.command);

            return (
              <div key={i} style={{
                marginBottom: 6,
                color: danger ? "#ff2d2d" : "#c9d1d9",
                fontWeight: danger ? "bold" : "normal"
              }}>
                [{e.timestamp?.slice(11, 19) || "--:--:--"}] [{e.ip}] {e.command}
              </div>
            );
          })
        )}
      </div>

      {/* SESSIONS */}
      <h2 style={{ marginTop: 30 }}>🚨 Attack Sessions</h2>

      {Object.entries(sessions).length === 0 ? (
        <p style={{ color: "#444" }}>No sessions yet...</p>
      ) : (
        Object.entries(sessions).map(([id, s]) => {
          const color = getColor(s.score);

          return (
            <div key={id} style={{
              border: `1px solid ${color}`,
              padding: 15,
              marginTop: 15,
              background: "#0d0d1a",
              borderRadius: 6
            }}>
              <b>IP:</b> {s.ip} <br />
              <b>Score:</b> <span style={{ color }}>{s.score}</span> <br />
              <b>Phase:</b> {s.phase || "—"} <br />

              <b>Attack Type:</b>{" "}
              <span style={{ color: "#00ff88" }}>
                {s.attack_label || "—"}
              </span>

              <br /><br />

              <b>Timeline:</b><br />

              {s.timeline?.length > 0 ? (
                s.timeline.map((t, i) => {
                  const danger = isDangerous(t.cmd);

                  return (
                    <div key={i} style={{ fontSize: 12 }}>
                      <span style={{ color: "#6b7280" }}>
                        [{t.time}]
                      </span>{" "}
                      <span style={{
                        color: danger ? "#ff2d2d" : "#c9d1d9",
                        fontWeight: danger ? "bold" : "normal"
                      }}>
                        {t.cmd}
                      </span>
                    </div>
                  );
                })
              ) : (
                <span style={{ color: "#444" }}>No timeline</span>
              )}

            </div>
          );
        })
      )}

    </div>
  );
}
