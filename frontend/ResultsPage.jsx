// frontend/src/pages/ResultsPage.jsx
import { useState } from "react";

const API_BASE = "http://localhost:8000";

// ── Highlighted Text Renderer ────────────────────────────────
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
        p.highlight ? (
          <mark key={i} className="highlight-suspicious" title="Detected threat phrase">
            {p.text}
          </mark>
        ) : (
          <span key={i}>{p.text}</span>
        )
      )}
    </span>
  );
}

// ── Circular Risk Confidence Meter ───────────────────────────
function ConfidenceMeter({ value, accentColor }) {
  const r = 38;
  const circ = 2 * Math.PI * r;
  const filled = (value / 100) * circ;

  return (
    <div style={{ position: "relative", width: 96, height: 96 }}>
      <svg width="96" height="96" style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx="48"
          cy="48"
          r={r}
          fill="none"
          stroke="var(--bg-elevated)"
          strokeWidth="6"
        />
        <circle
          cx="48"
          cy="48"
          r={r}
          fill="none"
          stroke={accentColor}
          strokeWidth="6"
          strokeDasharray={`${filled} ${circ - filled}`}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.6s ease" }}
        />
      </svg>
      <div style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}>
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize: "1.2rem",
          fontWeight: 700,
          color: accentColor,
          lineHeight: 1
        }}>
          {value}%
        </span>
        <span style={{
          fontSize: "0.58rem",
          color: "var(--text-muted)",
          fontFamily: "var(--font-mono)",
          marginTop: 3,
          letterSpacing: "0.05em"
        }}>
          CERTAINTY
        </span>
      </div>
    </div>
  );
}

// ── Model Score Bar ──────────────────────────────────────────
function RiskScoreBar({ score, accentColor }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)", letterSpacing: "0.04em" }}>
          COMPOSITE RISK INDEX
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: accentColor, fontWeight: 700 }}>
          {score} / 100
        </span>
      </div>
      <div className="risk-bar-track">
        <div
          className="risk-bar-fill"
          style={{ width: `${score}%`, background: accentColor }}
        />
      </div>
    </div>
  );
}

