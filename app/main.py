# ==================== IMPORTS ====================
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from jose import JWTError, jwt
import os
import uuid
import shutil
import numpy as np
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import authentication and database models
from models import Base, User, UserResume
from auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
    SECRET_KEY,
    ALGORITHM
)

# Import app modules
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

# ==================== FASTAPI APP ====================
app = FastAPI(
    title="Career Compass API",
    description="GenAI-powered career assistant with RAG + Authentication",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATABASE SETUP ====================
DATABASE_URL = "sqlite:///./career_compass.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

print("✅ Database initialized successfully!")

# ==================== AUTH HELPER ====================
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user from token"""
    from models import User
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

# ==================== PYDANTIC MODELS FOR AUTH ====================
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str
    email: str

class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    created_at: datetime
    resume_count: int

# ==================== SERVICE INITIALIZATION ====================
settings = get_settings()
os.makedirs(settings.upload_dir, exist_ok=True)

# Initialize services
parser = ResumeParser()
skill_extractor = SkillExtractor()
embedding_service = EmbeddingService()
vector_store = VectorStore()
rag_service = RAGService()

# In-memory storage for resume data
resume_storage: Dict[str, dict] = {}

# ==================== HELPER FUNCTION FOR RESUME LOADING ====================
def get_resume_data(resume_id: str, user_id: str, db: Session) -> dict:
    """Get resume data from memory or reload from database"""
    
    # Check if in memory
    if resume_id in resume_storage and resume_storage[resume_id]["user_id"] == user_id:
        return resume_storage[resume_id]
    
    # Not in memory - reload from database
    print(f"📂 Resume {resume_id} not in memory, reloading from database...")
    
    user_resume = db.query(UserResume).filter(
        UserResume.resume_id == resume_id,
        UserResume.user_id == user_id
    ).first()
    
    if not user_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Check if file still exists
    file_extensions = ['pdf', 'docx']
    file_path = None
    
    for ext in file_extensions:
        potential_path = f"{settings.upload_dir}/{resume_id}.{ext}"
        if os.path.exists(potential_path):
            file_path = potential_path
            break
    
    if not file_path:
        raise HTTPException(
            status_code=404, 
            detail="Resume file not found. Please upload the resume again."
        )
    
    # Extract text again
    try:
        if file_path.endswith('.pdf'):
            text = parser.extract_text_from_pdf(file_path)
        else:
            text = parser.extract_text_from_docx(file_path)
        
        # Extract skills again
        skills = skill_extractor.extract_skills(text)
        domains = skill_extractor.identify_domains(skills)
        
        # Restore to memory
        resume_storage[resume_id] = {
            "text": text,
            "skills": skills,
            "domains": domains,
            "file_path": file_path,
            "user_id": user_id
        }
        
        print(f"✅ Resume {resume_id} reloaded successfully")
        return resume_storage[resume_id]
        
    except Exception as e:
        print(f"❌ Error reloading resume: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error loading resume data. Please upload again."
        )

# ==================== ROOT ENDPOINT ====================
@app.get("/")
def root():
    return {
        "message": "Career Compass API - Your AI Career Assistant",
        "version": "2.0.0",
        "docs": "/docs",
        "features": ["Authentication", "Resume Analysis", "Job Matching", "Career Advice"]
    }

# ==================== AUTHENTICATION ENDPOINTS ====================
@app.post("/register", response_model=Token, tags=["Authentication"])
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Validate password length
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"✅ New user registered: {new_user.username}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
    }

@app.post("/login", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user (username field accepts email)"""
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    print(f"✅ User logged in: {user.username}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }

@app.get("/profile", response_model=UserProfile, tags=["Authentication"])
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    
    resume_count = db.query(UserResume).filter(UserResume.user_id == current_user.id).count()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at,
        "resume_count": resume_count
    }

@app.post("/logout", tags=["Authentication"])
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should delete token)"""
    print(f"✅ User logged out: {current_user.username}")
    return {"message": "Logged out successfully", "username": current_user.username}

# ==================== RESUME ENDPOINTS (PROTECTED) ====================
@app.post("/upload-resume", response_model=ResumeUploadResponse, tags=["Resume"])
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and parse resume (PDF or DOCX) - Authenticated users only"""
    
    print(f"📄 User {current_user.username} uploading: {file.filename}")
    
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
        
        # Truncate text if too long
        max_chars = 5000
        text_for_embedding = text[:max_chars] if len(text) > max_chars else text
        
        print(f"Text length for embedding: {len(text_for_embedding)} chars")
        
        # Generate embedding
        embedding = embedding_service.generate_embedding(text_for_embedding)
        print(f"Embedding type: {type(embedding)}, length: {len(embedding)}")
        
        # Convert to numpy array
        if isinstance(embedding, list):
            embedding_array = np.array([embedding]).astype('float32')
        else:
            embedding_array = np.array([embedding.tolist()]).astype('float32')
        
        print(f"Embedding array shape: {embedding_array.shape}")
        
        # Verify dimension
        if embedding_array.shape[1] != settings.vector_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: got {embedding_array.shape[1]}, "
                f"expected {settings.vector_dimension}"
            )
        
        vector_store.add_documents(
            embeddings=embedding_array,
            documents=[text_for_embedding],
            metadata=[{"resume_id": resume_id, "user_id": current_user.id, "type": "resume"}]
        )
        vector_store.save()
        print("✅ Embeddings stored successfully")
        
    except Exception as e:
        print(f"❌ Error generating embeddings: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating embeddings: {str(e)}"
        )
    
    # Store resume data in memory
    resume_storage[resume_id] = {
        "text": text,
        "skills": skills,
        "domains": domains,
        "file_path": file_path,
        "user_id": current_user.id
    }
    
    # Save to database
    try:
        user_resume = UserResume(
            user_id=current_user.id,
            resume_id=resume_id,
            filename=file.filename,
            skills_count=len(skills),
            extracted_text=text[:1000]
        )
        db.add(user_resume)
        db.commit()
        print(f"✅ Resume saved to DB for user: {current_user.username}")
    except Exception as e:
        print(f"❌ Error saving to DB: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving resume: {str(e)}")
    
    print(f"✅ Resume stored with ID: {resume_id}")
    
    return ResumeUploadResponse(
        resume_id=resume_id,
        extracted_text=text[:500] + "..." if len(text) > 500 else text,
        skills=skills,
        domains=domains
    )

