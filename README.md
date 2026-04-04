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
- rebuild_clf.py: Reproducible training script that creates all model artifacts
- UpdatedResumeDataSet.csv: Training dataset
- job_description.txt: Sample job description for testing
- skills.txt: Sample comma-separated skills for testing

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
python rebuild_clf.py
```

This creates:

- tfidf.pkl
- encoder.pkl
- clf.pkl

4. Run the app.

```powershell
streamlit run app.py
```

## Testing Instructions

Use the included files for a quick demo test:

1. Open job_description.txt and copy its content into the Job Description field in the app sidebar.
2. Open skills.txt and copy its comma-separated list into the Required Skills field in the app sidebar.
3. Upload a test resume (PDF, DOCX, or TXT) to check match score and skill coverage.

You can also use the combined reference file "Job Description & Skills for Res.txt" for additional test cases.

## Notes

- If model files are missing, run `python rebuild_clf.py` again.
- Notebook execution is optional for experimentation; it is not required to run the application.
