from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
import numpy as np
from typing import Dict

from app.models import (
    ResumeUploadResponse,
    JobMatchRequest,
    JobMatchResponse,
    CareerAdviceRequest,
    CareerAdviceResponse
)
from app.services.resume_parser import ResumeParser
from app.services.skill_extractor import SkillExtractor
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.rag_service import RAGService
from app.config import get_settings

app = FastAPI(
    title="Career Compass API",
    description="GenAI-powered job and career assistant with RAG",
    version="1.0.0"
)

settings = get_settings()
os.makedirs(settings.upload_dir, exist_ok=True)

# Initialize services
parser = ResumeParser()
skill_extractor = SkillExtractor()
embedding_service = EmbeddingService()
vector_store = VectorStore()
rag_service = RAGService()

# In-memory storage (replace with database in production)
resume_storage: Dict[str, dict] = {}

@app.get("/")
def root():
    return {"message": "Career Compass API - Your AI Career Assistant"}

@app.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse resume (PDF or DOCX)"""
    
    print(f"📄 Received file: {file.filename}")
    
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files supported")
    
    print("✅ File validation passed")
    
    # Save file temporarily
    resume_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1]
    file_path = f"{settings.upload_dir}/{resume_id}.{file_extension}"
    
    print(f"💾 Saving to: {file_path}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print("✅ File saved")
    
    # Extract text
    try:
        print("📖 Extracting text...")
        if file_extension == 'pdf':
            text = parser.extract_text_from_pdf(file_path)
        else:
            text = parser.extract_text_from_docx(file_path)
        print(f"✅ Text extracted: {len(text)} characters")
        
        if not text or len(text.strip()) < 10:
            raise ValueError("Extracted text is too short or empty. Please upload a valid resume.")
            
    except Exception as e:
        print(f"❌ Error parsing: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")
    
    # Extract skills and domains
    print("🔍 Extracting skills...")
    try:
        skills = skill_extractor.extract_skills(text)
        print(f"✅ Found {len(skills)} skills: {skills[:5]}")
        
        domains = skill_extractor.identify_domains(skills)
        print(f"✅ Identified domains: {domains}")
    except Exception as e:
        print(f"❌ Error extracting skills: {e}")
        skills = []
        domains = []
    
    # Generate and store embeddings
    try:
        print("🧠 Generating embeddings...")
        
        # Truncate text if too long (embedding models have token limits)
        max_chars = 5000
        text_for_embedding = text[:max_chars] if len(text) > max_chars else text
        
        print(f"Text length for embedding: {len(text_for_embedding)} chars")
        
        # Generate embedding
        embedding = embedding_service.generate_embedding(text_for_embedding)
        print(f"Embedding type: {type(embedding)}, length: {len(embedding)}")
        
        # Convert to numpy array with correct shape
        if isinstance(embedding, list):
            embedding_array = np.array([embedding]).astype('float32')
        else:
            embedding_array = np.array([embedding.tolist()]).astype('float32')
        
        print(f"Embedding array shape: {embedding_array.shape}")
        
        # Verify shape matches vector dimension
        if embedding_array.shape[1] != settings.vector_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: got {embedding_array.shape[1]}, "
                f"expected {settings.vector_dimension}. Check your .env VECTOR_DIMENSION setting."
            )
        
        vector_store.add_documents(
            embeddings=embedding_array,
            documents=[text_for_embedding],
            metadata=[{"resume_id": resume_id, "type": "resume"}]
        )
        vector_store.save()
        print("✅ Embeddings stored successfully")
        
    except Exception as e:
        print(f"❌ Error generating embeddings: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating embeddings: {str(e)}. Make sure VECTOR_DIMENSION in .env is set to 384 for all-MiniLM-L6-v2 model."
        )
    
    # Store resume data
    resume_storage[resume_id] = {
        "text": text,
        "skills": skills,
        "domains": domains,
        "file_path": file_path
    }
    
    print(f"✅ Resume stored with ID: {resume_id}")
    
    return ResumeUploadResponse(
        resume_id=resume_id,
        extracted_text=text[:500] + "..." if len(text) > 500 else text,
        skills=skills,
        domains=domains
    )

@app.post("/job-match", response_model=JobMatchResponse)
async def job_match(request: JobMatchRequest):
    """Match resume with job description"""
    
    if request.resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resume_storage[request.resume_id]
    
    try:
        # Analyze match using RAG
        result = rag_service.analyze_job_match(
            resume_text=resume_data["text"],
            job_description=request.job_description,
            resume_skills=resume_data["skills"]
        )
        
        return JobMatchResponse(**result)
    except Exception as e:
        print(f"Error in job matching: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing job match: {str(e)}")

@app.post("/career-advice", response_model=CareerAdviceResponse)
async def career_advice(request: CareerAdviceRequest):
    """Get personalized career advice"""
    
    if request.resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resume_storage[request.resume_id]
    
    try:
        # Get advice using RAG
        answer, context = rag_service.get_career_advice(
            query=request.query,
            resume_text=resume_data["text"]
        )
        
        return CareerAdviceResponse(
            answer=answer,
            relevant_context=context
        )
    except Exception as e:
        print(f"Error getting career advice: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting career advice: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Career Compass API"}

@app.get("/resumes")
def list_resumes():
    """List all uploaded resumes"""
    return {
        "count": len(resume_storage),
        "resumes": [
            {
                "resume_id": rid,
                "skills_count": len(data["skills"]),
                "domains": data["domains"]
            }
            for rid, data in resume_storage.items()
        ]
    }

@app.delete("/resume/{resume_id}")
def delete_resume(resume_id: str):
    """Delete a resume"""
    if resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Delete file
    file_path = resume_storage[resume_id]["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove from storage
    del resume_storage[resume_id]
    
    return {"message": "Resume deleted successfully", "resume_id": resume_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
