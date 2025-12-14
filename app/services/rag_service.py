from groq import Groq
from typing import List, Dict, Set
import numpy as np
import re
from app.config import get_settings
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.skill_extractor import SkillExtractor
from app.prompts import CAREER_ADVICE_PROMPT, JOB_MATCH_PROMPT


class RAGService:
    def __init__(self):
        self.settings = get_settings()
        if self.settings.groq_api_key:
            self.client = Groq(api_key=self.settings.groq_api_key)
        elif self.settings.openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.settings.openai_api_key)
        else:
            raise ValueError("API Key not found. Please set GROQ_API_KEY or OPENAI_API_KEY in .env")
        
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.vector_store.load()
        self.skill_extractor = SkillExtractor()
    
    def get_career_advice(self, query: str, resume_text: str, resume_id: str = None) -> tuple[str, List[str]]:
        """
        Get career advice using ONLY the provided resume (not vector search)
        This ensures advice is based on the CURRENT USER'S resume only
        """
        
        print(f"💬 Generating career advice for query: {query[:100]}...")
        print(f"📄 Using resume (first 200 chars): {resume_text[:200]}...")
        
        # ✅ Don't use vector search - use the resume_text directly
        # This prevents getting advice based on other users' resumes
        
        # Build prompt with ONLY current user's resume
        context = f"Candidate's Resume:\n{resume_text[:2000]}"
        
        prompt = CAREER_ADVICE_PROMPT.format(
            context=context,
            resume=resume_text[:2000],
            query=query
        )
        
        # Add system message to ensure LLM focuses ONLY on this resume
        system_message = """You are an expert career advisor. 

IMPORTANT: Base your advice ONLY on the specific resume provided below. Do NOT use general advice or reference other candidates.

Provide personalized, actionable career guidance based on:
1. The candidate's current skills and experience
2. Their career trajectory
3. Relevant industry trends
4. Specific next steps they can take

Be specific, encouraging, and practical."""
        
        try:
            # Call LLM with explicit system message
            response = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.settings.max_tokens,
                temperature=0.7  # Slightly higher for more personalized responses
            )
            
            answer = response.choices[0].message.content
            
            print(f"✅ Generated career advice ({len(answer)} chars)")
            
            # Return answer and resume snippet as context
            return answer, [resume_text[:500]]
            
        except Exception as e:
            print(f"❌ Error generating career advice: {e}")
            # Fallback response
            return self._fallback_career_advice(query, resume_text), [resume_text[:500]]
    
    def _fallback_career_advice(self, query: str, resume_text: str) -> str:
        """Fallback career advice if LLM fails"""
        return f"""Thank you for your question: "{query}"

Based on your background, here are some general recommendations:

1. **Continue Building Skills**: Focus on strengthening your existing technical skills and exploring complementary technologies.

2. **Stay Current**: Keep up with industry trends through courses, certifications, and hands-on projects.

3. **Network Actively**: Engage with professionals in your field through LinkedIn, conferences, and meetups.

4. **Document Your Work**: Maintain a portfolio showcasing your best projects and achievements.

Please try asking your question again for more personalized advice."""
    
    def analyze_job_match(self, resume_text: str, job_description: str, resume_skills: List[str]) -> dict:
        """
        IMPROVED: Hybrid job matching using BOTH algorithmic analysis AND LLM insights
        """
        print("\n🔍 Starting detailed job match analysis...")
        
        # ========== STEP 1: Extract skills from job description ==========
        print("📋 Extracting required skills from job description...")
        job_skills = self.skill_extractor.extract_skills(job_description)
        print(f"   Found {len(job_skills)} required skills")
        
        # ========== STEP 2: Normalize skills (handle synonyms) ==========
        resume_skills_normalized = self._normalize_skills(resume_skills)
        job_skills_normalized = self._normalize_skills(job_skills)
        
        print(f"📊 Resume skills (normalized): {len(resume_skills_normalized)}")
        print(f"📊 Job skills (normalized): {len(job_skills_normalized)}")
        
        # ========== STEP 3: Calculate exact skill matches ==========
        matched_skills = list(resume_skills_normalized & job_skills_normalized)
        missing_skills = list(job_skills_normalized - resume_skills_normalized)
        
        print(f"✅ Matched skills: {len(matched_skills)}")
        print(f"❌ Missing skills: {len(missing_skills)}")
        
        # ========== STEP 4: Calculate base match score ==========
        if len(job_skills_normalized) > 0:
            exact_match_score = (len(matched_skills) / len(job_skills_normalized)) * 100
        else:
            exact_match_score = 50.0  # Default if no skills found in JD
        
        print(f"📈 Exact match score: {exact_match_score:.1f}%")
        
        # ========== STEP 5: Semantic similarity using embeddings ==========
        print("🧠 Calculating semantic similarity...")
        resume_embedding = self.embedding_service.generate_embedding(resume_text[:4000])
        job_embedding = self.embedding_service.generate_embedding(job_description[:4000])
        
        # Cosine similarity
        resume_vec = np.array(resume_embedding)
        job_vec = np.array(job_embedding)
        
        cosine_sim = np.dot(resume_vec, job_vec) / (np.linalg.norm(resume_vec) * np.linalg.norm(job_vec))
        semantic_score = float(cosine_sim) * 100
        
        print(f"🧬 Semantic similarity score: {semantic_score:.1f}%")
        
        # ========== STEP 6: Extract experience years ==========
        resume_years = self._extract_years_experience(resume_text)
        required_years = self._extract_years_experience(job_description)
        
        experience_score = 100.0
        if required_years > 0:
            if resume_years >= required_years:
                experience_score = 100.0
            elif resume_years >= required_years * 0.7:
                experience_score = 80.0
            else:
                experience_score = max(50.0, (resume_years / required_years) * 100)
        
        print(f"📅 Experience: Resume {resume_years}y, Required {required_years}y → {experience_score:.1f}%")
        
        # ========== STEP 7: Calculate weighted final score ==========
        final_score = (
            exact_match_score * 0.50 +      # 50% weight on exact skill matches
            semantic_score * 0.30 +          # 30% weight on semantic similarity
            experience_score * 0.20          # 20% weight on experience
        )
        
        final_score = min(100.0, max(0.0, final_score))  # Clamp to 0-100
        
        print(f"🎯 FINAL MATCH SCORE: {final_score:.1f}%")
        print(f"   - Exact skill match: {exact_match_score:.1f}% (weight: 50%)")
        print(f"   - Semantic similarity: {semantic_score:.1f}% (weight: 30%)")
        print(f"   - Experience match: {experience_score:.1f}% (weight: 20%)")
        
        # ========== STEP 8: Use LLM for detailed recommendations ==========
        print("💡 Generating AI recommendations...")
        recommendations = self._generate_recommendations_with_llm(
            resume_text, job_description, matched_skills, missing_skills, final_score
        )
        
        return {
            "match_score": round(final_score, 1),
            "matched_skills": matched_skills[:15],  # Top 15
            "missing_skills": missing_skills[:15],  # Top 15
            "recommendations": recommendations
        }
    
    def _normalize_skills(self, skills: List[str]) -> Set[str]:
        """Normalize skills to handle synonyms and variations"""
        synonyms = {
            'javascript': ['js', 'javascript', 'ecmascript'],
            'python': ['python', 'python3', 'py'],
            'react': ['react', 'reactjs', 'react.js'],
            'node': ['node', 'nodejs', 'node.js'],
            'machine learning': ['ml', 'machine learning', 'machinelearning'],
            'artificial intelligence': ['ai', 'artificial intelligence'],
            'docker': ['docker', 'containerization'],
            'kubernetes': ['k8s', 'kubernetes'],
            'aws': ['aws', 'amazon web services'],
            'gcp': ['gcp', 'google cloud', 'google cloud platform'],
            'azure': ['azure', 'microsoft azure'],
            'typescript': ['ts', 'typescript'],
            'java': ['java', 'java8', 'java11'],
            'cpp': ['c++', 'cpp', 'cplusplus'],
            'csharp': ['c#', 'csharp', 'dotnet'],
            'sql': ['sql', 'mysql', 'postgresql', 'tsql'],
            'nosql': ['nosql', 'mongodb', 'cassandra', 'dynamodb'],
            'api': ['api', 'rest', 'restful', 'rest api'],
            'frontend': ['frontend', 'front-end', 'front end'],
            'backend': ['backend', 'back-end', 'back end'],
        }
        
        normalized = set()
        for skill in skills:
            skill_lower = skill.lower().strip()
            
            # Find canonical name
            canonical = skill_lower
            for key, variants in synonyms.items():
                if skill_lower in variants:
                    canonical = key
                    break
            
            normalized.add(canonical)
        
        return normalized
    
    def _extract_years_experience(self, text: str) -> int:
        """Extract years of experience from text"""
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)',
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(m) for m in matches])
        
        return max(years) if years else 0
    
    def _generate_recommendations_with_llm(
        self, resume: str, job_desc: str, matched: List[str], missing: List[str], score: float
    ) -> str:
        """Use LLM ONLY for generating recommendations, not the score"""
        
        prompt = f"""You are a career advisor. Analyze this job match and provide actionable recommendations.

MATCH SCORE: {score:.1f}%

MATCHED SKILLS: {', '.join(matched) if matched else 'None'}

MISSING SKILLS: {', '.join(missing) if missing else 'None'}

JOB DESCRIPTION (excerpt):
{job_desc[:1500]}

RESUME (excerpt):
{resume[:1500]}

Provide 3-5 specific, actionable recommendations to improve the candidate's chances. Focus on:
1. Which missing skills to prioritize learning
2. How to highlight existing relevant experience
3. Suggested certifications or courses
4. Resume improvements

Keep recommendations concise and practical. Maximum 150 words."""

        try:
            response = self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ LLM recommendation failed: {e}")
            return self._fallback_recommendations(matched, missing, score)
    
    def _fallback_recommendations(self, matched: List[str], missing: List[str], score: float) -> str:
        """Fallback recommendations if LLM fails"""
        if score >= 80:
            return f"Strong match! Highlight your experience with {', '.join(matched[:3])} in your application. Consider learning {missing[0] if missing else 'advanced topics'} to become an even stronger candidate."
        elif score >= 60:
            return f"Good match with room for improvement. Priority: Learn {', '.join(missing[:3])} through online courses. Emphasize your {', '.join(matched[:2])} skills in your resume."
        else:
            return f"Skill gap detected. Focus on: {', '.join(missing[:3])}. Consider certifications in these areas. Meanwhile, apply to positions requiring {', '.join(matched[:2])}."
    
    def _parse_job_match_response(self, response_text: str) -> dict:
        """Legacy parser - kept for compatibility"""
        import json
        import re
        
        try:
            parsed = json.loads(response_text)
            return parsed
        except:
            pass
        
        # Fallback parsing
        match_score = 70.0
        score_match = re.search(r'"?match_score"?:\s*(\d+(?:\.\d+)?)', response_text)
        if score_match:
            match_score = float(score_match.group(1))
        
        return {
            "match_score": match_score,
            "matched_skills": [],
            "missing_skills": [],
            "recommendations": "Analysis complete."
        }