@app.post("/job-match", response_model=JobMatchResponse, tags=["Analysis"])
async def job_match(
    request: JobMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Match resume with job description - Authenticated users only"""
    
    print(f"🎯 Job matching for user: {current_user.username}")
    print(f"Resume ID: {request.resume_id}")
    print(f"Job description length: {len(request.job_description)}")
    
    # Verify resume belongs to current user
    user_resume = db.query(UserResume).filter(
        UserResume.resume_id == request.resume_id,
        UserResume.user_id == current_user.id
    ).first()
    
    if not user_resume:
        print(f"❌ Resume not found in DB for user {current_user.username}")
        raise HTTPException(
            status_code=403,
            detail="Resume not found or access denied"
        )
    
    # Get resume data (reload from DB if not in memory)
    try:
        resume_data = get_resume_data(request.resume_id, current_user.id, db)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error loading resume: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error loading resume. Please try again or upload a new resume."
        )
    
    try:
        # Analyze match using RAG
        result = rag_service.analyze_job_match(
            resume_text=resume_data["text"],
            job_description=request.job_description,
            resume_skills=resume_data["skills"]
        )
        
        print(f"✅ Job match completed with score: {result.get('match_score', 0)}")
        
        return JobMatchResponse(**result)
    except Exception as e:
        print(f"❌ Error in job matching: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing job match: {str(e)}")


@app.post("/career-advice", response_model=CareerAdviceResponse, tags=["Analysis"])
async def career_advice(
    request: CareerAdviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized career advice - Authenticated users only"""
    
    # Verify resume belongs to current user
    user_resume = db.query(UserResume).filter(
        UserResume.resume_id == request.resume_id,
        UserResume.user_id == current_user.id
    ).first()
    
    if not user_resume:
        raise HTTPException(
            status_code=403,
            detail="Resume not found or access denied"
        )
    
    # Get resume data (reload from DB if not in memory)
    try:
        resume_data = get_resume_data(request.resume_id, current_user.id, db)
    except HTTPException:
        raise
    
    print(f"💬 Career advice for user: {current_user.username}")
    print(f"📄 Resume ID: {request.resume_id}")  # ✅ Added logging
    print(f"❓ Query: {request.query}")           # ✅ Added logging
    
    try:
        # ✅ Pass resume_id to ensure we use ONLY this user's resume
        answer, context = rag_service.get_career_advice(
            query=request.query,
            resume_text=resume_data["text"],
            resume_id=request.resume_id  # ✅ ADD THIS LINE
        )
        
        return CareerAdviceResponse(
            answer=answer,
            relevant_context=context
        )
    except Exception as e:
        print(f"❌ Error getting career advice: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting career advice: {str(e)}")

@app.get("/my-resumes", tags=["Resume"])
async def get_my_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all resumes for current authenticated user"""
    
    resumes = db.query(UserResume).filter(
        UserResume.user_id == current_user.id
    ).order_by(UserResume.uploaded_at.desc()).all()
    
    return {
        "count": len(resumes),
        "user_id": current_user.id,
        "username": current_user.username,
        "resumes": [
            {
                "resume_id": r.resume_id,
                "filename": r.filename,
                "uploaded_at": r.uploaded_at.isoformat(),
                "skills_count": r.skills_count
            }
            for r in resumes
        ]
    }

# ==================== ✅ FIXED VIEW RESUME ENDPOINT ====================
@app.get("/resume/{resume_id}/view", tags=["Resume"])
async def view_resume(
    resume_id: str,
    token: str,  # ✅ Get token from query parameter (?token=...)
    db: Session = Depends(get_db)
):
    """View/download resume file (token authentication via URL query)"""
    
    # ✅ Manually decode the token from query parameter
    current_user = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
        current_user = db.query(User).filter(User.id == user_id).first()
        
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired. Please login again."
        )
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    
    # Verify resume belongs to current user
    user_resume = db.query(UserResume).filter(
        UserResume.resume_id == resume_id,
        UserResume.user_id == current_user.id
    ).first()
    
    if not user_resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found or you don't have permission to view it"
        )
    
    # Find the file
    file_extensions = ['pdf', 'docx']
    file_path = None
    media_type = None
    
    for ext in file_extensions:
        potential_path = f"{settings.upload_dir}/{resume_id}.{ext}"
        if os.path.exists(potential_path):
            file_path = potential_path
            media_type = "application/pdf" if ext == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            break
    
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="Resume file not found"
        )
    
    print(f"✅ Serving resume: {user_resume.filename} to {current_user.username}")
    
    # Return file with original filename
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=user_resume.filename,
        headers={
            "Content-Disposition": f"inline; filename={user_resume.filename}"
        }
    )

@app.delete("/resume/{resume_id}", tags=["Resume"])
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume (owner only)"""
    
    # Verify resume belongs to current user
    user_resume = db.query(UserResume).filter(
        UserResume.resume_id == resume_id,
        UserResume.user_id == current_user.id
    ).first()
    
    if not user_resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found or you don't have permission to delete it"
        )
    
    # Delete file if exists
    if resume_id in resume_storage:
        file_path = resume_storage[resume_id]["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        del resume_storage[resume_id]
    
    # Delete from database
    db.delete(user_resume)
    db.commit()
    
    print(f"✅ Resume deleted by {current_user.username}: {resume_id}")
    
    return {"message": "Resume deleted successfully", "resume_id": resume_id}

# ==================== UTILITY ENDPOINTS ====================
@app.get("/health", tags=["Utility"])
def health_check():
    return {
        "status": "healthy",
        "service": "Career Compass API",
        "version": "2.0.0",
        "database": "connected",
        "resumes_in_memory": len(resume_storage)
    }

# ==================== RUN SERVER ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
