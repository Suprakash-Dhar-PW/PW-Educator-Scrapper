from typing import List, Dict, Any

class RankingService:
    def __init__(self):
        # Weights for the overall score
        self.weights = {
            "track_relevance": 0.20,
            "subject_relevance": 0.20,
            "location_relevance": 0.10,
            "teaching_evidence": 0.15,
            "professional_evidence": 0.05,
            "cross_platform_presence": 0.10,
            "audience_signal": 0.05,
            "profile_completeness": 0.05,
            "evidence_quality": 0.10
        }

    def rank_educator(self, educator: Dict[str, Any], social_profiles: List[Dict[str, Any]], verification_results: Dict[str, Any]) -> Dict[str, Any]:
        
        scores = {}
        
        # 1-3. Relevance from verification layer
        scores["track_relevance"] = min(100, verification_results.get("track_verification", {}).get("confidence", 0) * 100)
        scores["subject_relevance"] = min(100, verification_results.get("subject_verification", {}).get("confidence", 0) * 100)
        scores["location_relevance"] = min(100, verification_results.get("location_verification", {}).get("confidence", 0) * 100)
        
        # Aggregate text and metrics
        all_text = ""
        total_followers = 0
        populated_fields = 0
        total_fields_expected = len(social_profiles) * 4 # roughly expect name, bio, url, followers
        platforms_present = set()
        has_linkedin = False
        
        for profile in social_profiles:
            platform = profile.get("platform", "")
            platforms_present.add(platform)
            if platform == "LinkedIn":
                has_linkedin = True
                
            raw_data = profile.get("raw_profile_data", {})
            platform_data = raw_data.get("platform_profiles", [{}])[0]
            
            # Aggregate text
            texts = [
                platform_data.get("bio", ""),
                platform_data.get("description", ""),
                platform_data.get("about", "")
            ]
            all_text += " " + " ".join(t for t in texts if t)
            
            # Sum followers
            f = platform_data.get("followers") or platform_data.get("subscribers") or platform_data.get("connections")
            if f and isinstance(f, int):
                total_followers += f
                
            # Count completeness
            if platform_data.get("name") or platform_data.get("channel_name"): populated_fields += 1
            if platform_data.get("bio") or platform_data.get("description") or platform_data.get("about"): populated_fields += 1
            if platform_data.get("url"): populated_fields += 1
            if f: populated_fields += 1
                
        all_text_lower = all_text.lower()
        
        # 4. Teaching/educator evidence
        # Points for specific teaching keywords
        teaching_score = 0
        keywords = ["faculty", "teacher", "educator", "professor", "teaches", "classes", "mentor", "tutor", "coaching", "students"]
        for kw in keywords:
            if kw in all_text_lower:
                teaching_score += 20
        scores["teaching_evidence"] = min(100, teaching_score)
        
        # 5. Professional experience evidence
        prof_score = 0
        if has_linkedin:
            prof_score += 40
        if "experience" in all_text_lower or "years" in all_text_lower:
            prof_score += 30
        if len(all_text_lower) > 150: # Detailed bio
            prof_score += 30
        scores["professional_evidence"] = min(100, prof_score)
        
        # 6. Cross-platform presence
        # 1 platform = 33, 2 = 66, 3+ = 100
        platforms_count = len(platforms_present)
        scores["cross_platform_presence"] = min(100, platforms_count * 33.4)
        
        # 7. Audience metrics
        if total_followers > 10000:
            aud_score = 100
        elif total_followers > 1000:
            aud_score = 75
        elif total_followers > 100:
            aud_score = 50
        elif total_followers > 0:
            aud_score = 25
        else:
            aud_score = 0
        scores["audience_signal"] = aud_score
        
        # 8. Profile completeness
        completeness_ratio = (populated_fields / total_fields_expected) if total_fields_expected > 0 else 0
        scores["profile_completeness"] = min(100, completeness_ratio * 100)
        
        # 9. Evidence quality
        # Based on how many distinct platforms provided evidence for the dimensions
        evidence_platforms = set()
        for dim in ["location_verification", "track_verification", "subject_verification"]:
            ev_list = verification_results.get(dim, {}).get("evidence", [])
            for ev in ev_list:
                evidence_platforms.add(ev.get("platform"))
                
        ev_count = len(evidence_platforms)
        if ev_count >= 3:
            ev_score = 100
        elif ev_count == 2:
            ev_score = 70
        elif ev_count == 1:
            ev_score = 40
        else:
            ev_score = 0
        scores["evidence_quality"] = ev_score
        
        # Calculate overall score
        overall_score = sum(scores[key] * self.weights[key] for key in self.weights)
        
        # Generate reasons for UI
        reasons = []
        if scores["subject_relevance"] >= 80 and scores["track_relevance"] >= 80:
            reasons.append(f"Highly verified {verification_results.get('track_verification', {}).get('value')} {verification_results.get('subject_verification', {}).get('value')} educator.")
        if scores["teaching_evidence"] >= 60:
            reasons.append("Strong evidence of teaching experience found in profile bios.")
        if platforms_count >= 2:
            reasons.append(f"Established presence across {platforms_count} different platforms.")
        if total_followers > 1000:
            reasons.append(f"Strong audience signal with {total_followers}+ followers.")
        if scores["location_relevance"] >= 50:
            reasons.append(f"Location confirmed near {verification_results.get('location_verification', {}).get('value')}.")
            
        import logging
        logger = logging.getLogger("ranking")
        logger.info(f"[RANKING] Scored educator: {round(overall_score, 1)} (Platforms: {platforms_count}, Followers: {total_followers})")
        
        return {
            "scores": {k: round(v, 1) for k, v in scores.items()},
            "overall_relevance_score": round(overall_score, 1),
            "reasons": reasons
        }
