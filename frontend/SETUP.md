# JobShield Frontend Setup

## Quick Start

1. Install dependencies (including framer-motion):
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Make sure the backend is running at `http://localhost:8000`

## What's New

### Pages
- **LoginPage.jsx** - Animated login with fake auth (any credentials work)
- **LandingPage.jsx** - Hero page with interactive ripple grid background
- **HomePage.jsx** - Job analysis form (responsive)
- **ResultsPage.jsx** - Results display (responsive)
- **AdminPage.jsx** - Admin dashboard (responsive)

### Features
- ✅ Light/Dark mode toggle (persists in localStorage)
- ✅ Smooth page transitions with framer-motion
- ✅ Ripple effect on landing page
- ✅ Fully responsive design (mobile-friendly)
- ✅ JobShield branding throughout
- ✅ Logo changes based on theme

### Branding
- App name: **JobShield**
- Slogan: "Your First Line of Defense Against Job Fraud"
- Logos in `frontend/public/`:
  - `jobshield_logo.svg` (dark mode)
  - `jobshield_logo_light.svg` (light mode)
  - `jobshield_icon.svg` (favicon)

## Page Flow
1. Login → Landing → Home → Results
2. Navbar hidden on Login and Landing pages
3. Theme toggle in navbar (sun/moon icon)
