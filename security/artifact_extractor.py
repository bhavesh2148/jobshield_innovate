# ============================================================
# security/artifact_extractor.py
# ============================================================
"""
JobShield Security Artifact Extraction Subsystem.

Responsible for identifying, extracting, and normalizing observable digital
artifacts from raw text communications without assigning threat verdicts.

Extracted Artifact Categories:
- EMAIL: Recruiter or contact email addresses
- URL: Web addresses (HTTP/HTTPS)
- DOMAIN: Standalone hostnames/domains not already encapsulated in URLs or emails
- PHONE: Contact phone numbers with valid telecom formatting
- PAYMENT_IDENTIFIER: P2P payment handles, cryptocurrency addresses, and wire vectors
"""

import re
from typing import Optional
from urllib.parse import urlparse
from api.schemas import ArtifactType, ExtractedArtifact, ArtifactReport


# Consumer/public webmail providers (purely descriptive observation metadata)
CONSUMER_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "ymail.com",
    "hotmail.com", "outlook.com", "live.com", "msn.com",
    "icloud.com", "me.com", "mac.com", "aol.com",
    "proton.me", "protonmail.com", "zoho.com", "mail.com", "gmx.com"
}

# Standard regex patterns for observable digital artifacts
RE_EMAIL = re.compile(
    r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    re.IGNORECASE
)

RE_URL = re.compile(
    r'https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)',
    re.IGNORECASE
)

# Standalone domain regex (matching common TLDs, requiring word boundaries)
RE_DOMAIN = re.compile(
    r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|edu|gov|io|co|ai|info|biz|me|xyz|online|site|app|dev|tech|store|live|cloud|agency|careers|jobs)\b',
    re.IGNORECASE
)

# International (+1, +44, etc.) or standard delimited domestic phone numbers
RE_PHONE_INTL = re.compile(
    r'(?<![\w$€£₹])(?:\+|00)[1-9]\d{0,2}[\s.-]?(?:\(?\d{1,4}\)?[\s.-]?)?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{2,9}\b'
)
RE_PHONE_DOMESTIC = re.compile(
    r'(?<![\w$€£₹])(?:\(\d{3}\)|\b\d{3}\b)[\s.-]\d{3}[\s.-]\d{4}\b'
)

# Cryptocurrency Wallet Regexes
RE_CRYPTO_ETH = re.compile(r'\b0x[a-fA-F0-9]{40}\b')
RE_CRYPTO_BTC_LEGACY = re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
RE_CRYPTO_BTC_BECH32 = re.compile(r'\bbc1[ac-hj-np-z02-9]{11,71}\b')

# P2P Payment Handles & Channels
# CashApp: Starts with $, followed by at least one letter, then alphanumeric/underscore
RE_PAYMENT_CASHAPP = re.compile(r'(?<![\w$€£₹])\$[a-zA-Z][a-zA-Z0-9_-]{1,19}\b')
RE_PAYMENT_TELEGRAM_LINK = re.compile(r'\b(?:https?://)?t\.me/([a-zA-Z0-9_]{5,32})\b', re.IGNORECASE)
RE_PAYMENT_PAYPAL_LINK = re.compile(r'\b(?:https?://)?(?:www\.)?paypal\.me/([a-zA-Z0-9_-]+)\b', re.IGNORECASE)
RE_PAYMENT_WHATSAPP_LINK = re.compile(r'\b(?:https?://)?wa\.me/(\d{7,15})\b', re.IGNORECASE)

# Ignored domain names (documentation or test placeholders)
IGNORED_DOMAINS = {"example.com", "example.org", "localhost", "test.com", "schema.org"}

# Invalid file extensions that should not be mistaken for TLDs in emails
INVALID_EMAIL_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "pdf", "zip", "exe", "js", "py", "css", "html"}


def _spans_overlap(span_a: tuple[int, int], span_b: tuple[int, int]) -> bool:
    """Returns True if two character spans [start, end) overlap."""
    return max(span_a[0], span_b[0]) < min(span_a[1], span_b[1])


def _is_span_reserved(candidate_span: tuple[int, int], reserved_spans: list[tuple[int, int]]) -> bool:
    """Checks if a candidate character span overlaps with any previously claimed span."""
    for span in reserved_spans:
        if _spans_overlap(candidate_span, span):
            return True
    return False


def _clean_trailing_punctuation(raw_str: str, start: int) -> tuple[str, int, int]:
    """
    Trims trailing sentence punctuation (. , ) ] } ; :) from regex matches,
    adjusting the end character offset accordingly.
    """
    trimmed = raw_str
    while trimmed and trimmed[-1] in ".,);]}>:":
        trimmed = trimmed[:-1]
    new_end = start + len(trimmed)
    return trimmed, start, new_end


