# tests/test_job_parser.py
from utils.job_parser import parse_raw_job_text, parse_checkbox_value

SAMPLE_INFOSYS_POST = """Field Value Job Title Full Stack Developer Company Name Infosys Limited Salary Range $70,000–$95,000/year Employment Type Full-time Experience Required Associate level Has Company Logo ☑ Yes Has Screening Questions ☑ Yes Remote / Telecommute ☐ No Job Description: Infosys Limited is hiring Full Stack Developers for our Digital Experience practice in Chennai. You will design and develop scalable web applications for enterprise clients using React.js and Node.js. You will participate in Agile sprint planning, collaborate with UI/UX teams, and maintain CI/CD pipelines. The role involves code reviews, unit testing, and documentation. Growth opportunities into senior engineering and architect tracks are available after 18 months. Requirements: 1–3 years of experience in full stack development"""


def test_parse_checkbox_value():
    assert parse_checkbox_value("☑ Yes") == 1
    assert parse_checkbox_value("[x]") == 1
    assert parse_checkbox_value("yes") == 1
    assert parse_checkbox_value("True") == 1
    assert parse_checkbox_value("☐ No") == 0
    assert parse_checkbox_value("[ ]") == 0
    assert parse_checkbox_value("no") == 0


def test_parse_raw_job_text_infosys():
    extracted = parse_raw_job_text(SAMPLE_INFOSYS_POST)

    assert extracted["title"] == "Full Stack Developer"
    assert extracted["company"] == "Infosys Limited"
    assert extracted["salary_range"] == "$70,000–$95,000/year"
    assert extracted["employment_type"] == "Full-time"
    assert extracted["required_experience"] == "Associate level"
    assert extracted["has_company_logo"] == 1
    assert extracted["has_questions"] == 1
    assert extracted["telecommuting"] == 0
    assert "Infosys Limited is hiring" in extracted["description"]
    assert "1–3 years of experience" in extracted["requirements"]
    assert len(extracted["company_profile"]) > 0


def test_parse_plain_text():
    plain = "We are seeking a Python Engineer with 5 years experience to join our backend team."
    extracted = parse_raw_job_text(plain)
    assert extracted["description"] == plain
    assert extracted["has_company_logo"] == 0


def test_parse_text_endpoint():
    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app) as client:
        res = client.post("/parse-text", json={"text": SAMPLE_INFOSYS_POST})
        assert res.status_code == 200
        data = res.json()
        assert data["title"] == "Full Stack Developer"
        assert data["company"] == "Infosys Limited"
        assert data["has_company_logo"] == 1
        assert data["has_questions"] == 1


def test_predict_auto_enrichment_infosys():
    """Verify that posting raw Infosys text into description auto-hydrates metadata and scores as REAL."""
    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app) as client:
        # Submit with ONLY description, mimicking what the user did
        res = client.post("/predict", json={"description": SAMPLE_INFOSYS_POST})
        assert res.status_code == 200
        data = res.json()
        # Should now be recognized as REAL (low risk) because metadata was auto-hydrated
        assert data["prediction"] == "REAL"
        assert data["risk_level"] in ("LOW", "MEDIUM")
        assert data["risk_score"] < 50
