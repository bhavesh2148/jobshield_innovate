import { motion } from 'framer-motion';

export default function LandingPage({ onGetStarted, onViewThreats }) {
  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
      background: '#030303',
      color: '#ffffff',
      overflow: 'hidden',
      display: 'flex',
      alignItems: 'center',
      paddingTop: '64px',
      paddingBottom: '40px',
    }}>

      {/* ── Lower Hero Tonal Background Treatment (Lower 30–35%) ──
          Restrained photographic tonal gradient / muted gray surface emerging smoothly from the darkness.
          No objects, no illustrations, no decorative lines, purely background tonal depth.
      ── */}
      <div className="hero-lower-tonal-surface" aria-hidden="true" />

      {/* ── Hero Container ── */}
      <div style={{
        maxWidth: '1240px',
        margin: '0 auto',
        padding: '0 32px',
        width: '100%',
        position: 'relative',
        zIndex: 10,
      }}>
        <div
          className="hero-grid-split"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '48px',
            minHeight: 'calc(100vh - 160px)',
          }}
        >
          {/* ── LEFT COLUMN: Editorial Headline & CTAs ── */}
          <motion.div
            className="hero-left-content"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            style={{
              flex: '1 1 45%',
              maxWidth: '560px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-start',
              textAlign: 'left',
            }}
          >
            {/* Eyebrow label */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <span style={{
                width: '28px', height: '1.5px',
                background: 'linear-gradient(90deg, #8b5cf6, #06b6d4)',
                display: 'inline-block',
              }} />
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem',
                letterSpacing: '0.18em',
                color: 'rgba(255, 255, 255, 0.65)',
                fontWeight: 600,
                textTransform: 'uppercase',
              }}>
                RECRUITMENT THREAT INTELLIGENCE
              </span>
            </div>

            {/* Headline */}
            <h1 style={{
              fontFamily: 'var(--font-serif)',
              fontSize: 'clamp(52px, 5.8vw, 86px)',
              fontWeight: 400,
              lineHeight: '1.04',
              letterSpacing: '-0.015em',
              color: '#ffffff',
              margin: '0 0 22px 0',
            }}>
              Investigate <br />
              <span className="headline-gradient">suspicious</span> job offers.
            </h1>

            {/* Supporting copy */}
            <p style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 'clamp(15px, 1.6vw, 17px)',
              lineHeight: '1.65',
              color: 'rgba(255, 255, 255, 0.65)',
              margin: '0 0 36px 0',
              maxWidth: '470px',
              fontWeight: 400,
            }}>
              Analyze recruitment content, identify suspicious signals, and understand the risk before you engage.
            </p>

            {/* CTAs */}
            <div className="hero-actions-row" style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
              <button className="btn-glow-pill" onClick={onGetStarted}>
                Investigate a posting →
              </button>
              <button className="btn-link-subtle" onClick={onViewThreats || onGetStarted}>
                View threat activity →
              </button>
            </div>
          </motion.div>

          {/* ── RIGHT COLUMN: 3D Layered Job-Posting Cards ── */}
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            style={{
              flex: '1 1 55%',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              position: 'relative',
            }}
          >
            <div className="investigation-perspective-container">

              {/* Layer 3: Deep background (DNS / domain intel) */}
              <div className="artifact-card-layer-3">
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16,
                  color: 'rgba(255,255,255,0.4)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
                }}>
                  <span>🌐</span> DOMAIN_INTEL // DNS_VERIFY
                </div>
                <div className="skeleton-line" style={{ width: '85%' }} />
                <div className="skeleton-line" style={{ width: '60%' }} />
                <div className="skeleton-line" style={{ width: '75%' }} />
              </div>

              {/* Layer 2: Middle receding card (recruitment email) */}
              <div className="artifact-card-layer-2">
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18,
                  color: 'rgba(255,255,255,0.65)', fontSize: '0.82rem', fontWeight: 500,
                }}>
                  <span style={{ fontSize: '0.9rem' }}>✉</span> Recruitment Email
                </div>
                <div className="skeleton-line" style={{ width: '90%', height: 7 }} />
                <div className="skeleton-line" style={{ width: '70%', height: 7 }} />
                <div className="skeleton-line" style={{ width: '80%', height: 7 }} />
                <div className="skeleton-line" style={{ width: '50%', height: 7, marginBottom: 20 }} />
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 6,
                  color: 'rgba(255,255,255,0.5)', fontSize: '0.75rem',
                }}>
                  <span>📎</span> offer_letter_form.pdf
                </div>
              </div>

              {/* Layer 1: Foreground investigation report */}
              <div className="artifact-card-foreground">
                <div style={{
                  fontFamily: 'var(--font-mono)', fontSize: '0.72rem',
                  color: 'rgba(255,255,255,0.45)', letterSpacing: '0.04em', marginBottom: 10,
                }}>
                  Job Posting
                </div>
                <div style={{ fontSize: '1.35rem', fontWeight: 600, color: '#ffffff', letterSpacing: '-0.01em', marginBottom: 4 }}>
                  Software Engineer
                </div>
                <div style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.65)', marginBottom: 14 }}>
                  ABC Technologies
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 20, flexWrap: 'wrap' }}>
                  <span className="skeleton-pill"><span style={{ color: 'var(--accent-cyan)' }}>📍</span> Remote</span>
                  <span className="skeleton-pill"><span style={{ color: 'var(--accent-violet)' }}>💼</span> ₹18 - 25 LPA</span>
                </div>
                <div style={{ marginBottom: 22 }}>
                  <div className="skeleton-line" style={{ width: '100%', height: 6 }} />
                  <div className="skeleton-line" style={{ width: '92%',  height: 6 }} />
                  <div className="skeleton-line" style={{ width: '78%',  height: 6 }} />
                  <div className="skeleton-line" style={{ width: '60%',  height: 6 }} />
                </div>
                {/* Threat verdict */}
                <div className="threat-verdict-box">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <div className="threat-verdict-pill"><span>▲</span> HIGH RISK</div>
                    <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.9rem' }}>→</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: 8 }}>
                    <span style={{ fontSize: '0.82rem', color: 'rgba(255,255,255,0.85)', fontFamily: 'var(--font-sans)' }}>
                      Possible credential phishing
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', fontWeight: 700, color: '#ff304f', letterSpacing: '0.02em' }}>
                      91 / 100
                    </span>
                  </div>
                </div>
              </div>

              {/* Silver bevel streak — monochrome */}
              <div style={{
                position: 'absolute', left: '-8px', top: '30px', bottom: '40px', width: '2px',
                background: 'linear-gradient(to bottom, rgba(180,180,180,0) 0%, rgba(200,200,200,0.55) 40%, rgba(150,150,150,0.35) 80%, rgba(180,180,180,0) 100%)',
                filter: 'blur(0.8px)', zIndex: 20, pointerEvents: 'none',
              }} />

              {/* Floor reflection — monochrome */}
              <div style={{
                position: 'absolute', bottom: '-22px', left: '-30px', right: '-30px', height: '1px',
                background: 'linear-gradient(90deg, transparent 0%, rgba(160,160,160,0.18) 30%, rgba(210,210,210,0.28) 50%, rgba(160,160,160,0.18) 70%, transparent 100%)',
                boxShadow: '0 0 10px rgba(180,180,180,0.07)',
                zIndex: 1, pointerEvents: 'none',
              }} />
            </div>
          </motion.div>
        </div>
      </div>

    </div>
  );
}
