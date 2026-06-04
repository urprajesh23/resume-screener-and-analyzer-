from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.models.schemas import (
    ResumeBuilderRequest, CareerCoachRequest, JobSearchRequest,
    CoverLetterRequest, ATSBoosterRequest, InterviewPrepRequest, ProjectIdeaRequest
)
import backend.services.gemini_service as gemini_service
import backend.services.resume_parser as resume_parser

router = APIRouter()

@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    try:
        text = await resume_parser.handle_file_upload(file)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/build-resume")
async def build_resume(request: ResumeBuilderRequest):
    try:
        result = gemini_service.build_resume(request.dict())
        return {"resume_text": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/career-coach")
async def career_coach(request: CareerCoachRequest):
    try:
        result = gemini_service.career_coach_analysis(request.dict())
        return {"report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/job-search")
async def job_search(request: JobSearchRequest):
    try:
        jobs = gemini_service.live_job_search(request.dict())
        return {"jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cover-letter")
async def cover_letter(request: CoverLetterRequest):
    try:
        result = gemini_service.generate_cover_letter(request.name, request.resume_text, request.jd_text)
        return {"cover_letter": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ats-booster")
async def ats_booster(request: ATSBoosterRequest):
    try:
        result = gemini_service.boost_ats_score(request.resume_text, request.jd_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interview-prep")
async def interview_prep(request: InterviewPrepRequest):
    try:
        result = gemini_service.analyze_interview_prep(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/project-idea")
async def project_idea(request: ProjectIdeaRequest):
    try:
        result = gemini_service.project_idea_generator(request.skill, request.level)
        return {"blueprint": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
