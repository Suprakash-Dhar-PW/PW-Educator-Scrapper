import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

class RankingService:
    def __init__(self):
        self.score_version = "v1"
        self.weights = {
            "subject_match": 25,
            "exam_track_match": 20,
            "teaching_expertise": 15,
            "professional_identity": 15,
            "teaching_activity": 10,
            "location_match": 10,
            "source_quality": 5
        }
        self.logger = logging.getLogger("ranking")

    def rank_educator(self, educator: Dict[str, Any], social_profiles: List[Dict[str, Any]], verification_results: Dict[str, Any]) -> Dict[str, Any]:
        factors = []
        total_score = 0.0

        # 1. Subject match (25)
        subj_ver = verification_results.get("subject_verification", {})
        subj_conf = subj_ver.get("confidence", 0)
        subj_score = round(subj_conf * self.weights["subject_match"], 1)
        subj_status = "strong" if subj_conf >= 0.8 else "partial" if subj_conf > 0 else "unknown"
        factors.append({
            "key": "subject_match",
            "label": "Subject match",
            "earned_points": subj_score,
            "max_points": self.weights["subject_match"],
            "status": subj_status,
            "explanation": "Strong evidence of requested subject match found." if subj_status == "strong" else "Partial evidence of subject match." if subj_status == "partial" else "No strong evidence found for subject.",
            "evidence_ids": [ev.get("platform") for ev in subj_ver.get("evidence", [])]
        })
        total_score += subj_score

        # 2. Exam-track match (20)
        track_ver = verification_results.get("track_verification", {})
        track_conf = track_ver.get("confidence", 0)
        track_score = round(track_conf * self.weights["exam_track_match"], 1)
        track_status = "strong" if track_conf >= 0.8 else "partial" if track_conf > 0 else "unknown"
        factors.append({
            "key": "exam_track_match",
            "label": "Exam-track match",
            "earned_points": track_score,
            "max_points": self.weights["exam_track_match"],
            "status": track_status,
            "explanation": "Relevant exam-specific teaching evidence was found." if track_status == "strong" else "Partial evidence of exam-track match." if track_status == "partial" else "No strong evidence for exam-track.",
            "evidence_ids": [ev.get("platform") for ev in track_ver.get("evidence", [])]
        })
        total_score += track_score

        # Gather texts
        all_text = ""
        total_followers = 0
        platforms = set()
        has_linkedin = False
        
        for profile in social_profiles:
            plat = profile.get("platform", "")
            if plat: platforms.add(plat)
            if plat == "LinkedIn": has_linkedin = True
            
            raw_data = profile.get("raw_profile_data", {})
            platform_data = raw_data.get("platform_profiles", [{}])[0]
            
            texts = [
                platform_data.get("bio", ""),
                platform_data.get("description", ""),
                platform_data.get("about", "")
            ]
            
            experience_list = platform_data.get("experience", [])
            has_experience_roles = False
            if isinstance(experience_list, list):
                for exp in experience_list:
                    if isinstance(exp, dict):
                        texts.append(exp.get("title", ""))
                        texts.append(exp.get("employer", ""))
                        has_experience_roles = True
            
            all_text += " " + " ".join(t for t in texts if t and isinstance(t, str))
            
            f = platform_data.get("followers") or platform_data.get("subscribers") or platform_data.get("connections")
            if f and isinstance(f, int):
                total_followers += f

        all_text_lower = all_text.lower()

        # 3. Teaching expertise (15)
        teach_keywords = ["faculty", "teacher", "educator", "professor", "teaches", "classes", "mentor", "tutor", "coaching", "students", "experience", "years", "instructor", "lecturer"]
        teach_matches = sum(1 for kw in teach_keywords if kw in all_text_lower)
        teach_conf = min(1.0, teach_matches / 4.0)
        
        if has_experience_roles:
            teach_conf = min(1.0, teach_conf + 0.5)
            
        if teach_conf == 0 and len(all_text) > 100:
            teach_conf = 0.2
        teach_score = round(teach_conf * self.weights["teaching_expertise"], 1)
        teach_status = "strong" if teach_conf >= 0.8 else "partial" if teach_conf > 0 else "unknown"
        factors.append({
            "key": "teaching_expertise",
            "label": "Teaching expertise and experience",
            "earned_points": teach_score,
            "max_points": self.weights["teaching_expertise"],
            "status": teach_status,
            "explanation": "Strong evidence of teaching expertise and roles." if teach_status == "strong" else "Partial evidence of teaching expertise." if teach_status == "partial" else "Insufficient evidence of teaching roles.",
            "evidence_ids": list(platforms) if teach_score > 0 else []
        })
        total_score += teach_score

        # 4. Professional identity (15)
        ident_ver = verification_results.get("identity_verification", {})
        ident_conf = ident_ver.get("confidence", 0)
        ident_score = round(ident_conf * self.weights["professional_identity"], 1)
        ident_status = "strong" if ident_conf >= 0.8 else "partial" if ident_conf > 0 else "unknown"
        factors.append({
            "key": "professional_identity",
            "label": "Professional identity and role evidence",
            "earned_points": ident_score,
            "max_points": self.weights["professional_identity"],
            "status": ident_status,
            "explanation": "Clear connection to professional profile and role." if ident_status == "strong" else "Partial identity evidence." if ident_status == "partial" else "Unverified identity.",
            "evidence_ids": [ev.get("platform") for ev in ident_ver.get("evidence", [])]
        })
        total_score += ident_score

        # 5. Teaching activity (10)
        act_conf = 0.0
        if total_followers > 1000:
            act_conf = 1.0
        elif total_followers > 100:
            act_conf = 0.7
        elif platforms:
            act_conf = 0.4
            
        act_score = round(act_conf * self.weights["teaching_activity"], 1)
        act_status = "strong" if act_conf >= 0.8 else "partial" if act_conf > 0 else "unknown"
        factors.append({
            "key": "teaching_activity",
            "label": "Teaching activity and recency",
            "earned_points": act_score,
            "max_points": self.weights["teaching_activity"],
            "status": act_status,
            "explanation": "Recent or substantial public teaching activity found." if act_status == "strong" else "Some public activity found." if act_status == "partial" else "Limited evidence of recent activity.",
            "evidence_ids": list(platforms) if act_score > 0 else []
        })
        total_score += act_score

        # 6. Location match (10)
        loc_ver = verification_results.get("location_verification", {})
        loc_conf = loc_ver.get("confidence", 0)
        loc_score = round(loc_conf * self.weights["location_match"], 1)
        loc_status = "strong" if loc_conf >= 0.8 else "partial" if loc_conf > 0 else "unknown"
        factors.append({
            "key": "location_match",
            "label": "Location or mode match",
            "earned_points": loc_score,
            "max_points": self.weights["location_match"],
            "status": loc_status,
            "explanation": "Location matched requested area." if loc_status == "strong" else "Location partially matched." if loc_status == "partial" else "Location unknown or non-matching.",
            "evidence_ids": [ev.get("platform") for ev in loc_ver.get("evidence", [])]
        })
        total_score += loc_score

        # 7. Source quality (5)
        sq_conf = min(1.0, len(platforms) / 2.0)
        if has_linkedin: sq_conf = min(1.0, sq_conf + 0.3)
        sq_score = round(sq_conf * self.weights["source_quality"], 1)
        sq_status = "strong" if sq_conf >= 0.8 else "partial" if sq_conf > 0 else "unknown"
        factors.append({
            "key": "source_quality",
            "label": "Source quality and corroboration",
            "earned_points": sq_score,
            "max_points": self.weights["source_quality"],
            "status": sq_status,
            "explanation": "Multiple high-quality sources corroborate details." if sq_status == "strong" else "Single or average-quality source found." if sq_status == "partial" else "Low source quality.",
            "evidence_ids": list(platforms)
        })
        total_score += sq_score

        # Calculate evidence coverage
        evidence_factors = sum(1 for f in factors if f["status"] != "unknown")
        coverage_percent = round((evidence_factors / len(factors)) * 100, 1)

        result = {
            "relevance_score": round(total_score, 1),
            "score_version": self.score_version,
            "score_explanation": {
                "factors": factors,
                "evidence_coverage_percent": coverage_percent,
                "evaluated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        self.logger.info(f"[RANKING] Scored educator: {total_score}/100 (Coverage: {coverage_percent}%)")
        return result
