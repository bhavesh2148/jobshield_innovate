// frontend/src/pages/HomePage.jsx
import { useState } from "react";

const API_BASE = "http://localhost:8000";

export default function HomePage({ onResult }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  const handleAnalyze = async () => {
    if (!form.description.trim()) {
      setError("Job description is required.");
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
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      onResult(data, form);
    } catch (e) {
      setError(`Failed to connect to analysis server. Make sure the backend is running at ${API_BASE}. Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-up" style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Hero */}
      <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
        <div style={{
          display: "inline-flex", alignItems: "center", gap: 8,
          background: "var(--accent-dim)", border: "1px solid var(--accent)",
          borderRadius: 100, padding: "4px 16px",
          fontFamily: "var(--mono)", fontSize: "0.75rem", color: "var(--accent)",
          marginBottom: "1rem", letterSpacing: "0.05em",
        }}>
          ⚡ AI-POWERED · LOCAL MODELS · NO API KEYS
        </div>
        <h1 style={{
          fontFamily: "var(--mono)", fontSize: "clamp(1.8rem, 4vw, 2.8rem)",
          fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1.2,
          marginBottom: "0.75rem",
        }}>
          Detect Fake Job Postings
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "1.05rem", maxWidth: 540, margin: "0 auto" }}>
          Paste any job listing and get an instant AI analysis using BERT + XGBoost ensemble — fully offline.
        </p>
      </div>

      {/* Form */}
      <div className="card">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }}>
          {/* Title */}
          <div className="field-group">
            <label className="field-label">Job Title</label>
            <input className="field-input" placeholder="e.g. Senior Software Engineer"
              value={form.title} onChange={e => update("title", e.target.value)} />
          </div>
          {/* Company */}
          <div className="field-group">
            <label className="field-label">Company Name</label>
            <input className="field-input" placeholder="e.g. Acme Corp"
              value={form.company} onChange={e => update("company", e.target.value)} />
          </div>
        </div>

        {/* Description — full width */}
        <div className="field-group">
          <label className="field-label">
            Job Description <span style={{ color: "var(--fake)", marginLeft: 4 }}>*</span>
          </label>
          <textarea
            className="field-textarea"
            placeholder="Paste the full job description here…"
            style={{ minHeight: 180 }}
            value={form.description}
            onChange={e => update("description", e.target.value)}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }}>
          {/* Requirements */}
          <div className="field-group">
            <label className="field-label">Requirements</label>
            <textarea className="field-textarea" style={{ minHeight: 100 }}
              placeholder="Skills, qualifications required…"
              value={form.requirements} onChange={e => update("requirements", e.target.value)} />
          </div>
          {/* Company Profile */}
          <div className="field-group">
            <label className="field-label">Company Profile</label>
            <textarea className="field-textarea" style={{ minHeight: 100 }}
              placeholder="About the company…"
              value={form.company_profile} onChange={e => update("company_profile", e.target.value)} />
          </div>
        </div>

        {/* Row: salary, employment, experience */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
          <div className="field-group">
            <label className="field-label">Salary Range</label>
            <input className="field-input" placeholder="e.g. $50,000–$70,000"
              value={form.salary_range} onChange={e => update("salary_range", e.target.value)} />
          </div>
          <div className="field-group">
            <label className="field-label">Employment Type</label>
            <select className="field-select" value={form.employment_type}
              onChange={e => update("employment_type", e.target.value)}>
              <option value="">Unknown</option>
              <option>Full-time</option>
              <option>Part-time</option>
              <option>Contract</option>
              <option>Temporary</option>
              <option>Internship</option>
            </select>
          </div>
          <div className="field-group">
            <label className="field-label">Experience Required</label>
            <select className="field-select" value={form.required_experience}
              onChange={e => update("required_experience", e.target.value)}>
              <option value="">Not specified</option>
              <option>Internship</option>
              <option>Entry level</option>
              <option>Associate</option>
              <option>Mid-Senior level</option>
              <option>Director</option>
              <option>Executive</option>
            </select>
          </div>
        </div>

        {/* Checkboxes */}
        <div style={{ display: "flex", gap: "2rem", marginBottom: "1.25rem" }}>
          {[
            ["has_company_logo", "Has Company Logo"],
            ["has_questions", "Has Screening Questions"],
            ["telecommuting", "Remote / Telecommute"],
          ].map(([key, label]) => (
            <label key={key} style={{
              display: "flex", alignItems: "center", gap: 8,
              cursor: "pointer", fontSize: "0.9rem", color: "var(--text-dim)",
            }}>
              <input type="checkbox" checked={form[key] === 1}
                onChange={e => update(key, e.target.checked ? 1 : 0)}
                style={{ accentColor: "var(--accent)", width: 16, height: 16 }} />
              {label}
            </label>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div style={{
            background: "var(--fake-dim)", border: "1px solid #ff3d5750",
            borderRadius: "var(--radius)", padding: "0.75rem 1rem",
            color: "var(--fake)", fontSize: "0.875rem", marginBottom: "1rem",
          }}>
            ⚠ {error}
          </div>
        )}

        {/* Submit */}
        <button className="btn-primary" style={{ width: "100%" }}
          onClick={handleAnalyze} disabled={loading}>
          {loading ? <><div className="spinner" /> Analyzing…</> : <><span>🔍</span> Analyze Job Posting</>}
        </button>
      </div>

      {/* Stats strip */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "1rem", marginTop: "1.5rem",
      }}>
        {[
          { icon: "🤖", label: "BERT + XGBoost + LR", sub: "Ensemble Model" },
          { icon: "🧠", label: ">97% Target Accuracy", sub: "On Kaggle Dataset" },
          { icon: "⚡", label: "100% Local", sub: "No Data Sent Anywhere" },
        ].map(({ icon, label, sub }) => (
          <div key={label} className="card" style={{
            textAlign: "center", padding: "1.25rem",
            borderColor: "var(--border-glow)",
          }}>
            <div style={{ fontSize: "1.5rem", marginBottom: 6 }}>{icon}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: "0.85rem", fontWeight: 700 }}>{label}</div>
            <div style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginTop: 2 }}>{sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
