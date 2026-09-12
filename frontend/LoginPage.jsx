import { useState } from 'react';
import { motion } from 'framer-motion';

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email.trim() && password.trim()) {
      setIsLoading(true);
      setTimeout(() => {
        onLogin();
      }, 500);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#030303',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      overflow: 'auto'
    }}>
      <motion.div
        initial={{ opacity: 0, y: 25 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="card"
        style={{
          maxWidth: '400px',
          width: '100%',
          padding: '40px 32px',
          background: 'rgba(12, 14, 20, 0.85)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.7)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <img 
            src="/jobshield_logo.svg" 
            alt="JobShield" 
            style={{ height: '42px', marginBottom: '14px' }}
          />
          <div style={{
            fontFamily: 'var(--font-mono)',
            color: 'var(--accent)',
            fontSize: '0.72rem',
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            marginBottom: '4px',
            fontWeight: 600
          }}>
            Threat Intelligence Console
          </div>
          <p style={{
            color: 'var(--text-dim)',
            fontSize: '0.85rem',
            margin: 0
          }}>
            Sign in to access JobShield threat detection
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="field-group">
            <label className="field-label">
              Operator Email
            </label>
            <input
              type="email"
              className="field-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@security.local"
              required
            />
          </div>

          <div className="field-group" style={{ marginBottom: '22px' }}>
            <label className="field-label">
              Passcode
            </label>
            <input
              type="password"
              className="field-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary"
            style={{ width: '100%', padding: '0.8rem' }}
          >
            {isLoading ? (
              <><div className="spinner" /> Authenticating…</>
            ) : (
              'Access Console →'
            )}
          </button>

          <p style={{
            textAlign: 'center',
            color: 'var(--text-subtle)',
            fontSize: '0.75rem',
            fontFamily: 'var(--font-mono)',
            marginTop: '16px',
            marginBottom: 0
          }}>
            Evaluation sandbox — enter any credentials
          </p>
        </form>
      </motion.div>
    </div>
  );
}
