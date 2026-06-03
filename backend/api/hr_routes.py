from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import backend.services.resume_parser as resume_parser
import backend.services.ml_service as ml_service
import backend.services.gemini_service as gemini_service

router = APIRouter()

@router.post("/upload-resumes")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    jd_text: str = Form(default=""),
    custom_skills: str = Form(default="")
):
    try:
        results = []
        for file in files:
            # Extract text
            text = await resume_parser.handle_file_upload(file)
            
            # Predict Category via ML model
            category = ml_service.predict_category(text)
            
            # Extract candidate info (Regex + Spacy)
            info = ml_service.extract_candidate_info(text)
            
            # Skill Gap Analysis
            if custom_skills.strip():
                skill_gap = ml_service.analyze_custom_skill_gap(text, custom_skills)
            else:
                skill_gap = ml_service.analyze_skill_gap(text, jd_text)
                
            # Match Score (SentenceTransformers)
            raw_match_score = ml_service.calculate_match_score(text, jd_text)
            scaled_match_score = ml_service.scale_match_score(raw_match_score)
            
            # Career Timeline
            timeline = ml_service.extract_career_timeline(text)
            
            # Comprehensive Gemini Analysis (for the AI Summary and AI Progression ONLY)
            gemini_analysis = gemini_service.analyze_resume_for_hr(text, jd_text, custom_skills)
            
            c_name = gemini_analysis.get("candidate_name")
            if not c_name or c_name == "Unknown": c_name = info.get('name') or "Unknown"
            
            c_email = gemini_analysis.get("email")
            if not c_email or c_email == "Unknown": c_email = info.get('email') or "Unknown"
            
            c_phone = gemini_analysis.get("phone")
            if not c_phone or c_phone == "Unknown": c_phone = info.get('phone') or "Unknown"
            
            results.append({
                "filename": file.filename,
                "category": category,
                "extracted_length": len(text),
                "candidate_name": c_name,
                "email": c_email,
                "phone": c_phone,
                "match_score": scaled_match_score,
                "matched_skills": skill_gap['matched_skills'],
                "missing_skills": skill_gap['missing_skills'],
                "summary": gemini_analysis.get("summary", ""),
                "career_progression": gemini_analysis.get("career_progression", ""),
                "career_timeline": timeline
            })
            
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