def extract_artifacts(text: str) -> ArtifactReport:
    """
    Extracts and normalizes observable digital artifacts from raw recruitment content.
    
    Operates strictly in an artifact observation role:
    - Preserves character offsets
    - Enforces hierarchical span reservation to prevent duplicate overlapping extractions
    - Normalizes values for uniform downstream inspection
    - Deduplicates identical tokens while tracking occurrence counts
    - Does NOT compute threat verdicts or modify risk scores
    """
    if not text or not text.strip():
        return ArtifactReport()

    reserved_spans: list[tuple[int, int]] = []
    dedup_store: dict[tuple[ArtifactType, str], ExtractedArtifact] = {}

    def _record_artifact(
        artifact_type: ArtifactType,
        normalized_value: str,
        raw_token: str,
        domain_val: Optional[str],
        start_idx: int,
        end_idx: int,
        metadata_dict: dict[str, str]
    ):
        key = (artifact_type, normalized_value)
        if key in dedup_store:
            # Increment occurrence count on existing entry
            curr = dedup_store[key]
            count = int(curr.metadata.get("occurrences", 1)) + 1
            curr.metadata["occurrences"] = str(count)
        else:
            meta = dict(metadata_dict)
            meta["occurrences"] = "1"
            dedup_store[key] = ExtractedArtifact(
                type=artifact_type,
                value=normalized_value,
                raw=raw_token,
                domain=domain_val,
                start=start_idx,
                end=end_idx,
                metadata=meta
            )
        reserved_spans.append((start_idx, end_idx))

    # ─────────────────────────────────────────────────────────────
    # PASS 1: EMAIL EXTRACTION (Highest precedence for email spans)
    # ─────────────────────────────────────────────────────────────
    for m in RE_EMAIL.finditer(text):
        raw_match = m.group(0)
        cleaned_raw, start, end = _clean_trailing_punctuation(raw_match, m.start())
        if not cleaned_raw:
            continue

        parts = cleaned_raw.split("@")
        if len(parts) != 2:
            continue

        domain_part = parts[1].lower()
        tld = domain_part.split(".")[-1]
        if tld in INVALID_EMAIL_EXTENSIONS:
            continue

        normalized_email = cleaned_raw.lower()
        metadata = {}
        if domain_part in CONSUMER_MAIL_DOMAINS:
            metadata["provider_type"] = "consumer_webmail"
        else:
            metadata["provider_type"] = "organizational_domain"

        _record_artifact(
            ArtifactType.EMAIL,
            normalized_email,
            cleaned_raw,
            domain_part,
            start,
            end,
            metadata
        )

    # ─────────────────────────────────────────────────────────────
    # PASS 2: URL EXTRACTION
    # ─────────────────────────────────────────────────────────────
    for m in RE_URL.finditer(text):
        raw_match = m.group(0)
        cleaned_raw, start, end = _clean_trailing_punctuation(raw_match, m.start())
        if not cleaned_raw:
            continue

        if _is_span_reserved((start, end), reserved_spans):
            continue

        try:
            parsed = urlparse(cleaned_raw)
            hostname = parsed.hostname.lower() if parsed.hostname else None
        except Exception:
            hostname = None

        normalized_url = cleaned_raw
        metadata = {"scheme": parsed.scheme.lower() if parsed.scheme else "http"}
        if hostname and any(s in hostname for s in ["forms.gle", "docs.google.com/forms", "typeform.com"]):
            metadata["form_service"] = "hosted_form"

        _record_artifact(
            ArtifactType.URL,
            normalized_url,
            cleaned_raw,
            hostname,
            start,
            end,
            metadata
        )

    # ─────────────────────────────────────────────────────────────
    # PASS 3: PAYMENT IDENTIFIERS & P2P / MESSAGING CHANNELS
    # ─────────────────────────────────────────────────────────────
    # Ethereum
    for m in RE_CRYPTO_ETH.finditer(text):
        if not _is_span_reserved((m.start(), m.end()), reserved_spans):
            _record_artifact(
                ArtifactType.PAYMENT_IDENTIFIER,
                m.group(0).lower(),
                m.group(0),
                None,
                m.start(),
                m.end(),
                {"payment_type": "cryptocurrency", "network": "ethereum"}
            )

    # Bitcoin Legacy & Bech32
    for pattern, network in [(RE_CRYPTO_BTC_LEGACY, "bitcoin_legacy"), (RE_CRYPTO_BTC_BECH32, "bitcoin_bech32")]:
        for m in pattern.finditer(text):
            if not _is_span_reserved((m.start(), m.end()), reserved_spans):
                _record_artifact(
                    ArtifactType.PAYMENT_IDENTIFIER,
                    m.group(0),  # Base58 is case-sensitive
                    m.group(0),
                    None,
                    m.start(),
                    m.end(),
                    {"payment_type": "cryptocurrency", "network": network}
                )

    # CashApp Cashtag
    for m in RE_PAYMENT_CASHAPP.finditer(text):
        raw_match = m.group(0)
        cleaned_raw, start, end = _clean_trailing_punctuation(raw_match, m.start())
        if not _is_span_reserved((start, end), reserved_spans):
            _record_artifact(
                ArtifactType.PAYMENT_IDENTIFIER,
                cleaned_raw.lower(),
                cleaned_raw,
                None,
                start,
                end,
                {"payment_type": "p2p_transfer", "channel": "cashapp"}
            )

    # Telegram Link / Handle
    for m in RE_PAYMENT_TELEGRAM_LINK.finditer(text):
        cleaned_raw, start, end = _clean_trailing_punctuation(m.group(0), m.start())
        if not _is_span_reserved((start, end), reserved_spans):
            handle = m.group(1).lower()
            _record_artifact(
                ArtifactType.PAYMENT_IDENTIFIER,
                f"t.me/{handle}",
                cleaned_raw,
                "t.me",
                start,
                end,
                {"payment_type": "messaging_channel", "channel": "telegram", "handle": handle}
            )

    # WhatsApp Link
    for m in RE_PAYMENT_WHATSAPP_LINK.finditer(text):
        cleaned_raw, start, end = _clean_trailing_punctuation(m.group(0), m.start())
        if not _is_span_reserved((start, end), reserved_spans):
            phone_num = m.group(1)
            _record_artifact(
                ArtifactType.PAYMENT_IDENTIFIER,
                f"wa.me/{phone_num}",
                cleaned_raw,
                "wa.me",
                start,
                end,
                {"payment_type": "messaging_channel", "channel": "whatsapp", "phone": phone_num}
            )

    # PayPal.me Link
    for m in RE_PAYMENT_PAYPAL_LINK.finditer(text):
        cleaned_raw, start, end = _clean_trailing_punctuation(m.group(0), m.start())
        if not _is_span_reserved((start, end), reserved_spans):
            user_handle = m.group(1).lower()
            _record_artifact(
                ArtifactType.PAYMENT_IDENTIFIER,
                f"paypal.me/{user_handle}",
                cleaned_raw,
                "paypal.me",
                start,
                end,
                {"payment_type": "p2p_transfer", "channel": "paypal", "handle": user_handle}
            )

    # ─────────────────────────────────────────────────────────────
    # PASS 4: STANDALONE DOMAIN EXTRACTION (Non-overlapping)
    # ─────────────────────────────────────────────────────────────
    for m in RE_DOMAIN.finditer(text):
        raw_match = m.group(0)
        cleaned_raw, start, end = _clean_trailing_punctuation(raw_match, m.start())
        if not cleaned_raw:
            continue

        # If followed immediately by a slash, it's part of a path/URL, not a standalone domain
        if end < len(text) and text[end] == "/":
            continue

        # Reject if this domain is already covered by an extracted URL, Email, or Channel span
        if _is_span_reserved((start, end), reserved_spans):
            continue

        domain_lower = cleaned_raw.lower()
        if domain_lower.startswith("www."):
            domain_lower = domain_lower[4:]

        if domain_lower in IGNORED_DOMAINS:
            continue

        _record_artifact(
            ArtifactType.DOMAIN,
            domain_lower,
            cleaned_raw,
            domain_lower,
            start,
            end,
            {"standalone": "true"}
        )

    # ─────────────────────────────────────────────────────────────
    # PASS 5: PHONE NUMBERS
    # ─────────────────────────────────────────────────────────────
    for pattern in [RE_PHONE_INTL, RE_PHONE_DOMESTIC]:
        for m in pattern.finditer(text):
            raw_match = m.group(0)
            cleaned_raw, start, end = _clean_trailing_punctuation(raw_match, m.start())
            if not cleaned_raw:
                continue

            if _is_span_reserved((start, end), reserved_spans):
                continue

            # Digits-only check: Must contain at least 7 digits to prevent false phone numbers
            digits = re.sub(r'\D', '', cleaned_raw)
            if len(digits) < 7 or len(digits) > 15:
                continue

            # Format normalized string
            normalized_phone = ("+" + digits) if cleaned_raw.startswith("+") else digits
            _record_artifact(
                ArtifactType.PHONE,
                normalized_phone,
                cleaned_raw,
                None,
                start,
                end,
                {"digits_length": str(len(digits))}
            )

    # Group extracted artifacts into categories
    report = ArtifactReport()
    for artifact in dedup_store.values():
        if artifact.type == ArtifactType.EMAIL:
            report.emails.append(artifact)
        elif artifact.type == ArtifactType.URL:
            report.urls.append(artifact)
        elif artifact.type == ArtifactType.DOMAIN:
            report.domains.append(artifact)
        elif artifact.type == ArtifactType.PHONE:
            report.phones.append(artifact)
        elif artifact.type == ArtifactType.PAYMENT_IDENTIFIER:
            report.payment_identifiers.append(artifact)

    report.total_count = len(dedup_store)
    return report
