# AI Resume Builder and Candidate Screening System

This document provides a comprehensive A-to-Z overview of the platform, detailing its architecture, data pipeline, and core features. It is designed to help anyone—from developers to recruiters—understand exactly how the project works and the value it provides.

---

## 🏗️ Project Architecture & Tech Stack

The platform is built on a modern, decoupled architecture designed for speed, scalability, and AI integration.

*   **Frontend:** React.js + JavaScript (Vite) - *Provides a sleek, responsive, glassmorphism-inspired UI.*
*   **Backend:** Python + FastAPI - *Handles file processing, ML model execution, and RESTful API endpoints.*
*   **AI/ML Engine:** 
    *   **Google Gemini API:** Generates content, summaries, and complex text analysis.
    *   **SentenceTransformers:** Calculates semantic cosine similarity for match scoring.
    *   **scikit-learn & TF-IDF:** Powers the SVM-based resume category classification.
    *   **spaCy & Regex:** Extracts precise entities like Names, Emails, Phones, and Dates.

---

## 🔄 The Project Pipeline

The application operates as a dual-sided marketplace tool, serving two distinct types of users: **Students (Job Seekers)** and **HR Professionals (Recruiters)**.

### Path A: The Student Pipeline (Career Development)
1.  **Input Collection:** The student enters their raw details (education, unpolished experience bullet points, target job title, and target job description).
2.  **AI Transformation:** The data is sent to the FastAPI backend, where the Gemini API processes the raw inputs and restructures them into a highly professional, ATS-optimized format.
3.  **Ancillary Services:** The student can then trigger secondary pipelines to generate a tailored cover letter, receive career coaching advice, or generate a portfolio project idea based on their current skill level.

### Path B: The HR Pipeline (Candidate Screening)
1.  **Batch Upload:** The HR professional uploads multiple candidate resumes (PDF, DOCX, TXT, or Image) and pastes the target Job Description (JD) and any mandatory skills.
2.  **Text Extraction:** The backend parses the files. For standard documents, it uses `PyPDF2` and `python-docx`. For images, it uses Gemini's Vision capabilities to extract text via OCR.
3.  **Data Cleaning & Categorization:** The raw text is sanitized to remove special characters and URLs. An ML model (TF-IDF + SVM) predicts the candidate's domain (e.g., "Data Science", "Network Security").
4.  **Semantic Match Scoring:** `SentenceTransformers` encodes both the resume and the JD into vector embeddings, calculating the cosine similarity to generate an accurate, semantic "Match Score" percentage.
5.  **Information Extraction:** 
    *   `spaCy` and Regex extract contact info (Name, Email, Phone) and chronological Career Timelines.
    *   The system cross-references the resume text against a database of technical skills to generate a Skill Gap Analysis.
6.  **AI Summarization:** Gemini generates a concise 2-sentence summary and career progression note for the candidate.
7.  **Leaderboard Rendering:** The React frontend receives the structured JSON data and renders a ranked leaderboard, allowing HR to expand each candidate and view their detailed profile, timelines, and skill gaps.

---

## 🚀 Core Features & Their Uses

### For Students (Job Seekers)
*   **AI Resume Builder:** 
    *   *Use:* Turns messy, poorly written experience points into professional, action-oriented bullet points tailored to beat Applicant Tracking Systems (ATS).
*   **Dynamic Cover Letter Generator:** 
    *   *Use:* Instantly writes a compelling, personalized cover letter based on the user's specific resume and the target job description.
*   **AI Career Coach:** 
    *   *Use:* Analyzes the user's current skills against their dream job, providing a structured action plan, market trends, and specific interview tips to bridge the gap.
*   **Portfolio Project Generator:** 
    *   *Use:* Recommends step-by-step weekend projects tailored to the user's skill level so they can legitimately add missing technical skills to their resume.

### For HR (Recruiters)
*   **Automated Resume Leaderboard:** 
    *   *Use:* Automatically ranks dozens of resumes from highest match to lowest, ensuring recruiters focus their time on the most qualified candidates first.
*   **Semantic Match Scoring:** 
    *   *Use:* Goes beyond simple keyword matching. It understands the *context* of the candidate's experience and the JD to provide a highly accurate percentage score.
*   **Automated Skill Gap Analysis:** 
    *   *Use:* Visually separates "Matched Skills" (what the candidate has) from "Missing Skills" (what the JD requires but the candidate lacks), providing instant clarity on technical fit.
*   **Chronological Career Timeline:** 
    *   *Use:* Automatically extracts dates and roles, sorting them in reverse-chronological order, so HR can instantly spot employment gaps or job-hopping without reading the full text.
*   **AI Candidate Summaries:** 
    *   *Use:* Provides a 2-sentence "elevator pitch" of the candidate generated by AI, saving the recruiter from having to read the entire document to understand the candidate's background.
