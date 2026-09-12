import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import LoginPage from "./LoginPage.jsx";
import LandingPage from "./LandingPage.jsx";
import HomePage from "./HomePage.jsx";
import ResultsPage from "./ResultsPage.jsx";
import AdminPage from "./AdminPage.jsx";
import "./index.css";

export default function App() {
  const [page, setPage] = useState("landing");
  const [result, setResult] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("jobshield-theme") || "dark";
  });

  useEffect(() => {
    document.body.className = theme === "light" ? "light" : "";
    localStorage.setItem("jobshield-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === "dark" ? "light" : "dark"));
  };

  const navigate = (to, data = null) => {
    if (data) setResult(data);
    setPage(to);
  };

  const showNavbar = page !== "login";

  const pageVariants = {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -12 },
  };

  return (
    <div className="app" style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      
      {/* ── Floating Capsule Navbar (Reference 2) ── */}
      {showNavbar && (
        <div className="navbar-wrapper">
          <header className="navbar-capsule">
            
            {/* Left: Brand with Glowing Gradient Orb */}
            <div
              className="nav-brand-container"
              onClick={() => setPage("landing")}
              title="JobShield Recruitment Threat Intelligence"
            >
              <div className="nav-brand-orb" />
              <span className="nav-brand-title">JOBSHIELD</span>
            </div>

            {/* Center: Navigation Menu Links */}
            <nav className="nav-menu-links">
              <button
                className={`nav-link-item ${page === "landing" ? "active" : ""}`}
                onClick={() => setPage("landing")}
              >
                Home
                {page === "landing" && <div className="nav-active-glow" />}
              </button>

              <button
                className={`nav-link-item ${page === "home" ? "active" : ""}`}
                onClick={() => setPage("home")}
              >
                Investigate
                {page === "home" && <div className="nav-active-glow" />}
              </button>

              <button
                className={`nav-link-item ${page === "results" ? "active" : ""}`}
                onClick={() => {
                  if (result) setPage("results");
                  else setPage("home");
                }}
              >
                Dossier
                {page === "results" && <div className="nav-active-glow" />}
              </button>
            </nav>

            {/* Right: Engine Status, Admin, and Settings */}
            <div className="nav-actions-right">
              <div className="nav-status-badge">
                <span className="nav-status-dot" />
                <span>Engine Online</span>
              </div>

              <button
                className="nav-admin-btn"
                onClick={() => setPage("admin")}
              >
                <span>👤 Admin</span>
                <span style={{ fontSize: '0.65rem', opacity: 0.7 }}>⌄</span>
              </button>

              <button
                className="nav-settings-pill"
                onClick={toggleTheme}
                title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
              >
                <span>⚙</span>
                <span>{theme === "dark" ? "Settings" : "Theme"}</span>
              </button>
            </div>
          </header>
        </div>
      )}

      {/* ── Main View Switcher ── */}
      <main style={{
        paddingTop: showNavbar && page !== "landing" ? '90px' : '0',
        minHeight: '100vh',
        background: 'var(--bg)',
      }}>
        <AnimatePresence mode="wait">
          {page === "login" && (
            <motion.div
              key="login"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <LoginPage onLogin={() => setPage("landing")} />
            </motion.div>
          )}

          {page === "landing" && (
            <motion.div
              key="landing"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.35, ease: "easeOut" }}
            >
              <LandingPage
                onGetStarted={() => setPage("home")}
                onViewThreats={() => {
                  if (result) setPage("results");
                  else setPage("home");
                }}
              />
            </motion.div>
          )}

          {page === "home" && (
            <motion.div
              key="home"
              className="main-content"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              <HomePage onResult={(res, job) => {
                setJobData(job);
                navigate("results", res);
              }} />
            </motion.div>
          )}

          {page === "results" && result && (
            <motion.div
              key="results"
              className="main-content"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              <ResultsPage result={result} jobData={jobData} onBack={() => setPage("home")} />
            </motion.div>
          )}

          {page === "admin" && (
            <motion.div
              key="admin"
              className="main-content"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              <AdminPage />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
