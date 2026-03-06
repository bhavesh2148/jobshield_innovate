import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import LoginPage from "./LoginPage.jsx";
import LandingPage from "./LandingPage.jsx";
import HomePage from "./HomePage.jsx";
import ResultsPage from "./ResultsPage.jsx";
import AdminPage from "./AdminPage.jsx";
import "./index.css";

export default function App() {
  const [page, setPage] = useState("login");
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
    setTheme(prev => prev === "dark" ? "light" : "dark");
  };

  const navigate = (to, data = null) => {
    if (data) setResult(data);
    setPage(to);
  };

  const showNavbar = !["login", "landing"].includes(page);

  const pageVariants = {
    initial: { opacity: 0, x: 60 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -60 }
  };

  const landingVariants = {
    initial: { opacity: 0, scale: 0.96 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 1.04 }
  };

  const loginVariants = {
    initial: { opacity: 0, y: 40 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -40 }
  };

  return (
    <div className="app" style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {showNavbar && (
        <nav className="navbar">
          <div className="nav-brand" onClick={() => setPage("home")}>
            <img 
              src={theme === "light" ? "/jobshield_logo_light.svg" : "/jobshield_logo.svg"}
              alt="JobShield"
              style={{ height: '32px', cursor: 'pointer' }}
            />
          </div>
          <div className="nav-links">
            <button
              className={`nav-btn ${page === "home" ? "active" : ""}`}
              onClick={() => setPage("home")}
            >
              Analyze
            </button>
            {result && (
              <button
                className={`nav-btn ${page === "results" ? "active" : ""}`}
                onClick={() => setPage("results")}
              >
                Results
              </button>
            )}
            <button
              className={`nav-btn ${page === "admin" ? "active" : ""}`}
              onClick={() => setPage("admin")}
            >
              Admin
            </button>
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
          </div>
        </nav>
      )}

      <main className="main-content" style={{ 
        paddingTop: showNavbar ? '80px' : '0',
        minHeight: '100vh',
        background: 'var(--bg)'
      }}>
        <AnimatePresence mode="wait">
          {page === "login" && (
            <motion.div
              key="login"
              variants={loginVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              <LoginPage onLogin={() => setPage("landing")} />
            </motion.div>
          )}

          {page === "landing" && (
            <motion.div
              key="landing"
              variants={landingVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              <LandingPage onGetStarted={() => setPage("home")} />
            </motion.div>
          )}

          {page === "home" && (
            <motion.div
              key="home"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.4, ease: "easeInOut" }}
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
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              <ResultsPage result={result} jobData={jobData} onBack={() => setPage("home")} />
            </motion.div>
          )}

          {page === "admin" && (
            <motion.div
              key="admin"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              <AdminPage />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
