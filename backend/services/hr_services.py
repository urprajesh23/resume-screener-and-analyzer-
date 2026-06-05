import json
from google.genai import types
from backend.services.gemini_service import get_model, generate_with_retry

def generate_candidate_email(candidate_name: str, score: float, matched: list, missing: list, email_type: str) -> str:
    model = get_model()
    
    prompt = f'''
You are an expert tech recruiter. Draft a highly professional email to the candidate.

Candidate Details:
- Name: {candidate_name}
- Match Score: {score}%
- Matched Skills: {", ".join(matched) if matched else "None"}
- Missing Skills/Gaps: {", ".join(missing) if missing else "None"}

Email Type: {email_type}
(Types can be: 'interview' [to invite them for an interview], 'info' [to ask for more details or updated resume], or 'rejection' [a polite rejection with constructive feedback citing their missing skills so they know what to improve])

Rules:
- Keep the tone polite, professional, and clear.
- Do not use placeholders (like [Recruiter Name]), sign off as "The Recruitment Team".
- In the rejection email, specify the missing skills in a helpful, constructive way.
- Return ONLY the raw body of the email. Do not include markdown code fences or subject headers.
'''
    try:
        response = generate_with_retry(model, prompt)
        return response.text.strip()
    except Exception as e:
        print("Error generating candidate email:", e)
        return f"Failed to draft email: {str(e)}"

def generate_interviewer_guide(resume_text: str, jd_text: str, candidate_name: str) -> dict:
    model = get_model()
    
    # Truncate text to save input tokens
    short_resume = resume_text[:3000]
    short_jd = jd_text[:1500] if jd_text else ""
    
    prompt = f'''
You are a senior technical interviewer. Generate a structured candidate-specific interview guide for a recruiter/technical lead interviewing {candidate_name}.
Use their Resume and the target Job Description to generate 5 targeted interview questions:
- 3 specific technical questions challenging their claimed projects or investigating their identified skill gaps (against the JD).
- 2 behavioral/situational questions to test their collaboration and project execution.

Inputs:
- Candidate Name: {candidate_name}
- Candidate Resume (Truncated): {short_resume}
- Job Description (Truncated): {short_jd}

For each question, provide:
1. The question.
2. The type (Technical or Behavioral).
3. The evaluation rubric and ideal response guidelines.

Return your response ONLY as a VALID JSON object matching this schema. No markdown headers or commentary:
{{
  "questions": [
    {{
      "question": "The interview question",
      "type": "Technical / Behavioral",
      "ideal_answer": "Highly detailed rubric and expected candidate answer markers"
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
        return json.loads(text.strip())
    except Exception as e:
        print("Error generating interviewer guide:", e)
        return {
            "questions": [
                {
                    "question": f"Based on your resume, can you explain your experience and how it aligns with our job requirements?",
                    "type": "Technical",
                    "ideal_answer": "Candidate should walk through their relevant projects and experience."
                }
            ]
        }

def generate_boolean_query(jd_text: str) -> dict:
    model = get_model()
    
    prompt = f'''
You are an expert talent sourcer. Analyze this Job Description (JD) and construct optimized Boolean Search strings to find relevant talent on external search engines.

Job Description:
{jd_text}

Generate Boolean strings for:
1. **LinkedIn**: Optimized for LinkedIn search bar (standard LinkedIn constraints, using OR, AND, and quotes for multi-word phrases).
2. **GitHub**: Targeted at Google search operators to find GitHub profile pages of developers with these skills.
3. **Google**: A general x-ray search query targeting portfolio sites or resume pages on web domains.

Return your response ONLY as a VALID JSON object matching this schema. No markdown headers or commentary:
{{
  "linkedin": "Boolean search string for LinkedIn",
  "github": "Boolean search string for GitHub",
  "google": "Boolean search string for Google"
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
        return json.loads(text.strip())
    except Exception as e:
        print("Error generating boolean query:", e)
        return {
            "linkedin": '("Software Engineer" OR "Developer") AND "Python"',
            "github": 'site:github.com "python" "developer"',
            "google": 'site:linkedin.com/in/ "python developer"'
        }
