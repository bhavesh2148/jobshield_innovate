# JobShield Chrome Extension (Manifest V3)

The **JobShield Chrome Extension** provides zero-friction, in-browser recruitment fraud detection directly on **LinkedIn**, **Indeed**, **Glassdoor**, **Gmail**, and arbitrary job boards.

---

## 🚀 How to Install in Google Chrome

1. Open Google Chrome and navigate to:
   ```text
   chrome://extensions
   ```
2. Enable **Developer mode** using the toggle switch in the top-right corner.
3. Click the **Load unpacked** button in the top-left corner.
4. Select the directory:
   ```text
   C:\Users\bhave\jobshield\extension
   ```
5. The **JobShield** icon (🛡️) will now appear in your Chrome toolbar. Pin it for quick access!

---

## 🛡️ Features

### 1. In-Page Floating Scanner (LinkedIn / Indeed / Glassdoor / Gmail)
* When you browse any supported job board or email, a sleek **"Scan with JobShield"** button floats in the bottom-right corner.
* Clicking it extracts the job title, company name, and full description, and renders an instant **editorial glassmorphic threat drawer** right on the page.

### 2. Context-Menu Quick Scan
* Highlight any suspicious paragraph, email text, or WhatsApp/Telegram message on any webpage.
* Right-click and choose **"🛡️ Scan Selection with JobShield"**.
* The in-page threat drawer automatically slides in with the verdict, risk severity score (0–100), detected artifacts (emails, phones, payment handles), and MITRE ATT&CK techniques.

### 3. Standalone Popup Console
* Click the toolbar icon to view:
  * Backend connectivity status (`Connected to Port 8000` / `Backend Offline`).
  * Quick-paste text box for ad-hoc scanning.
  * One-click link to open the full JobShield Web Dashboard (`http://localhost:5173`).

---

## 🔒 Security & Privacy Guarantee
* **100% Offline & Local**: All analysis requests are sent strictly to `http://127.0.0.1:8000`. No candidate browsing data or scraped text ever leaves your local computer.
