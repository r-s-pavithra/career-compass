import pdfplumber
from docx import Document
from typing import Optional
import re

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return ResumeParser._clean_text(text)
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX"""
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return ResumeParser._clean_text(text)
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    @staticmethod
    def extract_contact_info(text: str) -> dict[str, Optional[str]]:
        """Extract email and phone from resume text"""
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{3,6}[-\s\.]?[0-9]{4,6}'
        
        email = re.search(email_pattern, text)
        phone = re.search(phone_pattern, text)
        
        return {
            "email": email.group(0) if email else None,
            "phone": phone.group(0) if phone else None
        }
