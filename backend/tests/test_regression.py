import pytest
from app.services.validator import ValidatorService

def test_chemistry_not_in_physics():
    validator = ValidatorService()
    educator = {"name": "Ravi Kumar"}
    profiles = [{"platform": "LinkedIn", "raw_profile_data": {"platform_profiles": [{"bio": "IIT JEE Chemistry Faculty at Allen"}]}}]
    result = validator.verify_educator(educator, profiles, "Kota", "IIT-JEE", "Physics")
    assert result["subject_verification"]["status"] == "not_relevant"

def test_research_physicist_not_educator():
    validator = ValidatorService()
    educator = {"name": "Dr. A. Sharma"}
    profiles = [{"platform": "LinkedIn", "raw_profile_data": {"platform_profiles": [{"bio": "Research Physicist and PhD Scholar studying quantum mechanics."}]}}]
    result = validator.verify_educator(educator, profiles, "Delhi", "IIT-JEE", "Physics")
    assert result["subject_verification"]["status"] == "not_relevant"

def test_neet_biology_not_iit_jee_physics():
    validator = ValidatorService()
    educator = {"name": "Anjali Gupta"}
    profiles = [{"platform": "LinkedIn", "raw_profile_data": {"platform_profiles": [{"bio": "NEET Biology Educator at Unacademy"}]}}]
    result = validator.verify_educator(educator, profiles, "Online", "IIT-JEE", "Physics")
    assert result["subject_verification"]["status"] == "not_relevant"
    assert result["track_verification"]["status"] == "not_relevant"

def test_generic_channel_not_individual():
    validator = ValidatorService()
    educator = {"name": "Physics Wallah Official Channel"}
    profiles = [{"platform": "YouTube", "raw_profile_data": {"platform_profiles": [{"bio": "Official PW channel for JEE preparation."}]}}]
    result = validator.verify_educator(educator, profiles, "Online", "IIT-JEE", "Physics")
    assert result["identity_verification"]["entity_type"] == "channel"
    assert result["identity_verification"]["status"] == "unconfirmed"

def test_malformed_name_from_city():
    validator = ValidatorService()
    educator = {"name": "Kota Best Physics Teacher"}
    profiles = [{"platform": "YouTube", "raw_profile_data": {"platform_profiles": [{"bio": "Best physics teacher in Kota"}]}}]
    result = validator.verify_educator(educator, profiles, "Kota", "IIT-JEE", "Physics")
    assert result["identity_verification"]["value"] == ""
    assert result["identity_verification"]["status"] == "unconfirmed"

def test_pw_educator_excluded():
    validator = ValidatorService()
    educator = {"name": "Alakh Pandey"}
    profiles = [{"platform": "LinkedIn", "raw_profile_data": {"platform_profiles": [{"bio": "Founder and Teacher at Physics Wallah"}]}}]
    result = validator.verify_educator(educator, profiles, "Delhi", "IIT-JEE", "Physics")
    assert result["employment_verification"]["value"] == "EXCLUDED_CURRENT_PW"

def test_former_pw_educator_excluded():
    validator = ValidatorService()
    educator = {"name": "Tarun Kumar"}
    profiles = [{"platform": "LinkedIn", "raw_profile_data": {"platform_profiles": [{"bio": "Ex-PW Faculty, now teaching at Sankalp Bharat"}]}}]
    result = validator.verify_educator(educator, profiles, "Delhi", "IIT-JEE", "Physics")
    assert result["employment_verification"]["value"] == "EXCLUDED_FORMER_PW"

