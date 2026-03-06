// frontend/src/pages/ResultsPage.jsx
import { useState } from "react";

const API_BASE = "http://localhost:8000";

// ── Highlighted text renderer ────────────────────────────────
function HighlightedText({ text, highlights }) {
  if (!highlights || highlights.length === 0) {
    return <span>{text}</span>;
  }

  const sorted = [...highlights].sort((a, b) => a.start - b.start);
  const parts = [];
  let cursor = 0;

  for (const h of sorted) {
    if (h.start > cursor) {
      parts.push({ text: text.slice(cursor, h.start), highlight: false });
    }
    parts.push({ text: text.slice(h.start, h.end), highlight: true });
    cursor = h.end;
  }
  if (cursor < text.length) {
    parts.push({ text: text.slice(cursor), highlight: false });
  }

  return (
    <span>
      {parts.map((p, i) =>
        p.highlight
          ? <mark key={i} className="highlight-suspicious" title="Suspicious phrase">{p.text}</mark>
          : <span key={i}>{p.text}</span>
      )}
    </span>
  );
}

// ── Circular confidence meter ─────────────────────────────────
function ConfidenceMeter({ value, isFake }) {
  const r = 44;
  const circ = 2 * Math.PI * r;
  const filled = (value / 100) * circ;
  const color = isFake ? "var(--fake)" : "var(--real)";

  return (
    <div style={{ position: "relative", width: 120, height: 120 }}>
      <svg width="120" height="120" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="60" cy="60" r={r} fill="none"
          stroke="var(--bg-elevated)" strokeWidth="8" />
        <circle cx="60" cy="60" r={r} fill="none"
          stroke={color} strokeWidth="8"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
      </svg>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
      }}>
        <span style={{
          fontFamily: "var(--mono)", fontSize: "1.4rem",
          fontWeight: 700, color,
        }}>{value}%</span>
        <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontFamily: "var(--mono)" }}>
          CONFIDENCE
        </span>
      </div>
    </div>
  );
}

// ── Risk bar ─────────────────────────────────────────────────
function RiskBar({ score }) {
  const color = score >= 70 ? "var(--fake)"
    : score >= 40 ? "var(--warn)"
    : "var(--real)";
  const label = score >= 70 ? "HIGH RISK" : score >= 40 ? "MEDIUM RISK" : "LOW RISK";
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontFamily: "var(--mono)", fontSize: "0.7rem", color: "var(--text-muted)" }}>
          RISK SCORE
        </span>
        <span style={{ fontFamily: "var(--mono)", fontSize: "0.8rem", color, fontWeight: 700 }}>
          {score}/100 — {label}
        </span>
      </div>
      <div className="risk-bar-track">
        <div className="risk-bar-fill"
          style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
}

