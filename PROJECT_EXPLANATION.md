# 🚀 AI-Powered Resume Screener & Career Analyzer

## 📖 What is this project about?
This project is an advanced, dual-portal application designed to bridge the gap between job seekers (students) and recruiters (HR). 
- **For HR Professionals:** It acts as an automated Applicant Tracking System (ATS). Recruiters can upload dozens of resumes at once and instantly see a ranked leaderboard of candidates based on semantic match scores against a specific Job Description (JD).
- **For Students/Job Seekers:** It acts as a personal AI Career Coach. It analyzes their resume, identifies skill gaps, rewrites their resume to beat ATS systems, generates custom cover letters, provides mock interview prep, and dynamically searches for live jobs on platforms like LinkedIn and Indeed.

## 🎯 Problems Solved
1. **Manual Screening Fatigue:** HR professionals waste countless hours reading through hundreds of unqualified resumes. This system automates the shortlisting process in seconds.
2. **Bias in Hiring:** Traditional screening can be subject to human bias. By using mathematical cosine-similarity (comparing the mathematical meaning of the JD vs Resume), candidates are ranked objectively based purely on their skills and experience.
3. **The "Black Box" of ATS:** Students often get rejected by ATS software without knowing why. The Student Portal breaks open this black box, telling students exactly which keywords they are missing and how to fix their resume.
4. **Job Hunting Friction:** Instead of manually searching job boards, the Live Job Search uses AI to predict the exact job titles a student is suited for and instantly generates direct application links.

## 💻 Tech Stack Used
### Frontend (User Interface)
* **React.js (via Vite):** For building a blazingly fast, component-based user interface.
* **Vanilla CSS (Glassmorphism UI):** Custom styling using translucent backgrounds, gradients, and modern dark-mode aesthetics without relying on heavy UI libraries.
* **React Markdown:** To safely parse and render AI-generated markdown responses into beautiful HTML elements.

### Backend (Server & API)
* **Python & FastAPI:** Chosen for its extremely high performance and asynchronous capabilities, which are crucial when processing large PDF files and waiting for AI API responses.
* **Uvicorn:** ASGI server to run the FastAPI application.

### Artificial Intelligence & Machine Learning
* **Google Gemini Pro API:** Generative AI used for complex reasoning (e.g., writing cover letters, generating coaching reports, extracting names, predicting job roles).
* **Sentence-Transformers (MiniLM-L6-v2):** A powerful NLP model used to convert text into high-dimensional vectors (embeddings) to calculate semantic similarity.
* **Scikit-Learn (TF-IDF & Support Vector Classifier):** Used to automatically categorize resumes into fields (e.g., "Data Science", "Web Development") based on keyword frequencies.
* **spaCy:** Used for Named Entity Recognition (NER) to extract entities like names and dates from raw text.

---

## ⚙️ How Each Feature Works Technically

### 1. Resume Parsing & Data Extraction
When a file is uploaded, the backend uses `pdfminer` (for PDFs) or `docx2txt` (for Word docs) to extract raw text. It then uses regex to clean the text (removing special characters and excessive whitespaces). 

### 2. Candidate Ranking & Match Scoring (HR Portal)
Instead of just counting matching words, the system uses **Semantic Search**. It passes both the Resume text and the Job Description through a Sentence Transformer model to generate vector embeddings. It then calculates the **Cosine Similarity** between these two vectors. If the meaning of the resume closely aligns with the meaning of the JD, it receives a high score (0-100%).

### 3. Skill Gap Analysis
The system maintains a predefined list of hundreds of tech skills. It scans the parsed resume and the JD using regular expressions. By comparing the two lists using Python `sets`, it instantly calculates mathematical intersections (Matched Skills) and differences (Missing Skills).

### 4. Career Enhancer & ATS Booster (Student Portal)
These tools send the parsed resume text to the **Google Gemini API** along with highly engineered system prompts. Gemini is instructed to act as a career coach, evaluating the text and returning structured feedback. The backend formats this response and streams it back to the React frontend, where `react-markdown` styles it dynamically.

### 5. Live Job Search Matcher
The backend receives the user's location and skills, and prompts Gemini to predict 10 exact job roles they are qualified for. The Python backend then processes this JSON response and dynamically constructs URL queries. For example, it takes the job title and location, URL-encodes them, and concatenates them into a live `https://www.linkedin.com/jobs/search/` or `https://www.indeed.com/jobs` link.

---

## 🧠 Concepts to Learn if You Want to Build This
If you want to understand or recreate this architecture, you should study:
1. **Natural Language Processing (NLP):** Understand TF-IDF (Term Frequency-Inverse Document Frequency) and how text is converted into numbers.
2. **Vector Embeddings & Cosine Similarity:** Learn how AI models plot sentences as coordinates in space to measure how "close" (similar) they are to each other.
3. **Prompt Engineering:** Learn how to write robust, programmatic prompts for LLMs (like Gemini) to force them to return strict JSON arrays instead of conversational text.
4. **RESTful APIs & Async Programming:** Learn how FastAPI handles multiple simultaneous requests asynchronously, which is vital when processing heavy ML models.
5. **React State Management:** Understand how to manage complex UI states (loading spinners, active tabs, form data) using React hooks like `useState` and `useEffect`.

---

## 🌍 How It Impacts Real Life
This project creates a fairer, faster, and more transparent job market. 
For **companies**, it drastically reduces the "Time-to-Hire" metric, saving thousands of dollars in HR costs while ensuring they don't accidentally skip over a highly qualified candidate due to human fatigue. 
For **individuals**, especially those from non-traditional backgrounds or those who cannot afford professional career coaching, it provides an elite, free AI mentor. It levels the playing field by teaching them exactly how to market themselves, fix their resumes, and apply directly to jobs they are actually qualified for.
