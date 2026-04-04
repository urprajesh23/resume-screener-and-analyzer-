# Resume Screening ATS

AI-powered ATS dashboard that classifies resumes, compares candidates against a job description, analyzes skill gaps, and extracts candidate insights using NLP and machine learning.

## Features

- Resume upload support for PDF, DOCX, and TXT
- Resume category prediction with TF-IDF + SVM
- Semantic JD match scoring with sentence embeddings
- Skill gap analysis with default or custom required skills
- Candidate info extraction (name, email, phone)
- Career progression and timeline analysis
- Single and multi-candidate evaluation dashboard

## Project Files

- app.py: Streamlit application
- scripts/rebuild_clf.py: Reproducible training script that creates all model artifacts
- data/UpdatedResumeDataSet.csv: Training dataset
- data/testing/job_description.txt: Sample job description for testing
- data/testing/skills.txt: Sample comma-separated skills for testing
- data/sample_resumes/: Sample resumes for testing
- models/: Generated model artifacts (created after training)
- notebooks/Resume Screening with Python.ipynb: Optional experimentation notebook

## Setup

1. Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r reqiurements.txt
```

3. Train and generate model artifacts.

```powershell
python scripts/rebuild_clf.py
```

This creates:

- models/tfidf.pkl
- models/encoder.pkl
- models/clf.pkl

4. Run the app.

```powershell
streamlit run app.py
```

## Testing Instructions

Use the included files for a quick demo test:

1. Open data/testing/job_description.txt and copy its content into the Job Description field in the app sidebar.
2. Open data/testing/skills.txt and copy its comma-separated list into the Required Skills field in the app sidebar.
3. Upload a test resume (PDF, DOCX, or TXT) to check match score and skill coverage.

Recommended paired test cases:

1. Use data/testing/Job Description & Skills for Res.txt case for Resume 1 with data/sample_resumes/nlp_resume_1.pdf.
2. Use data/testing/Job Description & Skills for Res.txt case for Resume 2 with data/sample_resumes/nlp_resume_2.pdf.

Paths:

- data/testing/job_description.txt
- data/testing/skills.txt
- data/testing/Job Description & Skills for Res.txt
- data/sample_resumes/nlp_resume_1.pdf
- data/sample_resumes/nlp_resume_2.pdf

## Notes

- If model files are missing, run `python scripts/rebuild_clf.py` again.
- Notebook execution is optional for experimentation; it is not required to run the application.
