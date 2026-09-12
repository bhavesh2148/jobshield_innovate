# ============================================================
# tests/test_artifact_extractor.py — Unit tests for Phase 2
# ============================================================

import pytest
from security.artifact_extractor import extract_artifacts
from api.schemas import ArtifactType


def test_empty_input():
    report = extract_artifacts("")
    assert report.total_count == 0
    assert len(report.emails) == 0


def test_email_extraction_and_trailing_punctuation():
    text = "Please reach out to recruiter@gmail.com. Alternately email hiring@corp-tech.co, or careers@apex.org)"
    report = extract_artifacts(text)
    
    assert report.total_count == 3
    assert len(report.emails) == 3
    
    # Check normalization and trailing punctuation removal
    emails_by_val = {e.value: e for e in report.emails}
    assert "recruiter@gmail.com" in emails_by_val
    assert emails_by_val["recruiter@gmail.com"].raw == "recruiter@gmail.com"
    assert emails_by_val["recruiter@gmail.com"].domain == "gmail.com"
    assert emails_by_val["recruiter@gmail.com"].metadata.get("provider_type") == "consumer_webmail"
    
    assert "hiring@corp-tech.co" in emails_by_val
    assert emails_by_val["hiring@corp-tech.co"].metadata.get("provider_type") == "organizational_domain"
    
    assert "careers@apex.org" in emails_by_val


def test_reject_email_with_invalid_extension():
    text = "Send your portfolio and header-graphic@2x.png to hr@company.com"
    report = extract_artifacts(text)
    
    # header-graphic@2x.png must be rejected as an image asset
    assert len(report.emails) == 1
    assert report.emails[0].value == "hr@company.com"


def test_url_extraction_and_domain_non_overlap():
    text = "Apply on our portal at https://careers.company.com/apply?job=42 before Monday."
    report = extract_artifacts(text)
    
    assert len(report.urls) == 1
    url = report.urls[0]
    assert url.value == "https://careers.company.com/apply?job=42"
    assert url.domain == "careers.company.com"
    
    # Standalone domain extraction must NOT duplicate 'careers.company.com'
    assert len(report.domains) == 0


def test_standalone_domain_extraction():
    text = "Check our careers website at hiring-portal.xyz or submit your inquiry to apex-jobs.net for review."
    report = extract_artifacts(text)
    
    domain_vals = [d.value for d in report.domains]
    assert "hiring-portal.xyz" in domain_vals
    assert "apex-jobs.net" in domain_vals


def test_phone_numbers_and_false_positive_rejection():
    text = "Call us at +1 555-019-2834 or (555) 234-5678. The salary is $120,000 for year 2024 with 500+ employees."
    report = extract_artifacts(text)
    
    # Only phone numbers should be extracted, NOT $120,000 or 2024 or 500+
    phones = [p.raw for p in report.phones]
    assert any("555-019-2834" in p for p in phones)
    assert any("555" in p and "234-5678" in p for p in phones)
    
    # Ensure numbers from currency, year, or headcount did not generate phone numbers
    for p in report.phones:
        assert "120" not in p.value
        assert "2024" not in p.value


def test_payment_identifiers_and_p2p():
    text = (
        "Send $350 onboarding fee to our CashApp $talentdesk or wire crypto to "
        "0x71C7656EC7ab88b098defB751B7401B5f6d8976F or BTC 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2. "
        "Contact Telegram t.me/quick_hr_rep"
    )
    report = extract_artifacts(text)
    
    pay_values = {p.value: p for p in report.payment_identifiers}
    
    assert "$talentdesk" in pay_values
    assert pay_values["$talentdesk"].metadata.get("channel") == "cashapp"
    
    assert "0x71c7656ec7ab88b098defb751b7401b5f6d8976f" in pay_values
    assert pay_values["0x71c7656ec7ab88b098defb751b7401b5f6d8976f"].metadata.get("network") == "ethereum"
    
    assert "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2" in pay_values
    assert pay_values["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"].metadata.get("network") == "bitcoin_legacy"
    
    assert "t.me/quick_hr_rep" in pay_values


def test_deduplication_and_occurrence_counter():
    text = "Contact hr@company.com immediately. Repeat: email hr@company.com today. Questions to hr@company.com"
    report = extract_artifacts(text)
    
    assert len(report.emails) == 1
    email = report.emails[0]
    assert email.value == "hr@company.com"
    assert email.metadata.get("occurrences") == "3"


def test_full_pipeline_compound_text():
    text = (
        "Urgent remote job opportunity. Contact our recruiter at recruiter@gmail.com or via WhatsApp at wa.me/15551234567. "
        "Send $300 for training equipment through Cash App to $fastonboard. Learn more at https://apex-remote-jobs.com/apply."
    )
    report = extract_artifacts(text)
    
    assert len(report.emails) == 1
    assert report.emails[0].value == "recruiter@gmail.com"
    assert len(report.urls) == 1
    assert report.urls[0].domain == "apex-remote-jobs.com"
    
    # CashApp and WhatsApp present
    pay_vals = [p.value for p in report.payment_identifiers]
    assert "$fastonboard" in pay_vals
    assert "wa.me/15551234567" in pay_vals
    
    # Overlapping domain check: 'apex-remote-jobs.com' was in URL, so domains list shouldn't duplicate it
    assert len(report.domains) == 0
