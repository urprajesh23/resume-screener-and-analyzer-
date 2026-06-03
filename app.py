import textwrap
# you need to install all these in your terminal
# pip install streamlit
# pip install scikit-learn
# pip install python-docx
# pip install PyPDF2


import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from io import BytesIO

# Load environment variables
load_dotenv()

# Configure Gemini once at startup with the API key from .env
_gemini_api_key = os.getenv("GEMINI_API_KEY")
if _gemini_api_key and _gemini_api_key != "your_gemini_api_key_here":
    genai.configure(api_key=_gemini_api_key)

import pickle
import docx  # Extract text from Word file
import PyPDF2  # Extract text from PDF
import re
from html import escape
import textwrap
# you need to install all these in your terminal
# pip install streamlit
# pip install scikit-learn
# pip install python-docx
# pip install PyPDF2


import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from io import BytesIO

# Load environment variables
load_dotenv()

# Configure Gemini once at startup with the API key from .env
_gemini_api_key = os.getenv("GEMINI_API_KEY")
if _gemini_api_key and _gemini_api_key != "your_gemini_api_key_here":
    genai.configure(api_key=_gemini_api_key)

import pickle
import docx  # Extract text from Word file
import PyPDF2  # Extract text from PDF
import re
from html import escape
from pathlib import Path
from PIL import Image
from sentence_transformers import SentenceTransformer, util
import spacy
import pandas as pd
from transformers import pipeline
import urllib.parse
import markdown

def markdown_to_styled_html(text):
    # Remove code fences if any
    text = text.replace('```html', '').replace('```', '')
    
    # Convert markdown to HTML using the markdown library
    html = markdown.markdown(
        text,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    
    # Style the tables
    html = html.replace(
        '<table>',
        '<table style="width:100%;border-collapse:collapse;margin:16px 0;">'
    )
    html = html.replace(
        '<th>',
        '<th style="border:1px solid #334155;padding:12px;background:#1e293b;color:#a78bfa;text-align:left;">'
    )
    html = html.replace(
        '<td>',
        '<td style="border:1px solid #334155;padding:10px;color:#e2e8f0;">'
    )
    
    # Style headings
    html = re.sub(
        r'<h1>(.*?)</h1>',
        r'<h1 style="color:#a78bfa;border-bottom:2px solid #7c3aed;padding-bottom:10px;margin-top:24px;">\1</h1>',
        html
    )
    html = re.sub(
        r'<h2>(.*?)</h2>',
        r'<h2 style="color:#a78bfa;border-bottom:1px solid #7c3aed;padding-bottom:8px;margin-top:20px;">\1</h2>',
        html
    )
    html = re.sub(
        r'<h3>(.*?)</h3>',
        r'<h3 style="color:#818cf8;margin-top:16px;">\1</h3>',
        html
    )
    html = re.sub(
        r'<h4>(.*?)</h4>',
        r'<h4 style="color:#c4b5fd;margin-top:12px;">\1</h4>',
        html
    )
    
    # Style lists
    html = html.replace(
        '<ul>',
        '<ul style="padding-left:20px;line-height:2;">'
    )
    html = html.replace(
        '<li>',
        '<li style="margin-bottom:6px;color:#cbd5e1;">'
    )
    
    # Style paragraphs
    html = html.replace(
        '<p>',
        '<p style="color:#cbd5e1;line-height:1.8;margin:10px 0;">'
    )
    
    # Style hr
    html = html.replace(
        '<hr />',
        '<hr style="border:none;border-top:1px solid #334155;margin:24px 0;">'
    )
    html = html.replace(
        '<hr>',
        '<hr style="border:none;border-top:1px solid #334155;margin:24px 0;">'
    )
    
    # Color gap level keywords
    html = html.replace(
        'Critical',
        '<span style="color:#f87171;font-weight:bold;">Critical</span>'
    )
    html = html.replace(
        'High',
        '<span style="color:#fb923c;font-weight:bold;">High</span>'
    )
    html = html.replace(
        'Medium',
        '<span style="color:#facc15;font-weight:bold;">Medium</span>'
    )
    html = html.replace(
        'Low',
        '<span style="color:#4ade80;font-weight:bold;">Low</span>'
    )
    
    return html

def sanitize_html_response(text):
    """
    Strip stray markdown artifacts that Gemini sometimes emits even when asked for pure HTML.
    The prompt already instructs Gemini to return fully-styled HTML, so we only need to
    clean up the wrapper noise — we do NOT re-process the content.
    """
    # Remove code fences (```html ... ``` or ``` ... ```)
    text = re.sub(r'```html?\s*', '', text)
    text = re.sub(r'```\s*', '', text)

    # Remove any bare markdown headings (## Heading) that slipped through
    text = re.sub(r'(?m)^#{1,6}\s+', '', text)

    # Remove bare **bold** markers that are outside HTML tags
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

    # Remove bare *italic* markers
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

    # Remove bare markdown horizontal rules (--- or ***)
    text = re.sub(r'(?m)^[-*]{3,}\s*$', '', text)

    return text.strip()

def _format_inline_markdown(text):
    """Escape unsafe text, then restore simple bold/italic emphasis."""
    text = escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'\b(Critical|High|Medium|Low)\b', lambda match: f'<span class="gap-badge gap-{match.group(1).lower()}">{match.group(1)}</span>', text)
    return text

def _split_markdown_table_row(line):
    line = line.strip().strip('|')
    return [cell.strip() for cell in line.split('|')]

