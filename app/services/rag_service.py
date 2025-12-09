from groq import Groq
from typing import List
import numpy as np
from app.config import get_settings
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.prompts import CAREER_ADVICE_PROMPT, JOB_MATCH_PROMPT

class RAGService:
    def __init__(self):
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.openai_api_key)
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.vector_store.load()
    
    def get_career_advice(self, query: str, resume_text: str) -> tuple[str, List[str]]:
        """Get career advice using RAG pipeline"""
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        query_embedding = np.array(query_embedding).astype('float32')
        
        # Retrieve relevant context from vector store
        results = self.vector_store.search(query_embedding, k=3)
        context_chunks = [doc for doc, _, _ in results]
        
        # Build prompt with context
        context = "\n\n".join(context_chunks) if context_chunks else "No additional context available."
        prompt = CAREER_ADVICE_PROMPT.format(
            context=context,
            resume=resume_text,
            query=query
        )
        
        # Call Groq LLM
        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature
        )
        
        answer = response.choices[0].message.content
        return answer, context_chunks
    
    def analyze_job_match(self, resume_text: str, job_description: str, resume_skills: List[str]) -> dict:
        """Analyze job match using Groq LLM"""
        prompt = JOB_MATCH_PROMPT.format(
            resume=resume_text,
            job_description=job_description,
            resume_skills=", ".join(resume_skills)
        )
        
        response = self.client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.2
        )
        
        # Parse structured response
        return self._parse_job_match_response(response.choices[0].message.content)
    
    def _parse_job_match_response(self, response_text: str) -> dict:
        """Parse LLM response into structured format"""
        import json
        import re
        
        print(f"Raw LLM response:\n{response_text}\n")
        
        try:
            # Try direct JSON parsing first
            parsed = json.loads(response_text)
            print("✅ Direct JSON parsing successful")
            return parsed
        except Exception as e:
            print(f"Direct JSON parsing failed: {e}")
        
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'``````', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                print("✅ Extracted JSON from markdown code block")
                return parsed
        except Exception as e:
            print(f"Markdown JSON extraction failed: {e}")
        
        try:
            # Try to find JSON object anywhere in the text
            json_match = re.search(r'\{[\s\S]*?"match_score"[\s\S]*?\}', response_text)
            if json_match:
                parsed = json.loads(json_match.group(0))
                print("✅ Extracted JSON object from text")
                return parsed
        except Exception as e:
            print(f"JSON object extraction failed: {e}")
        
        try:
            # Last attempt: find all JSON-like structures
            json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
            for json_obj in json_objects:
                try:
                    parsed = json.loads(json_obj)
                    if "match_score" in parsed:
                        print("✅ Found valid JSON with match_score")
                        return parsed
                except:
                    continue
        except Exception as e:
            print(f"Multiple JSON extraction failed: {e}")
        
        # Fallback: Extract information manually from text
        print("⚠️ Using fallback parsing")
        
        # Try to extract match score
        match_score = 70.0
        score_match = re.search(r'"match_score":\s*(\d+(?:\.\d+)?)', response_text)
        if score_match:
            match_score = float(score_match.group(1))
        
        # Try to extract matched skills
        matched_skills = []
        matched_match = re.search(r'"matched_skills":\s*\[(.*?)\]', response_text, re.DOTALL)
        if matched_match:
            skills_str = matched_match.group(1)
            matched_skills = [s.strip(' "\'') for s in skills_str.split(',') if s.strip()]
        
        # Try to extract missing skills
        missing_skills = []
        missing_match = re.search(r'"missing_skills":\s*\[(.*?)\]', response_text, re.DOTALL)
        if missing_match:
            skills_str = missing_match.group(1)
            missing_skills = [s.strip(' "\'') for s in skills_str.split(',') if s.strip()]
        
        # Try to extract recommendations
        recommendations = response_text
        rec_match = re.search(r'"recommendations":\s*"(.*?)"(?:\s*\})?$', response_text, re.DOTALL)
        if rec_match:
            recommendations = rec_match.group(1)
        
        return {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommendations": recommendations
        }
