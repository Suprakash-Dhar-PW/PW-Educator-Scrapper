import pytest
from app.services.ranking import RankingService
from app.services.validator import ValidatorService

def test_jaya_y_evidence_extraction():
    # Arrange
    educator_base = {
        "candidate_id": "1",
        "name": "Jaya Y",
        "requested_location": "Hyderabad",
        "requested_track": "NEET",
        "requested_subject": "Biology"
    }

    social_profiles = [{
        "platform": "LinkedIn",
        "raw_profile_data": {
            "platform_profiles": [{
                "name": "Jaya Y",
                "headline": "Biology lecturer NEET UG at SANSKRITI EXPERTS' ACADEMY - SEA",
                "experience": [
                    {
                        "title": "Biology lecturer NEET UG",
                        "employer": "Sanskriti Experts' Academy",
                        "start_date": "July 2026",
                        "end_date": "Present"
                    },
                    {
                        "title": "Biology Lecturer NEET",
                        "employer": "Magnet Tutorial Pvt. Ltd.",
                        "start_date": "April 2024",
                        "end_date": "March 2026"
                    },
                    {
                        "title": "Biology Instructor",
                        "employer": "BYJU'S",
                        "start_date": "October 2022",
                        "end_date": "April 2024"
                    }
                ]
            }]
        }
    }]

    validator = ValidatorService()
    ranking = RankingService()

    # Act
    verification = validator.verify_educator(
        educator_base, social_profiles, "Hyderabad", "NEET", "Biology"
    )
    
    score_data = ranking.rank_educator(
        educator_base, social_profiles, verification
    )

    # Assert Identity
    assert verification["identity_verification"]["value"] == "Jaya Y"
    
    # Assert Score Factors
    factors = score_data["score_explanation"]["factors"]
    factors_by_key = {f["key"]: f for f in factors}
    
    subj = factors_by_key["subject_match"]
    assert subj["earned_points"] > 0, "Subject match should have points based on headline and experience."
    
    track = factors_by_key["exam_track_match"]
    assert track["earned_points"] > 0, "Exam-track match should have points."
    
    expertise = factors_by_key["teaching_expertise"]
    assert expertise["earned_points"] > 0, "Teaching expertise should have points from experience list."
    
    # The total score must sum perfectly
    total_calculated = sum(f["earned_points"] for f in factors)
    assert score_data["relevance_score"] == round(total_calculated, 1)

def test_youtube_channel_exclusion():
    # Arrange
    educator_base = {
        "candidate_id": "2",
        "name": "NeetWalaz",
        "requested_location": "Delhi",
        "requested_track": "NEET",
        "requested_subject": "Biology"
    }

    social_profiles = [{
        "platform": "YouTube",
        "raw_profile_data": {
            "platform_profiles": [{
                "title": "NeetWalaz",
                "description": "Best NEET Classes online!"
            }]
        }
    }]

    validator = ValidatorService()
    
    # Act
    verification = validator.verify_educator(
        educator_base, social_profiles, "Delhi", "NEET", "Biology"
    )
    
    # Assert
    assert verification["identity_verification"]["entity_type"] == "channel"
