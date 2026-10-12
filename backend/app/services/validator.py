import re
import logging
from typing import List, Dict, Any, Tuple

class ValidatorService:
    def __init__(self):
        self.pw_keywords = [
            "physics wallah", "physicswallah", "pw", "vidyapeeth", "pw vidyapeeth",
            "vidyapith", "pw vidyapith", "pw pathshala", "pathshala", "physics wallah vidyapeeth",
            "physicswallah vidyapeeth", "pw mentor", "pw faculty", "pw star", "pw offline",
            "pw online", "pw iit", "pw coaching", "pw center", "pw centre",
            "physics wallah faculty", "physics wallah teacher", "former physics wallah faculty",
            "ex-pw faculty", "joined physics wallah", "left physics wallah", "ex-pw",
            "vidyapeeth faculty", "vidyapeeth teacher", "pw vidyapeeth faculty",
            "pw pathshala faculty", "pw educator", "pw teacher"
        ]
        self.student_signals = [
            "student", "aspiring", "learner", "pursuing", "fresher", "scholar",
            "undergrad", "undergraduate", "postgraduate", "postgrad", "phd scholar",
            "ph.d scholar", "intern", "trainee", "aspirant", "studying at",
            "btech student", "b.tech student", "msc student", "m.sc student",
            "college student", "school student", "jee aspirant", "neet aspirant",
            "aspiring educator", "aspiring teacher", "seeking entry level",
            "fresher looking", "graduated from"
        ]
        self.educator_roles = [
            "faculty", "teacher", "educator", "professor", "lecturer", "tutor",
            "mentor", "guide", "hod", "head of department", "assistant professor",
            "associate professor", "senior faculty", "lead faculty", "iit jee faculty",
            "jee faculty", "neet faculty", "maths faculty", "physics faculty",
            "chemistry faculty", "biology faculty", "teaching experience",
            "coaching faculty", "academic head", "teaching at", "teaches",
            "educator at", "tutor for", "mentor for"
        ]
        self.institution_signals = [
            "_official", "official", "institute", "institution", "academy", "classes",
            "university", "college", "department of", "admin", "team", "centre", "center",
            "tutorials", "education", "study", "channel", "hub", "point", "zone", "coaching",
            "iithyderabad", "iit hyderabad", "iit delhi", "iit bombay", "iit madras",
            "allen career", "fiitjee", "aakash", "unacademy", "group", "school"
        ]
        self.non_pw_employers = [
            "allen", "aakash", "unacademy", "fiitjee", "narayana", "sri chaitanya",
            "resonance", "vedantu", "byju", "pace", "vidyamandir", "motion", "vibrant"
        ]
        
    def verify_educator(
        self,
        educator: Dict[str, Any],
        social_profiles: List[Dict[str, Any]],
        target_location: str,
        target_track: str,
        target_subject: str
    ) -> Dict[str, Any]:
        
        text_sources = []
        for profile in social_profiles:
            platform = profile.get("platform", "Unknown")
            raw_data = profile.get("raw_profile_data", {})
            platform_data = raw_data.get("platform_profiles", [{}])[0]
            
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
            
            experience_list = platform_data.get("experience", [])
            if isinstance(experience_list, list):
                for exp in experience_list:
                    if isinstance(exp, dict):
                        texts.append(exp.get("title", ""))
                        texts.append(exp.get("employer", ""))
                        texts.append(exp.get("description", ""))
            
            combined_text = " ".join(t for t in texts if t and isinstance(t, str))
            if combined_text.strip():
                text_sources.append({
                    "platform": platform,
                    "text": combined_text,
                    "title": platform_data.get("title", raw_data.get("discovery", {}).get("title", ""))
                })

        logger = logging.getLogger("validator")
        
        identity = self._verify_identity(educator, text_sources, target_location, target_subject)
        role = self._verify_role(text_sources, identity.get("headline", ""), identity.get("value", ""))
        employment = self._verify_employment(text_sources, identity.get("employer"), identity.get("value", ""))

        result = {
            "identity_verification": identity,
            "role_verification": role,
            "employment_verification": employment,
            "location_verification": self._verify_dimension_location(target_location, text_sources),
            "track_verification": self._verify_dimension_track(target_track, target_subject, text_sources),
            "subject_verification": self._verify_dimension_subject(target_subject, target_track, text_sources)
        }
        
        logger.info(f"[VERIFICATION] Educator verification complete for '{identity.get('value')}'. "
                    f"Identity: {result['identity_verification']['status']} | "
                    f"Role: {'Educator' if role['is_educator'] else 'Student/Non-Educator'} | "
                    f"Employment: {result['employment_verification']['value']} | "
                    f"Location: {result['location_verification']['status']} | "
                    f"Track: {result['track_verification']['status']} | "
                    f"Subject: {result['subject_verification']['status']}")
                    
        return result

    def _verify_role(self, text_sources: List[Dict[str, Any]], headline: str, clean_name: str) -> Dict[str, Any]:
        combined_text = " ".join(s.get("text", "") for s in text_sources).lower()
        headline_lower = (headline or "").lower()
        
        is_student = False
        is_educator = False
        
        # Check student signals
        has_student_signal = any(sig in headline_lower or f" {sig} " in f" {combined_text} " for sig in self.student_signals)
        
        # Check educator signals
        has_educator_signal = any(sig in headline_lower or sig in combined_text for sig in self.educator_roles)
        
        # Explicit student / aspiring phrasing without active faculty/teaching position
        if "aspiring" in headline_lower or "aspiring educator" in combined_text or "msc student" in combined_text or "btech student" in combined_text or "aspirant" in headline_lower:
            is_student = True
            is_educator = False
        elif has_student_signal and not has_educator_signal:
            is_student = True
            is_educator = False
        elif has_educator_signal:
            is_educator = True
            is_student = False
        else:
            is_educator = False
            is_student = False
            
        return {
            "is_educator": is_educator,
            "is_student": is_student,
            "status": "verified" if is_educator else "rejected" if is_student else "unconfirmed"
        }

    def _verify_identity(self, educator: Dict[str, Any], text_sources: List[Dict[str, Any]], target_location: str, target_subject: str) -> Dict[str, Any]:
        original_name = educator.get("name") or educator.get("full_name") or ""
        clean_name = original_name.strip()
        
        if clean_name.startswith("#"): clean_name = ""
        if len(clean_name.split()) > 4: clean_name = ""
            
        lower_name = clean_name.lower()
        
        # Reject names containing the location or subject (leakage check)
        if target_location.lower() in lower_name and target_location.lower() != lower_name:
            clean_name = ""
        if target_subject.lower() in lower_name:
            clean_name = ""

        # Institutional / Channel / Organization / College detection
        is_institution = False
        is_channel = False
        channel_signals = ["classes", "walaz", "wallah", "point", "channel", "tutorials", "academy", "study", "prep", "zone"]
        for p in text_sources:
            if p.get("platform") == "YouTube":
                p_title = p.get("title", "").lower()
                if any(cs in lower_name for cs in channel_signals) or any(cs in p_title for cs in channel_signals):
                    is_channel = True
                    break

        for sig in self.institution_signals:
            if sig in lower_name or (f"@{sig}" in lower_name):
                is_institution = True
                break
                
        if is_channel:
            entity_type = "channel"
            clean_name = ""
        elif is_institution:
            entity_type = "institution"
            clean_name = ""
        else:
            entity_type = "individual"

        bad_words = [
            "faculty", "classes", "institute", "best teacher", "sir", "madam", "coaching",
            "iit", "jee", "neet", "chemistry", "physics", "maths", "mathematics", "biology",
            "practice", "academy", "tutorial", "tutorials", "education", "study", "channel",
            "official", "preparation", "exam", "board", "cbse", "icse", "state", "school",
            "college", "university", "center", "centre", "hub", "point", "zone", "tutor", "tutors",
            "instagram", "youtube", "linkedin", "facebook", "reddit", "twitter", "quora", "telegram",
            "whatsapp", "website", "profile", "page", "group", "login"
        ]
        
        is_bad = False
        for w in bad_words:
            if re.search(rf'\b{w}\b', lower_name):
                is_bad = True
                break

        if is_bad or not clean_name or len(clean_name) < 3:
            clean_name = ""

        headline = ""
        employer = ""
        evidence = []
        confidence = 0.0
        
        if is_institution:
            confidence = 0.0
        elif clean_name:
            confidence += 0.5
            
        for source in text_sources:
            t_lower = source["text"].lower()
            
            title = source.get("title", "")
            if title and len(title) > len(headline):
                if " - " in title: headline = title.split(" - ", 1)[1].strip()
                elif " | " in title: headline = title.split(" | ", 1)[1].strip()
                    
            for emp_kw in self.non_pw_employers:
                if emp_kw in t_lower:
                    employer = emp_kw.capitalize()
                    break
            
            if employer or headline:
                confidence += 0.3
                evidence.append({
                    "platform": source["platform"],
                    "text": source["text"][:150] + "..."
                })

        confidence = min(1.0, confidence)
        status = "verified" if confidence >= 0.5 and clean_name and entity_type == "individual" else "unconfirmed"
        
        return {
            "value": clean_name,
            "entity_type": entity_type,
            "is_institution": is_institution,
            "headline": headline,
            "employer": employer,
            "confidence": round(confidence, 2),
            "status": status,
            "evidence": evidence
        }

    def _verify_employment(self, text_sources: List[Dict[str, Any]], employer: str, clean_name: str = "") -> Dict[str, Any]:
        status = "ELIGIBILITY_UNCONFIRMED"
        confidence = 0.5
        evidence = []
        
        # 1. Check in-memory text sources for PW / Vidyapeeth keywords
        for source in text_sources:
            t_lower = source["text"].lower()
            is_pw = False
            for kw in self.pw_keywords:
                if kw == "pw":
                    if re.search(r'\bpw\b', t_lower): is_pw = True; break
                elif kw == "vidyapeeth":
                    if re.search(r'\bvidyapeeth\b', t_lower): is_pw = True; break
                elif kw == "pathshala":
                    if re.search(r'\bpathshala\b', t_lower): is_pw = True; break
                elif kw in t_lower:
                    is_pw = True
                    break
                    
            if is_pw:
                if any(x in t_lower for x in ["ex-pw", "former", "left", "ex pw", "ex-physics wallah"]):
                    status = "EXCLUDED_FORMER_PW"
                else:
                    status = "EXCLUDED_CURRENT_PW"
                confidence = 0.95
                evidence.append({
                    "platform": source["platform"],
                    "text": self._extract_snippet(source["text"], self.pw_keywords)
                })
                break

        # 2. If clean_name is known and not yet flagged as PW, verify against targeted web snippet check
        if status not in ["EXCLUDED_CURRENT_PW", "EXCLUDED_FORMER_PW"] and clean_name and len(clean_name) > 3:
            pw_match, is_former, snippet = self.check_pw_via_search(clean_name)
            if pw_match:
                status = "EXCLUDED_FORMER_PW" if is_former else "EXCLUDED_CURRENT_PW"
                confidence = 0.95
                evidence.append({
                    "platform": "Employment Verification",
                    "text": snippet
                })

        # 3. If still unconfirmed, verify if associated with a legitimate non-PW institute
        if status == "ELIGIBILITY_UNCONFIRMED":
            if employer and any(npe in employer.lower() for npe in self.non_pw_employers):
                status = "ELIGIBLE"
                confidence = 0.9
            else:
                total_text = " ".join(s["text"] for s in text_sources)
                if len(total_text) > 200:
                    status = "ELIGIBLE"
                    confidence = 0.7
                
        return {
            "value": status,
            "confidence": round(confidence, 2),
            "status": "verified" if confidence >= 0.8 else "unconfirmed",
            "evidence": evidence
        }

    def check_pw_via_search(self, clean_name: str) -> Tuple[bool, bool, str]:
        """Perform a quick zero-cost search engine snippet check to verify if the educator has PW/Vidyapeeth ties."""
        try:
            from app.services.anakin_search import AnakinSearchService
            search_service = AnakinSearchService()
            results = search_service.execute_query(
                "LinkedIn",
                f'"{clean_name}" ("Physics Wallah" OR "PW" OR "Vidyapeeth" OR "PhysicsWallah")',
                "India", "IIT-JEE", "Education"
            )
            for r in results:
                title_lower = (r.get("name") or "").lower()
                snippet_lower = (r.get("snippet") or "").lower()
                clean_name_lower = clean_name.lower()
                name_match = clean_name_lower in title_lower or clean_name_lower in snippet_lower
                if not name_match:
                    continue
                for kw in ["physics wallah", "physicswallah", "vidyapeeth", "pw"]:
                    matched = False
                    if kw == "pw":
                        if re.search(r'\bpw\b', snippet_lower): matched = True
                    elif kw == "vidyapeeth":
                        if re.search(r'\bvidyapeeth\b', snippet_lower): matched = True
                    elif kw in snippet_lower:
                        matched = True
                    if matched:
                        is_former = any(x in snippet_lower for x in ["ex-pw", "former", "left", "ex pw"])
                        return True, is_former, r.get("snippet")[:160] + "..."
        except Exception as e:
            logging.getLogger("validator").warning(f"PW search check skipped: {e}")
        return False, False, ""

    def _verify_dimension_location(self, target: str, text_sources: List[Dict[str, str]]) -> Dict[str, Any]:
        if not target or target.lower() == "online":
            return {"value": target, "confidence": 1.0, "status": "verified", "evidence": []}
            
        target_lower = target.lower().strip()
        keywords = [k.strip() for k in target_lower.split(",")]
        
        return self._do_match(target, keywords, text_sources, is_location=True)

    def _verify_dimension_track(self, target_track: str, target_subject: str, text_sources: List[Dict[str, str]]) -> Dict[str, Any]:
        if not target_track: return {"value": None, "confidence": 0.0, "status": "not_relevant", "evidence": []}
        
        target_lower = target_track.lower().strip()
        keywords = [target_lower, target_lower.replace("-", ""), target_lower.replace("-", " ")]
        keywords.extend(target_lower.split("-"))
        if "jee" in target_lower or "iit" in target_lower:
            keywords.extend(["iit-jee", "iit jee", "jee mains", "jee advanced", "jee main", "iit", "jee"])
        elif "neet" in target_lower:
            keywords.extend(["neet", "medical", "aiims", "pre-medical"])
        
        # Cross check if they teach the WRONG track
        wrong_tracks = []
        if "jee" in target_lower or "iit" in target_lower: wrong_tracks = ["neet", "medical", "upsc", "ssc", "bank"]
        elif "neet" in target_lower: wrong_tracks = ["jee", "iit", "engineering", "upsc", "ssc"]

        return self._do_match(target_track, keywords, text_sources, wrong_keywords=wrong_tracks, require_educator=True)

    def _verify_dimension_subject(self, target_subject: str, target_track: str, text_sources: List[Dict[str, str]]) -> Dict[str, Any]:
        if not target_subject: return {"value": None, "confidence": 0.0, "status": "not_relevant", "evidence": []}
        
        target_lower = target_subject.lower().strip()
        keywords = [target_lower]
        
        # Wrong subjects cross-check
        wrong_subjects = ["chemistry", "biology", "botany", "zoology", "maths", "mathematics", "physics"]
        if target_lower in wrong_subjects: wrong_subjects.remove(target_lower)
        if target_lower == "mathematics" and "maths" in wrong_subjects: wrong_subjects.remove("maths")
        if target_lower == "maths" and "mathematics" in wrong_subjects: wrong_subjects.remove("mathematics")
        
        return self._do_match(target_subject, keywords, text_sources, wrong_keywords=wrong_subjects, require_educator=True)

    def _do_match(self, target: str, keywords: List[str], text_sources: List[Dict[str, str]], wrong_keywords: List[str] = None, require_educator: bool = False, is_location: bool = False) -> Dict[str, Any]:
        evidence = []
        confidence_score = 0.0
        platforms_found = set()
        
        wrong_keywords = wrong_keywords or []
        
        for source in text_sources:
            source_text_lower = source["text"].lower()
            
            # Check for non-educator penalization if this requires an educator
            if require_educator:
                if any(re.search(rf'\b{r}\b', source_text_lower) for r in self.student_signals):
                    # They might be a student or aspiring learner
                    if not any(re.search(rf'\b{r}\b', source_text_lower) for r in self.educator_roles):
                        continue # Skip this source as evidence since it's likely just a student
            
            match_found = False
            for kw in keywords:
                if len(kw) < 3: continue
                if re.search(r'\b' + re.escape(kw) + r'\b', source_text_lower) or kw in source_text_lower:
                    match_found = True
                    break
                    
            if match_found:
                # Check if it also mentions wrong keywords heavily
                wrong_mentions = sum(1 for wk in wrong_keywords if re.search(r'\b' + re.escape(wk) + r'\b', source_text_lower))
                if wrong_mentions > 2:
                    continue # Likely teaches something else primarily
                    
                platforms_found.add(source["platform"])
                snippet = self._extract_snippet(source["text"], keywords)
                evidence.append({"platform": source["platform"], "text": snippet})
                confidence_score += 0.4
                
                if require_educator:
                    if any(indicator in source_text_lower for indicator in self.educator_roles):
                        confidence_score += 0.4 # Strong evidence of teaching

        confidence_score = min(1.0, confidence_score)
        if len(platforms_found) >= 2 and confidence_score < 1.0:
            confidence_score = min(1.0, confidence_score + 0.2)

        if confidence_score >= 0.8: status = "verified"
        elif confidence_score >= 0.4: status = "partially_verified"
        else: status = "not_relevant" if require_educator else "discovered"
            
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