def _is_markdown_table_separator(line):
    cells = _split_markdown_table_row(line)
    return bool(cells) and all(re.fullmatch(r':?-{3,}:?', cell) for cell in cells)

def _parse_markdown_table(lines, start_index):
    headers = _split_markdown_table_row(lines[start_index])
    rows = []
    index = start_index + 2

    while index < len(lines) and '|' in lines[index] and lines[index].strip():
        rows.append(_split_markdown_table_row(lines[index]))
        index += 1

    table_html = ['<div class="career-table-wrap"><table class="career-table"><thead><tr>']
    for header in headers:
        table_html.append(f'<th>{_format_inline_markdown(header)}</th>')
    table_html.append('</tr></thead><tbody>')

    for row in rows:
        table_html.append('<tr>')
        for cell in row[:len(headers)]:
            table_html.append(f'<td>{_format_inline_markdown(cell)}</td>')
        for _ in range(len(headers) - len(row)):
            table_html.append('<td></td>')
        table_html.append('</tr>')

    table_html.append('</tbody></table></div>')
    return ''.join(table_html), index

def format_career_coaching_response(text):
    """
    Convert Gemini's common Markdown output into clean HTML for the Career Enhancer.
    Handles headings, bullets, numbered lists, horizontal rules, and pipe tables.
    """
    text = text or ""
    text = re.sub(r'```html?\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    if re.search(r'<(div|h[1-6]|table|ul|ol|p|li)\b', text, re.IGNORECASE):
        return sanitize_html_response(text)
                                
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                                
        elif selected_feature == "🔍 Live Job & Internship Search":
            st.markdown("### 🔍 Live Job & Internship Search (Real-Time)")
            st.markdown("Enter your skills and preferences. Our AI will determine the exact 5 job titles you are best suited for, and automatically generate real-time search links filtered for the **latest** job postings.")
            
            with st.form("job_search_form"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    user_skills = st.text_area("Your Core Skills or Resume Summary", height=100)
                with col2:
                    location = st.text_input("Preferred Location (e.g., Remote, New York, London)", value="Remote")
                    job_type = st.radio("Looking For:", ["Internship", "Full-Time Job"])
                
                submit_search = st.form_submit_button("Find Latest Openings")
                
            if submit_search:
                if not user_skills:
                    st.error("Please enter your skills to get accurate job titles.")
                else:
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key or api_key == "your_gemini_api_key_here":
                        st.error("Gemini API key is not configured. Please add your real key to the .env file.")
                    else:
                        with st.spinner("Analyzing your profile to find the best job titles..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                
                                prompt = f'''
Based on the candidate's skills below, predict the top 5 exact job titles they are best suited for.
Return ONLY a comma-separated list of the 5 job titles. Do NOT include numbers, bullet points, or extra text.

Candidate Skills: {user_skills}
Target Type: {job_type}
'''
                                response = model.generate_content(prompt)
                                titles_raw = response.text
                                
                                # Parse the comma separated titles
                                titles = [t.strip() for t in titles_raw.split(',') if t.strip()]
                                # Fallback if Gemini formats weirdly
                                if len(titles) < 2:
                                    titles = [t.strip('- ').strip() for t in titles_raw.split('\\n') if t.strip()]
                                
                                # Take top 5
                                titles = titles[:5]
                                
                                st.success(f"Successfully identified your top {len(titles)} matching roles!")
                                st.markdown("### ⚡ Live Job Board Links (Filtered for Latest)")
                                
                                # Generate URLs for each title
                                for title in titles:
                                    st.markdown(f"#### 🎯 {title}")
                                    
                                    enc_title = urllib.parse.quote(title)
                                    enc_loc = urllib.parse.quote(location)
                                    
                                    # LinkedIn configuration
                                    # f_TPR=r86400 (Past 24 hours), f_E=1 (Internship) or f_E=2,3,4,5,6 (Full time)
                                    li_level = "1" if job_type == "Internship" else "2%2C3%2C4"
                                    linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={enc_title}&location={enc_loc}&f_TPR=r86400&f_E={li_level}"
                                    
                                    # Google Jobs URL (q=title+jobs+in+location)
                                    google_q = urllib.parse.quote(f"{title} {job_type.lower()}s in {location}")
                                    google_url = f"https://www.google.com/search?q={google_q}&ibp=htl;jobs#fpstate=tldetail&htivrt=jobs&htichips=date_posted:today"
                                    
                                    # Indeed URL (sort=date)
                                    indeed_url = f"https://www.indeed.com/jobs?q={enc_title}&l={enc_loc}&sort=date"
                                    
                                    st.markdown(f"""
                                    <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                                        <a href="{linkedin_url}" target="_blank" style="text-decoration: none;">
                                            <button style="background: #0077b5; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer;">
                                                Find on LinkedIn
                                            </button>
                                        </a>
                                        <a href="{google_url}" target="_blank" style="text-decoration: none;">
                                            <button style="background: #DB4437; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer;">
                                                Find on Google Jobs
                                            </button>
                                        </a>
                                        <a href="{indeed_url}" target="_blank" style="text-decoration: none;">
                                            <button style="background: #2164f4; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer;">
                                                Find on Indeed
                                            </button>
                                        </a>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    st.divider()
                                    
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                                

        elif selected_feature == "✉️ AI Cover Letter Generator":
            st.markdown("### ✉️ AI Cover Letter Generator")
            st.markdown("Instantly generate a highly personalized cover letter based on your resume and the target job description.")
            st.markdown("**1. Upload or Paste your Resume**")
            uploaded_cl_resume = st.file_uploader("Upload Resume (PDF, DOCX, TXT, Image)", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], key="cl_resume")
            
            with st.form("cl_form"):
                name = st.text_input("Your Name")
                resume_text = st.text_area("Or Paste Your Resume Summary / Full Text", height=150)
                jd_text = st.text_area("Target Job Description", height=150)
                submit_cl = st.form_submit_button("Generate Cover Letter")
                
            if submit_cl:
                final_resume_text = resume_text
                if uploaded_cl_resume:
                    try:
                        final_resume_text = handle_file_upload(uploaded_cl_resume) + "\n\n" + resume_text
                    except Exception as e:
                        st.error(f"Error parsing resume file: {str(e)}")
                        
                if not name or not final_resume_text.strip() or not jd_text:
                    st.error("Please fill in all fields (Provide a resume by uploading or pasting).")
                else:
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key or api_key == "your_gemini_api_key_here":
                        st.error("Gemini API key is not configured.")
                    else:
                        with st.spinner("Drafting a compelling cover letter..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                prompt = f"Write a professional, compelling cover letter for {name} based on this resume:\n{final_resume_text}\n\nTarget Job Description:\n{jd_text}\n\nDo not include placeholders, make it sound confident and highlight matching skills."
                                response = model.generate_content(prompt)
                                st.success("Cover Letter Generated!")
                                st.markdown("""<div style="background-color: rgba(30, 41, 59, 0.6); padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-top: 20px;">""", unsafe_allow_html=True)
                                st.markdown(response.text)
                                st.markdown("</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(str(e))
                                
        elif selected_feature == "⚡ ATS Resume Score Booster":
            st.markdown("### ⚡ ATS Resume Score Booster")
            st.markdown("Get specific, line-by-line wording suggestions to optimize your resume for ATS tracking.")
            st.markdown("**1. Upload or Paste your Resume**")
            uploaded_ats_resume = st.file_uploader("Upload Resume (PDF, DOCX, TXT, Image)", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], key="ats_resume")
            
            with st.form("ats_form"):
                resume_text = st.text_area("Or Paste your Current Resume text", height=200)
                jd_text = st.text_area("Paste the Target Job Description", height=150)
                submit_ats = st.form_submit_button("Analyze & Boost Score")
                
            if submit_ats:
                final_resume_text = resume_text
                if uploaded_ats_resume:
                    try:
                        final_resume_text = handle_file_upload(uploaded_ats_resume) + "\n\n" + resume_text
                    except Exception as e:
                        st.error(f"Error parsing resume file: {str(e)}")
                        
                if not final_resume_text.strip() or not jd_text:
                    st.error("Please provide both Resume (upload or paste) and Job Description.")
                else:
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key or api_key == "your_gemini_api_key_here":
                        st.error("Gemini API key is not configured.")
                    else:
                        with st.spinner("Analyzing keywords and formatting..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                prompt = f"Act as an ATS Optimization Expert. Analyze this resume against the JD.\nResume:\n{final_resume_text}\n\nJD:\n{jd_text}\n\n1. Provide an estimated ATS match score.\n2. Identify exactly which keywords are missing.\n3. Suggest 3 specific wording changes (e.g. Replace 'Did X' with 'Engineered X resulting in Y')."
                                response = model.generate_content(prompt)
                                st.success("Optimization Report Ready!")
                                st.markdown("""<div style="background-color: rgba(30, 41, 59, 0.6); padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-top: 20px;">""", unsafe_allow_html=True)
                                st.markdown(response.text)
                                st.markdown("</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(str(e))

        elif selected_feature == "🎤 AI Mock Interview Prep":
            st.markdown("### 🎤 AI Mock Interview Prep")
            st.markdown("Generate highly specific interview questions based on the intersection of your resume and the target job.")
            st.markdown("**1. Upload or Paste your Resume**")
            uploaded_interview_resume = st.file_uploader("Upload Resume (PDF, DOCX, TXT, Image)", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], key="int_resume")
            
            with st.form("interview_form"):
                resume_text = st.text_area("Or Paste Your Resume Summary", height=150)
                jd_text = st.text_area("Target Job Description", height=150)
                submit_interview = st.form_submit_button("Generate Interview Questions")
                
            if submit_interview:
                final_resume_text = resume_text
                if uploaded_interview_resume:
                    try:
                        final_resume_text = handle_file_upload(uploaded_interview_resume) + "\n\n" + resume_text
                    except Exception as e:
                        st.error(f"Error parsing resume file: {str(e)}")
                        
                if not final_resume_text.strip() or not jd_text:
                    st.error("Please provide both Resume (upload or paste) and Job Description.")
                else:
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key or api_key == "your_gemini_api_key_here":
                        st.error("Gemini API key is not configured.")
                    else:
                        with st.spinner("Preparing your custom interview panel..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                prompt = f"Act as a Senior Hiring Manager. Based on the candidate's resume and the JD, generate 5 highly specific interview questions (3 technical/role-specific, 2 behavioral).\nResume:\n{final_resume_text}\n\nJD:\n{jd_text}\n\nProvide the questions, and briefly explain what a 'good answer' should include for each."
                                response = model.generate_content(prompt)
                                st.success("Questions Generated! Time to practice.")
                                st.markdown("""<div style="background-color: rgba(30, 41, 59, 0.6); padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-top: 20px;">""", unsafe_allow_html=True)
                                st.markdown(response.text)
                                st.markdown("</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(str(e))
                                
        elif selected_feature == "🏗️ Project Idea Generator":
            st.markdown("### 🏗️ Project Idea Generator")
            st.markdown("Missing a crucial skill required by a job? Let AI generate a weekend portfolio project to help you learn it fast.")
            
            with st.form("project_form"):
                skill = st.text_input("Target Skill to Learn (e.g., AWS, React, Docker)")
                level = st.selectbox("Your Current Level", ["Complete Beginner", "Some Knowledge", "Intermediate"])
                submit_project = st.form_submit_button("Generate Project Blueprint")
                
            if submit_project:
                if not skill:
                    st.error("Please enter a skill.")
                else:
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key or api_key == "your_gemini_api_key_here":
                        st.error("Gemini API key is not configured.")
                    else:
                        with st.spinner("Architecting your project..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                prompt = f"Act as a Senior Developer and Mentor. The user wants to learn {skill} to add to their resume. Their current level is {level}. Give them a step-by-step blueprint for a weekend portfolio project they can build to honestly claim this skill on their resume. Include architecture, tools needed, and steps."
                                response = model.generate_content(prompt)
                                st.success("Project Blueprint Generated!")
                                st.markdown("""<div style="background-color: rgba(30, 41, 59, 0.6); padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-top: 20px;">""", unsafe_allow_html=True)
                                st.markdown(response.text)
                                st.markdown("</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(str(e))

        return
    # --- IF HR, CONTINUE WITH EXISTING APP ---


    # ===== PREMIUM UI INJECTION =====
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stApp {
        background-color: #0B0E14 !important;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.08), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(236, 72, 153, 0.08), transparent 25%);
        color: #F3F4F6 !important;
    }

    h1 {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #A5B4FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.04em !important;
    }
    
    h2 { font-size: 1.8rem !important; }
    h3 { font-size: 1.5rem !important; }

    /* Sidebar sizing */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Enlarge Form Labels */
    [data-testid="stWidgetLabel"] p, .stTextInput label p, .stTextArea label p, .stSelectbox label p {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        margin-bottom: 5px !important;
    }

    /* Bigger Inputs */
    .stTextArea textarea, .stTextInput input {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
        padding: 16px !important;
        line-height: 1.5 !important;
    }
    .stTextArea textarea {
        height: 250px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.4) !important;
    }

    /* Expander size bump */
    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
    }
    [data-testid="stExpander"] summary {
        padding: 16px !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stExpander"] summary p {
        font-size: 1.2rem !important; 
        font-weight: 700 !important;
    }

            /* Space before Tabs */
    [data-testid="stTabs"] {
        margin-top: 48px !important;
    }

    /* Tabs size bump */
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 99px !important;
        padding: 16px 32px !important; /* Enlarged padding */
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin-right: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    /* Target the text inside the tab */
    [data-testid="stTabs"] button[role="tab"] p, [data-testid="stTabs"] button[role="tab"] div {
        font-size: 1.5rem !important; /* Enlarged font */
        font-weight: 700 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #6366F1 0%, #EC4899 100%) !important;
        box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4) !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
        color: #FFFFFF !important;
    }

            /* Boxed Metrics */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.6) !important;
        padding: 24px !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    
    /* Metrics Sizes Adjusted based on user preference */
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div, [data-testid="stMetricValue"] p {
        font-size: 1.6rem !important; /* Values slightly smaller or equal */
        font-weight: 600 !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        color: #FFFFFF !important;
        width: 100% !important;
        text-align: center !important;
        justify-content: center !important;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] > div, [data-testid="stMetricLabel"] p, [data-testid="stMetricLabel"] label {
        font-size: 2.0rem !important; /* Labels significantly enlarged */
        font-weight: 800 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        color: #A5B4FC !important;
        width: 100% !important;
        text-align: center !important;
        justify-content: center !important;
        margin-bottom: 8px !important;
    }

    /* Hide standard dataframe to enforce our html one */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 12px 24px !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)


    # ===== MAIN DASHBOARD HEADER =====
    st.title("💼 Enterprise Applicant Tracking System")
    st.markdown("""
    **AI-Powered Resume Screening & Analysis Platform**  
    Upload candidate resumes, paste job descriptions, and get instant insights on candidate fit, 
    skill gaps, and actionable hiring recommendations.
    """)
    st.divider()

    # ===== SIDEBAR CONTROLS =====
    st.sidebar.title("⚙️ ATS Control Panel")
    
    # Add Exit Button for HR
    if st.sidebar.button("🚪 Exit HR Session", key="exit_hr"):
        st.session_state.role = None
        st.rerun()
        
    st.sidebar.divider()
    st.sidebar.markdown("Configure your screening parameters below:")
    
    # File uploader in sidebar - ACCEPTS MULTIPLE FILES
    uploaded_files = st.sidebar.file_uploader(
        "📤 Upload Candidate Resume(s)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload one or multiple resumes in PDF, DOCX, TXT, or Image format"
    )
    
    # Job Description in expandable section
    jd_text = ""
    with st.sidebar.expander("📝 Enter Job Description", expanded=False):
        jd_text = st.text_area(
            "Paste Job Description",
            height=250,
            placeholder="Paste the complete job description here to enable match scoring and skill gap analysis...",
            key="jd_input"
        )
    
    # Custom skills override in expandable section
    custom_skills_input = ""
    with st.sidebar.expander("🎯 Define Required Skills", expanded=False):
        st.markdown("**Optional:** Override default skill list")
        custom_skills_input = st.text_input(
            "Enter comma-separated skills",
            placeholder="e.g., Python, AWS, Machine Learning, Agile",
            help="Leave blank to use default skill library",
            key="custom_skills"
        )
    
    st.sidebar.divider()
    st.sidebar.markdown("---")
    st.sidebar.caption("🤖 Powered by ML & NLP")

    # ===== MAIN CONTENT AREA =====
    if uploaded_files is not None and len(uploaded_files) > 0:
        
        # ===== BATCH PROCESSING MODE (MULTIPLE RESUMES) =====
        if len(uploaded_files) > 1 and jd_text.strip():
            st.success(f"📊 Processing {len(uploaded_files)} candidates against Job Description...")
            
            # List to store all candidate results
            candidates_data = []
            
            # Process each resume
            for uploaded_file in uploaded_files:
                try:
                    # Extract and clean text
                    resume_text = handle_file_upload(uploaded_file)
                    cleaned_resume_text = cleanResume(resume_text)
                    
                    # Extract candidate info
                    candidate_info = extract_candidate_info(resume_text)
                    
                    # Predict category
                    category = pred(resume_text)
                    
                    # Calculate match score
                    cleaned_jd_text = cleanResume(jd_text)
                    raw_match_score = calculate_match_score(cleaned_resume_text, cleaned_jd_text)
                    scaled_match_score = scale_match_score(raw_match_score)
                    category_name, category_color = get_match_category(scaled_match_score)
                    
                    # Skill gap analysis
                    if custom_skills_input.strip():
                        skill_analysis = analyze_custom_skill_gap(resume_text, custom_skills_input)
                    else:
                        skill_analysis = analyze_skill_gap(resume_text, jd_text)
                    
                    # Calculate skill coverage
                    if skill_analysis['jd_skills']:
                        skill_coverage = (len(skill_analysis['matched_skills']) / len(skill_analysis['jd_skills'])) * 100
                    else:
                        skill_coverage = 0
                    
                    # Store candidate data
                    candidates_data.append({
                        'Filename': uploaded_file.name,
                        'Candidate Name': candidate_info['name'] if candidate_info['name'] else 'N/A',
                        'Email': candidate_info['email'] if candidate_info['email'] else 'N/A',
                        'Phone': candidate_info['phone'] if candidate_info['phone'] else 'N/A',
                        'Predicted Category': category,
                        'Match Score': scaled_match_score,
                        'Match Category': category_name,
                        'Skill Coverage': skill_coverage,
                        'Matched Skills Count': len(skill_analysis['matched_skills']),
                        'Missing Skills Count': len(skill_analysis['missing_skills']),
                        'Matched Skills': ', '.join(skill_analysis['matched_skills']) if skill_analysis['matched_skills'] else 'None',
                        'Missing Skills': ', '.join(skill_analysis['missing_skills']) if skill_analysis['missing_skills'] else 'None',
                        'Resume Text': resume_text,
                        'Cleaned Text': cleaned_resume_text,
                        'Skill Analysis': skill_analysis
                    })
                    
                except Exception as e:
                    st.warning(f"⚠️ Error processing {uploaded_file.name}: {str(e)}")
            
            # Create DataFrame and sort by Match Score (descending)
            if candidates_data:
                df = pd.DataFrame(candidates_data)
                df = df.sort_values('Match Score', ascending=False).reset_index(drop=True)
                
                # ===== LEADERBOARD DISPLAY =====
                st.subheader("🏆 Candidate Leaderboard")
                st.markdown("**All candidates ranked by Job Description match score (highest to lowest)**")
                
                # Display summary dataframe
                display_df = df[[
                    'Filename', 
                    'Candidate Name',
                    'Predicted Category', 
                    'Match Score', 
                    'Match Category',
                    'Skill Coverage',
                    'Matched Skills Count',
                    'Missing Skills Count'
                ]].copy()
                
                # Custom HTML Leaderboard (dedented)
                html_table = textwrap.dedent("""
                <div style='overflow-x: auto;'>
                    <table style='width: 100%; border-collapse: separate; border-spacing: 0 12px; font-family: Outfit, sans-serif;'>
                    <thead>
                        <tr style='color: #94A3B8; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px;'>
                            <th style='padding: 0 24px; text-align: left;'>Candidate</th>
                            <th style='text-align: left;'>Category</th>
                            <th style='text-align: center;'>Match Score</th>
                            <th style='text-align: center;'>Skill Coverage</th>
                        </tr>
                    </thead>
                    <tbody>
                """)
                for i, row_l in df.iterrows():
                    rank_medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "👤"
                    score_color = "#10B981" if row_l['Match Score'] >= 80 else "#F59E0B" if row_l['Match Score'] >= 50 else "#EF4444"
                    html_table += textwrap.dedent(f"""
                    <tr style='background: rgba(30, 41, 59, 0.5); backdrop-filter: blur(12px); box-shadow: 0 4px 16px rgba(0,0,0,0.15); transition: transform 0.2s ease;'>
                        <td style='padding: 20px 24px; border-top-left-radius: 16px; border-bottom-left-radius: 16px; font-size: 1.2rem; font-weight: 700; color: #FFFFFF;'>
                            <span style='font-size: 1.8rem; margin-right: 12px; vertical-align: middle;'>{rank_medal}</span> {row_l['Candidate Name']}
                        </td>
                        <td style='padding: 20px 24px; font-size: 1.1rem; color: #A5B4FC; font-weight: 500;'>{row_l['Predicted Category']}</td>
                        <td style='padding: 20px 24px; text-align: center;'>
                            <div style='background: {score_color}15; color: {score_color}; padding: 8px 20px; border-radius: 99px; display: inline-block; font-weight: 800; font-size: 1.3rem; border: 1px solid {score_color}40;'>
                                {row_l['Match Score']:.1f}%
                            </div>
                        </td>
                        <td style='padding: 20px 24px; border-top-right-radius: 16px; border-bottom-right-radius: 16px; text-align: center;'>
                            <div style='font-size: 1.2rem; font-weight: 700; color: #E0E7FF; margin-bottom: 8px;'>{row_l['Skill Coverage']:.1f}%</div>
                            <div style='width: 100%; background: rgba(255,255,255,0.05); height: 8px; border-radius: 99px; overflow: hidden;'>
                                <div style='width: {row_l["Skill Coverage"]}%; background: linear-gradient(90deg, #6366F1, #EC4899); height: 100%; border-radius: 99px;'></div>
                            </div>
                        </td>
                    </tr>
                    """)
                html_table += textwrap.dedent("""
                    </tbody>
                    </table>
                </div>
                """)
                st.markdown(re.sub(r"\s+", " ", html_table).strip(), unsafe_allow_html=True)
                
                # Top candidate highlight
                top_candidate = df.iloc[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "🥇 Top Candidate",
                        top_candidate['Candidate Name'] if top_candidate['Candidate Name'] != 'N/A' else top_candidate['Filename']
                    )
                with col2:
                    st.metric(
                        "Match Score",
                        f"{top_candidate['Match Score']:.1f}%",
                        delta=top_candidate['Match Category']
                    )
                with col3:
                    st.metric(
                        "Skill Coverage",
                        f"{top_candidate['Skill Coverage']:.1f}%"
                    )
                
                st.divider()
                
                # ===== INDIVIDUAL CANDIDATE DETAILS =====
                st.subheader("📋 Detailed Candidate Profiles")
                st.markdown("Expand any candidate below to view their complete analysis")
                
                for idx, row in df.iterrows():
                    # Create expander with rank and score
                    rank_emoji = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "📄"
                    
                    with st.expander(f"{rank_emoji} **{row['Filename']}** - {row['Match Score']:.1f}% Match ({row['Match Category']})"):
                        # Candidate overview
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("👤 Name", row['Candidate Name'])
                        with col2:
                            st.metric("🎓 Category", row['Predicted Category'])
                        with col3:
                            st.metric("🎯 Match Score", f"{row['Match Score']:.1f}%")
                        with col4:
                            st.metric("✅ Skill Coverage", f"{row['Skill Coverage']:.1f}%")

                        tab1, tab2, tab3, tab4 = st.tabs(["📊 Skill Gap Analysis", "📄 Extracted Resume Info", "📈 Career Progression", "⏱️ Career Timeline"])

                        with tab1:
                            st.markdown("**🎯 Skill Gap Analysis**")
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("**✅ Matched Skills**")
                                matched = row['Matched Skills'].split(', ') if row['Matched Skills'] != 'None' else []
                                if matched:
                                    for skill in matched[:10]:  # Show first 10
                                        st.success(f"✓ {skill}", icon="✅")
                                    if len(matched) > 10:
                                        st.caption(f"... and {len(matched) - 10} more")
                                else:
                                    st.info("No matches found")

                            with col2:
                                st.markdown("**⚠️ Missing Skills**")
                                missing = row['Missing Skills'].split(', ') if row['Missing Skills'] != 'None' else []
                                if missing:
                                    for skill in missing[:10]:  # Show first 10
                                        st.warning(f"✗ {skill}", icon="⚠️")
                                    if len(missing) > 10:
                                        st.caption(f"... and {len(missing) - 10} more")
                                else:
                                    st.success("All skills matched!")

                        with tab2:
                            st.markdown("**📞 Contact Information**")
                            info_col1, info_col2 = st.columns(2)
                            with info_col1:
                                st.write(f"**Email:** {row['Email']}")
                            with info_col2:
                                st.write(f"**Phone:** {row['Phone']}")

                            summary_key = f"summary_btn_{row['Filename']}"
                            if st.button("🤖 Generate AI Summary", key=summary_key):
                                with st.spinner("Generating AI Summary..."):
                                    summary_text = generate_candidate_summary(row['Cleaned Text'])
                                st.subheader("AI Candidate Summary")
                                st.info(summary_text)

                            if st.checkbox(f"Show extracted text for {row['Filename']}", key=f"show_text_{idx}"):
                                st.text_area(
                                    "Raw Resume Text",
                                    row['Resume Text'],
                                    height=300,
                                    key=f"text_area_{idx}"
                                )

                        with tab3:
                            total_promotions, progression_path = analyze_career_progression(row['Resume Text'])
                            st.metric(
                                label="Total Role Progressions/Promotions",
                                value=total_promotions
                            )

                            if progression_path:
                                prog_html = textwrap.dedent("""
                                <div style='display: flex; flex-direction: column; gap: 20px; margin-top: 20px; font-family: Outfit, sans-serif;'>
                                """)
                                for i, step in enumerate(progression_path):
                                    line_div = f"<div style='position: absolute; left: 11px; top: 24px; width: 2px; height: 100%; background: linear-gradient(to bottom, rgba(236,72,153,0.5), rgba(99,102,241,0.5)); z-index: 1;'></div>" if i < len(progression_path)-1 else ""
                                    prog_html += textwrap.dedent(f"""
                                    <div style='position: relative; padding-left: 48px;'>
                                        <div style='position: absolute; left: 0; top: 0; width: 24px; height: 24px; border-radius: 50%; background: #EC4899; box-shadow: 0 0 16px rgba(236, 72, 153, 0.6); z-index: 2; border: 3px solid #0B0E14;'></div>
                                        {line_div}
                                        <div style='background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; font-size: 1.1rem; color: #F8FAFC; font-weight: 500; margin-bottom: 4px; box-shadow: 0 4px 16px rgba(0,0,0,0.15);'>
                                            {step}
                                        </div>
                                    </div>
                                    """)
                                prog_html += "</div>"
                                st.markdown(re.sub(r"\s+", " ", prog_html).strip(), unsafe_allow_html=True)
                            else:
                                st.markdown("No objective upward role progression was detected from the extracted resume text.")

                        with tab4:
                            st.markdown("### ⏱️ Career Timeline")
                            timeline_entries = extract_career_timeline(row['Resume Text'])

                            if timeline_entries:
                                time_html = textwrap.dedent("""
                                <div style='display: flex; flex-direction: column; gap: 20px; margin-top: 20px; font-family: Outfit, sans-serif;'>
                                """)
                                for entry in timeline_entries:
                                    time_html += textwrap.dedent(f"""
                                    <div style='display: flex; align-items: stretch; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.15);'>
                                        <div style='background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); padding: 24px; display: flex; align-items: center; justify-content: center; min-width: 180px; font-weight: 800; font-size: 1.2rem; color: #FFFFFF; text-align: center; border-right: 1px solid rgba(255,255,255,0.1);'>
                                            {entry['date']}
                                        </div>
                                        <div style='padding: 24px; font-size: 1.1rem; color: #E0E7FF; line-height: 1.6;'>
                                            {entry['context']}
                                        </div>
                                    </div>
                                    """)
                                time_html += "</div>"
                                st.markdown(re.sub(r"\s+", " ", time_html).strip(), unsafe_allow_html=True)
                            else:
                                st.info('Could not automatically extract standard date ranges.')
            else:
                st.error("No candidates were successfully processed.")
        
        # ===== SINGLE RESUME MODE =====
        else:
            try:
                # Process single file
                uploaded_file = uploaded_files[0]
                
                # Extract text from uploaded file
                resume_text = handle_file_upload(uploaded_file)
                cleaned_resume_text = cleanResume(resume_text)
                
                # Extract candidate information
                candidate_info = extract_candidate_info(resume_text)
                
                # Make prediction
                category = pred(resume_text)
                
                # Calculate match score if JD is provided
                scaled_match_score = 0
                category_name = "N/A"
                skill_analysis = None
                
                if jd_text.strip():
                    cleaned_jd_text = cleanResume(jd_text)
                    raw_match_score = calculate_match_score(cleaned_resume_text, cleaned_jd_text)
                    scaled_match_score = scale_match_score(raw_match_score)
                    category_name, category_color = get_match_category(scaled_match_score)
                    
                    # Perform skill gap analysis (use custom skills if provided)
                    if custom_skills_input.strip():
                        skill_analysis = analyze_custom_skill_gap(resume_text, custom_skills_input)
                    else:
                        skill_analysis = analyze_skill_gap(resume_text, jd_text)
                
                # ===== TOP LEVEL METRICS (SIDE-BY-SIDE) =====
                st.subheader("📊 Candidate Overview")
                
                if jd_text.strip():
                    col1, col2, col3 = st.columns(3)
                else:
                    col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="🎓 Predicted Department",
                        value=category,
                        help="AI-predicted job category based on resume content"
                    )
                
                with col2:
                    if jd_text.strip():
                        # Determine delta for visual indicator
                        if scaled_match_score >= 80:
                            delta_text = "Excellent Match"
                            delta_color = "normal"
                        elif scaled_match_score >= 50:
                            delta_text = "Moderate Match"
                            delta_color = "normal"
                        else:
                            delta_text = "Low Match"
                            delta_color = "inverse"
                        
                        st.metric(
                            label="🎯 JD Match Score",
                            value=f"{scaled_match_score:.1f}%",
                            delta=delta_text,
                            help="Semantic similarity between resume and job description"
                        )
                    else:
                        st.metric(
                            label="🎯 JD Match Score",
                            value="—",
                            help="Upload a Job Description to calculate match score"
                        )
                
                with col3:
                    if jd_text.strip() and skill_analysis and skill_analysis['jd_skills']:
                        skill_coverage = (len(skill_analysis['matched_skills']) / len(skill_analysis['jd_skills'])) * 100
                        st.metric(
                            label="✅ Skill Coverage",
                            value=f"{skill_coverage:.1f}%",
                            delta=f"{len(skill_analysis['matched_skills'])}/{len(skill_analysis['jd_skills'])} skills",
                            help="Percentage of required skills found in resume"
                        )
                    else:
                        st.metric(
                            label="✅ Skill Coverage",
                            value="—",
                            help="Requires Job Description for skill analysis"
                        )
                
                st.divider()
                
                # ===== DETAILED ANALYSIS SECTION (TABS) =====
                if jd_text.strip():
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Skill Gap Analysis", "📄 Extracted Resume Info", "📈 Career Progression", "⏱️ Career Timeline", "👤 Candidate Details"])
                else:
                    tab1, tab2, tab3, tab4 = st.tabs(["📄 Extracted Resume Info", "📈 Career Progression", "⏱️ Career Timeline", "👤 Candidate Details"])
                    
                if jd_text.strip():
                    # TAB 1: SKILL GAP ANALYSIS
                    with tab1:
                        st.markdown("### 🎯 Skill Gap Analysis")
                        st.markdown("Compare candidate skills against job requirements")
                        
                        if skill_analysis:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### ✅ Matched Skills")
                                if skill_analysis['matched_skills']:
                                    for skill in skill_analysis['matched_skills']:
                                        st.success(f"✓ {skill}", icon="✅")
                                    st.caption(f"**Total: {len(skill_analysis['matched_skills'])} skills matched**")
                                else:
                                    st.info("No matching skills found between resume and JD")
                            
                            with col2:
                                st.markdown("#### ⚠️ Missing Skills")
                                if skill_analysis['missing_skills']:
                                    for skill in skill_analysis['missing_skills']:
                                        st.warning(f"✗ {skill}", icon="⚠️")
                                    st.caption(f"**Total: {len(skill_analysis['missing_skills'])} skills to develop**")
                                else:
                                    st.success("No missing skills - Perfect match!", icon="🎉")
                            
                            # Skill coverage progress bar
                            if skill_analysis['jd_skills']:
                                skill_coverage = (len(skill_analysis['matched_skills']) / len(skill_analysis['jd_skills'])) * 100
                                st.markdown("---")
                                st.markdown(f"**Overall Skill Match: {skill_coverage:.1f}%**")
                                st.progress(int(round(skill_coverage)) / 100)
                        else:
                            st.info("Skill analysis requires both resume and job description")
                
                # TAB: EXTRACTED RESUME INFO
                if jd_text.strip():
                    tab_index = tab2
                else:
                    tab_index = tab1
                    
                with tab_index:
                    st.markdown("### 📄 Resume Content Analysis")
                    
                    # Show extracted text with toggle
                    show_full_text = st.checkbox("Show Full Extracted Text", value=False)
                    if show_full_text:
                        st.text_area(
                            "Raw Resume Text",
                            resume_text,
                            height=400,
                            help="Original text extracted from the uploaded document"
                        )
                    
                    # Show cleaned text
                    with st.expander("View Cleaned & Processed Text"):
                        st.text_area(
                            "Processed Text (after cleaning)",
                            cleaned_resume_text,
                            height=300,
                            help="Text after removing URLs, special characters, etc."
                        )
                
                # TAB: CAREER PROGRESSION
                if jd_text.strip():
                    tab_index = tab3
                else:
                    tab_index = tab2

                with tab_index:
                    st.markdown("### 📈 Career Progression")
                    total_promotions, progression_path = analyze_career_progression(resume_text)
                    st.metric(
                        label="Total Role Progressions/Promotions",
                        value=total_promotions
                    )

                    if progression_path:
                        progression_df = pd.DataFrame({
                            'Progression Path': progression_path
                        })
                        st.table(progression_df)
                    else:
                        st.markdown("No objective upward role progression was detected from the extracted resume text.")

                # TAB: CAREER TIMELINE
                if jd_text.strip():
                    tab_index = tab4
                else:
                    tab_index = tab3

                with tab_index:
                    st.markdown("### ⏱️ Career Timeline")
                    timeline_entries = extract_career_timeline(resume_text)

                    if timeline_entries:
                        timeline_df = pd.DataFrame(timeline_entries)
                        timeline_df = timeline_df.rename(columns={'date': 'Date Range', 'context': 'Context'})
                        st.table(timeline_df)
                    else:
                        st.info('Could not automatically extract standard date ranges.')

                # TAB: CANDIDATE DETAILS
                if jd_text.strip():
                    tab_index = tab5
                else:
                    tab_index = tab4
                    
                with tab_index:
                    st.markdown("### 👤 Extracted Candidate Information")
                    st.markdown("Information automatically extracted using NLP")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**👤 Candidate Name**")
                        if candidate_info['name']:
                            st.success(candidate_info['name'])
                        else:
                            st.error("Not Found")
                            st.caption("Name extraction requires clear formatting at the top of resume")
                    
                    with col2:
                        st.markdown("**📧 Email Address**")
                        if candidate_info['email']:
                            st.success(candidate_info['email'])
                        else:
                            st.error("Not Found")
                            st.caption("No valid email pattern detected")
                    
                    with col3:
                        st.markdown("**📱 Phone Number**")
                        if candidate_info['phone']:
                            st.success(candidate_info['phone'])
                        else:
                            st.error("Not Found")
                            st.caption("No valid phone pattern detected")
                
                st.divider()
                st.success("✅ Analysis Complete! Review the tabs above for detailed insights.")
                
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                st.info("Please ensure the file is a valid PDF, DOCX, or TXT document.")
    
    else:
        # Welcome screen when no file is uploaded
        st.info("👈 **Get Started:** Upload a resume using the sidebar to begin analysis")
        
        st.markdown("### 🚀 Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📊 AI Classification**
            - Automatic job category prediction
            - ML-powered resume analysis
            - Department matching
            """)
        
        with col2:
            st.markdown("""
            **🎯 Match Scoring**
            - Semantic JD comparison
            - Skill gap analysis
            - Coverage metrics
            """)
        
        with col3:
            st.markdown("""
            **👤 Info Extraction**
            - Name detection
            - Contact extraction
            - Entity recognition
            """)


if __name__ == "__main__":
    main()
