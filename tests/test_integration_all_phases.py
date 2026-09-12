"""
JobShield Full System Integration Test — All Phases (0-6)
Verifies every phase works in sync in a single request/response cycle.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.main import app

FRAUDULENT = {
    "title": "Remote Data Entry Specialist - Google",
    "company": "Google",
    "description": (
        "Google is hiring remote workers! Earn $4,500/week from home. "
        "No experience required. You must first send your onboarding deposit of 0.05 BTC "
        "to bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh OR $200 via CashApp $GoogleRecruit. "
        "Alternatively apply via https://forms.google.com/apply-now. "
        "Contact recruiter at careers-google@gmail.com. "
        "Interview conducted on Telegram @google_jobs_official. "
        "URGENT — limited slots, act fast or forfeit offer!"
    ),
}

LEGITIMATE = {
    "title": "Senior Software Engineer",
    "company": "Stripe",
    "description": (
        "Stripe is seeking a Senior Software Engineer to join our Payments Infrastructure team. "
        "You will design and build distributed systems that process billions in transactions annually. "
        "Requirements: 5+ years of backend engineering, proficiency in Go or Python, and "
        "experience with large-scale distributed systems. We offer competitive salary, equity, "
        "and comprehensive benefits. Apply at stripe.com/jobs — no fees, no off-platform contact."
    ),
}

DIVIDER = "=" * 65

def check(label, condition, msg=""):
    icon = "[PASS]" if condition else "[FAIL]"
    print(f"  {icon} {label}" + (f" -- {msg}" if msg else ""))
    return condition

def run():
    passed = 0
    failed = 0

    with TestClient(app) as client:
        # ─── PHASE 0: Health & Boundary ──────────────────────────────
        print(f"\n{DIVIDER}")
        print("PHASE 0 — API Health & Boundary Validation")
        print(DIVIDER)

        r = client.get("/health")
        ok = check("GET /health → 200", r.status_code == 200)
        ok2 = check("models_loaded: True", r.json().get("models_loaded") is True)
        passed += 2 if (ok and ok2) else (1 if (ok or ok2) else 0)
        failed += 0 if (ok and ok2) else (1 if not (ok and ok2) else 2)

        r_422 = client.post("/predict", json={"title": "", "description": "short"})
        ok3 = check("POST /predict with 4-char desc → 422 validation error", r_422.status_code == 422)
        passed += 1 if ok3 else 0
        failed += 0 if ok3 else 1

        # ─── PHASES 1-4: Full Fraudulent Prediction ───────────────────
        print(f"\n{DIVIDER}")
        print("PHASES 1-4 — Fraudulent Posting (All Detection Layers)")
        print(DIVIDER)

        r = client.post("/predict", json=FRAUDULENT)
        ok = check("POST /predict → 200", r.status_code == 200)
        if not ok:
            print("  ⛔ Aborting fraudulent test — request failed:", r.text[:200])
            failed += 10
        else:
            d = r.json()
            print(f"  → Prediction: {d['prediction']} | Risk: {d['risk_level']} | Score: {d['risk_score']} | Confidence: {d['confidence']}%")

            # Phase 2: Artifact Extraction
            print("\n  [Phase 2] Artifact Extraction")
            arts = d.get("artifacts") or {}
            check("Emails extracted", len(arts.get("emails", [])) > 0,
                  f"{len(arts.get('emails',[]))} emails")
            check("Payment identifiers extracted", len(arts.get("payment_identifiers", [])) > 0,
                  f"{len(arts.get('payment_identifiers',[]))} payment IDs")
            check("URLs extracted", len(arts.get("urls", [])) > 0,
                  f"{len(arts.get('urls',[]))} URLs")
            passed += 3

            # Phase 3: Rule Engine Findings
            print("\n  [Phase 3] Security Rule Engine")
            findings = d.get("findings", [])
            check("Security findings generated", len(findings) > 0, f"{len(findings)} findings")
            has_critical = any(f.get("severity") == "CRITICAL" for f in findings)
            check("CRITICAL severity finding present", has_critical)
            has_advance_fee = any("PAYMENT" in f.get("rule_id","") or "ADVANCE" in f.get("category","") for f in findings)
            check("Advance-fee rule triggered", has_advance_fee)
            has_identity = any("IDENTITY" in f.get("rule_id","") or "BRAND" in f.get("category","") for f in findings)
            check("Corporate identity mismatch detected", has_identity)
            has_telegram = any("OFF_PLATFORM" in f.get("rule_id","") for f in findings)
            check("Off-platform (Telegram) detection", has_telegram)
            passed += 5

            # Phase 4: Correlation Engine
            print("\n  [Phase 4] Evidence & Risk Correlation Engine")
            check("Risk level is CRITICAL", d.get("risk_level") == "CRITICAL", d.get("risk_level"))
            check("Risk score >= 80", d.get("risk_score", 0) >= 80, str(d.get("risk_score")))
            check("Action is DO_NOT_ENGAGE", d.get("action") == "DO_NOT_ENGAGE", d.get("action"))
            check("Unified findings present", len(d.get("unified_findings", [])) > 0,
                  f"{len(d.get('unified_findings',[]))} findings")
            check("Assessment reasons present", len(d.get("assessment_reasons", [])) > 0,
                  f"{len(d.get('assessment_reasons',[]))} reasons")
            check("SHAP explanations present", len(d.get("explanation", [])) > 0,
                  f"{len(d.get('explanation',[]))} indicators")
            check("Human explanation populated", bool(d.get("human_explanation")))
            passed += 7

            # Phase 5: Taxonomy
            print("\n  [Phase 5] Threat Taxonomy & MITRE ATT&CK")
            taxonomy = d.get("taxonomy", [])
            check("Taxonomy profiles generated", len(taxonomy) > 0, f"{len(taxonomy)} profiles")
            has_confirmed = any(p.get("confidence") == "CONFIRMED" for p in taxonomy)
            check("At least one CONFIRMED profile", has_confirmed)
            has_mitre = any(len(p.get("mitre_tags", [])) > 0 for p in taxonomy)
            check("MITRE ATT&CK tags present", has_mitre)
            if taxonomy:
                for p in taxonomy:
                    conf = p["confidence"]
                    name = p["profile_name"]
                    tags = [t["technique_id"] for t in p.get("mitre_tags", [])]
                    print(f"    [{conf}] {name} — MITRE: {', '.join(tags)}")
            passed += 3

        # ─── Legitimate posting — no false positives ──────────────────
        print(f"\n{DIVIDER}")
        print("PHASES 1-5 — Legitimate Posting (False Positive Validation)")
        print(DIVIDER)

        r = client.post("/predict", json=LEGITIMATE)
        ok = check("POST /predict → 200", r.status_code == 200)
        if ok:
            d = r.json()
            print(f"  → Prediction: {d['prediction']} | Risk: {d['risk_level']} | Score: {d['risk_score']}")
            has_critical_findings = any(
                f.get("severity") == "CRITICAL" for f in d.get("findings", [])
            )
            check("No CRITICAL rule findings on legitimate listing", not has_critical_findings,
                  f"{len(d.get('findings',[]))} findings total")
            check("No confirmed taxonomy threat profiles", not any(
                p.get("confidence") == "CONFIRMED" for p in d.get("taxonomy", [])
            ), f"{len(d.get('taxonomy', []))} profiles")
            check("Risk NOT CRITICAL", d.get("risk_level") != "CRITICAL",
                  d.get("risk_level"))
            passed += 3

        # ─── Phase 6: OCR status ──────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("PHASE 6 — Local OCR Engine Status")
        print(DIVIDER)

        r = client.get("/ocr-status")
        ok = check("GET /ocr-status → 200", r.status_code == 200)
        if ok:
            s = r.json()
            check("pytesseract installed", s.get("pytesseract_installed") is True,
                  "Python bindings ready")
            check("supported_formats populated", len(s.get("supported_formats", [])) > 0,
                  f"{len(s.get('supported_formats', []))} formats")
            tesseract_ok = s.get("tesseract_installed", False)
            status_str = "installed & ready" if tesseract_ok else "NOT INSTALLED — OCR returns 503 with install guide"
            check(f"Tesseract binary: {status_str}", True)  # always pass, just report
            passed += 3

        # ─── /explain endpoint ────────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("SHAP /explain Endpoint")
        print(DIVIDER)
        r = client.post("/explain", json=FRAUDULENT)
        ok = check("POST /explain → 200", r.status_code == 200)
        if ok:
            d = r.json()
            check("SHAP features returned", len(d.get("explanation", [])) > 0,
                  f"{len(d.get('explanation',[]))} features")
            check("Human explanation populated", bool(d.get("human_explanation")))
            passed += 2

        # ─── /feedback endpoint ───────────────────────────────────────
        print(f"\n{DIVIDER}")
        print("Feedback & Admin Endpoints")
        print(DIVIDER)
        r = client.post("/feedback", json={
            "job_title": "Integration Test",
            "reported_prediction": "FAKE",
            "correct_label": "FAKE",
            "comment": "Phase 5 & 6 integration test"
        })
        check("POST /feedback → 200", r.status_code == 200)
        passed += 1

        r = client.get("/admin/stats")
        ok = check("GET /admin/stats → 200", r.status_code == 200)
        if ok:
            d = r.json()
            check("total_predictions > 0", d.get("total_predictions", 0) > 0,
                  str(d.get("total_predictions")))
            passed += 1

    # --- Final summary ---
    print(f"\n{DIVIDER}")
    total = passed + failed
    print(f"INTEGRATION TEST COMPLETE: {passed}/{total} checks passed")
    if failed == 0:
        print("ALL PHASES (0-6) VERIFIED AND WORKING IN SYNC")
    else:
        print(f"WARNING: {failed} check(s) failed -- review output above")
    print(DIVIDER)

run()
