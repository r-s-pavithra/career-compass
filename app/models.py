from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class ResumeUploadResponse(BaseModel):
    resume_id: str
    extracted_text: str
    skills: List[str]
    domains: List[str]


class JobMatchRequest(BaseModel):
    resume_id: str
    job_description: str
    
    @field_validator('job_description')
    @classmethod
    def clean_job_description(cls, v: str) -> str:
        """Clean and normalize job description text"""
        if not v or not v.strip():
            raise ValueError("Job description cannot be empty")
        return v.strip()


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
