# ============================================================
# security/domain_intel.py
# ============================================================
"""
JobShield Passive Local Domain & Brand Impersonation Subsystem (Phase 7).

Provides 100% offline, privacy-preserving threat intelligence for domains,
URLs, and email hostnames extracted from recruitment correspondence.

Key Capabilities:
1. Curated enterprise brand directory (Fortune 500 tech, finance, consulting).
2. Offline Levenshtein and Damerau-Levenshtein typo-squatting detection.
3. Unicode homoglyph / confusable character normalization (Cyrillic, Greek, Latin).
4. Brand keyword hijacking detection (e.g. `google-careers-portal.site`).
5. High-risk Top-Level Domain (TLD) correlation.
6. Shannon entropy metric for detecting Algorithmically Generated Domains (DGAs).
7. Zero outbound network calls — entirely deterministic and local.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


# ── Top Targeted Enterprise Brands & Legitimate Domains ───────────
TARGETED_ENTERPRISE_BRANDS = {
    "google": {"primary_domain": "google.com", "aliases": ["google.com", "alphabet.com"]},
    "microsoft": {"primary_domain": "microsoft.com", "aliases": ["microsoft.com", "linkedin.com"]},
    "amazon": {"primary_domain": "amazon.com", "aliases": ["amazon.com", "aws.amazon.com"]},
    "apple": {"primary_domain": "apple.com", "aliases": ["apple.com"]},
    "meta": {"primary_domain": "meta.com", "aliases": ["meta.com", "facebook.com", "instagram.com"]},
    "netflix": {"primary_domain": "netflix.com", "aliases": ["netflix.com"]},
    "infosys": {"primary_domain": "infosys.com", "aliases": ["infosys.com"]},
    "tcs": {"primary_domain": "tcs.com", "aliases": ["tcs.com", "tataconsultancy.com"]},
    "wipro": {"primary_domain": "wipro.com", "aliases": ["wipro.com"]},
    "accenture": {"primary_domain": "accenture.com", "aliases": ["accenture.com"]},
    "cognizant": {"primary_domain": "cognizant.com", "aliases": ["cognizant.com"]},
    "ibm": {"primary_domain": "ibm.com", "aliases": ["ibm.com"]},
    "cisco": {"primary_domain": "cisco.com", "aliases": ["cisco.com"]},
    "oracle": {"primary_domain": "oracle.com", "aliases": ["oracle.com"]},
    "salesforce": {"primary_domain": "salesforce.com", "aliases": ["salesforce.com"]},
    "stripe": {"primary_domain": "stripe.com", "aliases": ["stripe.com"]},
    "paypal": {"primary_domain": "paypal.com", "aliases": ["paypal.com"]},
    "deloitte": {"primary_domain": "deloitte.com", "aliases": ["deloitte.com"]},
    "pwc": {"primary_domain": "pwc.com", "aliases": ["pwc.com"]},
    "ey": {"primary_domain": "ey.com", "aliases": ["ey.com", "ernstyoung.com"]},
    "kpmg": {"primary_domain": "kpmg.com", "aliases": ["kpmg.com"]},
    "uber": {"primary_domain": "uber.com", "aliases": ["uber.com"]},
    "airbnb": {"primary_domain": "airbnb.com", "aliases": ["airbnb.com"]},
    "spotify": {"primary_domain": "spotify.com", "aliases": ["spotify.com"]},
    "adobe": {"primary_domain": "adobe.com", "aliases": ["adobe.com"]},
    "intel": {"primary_domain": "intel.com", "aliases": ["intel.com"]},
    "nvidia": {"primary_domain": "nvidia.com", "aliases": ["nvidia.com"]},
    "tesla": {"primary_domain": "tesla.com", "aliases": ["tesla.com"]},
    "goldmansachs": {"primary_domain": "goldmansachs.com", "aliases": ["goldmansachs.com", "gs.com"]},
    "jpmorgan": {"primary_domain": "jpmorgan.com", "aliases": ["jpmorgan.com", "jpmorganchase.com", "chase.com"]},
    "morganstanley": {"primary_domain": "morganstanley.com", "aliases": ["morganstanley.com"]},
}

# ── High-Risk Top-Level Domains (TLDs) frequently abused in recruitment lures ─
HIGH_RISK_TLDS = {
    "xyz", "top", "site", "online", "club", "work", "buzz", "fit",
    "rest", "tk", "ml", "ga", "cf", "gq", "pw", "cc", "icu", "click",
    "vip", "live", "cam", "space", "host", "uno"
}

# ── Recruitment / Corporate Keyword Lures in Malicious Hostnames ─
RECRUITMENT_LURE_KEYWORDS = {
    "career", "careers", "job", "jobs", "hiring", "recruit", "recruitment",
    "hr", "interview", "portal", "verify", "verification", "onboarding",
    "apply", "work", "talent", "staffing", "employment"
}

# ── Homoglyph / Confusable Mapping (Unicode to ASCII) ────────────
# Maps visual look-alikes across Cyrillic, Greek, and extended Latin
HOMOGLYPH_MAP = {
    # Cyrillic
    '\u0430': 'a', '\u0410': 'A',  # Cyrillic a / A
    '\u0441': 'c', '\u0421': 'C',  # Cyrillic c / C
    '\u0435': 'e', '\u0415': 'E',  # Cyrillic e / E
    '\u0456': 'i', '\u0406': 'I',  # Cyrillic i / I
    '\u0458': 'j', '\u0408': 'J',  # Cyrillic j / J
    '\u043e': 'o', '\u041e': 'O',  # Cyrillic o / O
    '\u0440': 'p', '\u0420': 'P',  # Cyrillic p / P
    '\u0455': 's', '\u0405': 'S',  # Cyrillic s / S
    '\u0445': 'x', '\u0425': 'X',  # Cyrillic x / X
    '\u0443': 'y', '\u0423': 'Y',  # Cyrillic y / Y
    # Latin Extended / Diacritics
    '\u0131': 'i',                 # Latin small letter dotless i
    '\u00e0': 'a', '\u00e1': 'a', '\u00e2': 'a', '\u00e3': 'a', '\u00e4': 'a',
    '\u00e8': 'e', '\u00e9': 'e', '\u00ea': 'e', '\u00eb': 'e',
    '\u00ec': 'i', '\u00ed': 'i', '\u00ee': 'i', '\u00ef': 'i',
    '\u00f2': 'o', '\u00f3': 'o', '\u00f4': 'o', '\u00f5': 'o', '\u00f6': 'o',
    '\u00f9': 'u', '\u00fa': 'u', '\u00fb': 'u', '\u00fc': 'u',
    # Common Leetspeak in Hostnames
    '0': 'o',
    '1': 'l',
    '3': 'e',
    '5': 's',
}


@dataclass
class DomainIntelFinding:
    domain: str
    finding_type: str                  # "HOMOGLYPH", "TYPOSQUATTING", "BRAND_HIJACKING", "HIGH_ENTROPY_DGA", "HIGH_RISK_TLD_LURE"
    target_brand: Optional[str]
    legitimate_domain: Optional[str]
    severity: str                      # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    confidence: float                  # 0.0 to 1.0
    description: str
    mitre_technique_id: str            # "T1583.001" or "T1566.002"
    mitre_technique_name: str
    entropy: float = 0.0


# ── Algorithmic Functions ─────────────────────────────────────────

def calculate_shannon_entropy(text: str) -> float:
    """
    Calculates the Shannon Entropy of a string.
    High entropy (e.g. > 3.8 on 8+ character stems) indicates random/DGA naming.
    """
    if not text:
        return 0.0
    text_clean = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    if not text_clean:
        return 0.0
    prob_dict = {}
    length = len(text_clean)
    for ch in text_clean:
        prob_dict[ch] = prob_dict.get(ch, 0) + 1
    entropy = -sum((count / length) * math.log2(count / length) for count in prob_dict.values())
    return round(entropy, 3)


def normalize_homoglyphs(text: str) -> str:
    """Normalizes Unicode confusables and numeric leetspeak to canonical Latin."""
    chars = []
    for ch in text:
        chars.append(HOMOGLYPH_MAP.get(ch, ch.lower()))
    return "".join(chars)


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes Damerau-Levenshtein distance (insertions, deletions,
    substitutions, and adjacent transpositions) between two strings.
    """
    d = {}
    len1 = len(s1)
    len2 = len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,       # deletion
                d[(i, j - 1)] + 1,       # insertion
                d[(i - 1, j - 1)] + cost # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + cost) # transposition

    return d[(len1 - 1, len2 - 1)]