// ── Model breakdown ───────────────────────────────────────────
function ModelBreakdown({ result }) {
  const models = [
    { name: "BERT", prob: result.bert_prob, icon: "🤖" },
    { name: "XGBoost", prob: result.xgb_prob, icon: "🌳" },
    { name: "Logistic Reg.", prob: result.lr_prob, icon: "📐" },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {models.map(({ name, prob, icon }) => {
        const pct = Math.round(prob * 100);
        const color = pct >= 50 ? "var(--fake)" : "var(--real)";
        return (
          <div key={name}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: "0.85rem" }}>
              <span style={{ color: "var(--text-dim)" }}>{icon} {name}</span>
              <span style={{ fontFamily: "var(--mono)", color, fontWeight: 700 }}>{pct}% fraud</span>
            </div>
            <div className="risk-bar-track" style={{ height: 6 }}>
              <div className="risk-bar-fill"
                style={{ width: `${pct}%`, background: color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main ResultsPage ──────────────────────────────────────────
export default function ResultsPage({ result, jobData, onBack }) {
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackLabel, setFeedbackLabel] = useState("REAL");
  const [comment, setComment] = useState("");

  const isFake = result.prediction === "FAKE";
  const mainColor = isFake ? "var(--fake)" : "var(--real)";

  const sendFeedback = async () => {
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: jobData?.title || "",
          reported_prediction: result.prediction,
          correct_label: feedbackLabel,
          comment,
        }),
      });
    } catch (_) {}
    setFeedbackSent(true);
    setShowFeedback(false);
  };

  const descText = jobData?.description || "";

  return (
    <div className="fade-up" style={{ display: "flex", flexDirection: "column", gap: "1.25rem", minHeight: '100vh', background: 'var(--bg)' }}>

      {/* Back */}
      <button className="btn-secondary" onClick={onBack} style={{ alignSelf: "flex-start" }}>
        ← Analyze Another Job
      </button>

      {/* ── Hero result card ── */}
      <div className="card" style={{
        border: `2px solid ${mainColor}`,
        boxShadow: isFake ? "var(--fake-glow)" : "var(--real-glow)",
        animation: isFake ? "pulse-fake 3s ease infinite" : "pulse-real 3s ease infinite",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "2rem", flexWrap: "wrap" }}>
          {/* Verdict badge */}
          <div>
            {isFake
              ? <div className="badge-fake">⚠ FAKE JOB</div>
              : <div className="badge-real">✓ REAL JOB</div>}
            {jobData?.title && (
              <div style={{ marginTop: 8, color: "var(--text-muted)", fontSize: "0.875rem" }}>
                {jobData.title}{jobData.company ? ` · ${jobData.company}` : ""}
              </div>
            )}
          </div>

          {/* Confidence meter */}
          <ConfidenceMeter value={result.confidence} isFake={isFake} />

          {/* Risk bar */}
          <div style={{ flex: 1, minWidth: 200 }}>
            <RiskBar score={result.risk_score} />
            <div style={{ marginTop: 12 }}>
              <ModelBreakdown result={result} />
            </div>
          </div>
        </div>
      </div>

      {/* ── Two-column layout ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "1.25rem" }}>

        {/* Explanation panel */}
        <div className="card">
          <div className="section-title">🔎 Why this prediction?</div>
          <div style={{
            background: "var(--bg-elevated)", borderRadius: "var(--radius)",
            padding: "1rem", marginBottom: "1rem",
            fontSize: "0.875rem", lineHeight: 1.8,
            fontFamily: "var(--mono)", color: "var(--text-dim)",
            whiteSpace: "pre-line", borderLeft: `3px solid ${mainColor}`,
          }}>
            {result.human_explanation}
          </div>

          <div className="section-title">Top 5 Factors</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {result.explanation.slice(0, 5).map((r, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "0.6rem 0.8rem",
                background: r.is_risk ? "var(--fake-dim)" : "var(--real-dim)",
                border: `1px solid ${r.is_risk ? "#ff3d5730" : "#00e67630"}`,
                borderRadius: "var(--radius)",
                fontSize: "0.85rem",
              }}>
                <span style={{ fontSize: "1rem" }}>{r.is_risk ? "🔴" : "🟢"}</span>
                <div>
                  <div style={{ fontWeight: 600, color: r.is_risk ? "var(--fake)" : "var(--real)" }}>
                    {r.message}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
                    SHAP: {r.shap_value > 0 ? "+" : ""}{r.shap_value.toFixed(3)} · value: {r.value}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>

          {/* Similarity card */}
          {result.similarity_score > 0 && (
            <div className="card" style={{
              borderColor: result.similarity_score >= 0.85 ? "#ff3d5750" : "var(--border)",
            }}>
              <div className="section-title">🔗 Similarity Check</div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <div style={{
                  fontFamily: "var(--mono)", fontSize: "1.5rem", fontWeight: 700,
                  color: result.similarity_score >= 0.85 ? "var(--fake)" : "var(--text-muted)",
                }}>
                  {Math.round(result.similarity_score * 100)}%
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-dim)" }}>
                  {result.similarity_message || "similarity to known fake jobs"}
                </div>
              </div>
              {result.top_match_snippet && (
                <div style={{
                  fontSize: "0.8rem", color: "var(--text-muted)",
                  fontStyle: "italic", background: "var(--bg-elevated)",
                  padding: "0.6rem", borderRadius: 8,
                }}>
                  Closest match: "{result.top_match_snippet.slice(0, 120)}…"
                </div>
              )}
            </div>
          )}

          {/* Highlighted description */}
          {descText && (
            <div className="card">
              <div className="section-title">
                🚩 Suspicious Phrases
                {result.highlights.length > 0 && (
                  <span style={{
                    marginLeft: 8, background: "var(--fake-dim)",
                    color: "var(--fake)", border: "1px solid #ff3d5740",
                    borderRadius: 100, padding: "1px 10px",
                    fontSize: "0.7rem",
                  }}>
                    {result.highlights.length} found
                  </span>
                )}
              </div>
              <div style={{
                fontSize: "0.875rem", lineHeight: 1.8,
                color: "var(--text-dim)",
                maxHeight: 200, overflowY: "auto",
                background: "var(--bg-elevated)",
                padding: "0.75rem", borderRadius: "var(--radius)",
              }}>
                <HighlightedText
                  text={descText.slice(0, 800) + (descText.length > 800 ? "…" : "")}
                  highlights={result.highlights}
                />
              </div>
              {result.highlights.length === 0 && (
                <div style={{ color: "var(--real)", fontSize: "0.8rem", marginTop: 6 }}>
                  ✓ No suspicious phrases detected
                </div>
              )}
            </div>
          )}

          {/* Feedback */}
          <div className="card">
            <div className="section-title">📣 Report Incorrect Prediction</div>
            {feedbackSent ? (
              <div style={{ color: "var(--real)", fontSize: "0.875rem" }}>
                ✓ Feedback received — thank you!
              </div>
            ) : showFeedback ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
                  What should the correct label be?
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {["REAL", "FAKE"].map(l => (
                    <button key={l} onClick={() => setFeedbackLabel(l)}
                      style={{
                        flex: 1, padding: "0.5rem",
                        background: feedbackLabel === l
                          ? (l === "FAKE" ? "var(--fake-dim)" : "var(--real-dim)")
                          : "var(--bg-elevated)",
                        border: `1px solid ${feedbackLabel === l
                          ? (l === "FAKE" ? "var(--fake)" : "var(--real)")
                          : "var(--border)"}`,
                        color: feedbackLabel === l
                          ? (l === "FAKE" ? "var(--fake)" : "var(--real)")
                          : "var(--text-muted)",
                        borderRadius: 8, cursor: "pointer",
                        fontFamily: "var(--mono)", fontSize: "0.8rem",
                      }}>
                      {l}
                    </button>
                  ))}
                </div>
                <textarea className="field-textarea" style={{ minHeight: 60 }}
                  placeholder="Optional: why do you think the prediction is wrong?"
                  value={comment} onChange={e => setComment(e.target.value)} />
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn-primary" style={{ flex: 1, padding: "0.6rem" }}
                    onClick={sendFeedback}>
                    Submit Feedback
                  </button>
                  <button className="btn-secondary" onClick={() => setShowFeedback(false)}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button className="btn-danger" onClick={() => setShowFeedback(true)}>
                ⚠ Report Incorrect Prediction
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
