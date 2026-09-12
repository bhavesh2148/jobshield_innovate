// frontend/src/pages/HomePage.jsx
import { useState, useRef } from "react";

const API_BASE = "http://localhost:8000";

export default function HomePage({ onResult }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showOptionalFields, setShowOptionalFields] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrStatus, setOcrStatus] = useState(null);  // null | 'success' | 'unavailable' | 'error'
  const [ocrError, setOcrError] = useState("");
  const [ocrInstallGuide, setOcrInstallGuide] = useState("");
  const fileInputRef = useRef(null);

  const [form, setForm] = useState({
    title: "",
    company: "",
    description: "",
    requirements: "",
    benefits: "",
    company_profile: "",
    salary_range: "",
    employment_type: "",
    required_experience: "",
    required_education: "",
    industry: "",
    telecommuting: 0,
    has_company_logo: 0,
    has_questions: 0,
  });

  const update = (k, v) => setForm(p => ({ ...p, [k]: v }));

  // ── Phase 6: OCR Upload Handler ───────────────────────────
  const runOcr = async (file) => {
    if (!file) return;
    const imageTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp", "image/tiff", "image/gif"];
    if (!imageTypes.some(t => file.type.startsWith(t.split("/")[0]) && file.type.includes(t.split("/")[1]))) {
      // Not an image, skip OCR
      return;
    }

    setOcrLoading(true);
    setOcrStatus(null);
    setOcrError("");
    setOcrInstallGuide("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/ocr-ingest`, {
        method: "POST",
        body: formData,
      });

      if (res.status === 503) {
        const data = await res.json();
        const detail = data.detail || {};
        setOcrStatus("unavailable");
        setOcrInstallGuide(detail.install_guide || "Tesseract OCR is not installed. See README_DEV.md for setup instructions.");
        return;
      }

      if (!res.ok) {
        const data = await res.json();
        const detail = data.detail || {};
        setOcrStatus("error");
        setOcrError(detail.message || `OCR failed (${res.status})`);
        return;
      }

      const data = await res.json();
      if (data.extracted_text && data.extracted_text.trim().length >= 20) {
        update("description", data.extracted_text.trim());
        setOcrStatus("success");
      } else {
        setOcrStatus("error");
        setOcrError("Extracted text is too short. Try a higher-resolution image.");
      }
    } catch (e) {
      setOcrStatus("error");
      setOcrError(`OCR request failed: ${e.message}`);
    } finally {
      setOcrLoading(false);
    }
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setAttachedFile(file);
      runOcr(file);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setAttachedFile(file);
      runOcr(file);
    }
  };

  const handleAnalyze = async () => {
    if (!form.description.trim()) {
      setError("Investigation content is required. Please paste the job description, message, or email body.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(`Analysis failed (Code ${res.status})`);
      const data = await res.json();
      onResult(data, form);
    } catch (e) {
      setError(`Detection service unavailable. Verify backend service is online. Details: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-up" style={{ minHeight: '100vh', maxWidth: 940, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          background: "var(--accent-dim)",
          border: "1px solid rgba(6, 182, 212, 0.25)",
          borderRadius: 100,
          padding: "3px 14px",
          fontFamily: "var(--font-mono)",
          fontSize: "0.72rem",
          color: "var(--accent)",
          marginBottom: "0.85rem",
          letterSpacing: "0.04em",
          fontWeight: 600
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)' }} />
          THREAT INVESTIGATION CONSOLE
        </div>
        <h1 style={{
          fontFamily: "var(--font-serif)",
          fontSize: "clamp(2rem, 4vw, 3rem)",
          fontWeight: 400,
          letterSpacing: "-0.01em",
          lineHeight: 1.15,
          marginBottom: "0.5rem",
        }}>
          Recruitment Threat Ingestion
        </h1>
        <p style={{ color: "var(--text-dim)", fontSize: "0.95rem", maxWidth: 620, margin: "0 auto", lineHeight: 1.6 }}>
          Submit unsolicited job postings, recruitment correspondence, or suspicious hiring solicitations to evaluate threat severity and risk posture.
        </p>
      </div>

      {/* Main Ingestion Panel */}
      <div className="card" style={{ padding: "1.75rem" }}>
        
        {/* Primary Unstructured Content Input */}
        <div className="field-group">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
            <label className="field-label" style={{ marginBottom: 0 }}>
              Suspicious Content / Listing Body <span style={{ color: "var(--threat)", marginLeft: 2 }}>*</span>
            </label>
            <span style={{ fontSize: "0.72rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
              {form.description.length} characters
            </span>
          </div>
          <textarea
            className="field-textarea"
            placeholder="Paste the raw job description, recruiter outreach email, WhatsApp/Telegram message, or interview invitation here…"
            style={{ minHeight: 220, lineHeight: 1.6, fontSize: "0.9rem" }}
            value={form.description}
            onChange={e => update("description", e.target.value)}
          />
        </div>

        {/* Screenshot / Artifact Ingestion Zone */}
        <div 
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleFileDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `1px dashed ${ocrStatus === 'success' ? 'var(--safe-border)' : ocrStatus === 'unavailable' ? 'rgba(245,158,11,0.4)' : ocrStatus === 'error' ? 'var(--threat-border)' : 'var(--border)'}`,
            borderRadius: "var(--radius)",
            padding: "1.1rem 1.5rem",
            background: attachedFile
              ? (ocrStatus === 'success' ? 'var(--safe-dim)' : ocrStatus === 'unavailable' ? 'rgba(245,158,11,0.07)' : ocrStatus === 'error' ? 'var(--threat-dim)' : 'var(--accent-dim)')
              : "var(--bg-elevated)",
            cursor: "pointer",
            marginBottom: "0.75rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "1rem",
            transition: "border-color 0.2s ease, background 0.2s ease",
          }}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/png,image/jpeg,image/webp,image/bmp,image/tiff,image/gif" 
            style={{ display: "none" }} 
          />
          <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
            <span style={{ fontSize: "1.3rem", opacity: 0.85 }}>
              {ocrLoading ? "⏳" : ocrStatus === "success" ? "✅" : ocrStatus === "unavailable" ? "⚠" : ocrStatus === "error" ? "❌" : "📎"}
            </span>
            <div>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text)" }}>
                {ocrLoading
                  ? "Extracting text from image…"
                  : ocrStatus === "success"
                  ? `Text extracted from ${attachedFile?.name || "image"}`
                  : ocrStatus === "unavailable"
                  ? "Tesseract OCR not installed"
                  : ocrStatus === "error"
                  ? "OCR extraction failed"
                  : attachedFile ? attachedFile.name : "Attach Screenshot or Artifact"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>
                {ocrLoading
                  ? "Running local Tesseract analysis…"
                  : ocrStatus === "success"
                  ? `Description field auto-populated (${form.description.length} chars)`
                  : ocrStatus === "unavailable"
                  ? "Install Tesseract to enable screenshot-to-text ingestion"
                  : ocrStatus === "error"
                  ? ocrError
                  : attachedFile
                  ? `${(attachedFile.size / 1024).toFixed(1)} KB · Drop image to extract text via OCR`
                  : "Supports PNG, JPG, WEBP, BMP — text auto-extracted via local OCR"}
              </div>
            </div>
          </div>
          {attachedFile ? (
            <button
              type="button"
              className="btn-secondary"
              style={{ padding: "0.3rem 0.75rem", fontSize: "0.72rem", flexShrink: 0 }}
              onClick={(e) => {
                e.stopPropagation();
                setAttachedFile(null);
                setOcrStatus(null);
                setOcrError("");
                setOcrInstallGuide("");
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
            >
              Remove
            </button>
          ) : (
            <span style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.75rem",
              color: "var(--accent)",
              fontWeight: 500,
              flexShrink: 0,
            }}>
              Browse Files
            </span>
          )}
        </div>

        {/* Phase 6: Tesseract install guide banner */}
        {ocrStatus === 'unavailable' && ocrInstallGuide && (
          <div style={{
            background: "rgba(245,158,11,0.08)",
            border: "1px solid rgba(245,158,11,0.35)",
            borderRadius: "var(--radius-sm)",
            padding: "0.75rem 1rem",
            fontSize: "0.8rem",
            color: "var(--warn)",
            marginBottom: "0.75rem",
            lineHeight: 1.55,
          }}>
            <strong style={{ display: "block", marginBottom: 4 }}>⚠ OCR Unavailable — Manual Text Entry Required</strong>
            <span style={{ color: "var(--text-dim)", whiteSpace: "pre-line" }}>{ocrInstallGuide}</span>
            <button
              type="button"
              style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.75rem", marginTop: 4, display: "block" }}
              onClick={() => setOcrStatus(null)}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Collapsible Optional Target Context */}
        <div style={{ marginBottom: "1.25rem" }}>
          <button
            type="button"
            onClick={() => setShowOptionalFields(!showOptionalFields)}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-dim)",
              fontSize: "0.82rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "4px 0",
              fontFamily: "var(--font-mono)",
            }}
          >
            <span style={{ transform: showOptionalFields ? "rotate(90deg)" : "none", transition: "transform 0.15s ease" }}>
              ▸
            </span>
            <span>{showOptionalFields ? "Hide Optional Metadata" : "Add Optional Context (Job Title, Organization)"}</span>
          </button>

          {showOptionalFields && (
            <div style={{
              marginTop: "0.85rem",
              padding: "1rem",
              background: "var(--bg-elevated)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "1rem"
            }}>
              <div className="field-group" style={{ marginBottom: 0 }}>
                <label className="field-label">Target Role / Title</label>
                <input
                  className="field-input"
                  placeholder="e.g. Cloud Operations Specialist"
                  value={form.title}
                  onChange={e => update("title", e.target.value)}
                />
              </div>
              <div className="field-group" style={{ marginBottom: 0 }}>
                <label className="field-label">Stated Organization / Entity</label>
                <input
                  className="field-input"
                  placeholder="e.g. Apex Global Logistics"
                  value={form.company}
                  onChange={e => update("company", e.target.value)}
                />
              </div>
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            background: "var(--threat-dim)",
            border: "1px solid var(--threat-border)",
            borderRadius: "var(--radius)",
            padding: "0.75rem 1rem",
            color: "var(--threat)",
            fontSize: "0.85rem",
            marginBottom: "1rem",
          }}>
            ⚠ {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          className="btn-primary"
          style={{ width: "100%", padding: "0.95rem" }}
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? (
            <><div className="spinner" /> Evaluating Threat Signals…</>
          ) : (
            <>Run Threat Assessment →</>
          )}
        </button>
      </div>

      {/* Security Posture Status Bar */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "1rem",
        marginTop: "1.5rem",
      }}>
        {[
          { label: "Threat Signature Index", value: "866 Active Signatures", tag: "FAISS Vector Corpus" },
          { label: "Multidimensional Engine", value: "Ensemble Pipeline", tag: "NLP & Statistical Scoring" },
          { label: "Threat Taxonomy", value: "MITRE ATT&CK", tag: "Phase 5: ATT&CK Classification" },
          { label: "OCR Engine", value: "Tesseract Local", tag: "Phase 6: Offline Image Ingestion" },
        ].map(({ label, value, tag }) => (
          <div key={label} className="card" style={{
            padding: "1rem 1.25rem",
            background: "rgba(14, 16, 22, 0.5)",
          }}>
            <div style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.7rem",
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              marginBottom: 4
            }}>
              {label}
            </div>
            <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "var(--text)" }}>
              {value}
            </div>
            <div style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.72rem",
              color: "var(--text-subtle)",
              marginTop: 2
            }}>
              {tag}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