def extract_domain_stem_and_tld(hostname: str) -> tuple[str, str, str]:
    """
    Splits hostname into (subdomain, stem, tld).
    e.g. 'careers.google.com' -> ('careers', 'google', 'com')
         'inf0sys-careers.site' -> ('', 'inf0sys-careers', 'site')
    """
    hostname = hostname.lower().strip()
    if ":" in hostname:
        hostname = hostname.split(":")[0]
    parts = hostname.split(".")
    if len(parts) < 2:
        return "", hostname, ""
    tld = parts[-1]
    stem = parts[-2]
    subdomain = ".".join(parts[:-2]) if len(parts) > 2 else ""
    return subdomain, stem, tld


# ── Core Domain Intel Analysis Engine ─────────────────────────────

def analyze_domain_intel(domain: str, claimed_company: str = "") -> list[DomainIntelFinding]:
    """
    Performs comprehensive passive threat analysis on a single domain.

    Returns a list of `DomainIntelFinding` objects if any suspicious
    indicators (typo-squatting, homoglyphs, brand hijacking, DGA entropy) are detected.
    """
    findings: list[DomainIntelFinding] = []
    clean_domain = domain.lower().strip()
    if clean_domain.startswith("http://") or clean_domain.startswith("https://"):
        clean_domain = urlparse(clean_domain).netloc.split(":")[0]

    subdomain, stem, tld = extract_domain_stem_and_tld(clean_domain)
    if not stem:
        return findings

    # Check for exact legitimate domain match
    for brand, info in TARGETED_ENTERPRISE_BRANDS.items():
        if clean_domain in info["aliases"] or clean_domain.endswith("." + info["primary_domain"]):
            # Fully authorized enterprise domain
            return findings

    # 1. Homoglyph / Confusable Detection
    has_unicode_homoglyphs = any(ch in HOMOGLYPH_MAP and ord(ch) > 127 for ch in domain)
    if has_unicode_homoglyphs:
        normalized_stem = normalize_homoglyphs(stem)
        for brand, info in TARGETED_ENTERPRISE_BRANDS.items():
            if brand in normalized_stem:
                findings.append(DomainIntelFinding(
                    domain=clean_domain,
                    finding_type="HOMOGLYPH",
                    target_brand=brand,
                    legitimate_domain=info["primary_domain"],
                    severity="CRITICAL",
                    confidence=0.95,
                    description=(
                        f"Internationalized Domain Name (IDN) homoglyph attack detected. "
                        f"Domain '{clean_domain}' uses non-Latin lookalike characters to impersonate '{info['primary_domain']}'."
                    ),
                    mitre_technique_id="T1583.001",
                    mitre_technique_name="Acquire Infrastructure: Domains",
                ))
                return findings  # Critical finding, return early

    # 2. Levenshtein / Damerau-Levenshtein Typo-Squatting & Leetspeak
    normalized_stem = normalize_homoglyphs(stem)
    for brand, info in TARGETED_ENTERPRISE_BRANDS.items():
        brand_len = len(brand)
        if brand_len < 4:
            continue  # Avoid false positive edits on very short names like "ey"

        # Case A: Exact brand match via homoglyph/leetspeak substitution (e.g. inf0sys -> infosys)
        if normalized_stem == brand and stem != brand:
            findings.append(DomainIntelFinding(
                domain=clean_domain,
                finding_type="TYPOSQUATTING",
                target_brand=brand,
                legitimate_domain=info["primary_domain"],
                severity="CRITICAL",
                confidence=0.96,
                description=(
                    f"Brand leetspeak/homoglyph impersonation detected targeting '{info['primary_domain']}'. "
                    f"Domain stem '{stem}' substitutes characters to spoof authentic brand '{brand}'."
                ),
                mitre_technique_id="T1583.001",
                mitre_technique_name="Acquire Infrastructure: Domains",
            ))
            return findings

        # Case B: Edit distance typo-squatting
        dist_raw = damerau_levenshtein_distance(stem, brand)
        dist_norm = damerau_levenshtein_distance(normalized_stem, brand)
        best_dist = min(dist_raw, dist_norm)

        # Distance of 1 (or 2 for longer brand names >= 7 chars)
        max_dist = 2 if brand_len >= 7 else 1
        if 1 <= best_dist <= max_dist and stem != brand and normalized_stem != brand:
            findings.append(DomainIntelFinding(
                domain=clean_domain,
                finding_type="TYPOSQUATTING",
                target_brand=brand,
                legitimate_domain=info["primary_domain"],
                severity="CRITICAL",
                confidence=0.92,
                description=(
                    f"Brand typo-squatting detected targeting '{info['primary_domain']}'. "
                    f"Domain stem '{stem}' is only edit distance {best_dist} from authentic brand '{brand}'."
                ),
                mitre_technique_id="T1583.001",
                mitre_technique_name="Acquire Infrastructure: Domains",
            ))
            return findings

    # 3. Brand Keyword Hijacking (e.g. google-careers.site, infosys-portal.online)
    stem_tokens = re.split(r'[-_.]', normalized_stem)
    for brand, info in TARGETED_ENTERPRISE_BRANDS.items():
        if brand in stem_tokens or (len(brand) >= 5 and brand in normalized_stem):
            # Brand is present in stem, but this is NOT the authentic domain
            has_lure_keyword = any(kw in stem_tokens or kw in normalized_stem for kw in RECRUITMENT_LURE_KEYWORDS)
            is_high_risk_tld = tld in HIGH_RISK_TLDS

            if has_lure_keyword or is_high_risk_tld or (claimed_company and brand in claimed_company.lower()):
                sev = "CRITICAL" if (has_lure_keyword and is_high_risk_tld) else "HIGH"
                findings.append(DomainIntelFinding(
                    domain=clean_domain,
                    finding_type="BRAND_HIJACKING",
                    target_brand=brand,
                    legitimate_domain=info["primary_domain"],
                    severity=sev,
                    confidence=0.88,
                    description=(
                        f"Corporate brand hijacking detected. Unauthorized domain '{clean_domain}' "
                        f"combines brand name '{brand}' with recruitment lures or high-risk TLD (.{tld}), "
                        f"impersonating authentic domain '{info['primary_domain']}'."
                    ),
                    mitre_technique_id="T1583.001",
                    mitre_technique_name="Acquire Infrastructure: Domains",
                ))
                return findings

    # 4. High-Risk TLD paired with Claimed Corporate Identity
    if claimed_company:
        clean_company = claimed_company.lower().strip()
        for brand, info in TARGETED_ENTERPRISE_BRANDS.items():
            if brand in clean_company and clean_domain != info["primary_domain"] and not clean_domain.endswith("." + info["primary_domain"]):
                if tld in HIGH_RISK_TLDS or any(kw in normalized_stem for kw in RECRUITMENT_LURE_KEYWORDS):
                    findings.append(DomainIntelFinding(
                        domain=clean_domain,
                        finding_type="HIGH_RISK_TLD_LURE",
                        target_brand=brand,
                        legitimate_domain=info["primary_domain"],
                        severity="HIGH",
                        confidence=0.85,
                        description=(
                            f"Suspicious recruitment portal detected. Correspondence claims company '{claimed_company}', "
                            f"but directs applicants to external untrusted domain '{clean_domain}' (.{tld}) instead of '{info['primary_domain']}'."
                        ),
                        mitre_technique_id="T1566.002",
                        mitre_technique_name="Spearphishing Link",
                    ))
                    return findings

    # 5. Shannon Entropy & DGA Detection
    entropy = calculate_shannon_entropy(stem)
    # Thresholds: length >= 8 and entropy >= 3.2 with mixed characters indicates machine-generated random hostname
    has_digits = any(ch.isdigit() for ch in stem)
    if len(stem) >= 8 and entropy >= 3.2 and (has_digits or len(stem) >= 12) and not any(kw in stem for kw in RECRUITMENT_LURE_KEYWORDS):
        findings.append(DomainIntelFinding(
            domain=clean_domain,
            finding_type="HIGH_ENTROPY_DGA",
            target_brand=None,
            legitimate_domain=None,
            severity="MEDIUM",
            confidence=0.75,
            description=(
                f"High-entropy hostname detected ('{stem}' entropy: {entropy:.2f}). "
                f"Pattern is characteristic of an Algorithmically Generated Domain (DGA) or disposable lure."
            ),
            mitre_technique_id="T1566.002",
            mitre_technique_name="Spearphishing Link",
            entropy=entropy,
        ))

    return findings
