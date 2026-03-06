// frontend/src/pages/AdminPage.jsx
import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";
const ADMIN_TOKEN = "admin-secret-2024";

export default function AdminPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [retrainMsg, setRetrainMsg] = useState("");
  const [error, setError] = useState("");

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/stats`);
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setStats(data);
      setError("");
    } catch (e) {
      setError(`Cannot connect to backend: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  const triggerRetrain = async () => {
    setRetraining(true);
    setRetrainMsg("");
    try {
      const res = await fetch(`${API_BASE}/retrain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admin_token: ADMIN_TOKEN, admin_approved: true }),
      });
      const data = await res.json();
      setRetrainMsg(data.message);
    } catch (e) {
      setRetrainMsg(`Error: ${e.message}`);
    } finally {
      setRetraining(false);
    }
  };

  const statCards = stats ? [
    {
      icon: "🔢", label: "Total Predictions",
      value: stats.total_predictions.toLocaleString(),
      color: "var(--accent)",
    },
    {
      icon: "🏷", label: "Pseudo-Labels",
      value: stats.pseudo_label_count.toLocaleString(),
      sub: `${stats.pending_validation} pending`,
      color: "var(--warn)",
    },
    {
      icon: "💬", label: "User Feedback",
      value: stats.feedback_count.toLocaleString(),
      color: "var(--text-muted)",
    },
    {
      icon: stats.drift_detected ? "⚠" : "✓",
      label: "Drift Status",
      value: stats.drift_detected ? "DRIFT DETECTED" : "STABLE",
      color: stats.drift_detected ? "var(--fake)" : "var(--real)",
    },
  ] : [];

  return (
    <div className="fade-up" style={{ display: "flex", flexDirection: "column", gap: "1.5rem", minHeight: '100vh', background: 'var(--bg)' }}>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ fontFamily: "var(--mono)", fontSize: "1.4rem", fontWeight: 700 }}>
            Admin Dashboard
          </h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
            Model health, drift detection, and retraining controls
          </p>
        </div>
        <button className="btn-secondary" onClick={fetchStats} disabled={loading}>
          {loading ? <div className="spinner" /> : "↻"} Refresh
        </button>
      </div>

      {error && (
        <div style={{
          background: "var(--fake-dim)", border: "1px solid #ff3d5740",
          borderRadius: "var(--radius)", padding: "0.75rem 1rem",
          color: "var(--fake)", fontSize: "0.875rem",
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Stat cards */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
          {statCards.map(({ icon, label, value, sub, color }) => (
            <div key={label} className="card" style={{ textAlign: "center" }}>
              <div style={{ fontSize: "1.5rem", marginBottom: 4 }}>{icon}</div>
              <div style={{
                fontFamily: "var(--mono)", fontSize: "0.7rem",
                color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase",
              }}>{label}</div>
              <div style={{ fontFamily: "var(--mono)", fontSize: "1.2rem", fontWeight: 700, color }}>
                {value}
              </div>
              {sub && <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>{sub}</div>}
            </div>
          ))}
        </div>
      )}

      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))", gap: "1.25rem" }}>

          {/* Retraining control */}
          <div className="card">
            <div className="section-title">🔁 Model Retraining</div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Retrain needed</span>
                <span style={{
                  fontFamily: "var(--mono)",
                  color: stats.retrain_needed ? "var(--warn)" : "var(--real)",
                }}>
                  {stats.retrain_needed ? "YES" : "NO"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Pending pseudo-labels</span>
                <span style={{ fontFamily: "var(--mono)", color: "var(--accent)" }}>
                  {stats.pending_validation}
                </span>
              </div>
            </div>

            <button
              className={stats.drift_detected || stats.retrain_needed ? "btn-primary" : "btn-secondary"}
              style={{ width: "100%" }}
              onClick={triggerRetrain}
              disabled={retraining}
            >
              {retraining
                ? <><div className="spinner" /> Scheduling Retrain…</>
                : "🔁 Trigger Retraining Now"
              }
            </button>

            {retrainMsg && (
              <div style={{
                marginTop: 10, padding: "0.6rem 0.8rem",
                background: "var(--real-dim)", border: "1px solid #00e67630",
                borderRadius: 8, color: "var(--real)", fontSize: "0.8rem",
              }}>
                ✓ {retrainMsg}
              </div>
            )}
          </div>

          {/* Drift events */}
          <div className="card">
            <div className="section-title">
              📡 Drift Events
              {stats.drift_detected && (
                <span style={{
                  marginLeft: 8, background: "var(--fake-dim)",
                  color: "var(--fake)", border: "1px solid #ff3d5740",
                  borderRadius: 100, padding: "1px 10px", fontSize: "0.7rem",
                }}>
                  {stats.drift_events.length} events
                </span>
              )}
            </div>
            {stats.drift_events.length === 0 ? (
              <div style={{
                color: "var(--real)", fontSize: "0.875rem",
                padding: "1rem", textAlign: "center",
                background: "var(--real-dim)", borderRadius: "var(--radius)",
              }}>
                ✓ No drift detected — model distribution is stable
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 200, overflowY: "auto" }}>
                {stats.drift_events.map((ev, i) => (
                  <div key={i} style={{
                    padding: "0.6rem 0.8rem",
                    background: "var(--fake-dim)", border: "1px solid #ff3d5730",
                    borderRadius: 8, fontSize: "0.8rem",
                  }}>
                    <div style={{ fontFamily: "var(--mono)", color: "var(--fake)", marginBottom: 2 }}>
                      Prediction #{ev.n_predictions_at_drift}
                    </div>
                    <div style={{ color: "var(--text-muted)" }}>
                      {new Date(ev.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Architecture note */}
      <div className="card" style={{ borderColor: "var(--accent-dim)" }}>
        <div className="section-title">🏗 System Architecture</div>
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "0.75rem", fontSize: "0.85rem",
        }}>
          {[
            { title: "Text Model", detail: "DistilBERT fine-tuned", icon: "🤖" },
            { title: "Structured Model", detail: "XGBoost (500 trees)", icon: "🌳" },
            { title: "Baseline Model", detail: "Logistic Regression", icon: "📐" },
            { title: "Ensemble", detail: "Weighted soft voting", icon: "⚖" },
            { title: "Similarity", detail: "SBERT + FAISS index", icon: "🔗" },
            { title: "Explainability", detail: "SHAP TreeExplainer", icon: "💡" },
          ].map(({ title, detail, icon }) => (
            <div key={title} style={{
              padding: "0.75rem",
              background: "var(--bg-elevated)",
              borderRadius: "var(--radius)",
              border: "1px solid var(--border-glow)",
            }}>
              <div style={{ marginBottom: 4 }}>{icon} <strong>{title}</strong></div>
              <div style={{ color: "var(--text-muted)", fontFamily: "var(--mono)", fontSize: "0.75rem" }}>
                {detail}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
