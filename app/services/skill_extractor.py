import json
from typing import List, Set
import re

class SkillExtractor:
    def __init__(self, skills_db_path: str = "data/skills_database.json"):
        with open(skills_db_path, 'r') as f:
            self.skills_data = json.load(f)
        self.all_skills = self._flatten_skills()
    
    def _flatten_skills(self) -> Set[str]:
        """Create flat set of all skills from database"""
        skills = set()
        for domain_data in self.skills_data.values():
            skills.update([s.lower() for s in domain_data.get("skills", [])])
        return skills
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills using keyword matching"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.all_skills:
            # Use word boundaries for accurate matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    def identify_domains(self, skills: List[str]) -> List[str]:
        """Identify career domains based on extracted skills"""
        domain_scores = {}
        
        for domain, data in self.skills_data.items():
            domain_skills = [s.lower() for s in data.get("skills", [])]
            overlap = len(set(skills) & set(domain_skills))
            if overlap > 0:
                domain_scores[domain] = overlap
        
        # Return top domains sorted by skill overlap
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return [domain for domain, _ in sorted_domains[:3]]
