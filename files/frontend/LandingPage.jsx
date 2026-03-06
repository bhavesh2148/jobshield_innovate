import { useState, useRef } from 'react';
import { motion, useAnimation } from 'framer-motion';

const GRID_SIZE = 20;
const RIPPLE_SPEED = 100;

export default function LandingPage({ onGetStarted }) {
  const [hoveredCell, setHoveredCell] = useState(null);
  const cellAnimations = useRef({});

  const getCellAnimation = (index) => {
    if (!cellAnimations.current[index]) {
      cellAnimations.current[index] = useAnimation();
    }
    return cellAnimations.current[index];
  };

  const handleCellClick = async (clickedIndex) => {
    const clickedRow = Math.floor(clickedIndex / GRID_SIZE);
    const clickedCol = clickedIndex % GRID_SIZE;

    for (let i = 0; i < GRID_SIZE * GRID_SIZE; i++) {
      const row = Math.floor(i / GRID_SIZE);
      const col = i % GRID_SIZE;
      const distance = Math.sqrt(
        Math.pow(row - clickedRow, 2) + Math.pow(col - clickedCol, 2)
      );

      const animation = getCellAnimation(i);
      
      setTimeout(() => {
        animation.start({
          backgroundColor: ['rgba(14, 165, 233, 0)', 'rgba(14, 165, 233, 0.5)', 'rgba(14, 165, 233, 0)'],
          transition: { duration: 0.6, ease: 'easeOut' }
        });
      }, distance * RIPPLE_SPEED);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0c10',
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      overflow: 'hidden'
    }}>
      {/* Ripple Grid Background */}
      <div style={{
        position: 'absolute',
        inset: 0,
        display: 'grid',
        gridTemplateColumns: `repeat(${GRID_SIZE}, 1fr)`,
        gridTemplateRows: `repeat(${GRID_SIZE}, 1fr)`,
        opacity: 0.6
      }}>
        {Array.from({ length: GRID_SIZE * GRID_SIZE }).map((_, i) => (
          <motion.div
            key={i}
            animate={getCellAnimation(i)}
            onMouseEnter={() => setHoveredCell(i)}
            onMouseLeave={() => setHoveredCell(null)}
            onClick={() => handleCellClick(i)}
            style={{
              border: '1px solid rgba(255, 255, 255, 0.03)',
              backgroundColor: hoveredCell === i ? 'rgba(14, 165, 233, 0.3)' : 'transparent',
              transition: 'background-color 0.2s ease',
              cursor: 'pointer'
            }}
          />
        ))}
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        style={{
          position: 'relative',
          zIndex: 10,
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px 20px',
          textAlign: 'center'
        }}
      >
        <motion.img
          src="/jobshield_logo.svg"
          alt="JobShield"
          style={{ height: '80px', marginBottom: '32px' }}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        />

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          style={{
            fontSize: 'clamp(36px, 8vw, 64px)',
            fontWeight: '700',
            color: 'var(--text)',
            margin: '0 0 24px 0',
            lineHeight: '1.2',
            maxWidth: '900px'
          }}
        >
          Detect Fake Jobs Instantly
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          style={{
            fontSize: 'clamp(16px, 2vw, 18px)',
            color: 'var(--text-muted)',
            margin: '0 0 40px 0',
            maxWidth: '700px',
            lineHeight: '1.6'
          }}
        >
          AI-powered fraud detection using BERT + XGBoost ensemble — fully local, no data shared
        </motion.p>

        <motion.button
          onClick={onGetStarted}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          style={{
            padding: '16px 48px',
            background: 'var(--accent)',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            fontSize: '18px',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 0 30px rgba(74, 158, 255, 0.5)',
            transition: 'all 0.3s ease',
            marginBottom: '24px'
          }}
        >
          Get Started →
        </motion.button>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          style={{
            fontSize: '14px',
            color: 'var(--text-muted)',
            fontStyle: 'italic',
            margin: '0 0 48px 0'
          }}
        >
          Your First Line of Defense Against Job Fraud
        </motion.p>

        {/* Stats Badges */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.6 }}
          style={{
            display: 'flex',
            gap: '20px',
            flexWrap: 'wrap',
            justifyContent: 'center',
            maxWidth: '800px'
          }}
        >
          <StatBadge color="#00e676" delay={0.8}>
            &gt;97% Accuracy
          </StatBadge>
          <StatBadge color="#4a9eff" delay={0.9}>
            100% Local
          </StatBadge>
          <StatBadge color="#f59e0b" delay={1.0}>
            SHAP Explainable
          </StatBadge>
        </motion.div>
      </motion.div>
    </div>
  );
}

function StatBadge({ children, color, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ y: -4, scale: 1.05 }}
      style={{
        padding: '12px 24px',
        background: 'var(--bg-card)',
        border: `2px solid ${color}`,
        borderRadius: '24px',
        color: color,
        fontSize: '14px',
        fontWeight: '600',
        boxShadow: `0 0 20px ${color}40`,
        transition: 'all 0.3s ease'
      }}
    >
      {children}
    </motion.div>
  );
}
