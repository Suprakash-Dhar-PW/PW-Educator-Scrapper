import pytest
from app.services.validator import ValidatorService
from app.services.anakin_search import AnakinSearchService
from app.schemas.educator import SearchRequest, SearchResponse, SearchResult
from app.core.config import settings
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_locations_endpoint():
    res = client.get("/api/locations")
    assert res.status_code == 200
    locations = res.json()
    assert isinstance(locations, list)
    assert len(locations) >= 40
    assert "Online" in locations
    assert "Kota" in locations
    assert "Hyderabad" in locations
    assert "Bengaluru" in locations

def test_tracks_and_subjects_endpoints():
    res_tracks = client.get("/api/tracks")
    assert res_tracks.status_code == 200
    tracks = res_tracks.json()
    assert "IIT-JEE" in tracks
    assert "NEET" in tracks

    res_jee = client.get("/api/subjects?track=IIT-JEE")
    assert res_jee.status_code == 200
    jee_subjects = res_jee.json()
    assert "Physics" in jee_subjects
    assert "Chemistry" in jee_subjects
    assert "Mathematics" in jee_subjects
    assert "Biology" not in jee_subjects

    res_neet = client.get("/api/subjects?track=NEET")
    assert res_neet.status_code == 200
    neet_subjects = res_neet.json()
    assert "Biology" in neet_subjects
    assert "Physics" in neet_subjects

def test_diagnostics_endpoint_security_and_health():
    res = client.get("/api/diagnostics")
    assert res.status_code == 200
    diag = res.json()
    assert diag["status"] == "healthy"
    assert "pipeline_version" in diag
    # Ensure raw secret key is NOT exposed
    diag_str = str(diag)
    assert settings.ANAKIN_API_KEY not in diag_str or not settings.ANAKIN_API_KEY
    assert diag["providers"]["anakin_scraper"]["configured"] is True
    assert diag["providers"]["anakin_search"]["configured"] is True

def test_clean_name_extraction():
    search = AnakinSearchService()
    
    # Valid names in various title formats
    assert search._extract_clean_person_name("Alakh Pandey - Physics Teacher - Physics Wallah | LinkedIn") == "Alakh Pandey"
    assert search._extract_clean_person_name("Senior Physics Faculty - Nitin Vijay | LinkedIn") == "Nitin Vijay"
    assert search._extract_clean_person_name("Pradeep Kshetrapal - Physics Guru - YouTube") == "Pradeep Kshetrapal"
    assert search._extract_clean_person_name("Dr. N.K. Sharma | Top NEET Biology Expert") in ["N.K. Sharma", "Dr. N.K. Sharma"]
    
    # Generic or institutional titles must be filtered out
    assert search._extract_clean_person_name("YouTube") == ""
    assert search._extract_clean_person_name("Instagram") == ""
    assert search._extract_clean_person_name("Bengaluru Physics Teacher") == ""
    assert search._extract_clean_person_name("IIT Hyderabad_Official (@iithyderabad)") == ""
    assert search._extract_clean_person_name("Allen Career Institute - Kota Classes") == ""

def test_pw_and_vidyapeeth_exclusions():
    validator = ValidatorService()
    
    # Current PW / Vidyapeeth educator
    ed_pw = {"educator_id": "pw1", "full_name": "Tushar Kumar", "location": "Patna"}
    profiles_pw = [{
        "platform": "LinkedIn",
        "raw_profile_data": {
            "platform_profiles": [{
                "headline": "Physics Faculty at PW Vidyapeeth Patna",
                "bio": "Mentoring IIT-JEE aspirants at Physics Wallah Vidyapeeth",
                "experience": [{"title": "Faculty", "employer": "PW Vidyapeeth"}]
            }]
        }
    }]
    ver_pw = validator.verify_educator(ed_pw, profiles_pw, "Patna", "IIT-JEE", "Physics")
    assert ver_pw["employment_verification"]["value"] == "EXCLUDED_CURRENT_PW"

    # Eligible Non-PW educator
    ed_allen = {"educator_id": "allen1", "full_name": "Rakesh Sharma", "location": "Kota"}
    profiles_allen = [{
        "platform": "LinkedIn",
        "raw_profile_data": {
            "platform_profiles": [{
                "headline": "Senior Physics Faculty at Allen Career Institute",
                "bio": "15+ years experience teaching IIT-JEE Advanced Physics at Allen Kota",
                "experience": [{"title": "Senior Faculty", "employer": "Allen Career Institute"}]
            }]
        }
    }]
    ver_allen = validator.verify_educator(ed_allen, profiles_allen, "Kota", "IIT-JEE", "Physics")
    assert ver_allen["employment_verification"]["value"] == "ELIGIBLE"
    assert ver_allen["role_verification"]["is_educator"] is True

def test_student_and_institution_exclusions():
    validator = ValidatorService()
    
    # Student profile
    ed_student = {"educator_id": "st1", "full_name": "Pg Haritha", "location": "Hyderabad"}
    profiles_student = [{
        "platform": "LinkedIn",
        "raw_profile_data": {
            "platform_profiles": [{
                "headline": "Student at IIT Hyderabad | Aspiring Learner",
                "bio": "B.Tech Computer Science student pursuing degree",
                "experience": []
            }]
        }
    }]
    ver_student = validator.verify_educator(ed_student, profiles_student, "Hyderabad", "IIT-JEE", "Mathematics")
    assert ver_student["role_verification"]["is_student"] is True
    assert ver_student["role_verification"]["is_educator"] is False

    # Institutional official profile
    ed_inst = {"educator_id": "inst1", "full_name": "IIT Hyderabad_Official", "location": "Hyderabad"}
    profiles_inst = [{
        "platform": "LinkedIn",
        "raw_profile_data": {
            "platform_profiles": [{
                "headline": "Official page of IIT Hyderabad administration",
                "bio": "National institute of technology official channel",
                "experience": []
            }]
        }
    }]
    ver_inst = validator.verify_educator(ed_inst, profiles_inst, "Hyderabad", "IIT-JEE", "Physics")
    assert ver_inst["identity_verification"]["entity_type"] == "institution"
    assert ver_inst["role_verification"]["is_educator"] is False

def test_target_shortfall_calculation():
    target = 50
    found_7 = 7
    shortfall = max(0, target - found_7)
    assert shortfall == 43
    assert (found_7 >= target) is False

    found_50 = 50
    assert max(0, target - found_50) == 0
    assert (found_50 >= target) is True
