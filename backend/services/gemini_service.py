import os
from google import genai
from google.genai import types
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

def generate_with_retry(model, prompt, config=None, max_retries=3):
    import re
    for attempt in range(max_retries):
        _wait_for_rate_limit()
        try:
            return model.models.generate_content(model='gemini-2.5-flash', contents=prompt, config=config)
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

def boost_ats_score(resume_text: str, jd_text: str) -> dict:
    import backend.services.ml_service as ml_service
    model = get_model()
    
    # 1. Local parsing to find missing keywords
    skills_gap = ml_service.analyze_skill_gap(resume_text, jd_text)
    missing_skills = skills_gap.get('missing_skills', [])
    
    # 2. Local semantic match score as a baseline anchor
    raw_similarity = ml_service.calculate_match_score(ml_service.clean_resume(resume_text), jd_text)
    local_score = ml_service.scale_match_score(raw_similarity)

    prompt = f'''
Act as an expert ATS (Applicant Tracking System) Optimization specialist.
Analyze the candidate's Resume against the Job Description (JD) and provide a highly targeted ATS score boost analysis in JSON format.

Inputs:
- Resume: {resume_text}
- Job Description: {jd_text}
- Locally Identified Missing Keywords: {json.dumps(missing_skills)}
- Local Similarity Match Score: {local_score}

Your task:
1. **Calculate hybrid ATS Score**: Formulate a final ATS Match Score (0 to 100) based on the local similarity match score and your own deep semantic evaluation. 
2. **Identify Missing Keywords**: Review the locally identified missing keywords and cross-reference them. Choose the top 10-15 most critical keywords/skills that are actually relevant to the role and missing in the resume text.
3. **Generate Professional Summary Rewrites**: Rewrite the candidate's professional summary to be highly optimized for the target role, integrating missing key terms naturally.
4. **Wording Replacements**: Identify 3 to 5 specific sentences or bullet points in the raw Resume that are weak, and suggest high-impact rewrites for each. Each replacement must specify:
   - "original": The exact text from the resume (MUST match a substring in the resume exactly so it can be replaced automatically).
   - "suggested": The new optimized bullet point integrating missing keywords.
   - "reason": Rationale for the change.

Return your response ONLY as a VALID JSON object matching this schema. No markdown headers or commentary:
{{
  "ats_score": 75,
  "missing_keywords": ["MLOps", "CI/CD", "Docker"],
  "new_summary": "ATS-optimized professional summary...",
  "suggestions": [
    {{
      "original": "Exact text from original resume",
      "suggested": "Optimized text with action verbs and metrics",
      "reason": "Why this change is suggested"
    }}
  ]
}}
'''
    try:
        config = types.GenerateContentConfig(response_mime_type="application/json")
        response = generate_with_retry(model, prompt, config=config)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        import re
        try:
            return json.loads(text)
        except Exception:
            cleaned = re.sub(r'^.*?{', '{', text, flags=re.DOTALL)
            cleaned = re.sub(r'}.*?$', '}', cleaned, flags=re.DOTALL)
            return json.loads(cleaned)
    except Exception as e:
        print("Error in boost_ats_score:", e)
        return {
            "ats_score": int(local_score),
            "missing_keywords": missing_skills[:10],
            "new_summary": "Failed to generate optimized summary.",
            "suggestions": []
        }

def analyze_interview_prep(details: dict) -> dict:
    import backend.services.ml_service as ml_service
    model = get_model()
    resume_text = details.get("resume_text", "")
    jd_text = details.get("jd_text", "")
    company_name = details.get("company_name", "") or ""
    role = details.get("role", "") or ""

    evidence = ml_service.extract_evidence_and_keywords(resume_text)
    evidence_json = json.dumps(evidence, indent=2)

    company_clause = f" specifically for the company '{company_name}' and role '{role}'" if (company_name or role) else ""
    prompt = f'''
Act as an expert technical recruiter and senior interviewer.
Analyze the candidate's Resume against the Job Description (JD) and provide a comprehensive interview prep and domain analysis package using a hybrid evaluation approach.

Inputs:
- Resume: {resume_text}
- Job Description: {jd_text}
- Target Company: {company_name or "General / Unspecified"}
- Target Role: {role or "Target Role based on JD"}

Locally Extracted Evidence & Keyword Matches (for validation):
{evidence_json}

Your task:
1. **Domain Strength Scoring**: Identify 3 to 5 core domains required by the Job Description (e.g. Machine Learning, Cloud Systems, Frontend Web, Backend API, Databases). 
   Score the candidate from 0 to 100 on how strong they are in each domain using a hybrid evaluation:
   - Carefully review the raw Resume and cross-reference it with the "Locally Extracted Evidence & Keyword Matches" provided above.
   - A domain (especially highly specialized fields like Machine Learning, AI, Deep Learning, computer vision, etc.) MUST receive a high/good score (70+) ONLY if the candidate's resume shows explicit, concrete evidence of projects, certifications, or awards in that field.
   - If the candidate lists the domain/skill as a buzzword in a skills list but has 0 corresponding projects, certifications, or awards, or if the local matches show minimal evidence, you MUST assign a lower score (below 50).
   - For each domain, explain your scoring rationale in a short sentence, explicitly citing the specific projects, certifications, or awards found (e.g., 'Scored 85 because they have a Coursera Neural Networks certificate and built a CNN Classifier project'). If no concrete projects or certificates are present, explain that the score is low due to a lack of hands-on evidence.
2. **Simplified Focus Suggestions**: Based on the domain scores, suggest 2 to 4 actionable focus areas/topics the candidate needs to develop to cover their gaps.
3. **Interview Q&A Prep**: Generate interview questions and detailed answers/model response guides.
   - If a target company or role is specified, generate 10 to 15 highly important, company-specific and role-specific past interview questions with answers.
   - If no company/role is specified, generate 5 to 7 highly specific role-based technical and behavioral questions with model answers.

Return your response ONLY as a VALID JSON object matching this schema exactly. No markdown headers or wrapper commentary other than the json block wrapper:
{{
  "domain_scores": [
    {{
      "domain": "Domain Name (e.g., Machine Learning)",
      "score": 85,
      "reason": "Rationale referencing specific resume items"
    }}
  ],
  "focus_areas": [
    "Simplified actionable suggestion on what topics/skills/projects to learn or build"
  ],
  "interview_questions": [
    {{
      "question": "The interview question",
      "answer": "Highly detailed response guide and model answer"
    }}
  ]
}}
'''
    try:
        config = types.GenerateContentConfig(response_mime_type="application/json")
        response = generate_with_retry(model, prompt, config=config)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Clean trailing issues if any
        import re
        try:
            return json.loads(text)
        except Exception:
            cleaned = re.sub(r'^.*?{', '{', text, flags=re.DOTALL)
            cleaned = re.sub(r'}.*?$', '}', cleaned, flags=re.DOTALL)
            return json.loads(cleaned)
    except Exception as e:
        print("Error in analyze_interview_prep:", e)
        # Fallback response so frontend doesn't crash
        return {
            "domain_scores": [{"domain": "Analysis Failed", "score": 0, "reason": str(e)}],
            "focus_areas": ["Retry generating your interview prep report."],
            "interview_questions": [{"question": "Failed to load questions", "answer": "Please verify your configuration and try again."}]
        }

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