// ── Subsystem Signals Breakdown ──────────────────────────────
function SubsystemSignalBreakdown({ result }) {
  const signals = [
    { label: "Linguistic Anomaly Index", score: Math.round(result.bert_prob * 100), desc: "Communication cues & phrasing patterns" },
    { label: "Structural Discrepancy Score", score: Math.round(result.xgb_prob * 100), desc: "Syntactic structure & compositional attributes" },
    { label: "Baseline Distribution Alignment", score: Math.round(result.lr_prob * 100), desc: "Linear baseline feature variance" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 9, marginTop: 14 }}>
      {signals.map(({ label, score }) => {
        const color = score >= 65 ? "var(--threat)" : score >= 40 ? "var(--warn)" : "var(--safe)";
        return (
          <div key={label}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3, fontSize: "0.78rem" }}>
              <span style={{ color: "var(--text-dim)", fontWeight: 500 }}>{label}</span>
              <span style={{ fontFamily: "var(--font-mono)", color, fontWeight: 600 }}>{score}%</span>
            </div>
            <div className="risk-bar-track" style={{ height: 4 }}>
              <div className="risk-bar-fill" style={{ width: `${score}%`, background: color }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Main Results Page Component ──────────────────────────────
export default function ResultsPage({ result, jobData, onBack }) {
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackLabel, setFeedbackLabel] = useState("REAL");
  const [comment, setComment] = useState("");

  // Derive 4-tier posture metadata
  const riskLevel = (result.risk_level || (result.risk_score >= 80 ? "CRITICAL" : result.risk_score >= 60 ? "HIGH" : result.risk_score >= 35 ? "MEDIUM" : "LOW")).toUpperCase();

  const levelConfig = {
    CRITICAL: {
      color: "var(--threat)",
      border: "var(--threat-border)",
      bgDim: "var(--threat-dim)",
      glow: "var(--threat-glow)",
      title: "CRITICAL RISK POSTURE",
      icon: "⛔",
    },
    HIGH: {
      color: "#f87171",
      border: "rgba(248, 113, 113, 0.35)",
      bgDim: "rgba(248, 113, 113, 0.1)",
      glow: "0 0 20px rgba(248, 113, 113, 0.15)",
      title: "HIGH RISK POSTURE",
      icon: "⚠",
    },
    MEDIUM: {
      color: "var(--warn)",
      border: "rgba(245, 158, 11, 0.35)",
      bgDim: "rgba(245, 158, 11, 0.1)",
      glow: "0 0 20px rgba(245, 158, 11, 0.15)",
      title: "ELEVATED RISK POSTURE",
      icon: "▲",
    },
    LOW: {
      color: "var(--safe)",
      border: "var(--safe-border)",
      bgDim: "var(--safe-dim)",
      glow: "var(--safe-glow)",
      title: "LOW RISK POSTURE",
      icon: "✓",
    },
  }[riskLevel] || {
    color: "var(--safe)",
    border: "var(--safe-border)",
    bgDim: "var(--safe-dim)",
    glow: "var(--safe-glow)",
    title: "EVALUATED POSTURE",
    icon: "•",
  };

  // Format action string nicely (e.g. DO_NOT_ENGAGE -> DO NOT ENGAGE)
  const actionText = (result.action || (riskLevel === "CRITICAL" || riskLevel === "HIGH" ? "MANUAL_VERIFICATION_REQUIRED" : "SAFE_TO_PROCEED")).replace(/_/g, " ");

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
  const caseId = Math.abs(((jobData?.title || "") + (jobData?.company || "") + descText.slice(0, 30))
    .split("").reduce((a, b) => ((a << 5) - a) + b.charCodeAt(0), 0))
    .toString(16).toUpperCase().padStart(8, "0").slice(0, 8);

  return (
    <div className="fade-up" style={{ display: "flex", flexDirection: "column", gap: "1.25rem", minHeight: '100vh', maxWidth: 1080, margin: '0 auto' }}>
      
      {/* Top Action Bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <button className="btn-secondary" onClick={onBack}>
          ← Back to Investigation
        </button>
        <div style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.75rem",
          color: "var(--text-muted)",
          letterSpacing: "0.04em",
          display: "flex",
          alignItems: "center",
          gap: 8
        }}>
          <span>DOSSIER RECORD #{caseId}</span>
        </div>
      </div>

      {/* ── Primary Dossier Posture Banner ── */}
      <div className="card" style={{
        borderColor: levelConfig.border,
        boxShadow: levelConfig.glow,
        padding: "1.75rem",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "2rem", flexWrap: "wrap" }}>
          
          {/* Posture Badge & Entity Target */}
          <div style={{ minWidth: "240px" }}>
            <div style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "0.45rem 1rem",
              borderRadius: "var(--radius-sm)",
              background: levelConfig.bgDim,
              border: `1px solid ${levelConfig.border}`,
              color: levelConfig.color,
              fontFamily: "var(--font-mono)",
              fontSize: "0.85rem",
              fontWeight: 700,
              letterSpacing: "0.05em"
            }}>
              <span>{levelConfig.icon}</span> {levelConfig.title}
            </div>

            {(jobData?.title || jobData?.company) ? (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text)" }}>
                  {jobData.title || "Unspecified Role"}
                </div>
                {jobData.company && (
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 2 }}>
                    Entity: {jobData.company}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ marginTop: 10, color: "var(--text-muted)", fontSize: "0.8rem", fontFamily: "var(--font-mono)" }}>
                Target Entity: Unspecified
              </div>
            )}
          </div>

          {/* Model Certainty */}
          <ConfidenceMeter value={result.confidence} accentColor={levelConfig.color} />

          {/* Threat Metric Bar & Subsystem Breakdown */}
          <div style={{ flex: 1, minWidth: 260 }}>
            <RiskScoreBar score={result.risk_score} accentColor={levelConfig.color} />
            <SubsystemSignalBreakdown result={result} />
          </div>
        </div>
      </div>

      {/* ── Actionable Guidance Card ── */}
      {result.recommendation && (
        <div className="card" style={{
          padding: "1.25rem 1.5rem",
          background: levelConfig.bgDim,
          border: `1px solid ${levelConfig.border}`,
          display: "flex",
          alignItems: "flex-start",
          gap: "1.25rem"
        }}>
          <div style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.72rem",
            fontWeight: 700,
            letterSpacing: "0.06em",
            padding: "0.35rem 0.75rem",
            borderRadius: "var(--radius-sm)",
            background: "rgba(0, 0, 0, 0.4)",
            border: `1px solid ${levelConfig.border}`,
            color: levelConfig.color,
            whiteSpace: "nowrap",
            marginTop: 2
          }}>
            {actionText}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.68rem",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              color: "var(--text-muted)",
              marginBottom: 4
            }}>
              Operational Recommendation
            </div>
            <div style={{ fontSize: "0.88rem", color: "var(--text)", lineHeight: 1.55 }}>
              {result.recommendation}
            </div>
          </div>
        </div>
      )}

      {/* ── Investigation Details Layout ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: "1.25rem" }}>
        
        {/* Left Column: Synthesis & Model Contributing Factors */}
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          
          {/* Synthesis */}
          <div>
            <div className="section-title">
              <span>📋</span> Threat Assessment Synthesis
            </div>
            <div style={{
              background: "var(--bg-elevated)",
              borderRadius: "var(--radius)",
              padding: "0.95rem 1.1rem",
              fontSize: "0.86rem",
              lineHeight: 1.7,
              color: "var(--text-dim)",
              whiteSpace: "pre-line",
              borderLeft: `3px solid ${levelConfig.color}`,
            }}>
              {result.human_explanation}
            </div>
          </div>

          {/* Model Contributing Indicators */}
          <div>
            <div className="section-title" style={{ marginBottom: 4 }}>
              <span>⚡</span> Model-Derived Contributing Indicators
            </div>
            <div style={{ fontSize: "0.74rem", color: "var(--text-muted)", marginBottom: 12 }}>
              Statistical indicators extracted by machine learning ensemble analysis.
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {result.explanation && result.explanation.slice(0, 5).map((r, i) => (
                <div key={i} style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                  padding: "0.65rem 0.85rem",
                  background: r.is_risk ? "var(--threat-dim)" : "var(--safe-dim)",
                  border: `1px solid ${r.is_risk ? "var(--threat-border)" : "var(--safe-border)"}`,
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.84rem",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                    <span style={{ fontSize: "0.8rem", color: r.is_risk ? "var(--threat)" : "var(--safe)" }}>
                      {r.is_risk ? "▲" : "▼"}
                    </span>
                    <span style={{ fontWeight: 500, color: "var(--text)" }}>
                      {r.message}
                    </span>
                  </div>
                  <span style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.68rem",
                    fontWeight: 600,
                    color: r.is_risk ? "var(--threat)" : "var(--safe)",
                    whiteSpace: "nowrap"
                  }}>
                    {r.is_risk ? "Elevates Risk" : "Reduces Risk"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Signatures, Flags, Discrepancies */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          
          {/* Threat Intelligence / Cataloged Signature Check */}
          {result.similarity_score > 0 && (
            <div className="card" style={{
              borderColor: result.similarity_score >= 0.85 ? "var(--threat-border)" : "var(--border)",
            }}>
              <div className="section-title">
                <span>🔗</span> Cataloged Scam Signature Proximity
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <div style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "1.4rem",
                  fontWeight: 700,
                  color: result.similarity_score >= 0.85 ? "var(--threat)" : "var(--text-muted)",
                }}>
                  {Math.round(result.similarity_score * 100)}%
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-dim)" }}>
                  {result.similarity_message || "Structural alignment with known malicious recruitment campaigns"}
                </div>
              </div>
              {result.top_match_snippet && (
                <div style={{
                  fontSize: "0.76rem",
                  color: "var(--text-muted)",
                  fontFamily: "var(--font-mono)",
                  background: "var(--bg-elevated)",
                  padding: "0.6rem 0.75rem",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border)",
                }}>
                  Correlated pattern: "{result.top_match_snippet.slice(0, 110)}…"
                </div>
              )}
            </div>
          )}

          {/* Highlighted Red Flags */}
          {descText && (
            <div className="card">
              <div className="section-title">
                <span>🚩</span> Detected Red Flags & Phrasing
                {result.highlights && result.highlights.length > 0 && (
                  <span style={{
                    marginLeft: "auto",
                    background: "var(--threat-dim)",
                    color: "var(--threat)",
                    border: "1px solid var(--threat-border)",
                    borderRadius: 100,
                    padding: "1px 8px",
                    fontSize: "0.68rem",
                  }}>
                    {result.highlights.length} flags
                  </span>
                )}
              </div>
              <div style={{
                fontSize: "0.85rem",
                lineHeight: 1.7,
                color: "var(--text-dim)",
                maxHeight: 180,
                overflowY: "auto",
                background: "var(--bg-elevated)",
                padding: "0.75rem",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border)",
              }}>
                <HighlightedText
                  text={descText.slice(0, 800) + (descText.length > 800 ? "…" : "")}
                  highlights={result.highlights || []}
                />
              </div>
              {(!result.highlights || result.highlights.length === 0) && (
                <div style={{ color: "var(--safe)", fontSize: "0.8rem", marginTop: 8 }}>
                  ✓ No high-risk urgency phrases identified
                </div>
              )}
            </div>
          )}

          {/* Feedback / Discrepancy Reporting */}
          <div className="card">
            <div className="section-title">
              <span>📣</span> Discrepancy Review & Audit Log
            </div>
            {feedbackSent ? (
              <div style={{ color: "var(--safe)", fontSize: "0.85rem" }}>
                ✓ Classification feedback logged for retraining pipeline.
              </div>
            ) : showFeedback ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Correct classification label:
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {["REAL", "FAKE"].map(l => (
                    <button
                      key={l}
                      onClick={() => setFeedbackLabel(l)}
                      style={{
                        flex: 1,
                        padding: "0.45rem",
                        background: feedbackLabel === l
                          ? (l === "FAKE" ? "var(--threat-dim)" : "var(--safe-dim)")
                          : "var(--bg-elevated)",
                        border: `1px solid ${feedbackLabel === l
                          ? (l === "FAKE" ? "var(--threat)" : "var(--safe)")
                          : "var(--border)"}`,
                        color: feedbackLabel === l
                          ? (l === "FAKE" ? "var(--threat)" : "var(--safe)")
                          : "var(--text-muted)",
                        borderRadius: "var(--radius-sm)",
                        cursor: "pointer",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.75rem",
                        fontWeight: 600
                      }}
                    >
                      {l === "FAKE" ? "FRAUDULENT / UNTRUSTED" : "VERIFIED LEGITIMATE"}
                    </button>
                  ))}
                </div>
                <textarea
                  className="field-textarea"
                  style={{ minHeight: 50, fontSize: "0.82rem" }}
                  placeholder="Optional notes regarding discrepancy…"
                  value={comment}
                  onChange={e => setComment(e.target.value)}
                />
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    className="btn-primary"
                    style={{ flex: 1, padding: "0.5rem", fontSize: "0.82rem" }}
                    onClick={sendFeedback}
                  >
                    Submit Audit Entry
                  </button>
                  <button
                    className="btn-secondary"
                    style={{ padding: "0.5rem", fontSize: "0.82rem" }}
                    onClick={() => setShowFeedback(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                className="btn-secondary"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => setShowFeedback(true)}
              >
                Log Discrepancy Note
              </button>
            )}
          </div>
        </div>
      </div>
        {/* ── Phase 5: Threat Taxonomy & MITRE ATT&CK Intelligence ── */}
      {result.taxonomy && result.taxonomy.length > 0 && (
        <div className="card" style={{ marginTop: "0.5rem" }}>
          <div className="section-title" style={{ marginBottom: "1rem" }}>
            <span>🛡</span> Threat Taxonomy & MITRE ATT&amp;CK Classification
            <span style={{
              marginLeft: "auto",
              fontFamily: "var(--font-mono)",
              fontSize: "0.66rem",
              color: "var(--text-muted)",
              letterSpacing: "0.05em"
            }}>
              {result.taxonomy.length} PROFILE{result.taxonomy.length !== 1 ? "S" : ""} IDENTIFIED
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {result.taxonomy.map((profile, idx) => {
              const confConfig = {
                CONFIRMED: { color: "var(--threat)", bg: "var(--threat-dim)", border: "var(--threat-border)", label: "CONFIRMED" },
                PROBABLE:  { color: "var(--warn)", bg: "rgba(245,158,11,0.1)", border: "rgba(245,158,11,0.35)", label: "PROBABLE" },
                SUSPECTED: { color: "var(--accent)", bg: "var(--accent-dim)", border: "rgba(6,182,212,0.25)", label: "SUSPECTED" },
              }[profile.confidence] || { color: "var(--text-muted)", bg: "var(--bg-elevated)", border: "var(--border)", label: profile.confidence };

              return (
                <div key={idx} style={{
                  background: "var(--bg-elevated)",
                  border: `1px solid ${confConfig.border}`,
                  borderRadius: "var(--radius)",
                  padding: "1rem 1.25rem",
                  borderLeft: `3px solid ${confConfig.color}`,
                }}>
                  {/* Profile Header */}
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: "0.6rem", flexWrap: "wrap" }}>
                    {/* Attack Type Badge */}
                    <span style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.65rem",
                      fontWeight: 700,
                      letterSpacing: "0.06em",
                      padding: "2px 8px",
                      borderRadius: "var(--radius-sm)",
                      background: confConfig.bg,
                      border: `1px solid ${confConfig.border}`,
                      color: confConfig.color,
                    }}>
                      {profile.attack_type.replace(/_/g, " ")}
                    </span>
                    {/* Confidence Badge */}
                    <span style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.62rem",
                      fontWeight: 600,
                      letterSpacing: "0.06em",
                      padding: "2px 8px",
                      borderRadius: "var(--radius-sm)",
                      background: "rgba(0,0,0,0.3)",
                      border: "1px solid var(--border)",
                      color: confConfig.color,
                    }}>
                      {confConfig.label}
                    </span>
                    {/* Profile Name */}
                    <span style={{ fontWeight: 600, fontSize: "0.88rem", color: "var(--text)" }}>
                      {profile.profile_name}
                    </span>
                  </div>

                  {/* Description */}
                  <div style={{
                    fontSize: "0.82rem",
                    color: "var(--text-dim)",
                    lineHeight: 1.6,
                    marginBottom: profile.mitre_tags && profile.mitre_tags.length > 0 ? "0.85rem" : 0,
                  }}>
                    {profile.description}
                  </div>

                  {/* MITRE ATT&CK Tags */}
                  {profile.mitre_tags && profile.mitre_tags.length > 0 && (
                    <div>
                      <div style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.62rem",
                        letterSpacing: "0.06em",
                        color: "var(--text-muted)",
                        marginBottom: "0.45rem",
                        textTransform: "uppercase",
                      }}>
                        MITRE ATT&amp;CK Techniques
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                        {profile.mitre_tags.map((tag, ti) => (
                          <a
                            key={ti}
                            href={tag.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title={`${tag.tactic} — ${tag.technique_name}`}
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 5,
                              fontFamily: "var(--font-mono)",
                              fontSize: "0.7rem",
                              fontWeight: 600,
                              padding: "3px 9px",
                              borderRadius: "var(--radius-sm)",
                              background: "var(--bg-base)",
                              border: `1px solid ${tag.relevance === "HIGH" ? confConfig.border : "var(--border)"}`,
                              color: tag.relevance === "HIGH" ? confConfig.color : "var(--text-muted)",
                              textDecoration: "none",
                              transition: "all 0.15s ease",
                            }}
                            onMouseEnter={e => { e.currentTarget.style.borderColor = confConfig.color; e.currentTarget.style.color = confConfig.color; }}
                            onMouseLeave={e => { e.currentTarget.style.borderColor = tag.relevance === "HIGH" ? confConfig.border : "var(--border)"; e.currentTarget.style.color = tag.relevance === "HIGH" ? confConfig.color : "var(--text-muted)"; }}
                          >
                            <span>{tag.technique_id}</span>
                            <span style={{ opacity: 0.6, fontSize: "0.62rem" }}>·</span>
                            <span style={{ fontWeight: 400, opacity: 0.9 }}>{tag.technique_name}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
