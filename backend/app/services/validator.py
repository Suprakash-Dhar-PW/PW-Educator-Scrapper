import re
from typing import List, Dict, Any, Tuple

class ValidatorService:
    def __init__(self):
        pass

    def verify_educator(
        self,
        educator: Dict[str, Any],
        social_profiles: List[Dict[str, Any]],
        target_location: str,
        target_track: str,
        target_subject: str
    ) -> Dict[str, Any]:
        
        # Consolidate all available text sources for this educator
        text_sources = []
        for profile in social_profiles:
            # We assume the profile object has either raw_profile_data or fields we can inspect
            platform = profile.get("platform", "Unknown")
            
            # For simplicity, if we stored raw_profile_data, we can scan it
            raw_data = profile.get("raw_profile_data", {})
            platform_data = raw_data.get("platform_profiles", [{}])[0]
            
            # Gather text fields
            texts = [
                platform_data.get("bio", ""),
                platform_data.get("description", ""),
                platform_data.get("about", ""),
                platform_data.get("title", ""),
                platform_data.get("headline", ""),
                platform_data.get("location", ""),
                raw_data.get("discovery_snippet", ""),
                raw_data.get("discovery", {}).get("snippet", "")
            ]
            
            combined_text = " ".join(t for t in texts if t)
            if combined_text.strip():
                text_sources.append({
                    "platform": platform,
                    "text": combined_text
                })

        import logging
        logger = logging.getLogger("validator")
        
        result = {
            "location_verification": self._verify_dimension(target_location, text_sources, is_location=True),
            "track_verification": self._verify_dimension(target_track, text_sources, is_track=True),
            "subject_verification": self._verify_dimension(target_subject, text_sources)
        }
        
        logger.info(f"[VERIFICATION] Educator verification complete. "
                    f"Location: {result['location_verification']['status']} | "
                    f"Track: {result['track_verification']['status']} | "
                    f"Subject: {result['subject_verification']['status']}")
                    
        return result

    def _verify_dimension(self, target: str, text_sources: List[Dict[str, str]], is_location: bool = False, is_track: bool = False) -> Dict[str, Any]:
        if not target:
            return {
                "value": None,
                "confidence": 0.0,
                "status": "not_relevant",
                "evidence": []
            }
            
        target_lower = target.lower().strip()
        
        # Split target into key terms if it's a compound string like "Lucknow, Uttar Pradesh"
        if is_location and "," in target_lower:
            keywords = [k.strip() for k in target_lower.split(",")]
        elif is_track and "-" in target_lower:
            # E.g. IIT-JEE -> check IIT or JEE
            keywords = [target_lower, target_lower.replace("-", ""), target_lower.replace("-", " ")]
            # Also allow splitting by -
            keywords.extend(target_lower.split("-"))
        else:
            keywords = [target_lower]

        evidence = []
        confidence_score = 0.0
        platforms_found = set()
        
        for source in text_sources:
            source_text_lower = source["text"].lower()
            
            match_found = False
            for kw in keywords:
                if len(kw) < 3:
                    continue # Skip very short ambiguous tokens
                    
                # Use regex word boundaries for safety against substring matches
                # Escaping kw to handle special chars like '-'
                pattern = r'\b' + re.escape(kw) + r'\b'
                
                if re.search(pattern, source_text_lower):
                    match_found = True
                    break
                # Fallback simple 'in' check for locations which might lack word boundaries if joined
                elif kw in source_text_lower:
                    match_found = True
                    break
                    
            if match_found:
                platforms_found.add(source["platform"])
                
                # Extract a short window around the keyword as evidence
                # For simplicity, we just save the platform and a truncated version of the text
                snippet = self._extract_snippet(source["text"], keywords)
                
                evidence.append({
                    "platform": source["platform"],
                    "text": snippet
                })
                
                # Base confidence for finding it
                confidence_score += 0.4
                
                # Additional confidence if the text strongly implies they teach it
                if not is_location:
                    strong_indicators = ["faculty", "teacher", "educator", "teaches", "expert", "professor", "classes"]
                    if any(indicator in source_text_lower for indicator in strong_indicators):
                        confidence_score += 0.25

        # Cap confidence at 1.0
        confidence_score = min(1.0, confidence_score)
        
        # Multiple platforms confirming it increases confidence
        if len(platforms_found) >= 2 and confidence_score < 1.0:
            confidence_score = min(1.0, confidence_score + 0.2)

        # Determine status based on confidence
        if confidence_score >= 0.8:
            status = "verified"
        elif confidence_score >= 0.4:
            status = "partially_verified"
        else:
            status = "discovered"
            
        # Do not invent location: if not found, we don't return one
        return {
            "value": target if confidence_score > 0 else None,
            "confidence": round(confidence_score, 2),
            "status": status,
            "evidence": evidence
        }
        
    def _extract_snippet(self, full_text: str, keywords: List[str]) -> str:
        full_text_lower = full_text.lower()
        for kw in keywords:
            if len(kw) < 3: continue
            
            idx = full_text_lower.find(kw)
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(full_text), idx + len(kw) + 40)
                snippet = full_text[start:end].replace('\n', ' ').strip()
                if start > 0: snippet = "..." + snippet
                if end < len(full_text): snippet = snippet + "..."
                return snippet
                
        return full_text[:100] + "..." if len(full_text) > 100 else full_text
