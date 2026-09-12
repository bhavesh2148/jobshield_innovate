"""
Unit tests for JobShield Phase 7: Passive Local Domain & Impersonation Intel.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from security.domain_intel import (
    calculate_shannon_entropy,
    normalize_homoglyphs,
    damerau_levenshtein_distance,
    analyze_domain_intel,
)


def test_shannon_entropy_calculation():
    # Low entropy: highly repetitive string
    e_low = calculate_shannon_entropy("aaaaaaaaaa")
    assert e_low == 0.0

    # Normal dictionary word
    e_word = calculate_shannon_entropy("google")
    assert 1.5 < e_word < 2.5

    # High entropy: randomized string
    e_high = calculate_shannon_entropy("7x9q2w4m1z")
    assert e_high > 3.2


def test_homoglyph_normalization():
    # Cyrillic 'a' (\u0430) and 'o' (\u043e)
    cyrillic_text = "g\u043e\u043egle"
    normalized = normalize_homoglyphs(cyrillic_text)
    assert normalized == "google"

    # Latin dotless i (\u0131)
    dotless_stripe = "str\u0131pe"
    assert normalize_homoglyphs(dotless_stripe) == "stripe"

    # Leetspeak numbers
    assert normalize_homoglyphs("inf0sys") == "infosys"


def test_damerau_levenshtein_distance():
    # Identical
    assert damerau_levenshtein_distance("google", "google") == 0
    # 1 insertion
    assert damerau_levenshtein_distance("google", "googles") == 1
    # 1 deletion
    assert damerau_levenshtein_distance("infosys", "infoss") == 1
    # 1 substitution
    assert damerau_levenshtein_distance("stripe", "strape") == 1
    # 1 adjacent transposition
    assert damerau_levenshtein_distance("amazon", "amzaon") == 1


def test_authentic_domains_produce_no_findings():
    authentic = [
        "google.com",
        "careers.google.com",
        "microsoft.com",
        "infosys.com",
        "stripe.com",
        "amazon.com",
        "aws.amazon.com",
    ]
    for dom in authentic:
        findings = analyze_domain_intel(dom)
        assert len(findings) == 0, f"Authentic domain {dom} should not trigger findings"


def test_homoglyph_domain_attack_detection():
    # gооgle.com with Cyrillic 'о'
    spoofed = "g\u043e\u043egle.com"
    findings = analyze_domain_intel(spoofed)
    assert len(findings) > 0
    f = findings[0]
    assert f.finding_type == "HOMOGLYPH"
    assert f.severity == "CRITICAL"
    assert f.target_brand == "google"
    assert f.legitimate_domain == "google.com"


def test_typosquatting_detection():
    # inf0sys.com (leetspeak zero)
    findings = analyze_domain_intel("inf0sys.com")
    assert len(findings) > 0
    assert findings[0].finding_type == "TYPOSQUATTING"
    assert findings[0].target_brand == "infosys"
    assert findings[0].severity == "CRITICAL"

    # micros0ft.com
    findings_ms = analyze_domain_intel("micros0ft.com")
    assert len(findings_ms) > 0
    assert findings_ms[0].finding_type == "TYPOSQUATTING"
    assert findings_ms[0].target_brand == "microsoft"


def test_brand_hijacking_with_high_risk_tld():
    # google-careers-portal.site
    findings = analyze_domain_intel("google-careers-portal.site")
    assert len(findings) > 0
    f = findings[0]
    assert f.finding_type == "BRAND_HIJACKING"
    assert f.target_brand == "google"
    assert f.severity == "CRITICAL"


def test_high_entropy_dga_detection():
    # Random generated domain stem
    dga_domain = "qx9z4k2b7v1.com"
    findings = analyze_domain_intel(dga_domain)
    assert len(findings) > 0
    assert findings[0].finding_type == "HIGH_ENTROPY_DGA"
    assert findings[0].severity == "MEDIUM"
