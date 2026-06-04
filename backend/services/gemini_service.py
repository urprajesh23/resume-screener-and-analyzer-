import os
from google import genai
import json
import urllib.parse
import time
import threading

# Global rate limiter state
_last_request_time = 0.0
_rate_limit_lock = threading.Lock()

def _wait_for_rate_limit():
    global _last_request_time
    with _rate_limit_lock:
        current_time = time.time()
        # Enforce a 4.1-second delay between requests to stay safely under 15 RPM
        elapsed = current_time - _last_request_time
        if elapsed < 4.1:
            time.sleep(4.1 - elapsed)
        _last_request_time = time.time()

def generate_with_retry(model, prompt, max_retries=3):
    import re
    for attempt in range(max_retries):
        _wait_for_rate_limit()
        try:
            return model.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < max_retries - 1:
                match = re.search(r'retry in (\d+\.?\d*)s', error_str)
                delay = float(match.group(1)) + 1 if match else 35.0
                print(f"Rate limit hit. Retrying in {delay:.2f} seconds (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
            else:
                raise

def get_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise Exception("Gemini API key is not configured.")
    return genai.Client(api_key=api_key)

def generate_cover_letter(name: str, resume_text: str, jd_text: str) -> str:
    model = get_model()
    prompt = f"Write a professional, compelling cover letter for {name} based on this resume:\n{resume_text}\n\nTarget Job Description:\n{jd_text}\n\nDo not include placeholders, make it sound confident and highlight matching skills."
    return generate_with_retry(model, prompt).text

def boost_ats_score(resume_text: str, jd_text: str) -> str:
    model = get_model()
    prompt = f"Act as an ATS Optimization Expert. Analyze this resume against the JD.\nResume:\n{resume_text}\n\nJD:\n{jd_text}\n\n1. Provide an estimated ATS match score.\n2. Identify exactly which keywords are missing.\n3. Suggest 3 specific wording changes (e.g. Replace 'Did X' with 'Engineered X resulting in Y')."
    return generate_with_retry(model, prompt).text

def generate_interview_questions(resume_text: str, jd_text: str) -> str:
    model = get_model()
    prompt = f"Act as a Senior Hiring Manager. Based on the candidate's resume and the JD, generate 5 highly specific interview questions (3 technical/role-specific, 2 behavioral).\nResume:\n{resume_text}\n\nJD:\n{jd_text}\n\nProvide the questions, and briefly explain what a 'good answer' should include for each."
    return generate_with_retry(model, prompt).text

def build_resume(details: dict) -> str:
    model = get_model()
    prompt = f'''
You are an expert ATS resume writer. Based on the user's name, target job title, and experience, generate a complete ATS-optimized resume.

Return your response as a VALID JSON object only. No markdown, no explanation, no backticks. Strictly follow this schema:

{{
  "name": "string",
  "email": "string (use placeholder if not provided)",
  "phone": "string (use placeholder if not provided)",
  "linkedin": "string (use placeholder if not provided)",
  "summary": "2-3 sentence professional summary tailored to the job title",
  "skills": {{
    "languages": ["string"],
    "frameworks": ["string"],
    "tools": ["string"],
    "concepts": ["string"]
  }},
  "projects": [
    {{
      "name": "string",
      "tech": "string (tech stack used)",
      "year": "string",
      "bullets": ["string", "string", "string"]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "institution": "string",
      "year": "string"
    }}
  ],
  "certifications": ["string"]
}}

Candidate Details:
Name: {details.get('name', '')}
Email: {details.get('email', '')}
Phone: {details.get('phone', '')}
LinkedIn: {details.get('linkedin', '')}
Education: {details.get('education', '')}
Raw Experience & Projects: {details.get('experience', '')}
Target Job Title: {details.get('job_title', '')}
Target Job Description: {details.get('job_desc', '')}

Rules:
- Every bullet point must start with a strong action verb (Architected, Engineered, Designed, Deployed, etc.)
- Quantify achievements wherever possible (e.g., reduced latency by 40%, served 10k+ users)
- Tailor all content to the target job title provided
- Keep summary concise, keyword-rich, and ATS-friendly
- If any field data is missing, infer reasonable professional defaults based on the job title
'''
    try:
        response = generate_with_retry(model, prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    except Exception as e:
        print("Error in build_resume:", e)
        return "{}"


def career_coach_analysis(details: dict) -> str:
    model = get_model()
    prompt = f'''
You are an elite Career Coach and Tech Industry Expert. Analyze the candidate's current profile against their dream job.

Candidate's Current Role: {details.get('current_role', '')}
Candidate's Current Skills: {details.get('current_skills', '')}

Dream Job Title: {details.get('target_role', '')}
Dream Job Description:
{details.get('target_jd', '')}

Based on this, provide a highly structured, actionable coaching report formatted in clean Markdown. Include:
1. Market Trends
2. Skill Gap Analysis
3. Action Plan
4. Interview Tip

CRITICAL MARKDOWN RULES:
- If you use a table, you MUST use standard GitHub Flavored Markdown format.
- Only use ONE dashed separator row directly below the header (e.g. |---|---|).
- NEVER use horizontal dashed lines (like |---|) between normal rows or at the bottom of the table. This will break the UI parser!
'''
    return generate_with_retry(model, prompt).text

def project_idea_generator(skill: str, level: str) -> str:
    model = get_model()
    prompt = f"Act as a Senior Developer and Mentor. The user wants to learn {skill} to add to their resume. Their current level is {level}. Give them a step-by-step blueprint for a weekend portfolio project they can build to honestly claim this skill on their resume. Include architecture, tools needed, and steps."
    return generate_with_retry(model, prompt).text

def live_job_search(details: dict) -> list:
    model = get_model()
    prompt = f'''
Based on the candidate's detailed profile below, act as a Job Matcher AI.
Predict the top 10 exact job roles they are best suited for right now.

Candidate Skills: {details.get('skills', '')}
Target Role: {details.get('role', '')}
Work Type Preference: {details.get('work_type', '')}
Country: {details.get('country', '')}
State: {details.get('state', '')}
Locations: {details.get('locations', '')}

For each of the 10 recommended roles, provide a realistic example company type, and a short 1-sentence explanation of why it matches their profile.

Return ONLY a valid JSON array of 10 objects. Do not include markdown code fences (like ```json), just the raw JSON array.
Schema for each object:
{{
  "title": "Job Title Here",
  "company": "Example Company Type (e.g. Fintech Startup)",
  "match_reason": "Reason why it matches...",
  "location": "Best matching location from their list",
  "work_type": "Their preferred work type"
}}
'''
    try:
        response = generate_with_retry(model, prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        jobs = json.loads(text.strip())
        
        # Post-process to add dynamic search URLs from multiple trusted sources
        for i, job in enumerate(jobs):
            loc = f"{job.get('location', '')}, {details.get('state', '')}, {details.get('country', '')}"
            wt_is_remote = "home" in str(job.get('work_type', '')).lower()
            
            if i < 5:
                # 5 LinkedIn
                wt = "2" if wt_is_remote else ""
                query_params = {'keywords': job.get('title', ''), 'location': loc}
                if wt:
                    query_params['f_WT'] = wt
                query = urllib.parse.urlencode(query_params)
                job['search_url'] = f"https://www.linkedin.com/jobs/search/?{query}"
                job['platform'] = "LinkedIn"
            elif i < 8:
                # 3 Indeed
                q = job.get('title', '')
                if wt_is_remote:
                    q += " remote"
                query = urllib.parse.urlencode({'q': q, 'l': loc})
                job['search_url'] = f"https://www.indeed.com/jobs?{query}"
                job['platform'] = "Indeed"
            else:
                # 2 Google Jobs
                q = f"{job.get('title', '')} jobs in {loc}"
                if wt_is_remote:
                    q += " remote"
                query = urllib.parse.urlencode({'q': q})
                job['search_url'] = f"https://www.google.com/search?{query}&ibp=htl;jobs"
                job['platform'] = "Google"
            
        return jobs
    except Exception as e:
        print("Error in live_job_search:", e)
        return []

def analyze_resume_for_hr(resume_text: str, jd_text: str, custom_skills: str = "") -> dict:
    try:
        model = get_model()
    except Exception as e:
        print("Error initializing Gemini model for HR Analysis:", e)
        return {
            "candidate_name": "Unknown",
            "email": "Unknown",
            "phone": "Unknown",
            "match_score_percentage": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": "Analysis unavailable because the Gemini API key is not configured.",
            "career_progression": "Unknown",
            "career_timeline": []
        }

    prompt = f'''
You are an expert HR Applicant Tracking System evaluator.
Analyze the following candidate resume against the provided Job Description.

Candidate Resume:
{resume_text}

Target Job Description:
{jd_text}

Custom Required Skills (if any, prioritize these over JD skills):
{custom_skills}

Perform a comprehensive analysis and return the result ONLY as a valid JSON object with no markdown wrappers or formatting blocks. Use the exact following structure:
{{
  "candidate_name": "string",
  "email": "string",
  "phone": "string",
  "match_score_percentage": number (0-100 indicating semantic match quality),
  "matched_skills": ["string", "string"],
  "missing_skills": ["string", "string"],
  "summary": "A concise 2-sentence summary of the candidate's profile.",
  "career_progression": "A brief note on their role trajectory (e.g., '1 promotion from Intern to Developer').",
  "career_timeline": [
    {{"date": "Jan 2020 - Present", "context": "Software Engineer at TechCorp"}},
    {{"date": "2018 - 2020", "context": "Junior Developer at Startup"}}
  ]
}}

Ensure the JSON is strictly valid. Do NOT return anything outside the JSON object.
'''
    try:
        response = generate_with_retry(model, prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        import json
        return json.loads(text.strip())
    except Exception as e:
        print("Error in Gemini HR Analysis:", e)
        return {
            "candidate_name": "Unknown",
            "email": "Unknown",
            "phone": "Unknown",
            "match_score_percentage": 0,
            "matched_skills": [],
            "missing_skills": [],
            "summary": "Analysis failed due to AI API format error.",
            "career_progression": "Unknown",
            "career_timeline": []
        }
