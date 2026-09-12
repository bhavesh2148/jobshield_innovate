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
      setError(`Detection service unavailable: ${e.message}`);
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
      label: "Total Investigations",
      value: stats.total_predictions.toLocaleString(),
      color: "var(--accent)",
      detail: "Queries processed"
    },
    {
      label: "Accumulated Signatures",
      value: stats.pseudo_label_count.toLocaleString(),
      sub: `${stats.pending_validation} pending verification`,
      color: "var(--warn)",
      detail: "Candidate threat vectors"
    },
    {
      label: "Discrepancy Reports",
      value: stats.feedback_count.toLocaleString(),
      color: "var(--text-muted)",
      detail: "User audit feedback"
    },
    {
      label: "Distribution Stability",
      value: stats.drift_detected ? "DRIFT ALERT" : "STABLE",
      color: stats.drift_detected ? "var(--threat)" : "var(--safe)",
      detail: "Statistical stream monitor"
    },
  ] : [];

  return (
    <div className="fade-up" style={{ display: "flex", flexDirection: "column", gap: "1.5rem", minHeight: '100vh' }}>
      
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{
            fontFamily: "var(--font-serif)",
            fontSize: "clamp(1.8rem, 3.5vw, 2.6rem)",
            fontWeight: 400,
            marginBottom: 2
          }}>
            Security Operations Console
          </h1>
          <p style={{ color: "var(--text-dim)", fontSize: "0.85rem" }}>
            Threat engine telemetry, distribution drift detection, and signature calibration
          </p>
        </div>
        <button className="btn-secondary" onClick={fetchStats} disabled={loading}>
          {loading ? <div className="spinner" style={{ width: 14, height: 14 }} /> : "↻"} Refresh Telemetry
        </button>
      </div>

      {error && (
        <div style={{
          background: "var(--threat-dim)",
          border: "1px solid var(--threat-border)",
          borderRadius: "var(--radius)",
          padding: "0.75rem 1rem",
          color: "var(--threat)",
          fontSize: "0.85rem",
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Stat Cards */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
          {statCards.map(({ label, value, sub, color, detail }) => (
            <div key={label} className="card" style={{ padding: "1.25rem" }}>
              <div style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.68rem",
                color: "var(--text-muted)",
                marginBottom: 6,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                fontWeight: 600
              }}>
                {label}
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "1.4rem", fontWeight: 700, color, marginBottom: 2 }}>
                {value}
              </div>
              {sub ? (
                <div style={{ color: "var(--text-dim)", fontSize: "0.75rem", fontFamily: "var(--font-mono)" }}>{sub}</div>
              ) : (
                <div style={{ color: "var(--text-subtle)", fontSize: "0.75rem" }}>{detail}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Operational Controls & Stream Health */}
      {stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "1.25rem" }}>
          
          {/* Continuous Tuning & Signature Integration */}
          <div className="card">
            <div className="section-title">
              <span>⚙</span> Engine Calibration & Signatures
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Calibration Status</span>
                <span style={{
                  fontFamily: "var(--font-mono)",
                  color: stats.retrain_needed ? "var(--warn)" : "var(--safe)",
                  fontWeight: 600
                }}>
                  {stats.retrain_needed ? "CALIBRATION RECOMMENDED" : "NOMINAL"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Pending Signature Batch</span>
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontWeight: 600 }}>
                  {stats.pending_validation} samples
                </span>
              </div>
            </div>

            <button
              className={stats.drift_detected || stats.retrain_needed ? "btn-primary" : "btn-secondary"}
              style={{ width: "100%", justifyContent: "center" }}
              onClick={triggerRetrain}
              disabled={retraining}
            >
              {retraining ? (
                <><div className="spinner" style={{ width: 16, height: 16 }} /> Calibrating Detection Weights…</>
              ) : (
                "Calibrate Detection Engine Now"
              )}
            </button>

            {retrainMsg && (
              <div style={{
                marginTop: 10,
                padding: "0.6rem 0.8rem",
                background: "var(--safe-dim)",
                border: "1px solid var(--safe-border)",
                borderRadius: "var(--radius-sm)",
                color: "var(--safe)",
                fontSize: "0.8rem",
              }}>
                ✓ {retrainMsg}
              </div>
            )}
          </div>

          {/* Drift Telemetry */}
          <div className="card">
            <div className="section-title">
              <span>📡</span> Concept Drift Stream Monitor
              {stats.drift_detected && (
                <span style={{
                  marginLeft: "auto",
                  background: "var(--threat-dim)",
                  color: "var(--threat)",
                  border: "1px solid var(--threat-border)",
                  borderRadius: 100,
                  padding: "1px 8px",
                  fontSize: "0.68rem",
                }}>
                  {stats.drift_events.length} shifts
                </span>
              )}
            </div>
            {stats.drift_events.length === 0 ? (
              <div style={{
                color: "var(--safe)",
                fontSize: "0.85rem",
                padding: "1.25rem",
                textAlign: "center",
                background: "var(--safe-dim)",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--safe-border)"
              }}>
                ✓ Statistical distribution stable — no anomalous pattern drift detected
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 180, overflowY: "auto" }}>
                {stats.drift_events.map((ev, i) => (
                  <div key={i} style={{
                    padding: "0.6rem 0.8rem",
                    background: "var(--threat-dim)",
                    border: "1px solid var(--threat-border)",
                    borderRadius: "var(--radius-sm)",
                    fontSize: "0.78rem",
                  }}>
                    <div style={{ fontFamily: "var(--font-mono)", color: "var(--threat)", fontWeight: 600, marginBottom: 2 }}>
                      Distribution Shift @ Prediction #{ev.n_predictions_at_drift}
                    </div>
                    <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      {new Date(ev.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Security Engine Architecture Overview */}
      <div className="card">
        <div className="section-title">
          <span>🛡</span> Detection Engine Subsystems
        </div>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "0.75rem",
          fontSize: "0.85rem",
        }}>
          {[
            { title: "Linguistic Threat Analyzer", detail: "Deep semantic & urgency phrasing analysis", tag: "NLP Pipeline" },
            { title: "Structural Risk Classifier", detail: "Domain, compensation & entity verification", tag: "Decision Trees" },
            { title: "Baseline Anomaly Monitor", detail: "Statistical baseline distribution stabilizer", tag: "Regression Baseline" },
            { title: "Threat Signature Vector DB", detail: "Cosine similarity memory over 866 scam profiles", tag: "Vector Index" },
            { title: "Attribution Engine", detail: "Mathematical feature-level risk decomposition", tag: "Attribution (XAI)" },
            { title: "Continuous Drift Monitor", detail: "Adaptive windowing stream anomaly detector", tag: "ADWIN Telemetry" },
          ].map(({ title, detail, tag }) => (
            <div key={title} style={{
              padding: "0.75rem 0.9rem",
              background: "var(--bg-elevated)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border)",
            }}>
              <div style={{ fontWeight: 600, color: "var(--text)", marginBottom: 2 }}>{title}</div>
              <div style={{ color: "var(--text-dim)", fontSize: "0.78rem", lineHeight: 1.4, marginBottom: 4 }}>
                {detail}
              </div>
              <div style={{ color: "var(--text-subtle)", fontFamily: "var(--font-mono)", fontSize: "0.68rem" }}>
                {tag}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
