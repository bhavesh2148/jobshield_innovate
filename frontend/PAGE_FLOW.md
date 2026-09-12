# JobShield Page Flow

## Navigation Flow

```
┌─────────────┐
│ LoginPage   │ (No navbar)
│             │
│ - Logo      │
│ - Slogan    │
│ - Email     │
│ - Password  │
│ - Sign In → │
└──────┬──────┘
       │ (slide up + fade)
       ▼
┌─────────────┐
│ LandingPage │ (No navbar)
│             │
│ - Ripple    │
│   Grid BG   │
│ - Hero Text │
│ - Stats     │
│ - Get       │
│   Started → │
└──────┬──────┘
       │ (fade + scale)
       ▼
┌─────────────┐
│ HomePage    │ ← Navbar appears
│             │   (with theme toggle)
│ - Job Form  │
│ - Analyze   │
└──────┬──────┘
       │ (slide in from right)
       ▼
┌─────────────┐
│ ResultsPage │
│             │
│ - Verdict   │
│ - Analysis  │
│ - Back      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ AdminPage   │ (accessible from navbar)
│             │
│ - Stats     │
│ - Retrain   │
│ - Drift     │
└─────────────┘
```

## Page Details

### 1. LoginPage (No Navbar)
- **Background**: Full screen dark (#0a0c10)
- **Content**: Centered card with logo, slogan, inputs
- **Animation**: Fade up on load
- **Auth**: Fake - any non-empty credentials work
- **Transition**: Slide up + fade to Landing

### 2. LandingPage (No Navbar)
- **Background**: Ripple grid (20x20 cells)
  - Hover: Cell lights up
  - Click: Ripple wave spreads
- **Content**: 
  - Logo (64px height)
  - Hero: "Detect Fake Jobs Instantly"
  - Subtitle with tech details
  - Glowing "Get Started →" button
  - 3 stat badges (>97%, 100% Local, SHAP)
- **Animation**: Fade up + scale on load
- **Transition**: Fade + scale to Home

### 3. HomePage (Navbar Visible)
- **Navbar**: 
  - Logo (switches with theme)
  - Analyze | Results | Admin buttons
  - Theme toggle (☀️/🌙)
- **Content**: Job analysis form
- **Responsive**: Grids stack on mobile
- **Transition**: Slide in from right

### 4. ResultsPage (Navbar Visible)
- **Content**: 
  - Verdict badge (FAKE/REAL)
  - Confidence meter (circular)
  - Risk score bar
  - Model breakdown
  - Explanation
  - Similarity check
  - Highlighted suspicious phrases
  - Feedback form
- **Responsive**: Two columns → single column on mobile
- **Transition**: Slide in from right

### 5. AdminPage (Navbar Visible)
- **Content**:
  - 4 stat cards (predictions, pseudo-labels, feedback, drift)
  - Retrain control panel
  - Drift events log
  - System architecture overview
- **Responsive**: Grid adapts to screen size
- **Transition**: Slide in from right

## Theme Toggle Behavior

### Dark Mode (Default)
- Logo: `jobshield_logo.svg`
- Background: #0a0c10
- Cards: #111318
- Text: #e8eaf0

### Light Mode
- Logo: `jobshield_logo_light.svg`
- Background: #f8fafc
- Cards: #ffffff
- Text: #0f172a

### Toggle Location
- Top right of navbar
- Sun icon (☀️) in dark mode → click for light
- Moon icon (🌙) in light mode → click for dark
- Persists in localStorage

## Animations

### Page Transitions (AnimatePresence)
```javascript
Login → Landing:
  initial: { opacity: 0, y: 40 }
  animate: { opacity: 1, y: 0 }
  duration: 0.4s

Landing → Home:
  initial: { opacity: 0, scale: 0.96 }
  animate: { opacity: 1, scale: 1 }
  duration: 0.4s

Home ↔ Results ↔ Admin:
  initial: { opacity: 0, x: 60 }
  animate: { opacity: 1, x: 0 }
  exit: { opacity: 0, x: -60 }
  duration: 0.4s
```

### Hover Effects
- Cards: `translateY(-2px)` + shadow increase
- Buttons: `scale(1.02)` on hover, `scale(0.98)` on click
- Theme toggle: `scale(1.1)` on hover

### Ripple Grid (LandingPage)
- Hover: Cell background → `rgba(14, 165, 233, 0.3)`
- Click: Ripple spreads from clicked cell
  - Distance-based delay (100ms per cell)
  - Color: `rgba(14, 165, 233, 0.5)` → fade out
  - Duration: 0.6s per cell

## Responsive Breakpoints

### Mobile (< 768px)
- Navbar: Hide subtitle
- Grids: Stack to single column
- Padding: Reduced from 2rem to 1rem
- Font sizes: Clamp to smaller values

### Tablet (768px - 1024px)
- Grids: 2 columns where possible
- Full navbar visible

### Desktop (> 1024px)
- Full layout
- All columns visible
- Maximum width: 1100px (centered)
