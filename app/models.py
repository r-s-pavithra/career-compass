from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ResumeUploadResponse(BaseModel):
    resume_id: str
    extracted_text: str
    skills: List[str]
    domains: List[str]

class JobMatchRequest(BaseModel):
    resume_id: str
    job_description: str

class JobMatchResponse(BaseModel):
    match_score: float = Field(ge=0, le=100)
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: str

class CareerAdviceRequest(BaseModel):
    resume_id: str
    query: str

class CareerAdviceResponse(BaseModel):
    answer: str
    relevant_context: List[str]
