from pydantic import BaseModel
from typing import Optional

class ResumeBuilderRequest(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: Optional[str] = None
    education: str
    experience: str
    job_title: str
    job_desc: str

class CareerCoachRequest(BaseModel):
    current_role: str
    current_skills: str
    target_role: str
    target_jd: str

class JobSearchRequest(BaseModel):
    skills: str
    role: str
    work_type: str
    country: str
    state: str
    locations: str

class CoverLetterRequest(BaseModel):
    name: str
    resume_text: str
    jd_text: str

class ATSBoosterRequest(BaseModel):
    resume_text: str
    jd_text: str

class InterviewPrepRequest(BaseModel):
    resume_text: str
    jd_text: str
    company_name: Optional[str] = None
    role: Optional[str] = None

class ProjectIdeaRequest(BaseModel):
    skill: str
    level: str
