# you need to install all these in your terminal
# pip install streamlit
# pip install scikit-learn
# pip install python-docx
# pip install PyPDF2


import streamlit as st
import pickle
import docx  # Extract text from Word file
import PyPDF2  # Extract text from PDF
import re
from sentence_transformers import SentenceTransformer, util
import spacy
import pandas as pd
from transformers import pipeline

# Load pre-trained model and TF-IDF vectorizer (ensure these are saved earlier)
svc_model = pickle.load(open('clf.pkl', 'rb'))  # Example file name, adjust as needed
tfidf = pickle.load(open('tfidf.pkl', 'rb'))  # Example file name, adjust as needed
le = pickle.load(open('encoder.pkl', 'rb'))  # Example file name, adjust as needed

# Hardcoded list of common tech/business skills for skill gap analysis
COMMON_SKILLS = [
    # Programming Languages
    'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Go', 'Rust',
    'TypeScript', 'R', 'MATLAB', 'Scala', 'Perl', 'Shell', 'Bash',
    
    # Web Technologies
    'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring',
    'Express.js', 'jQuery', 'Bootstrap', 'REST API', 'GraphQL', 'WebSocket',
    
    # Databases
    'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Oracle', 'SQL Server', 'Redis', 'Cassandra',
    'DynamoDB', 'ElasticSearch', 'Neo4j', 'SQLite',
    
    # Cloud & DevOps
    'AWS', 'Azure', 'Google Cloud', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
    'Terraform', 'Ansible', 'GitLab', 'CircleCI', 'Travis CI',
    
    # Data Science & ML
    'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'TensorFlow', 'PyTorch',
    'Scikit-learn', 'Keras', 'Pandas', 'NumPy', 'Matplotlib', 'Seaborn', 'Jupyter',
    'Data Analysis', 'Statistics', 'A/B Testing', 'Neural Networks', 'CNN', 'RNN', 'LSTM',
    
    # Big Data
    'Hadoop', 'Spark', 'Kafka', 'Hive', 'Pig', 'ETL', 'Data Pipeline', 'Data Warehouse',
    'Airflow', 'Flink',
    
    # Version Control & Collaboration
    'Git', 'GitHub', 'GitLab', 'Bitbucket', 'SVN', 'Mercurial',
    
    # Business & Soft Skills
    'Agile', 'Scrum', 'Kanban', 'JIRA', 'Project Management', 'Leadership', 'Communication',
    'Teamwork', 'Problem Solving', 'Critical Thinking', 'Time Management', 'Presentation',
    
    # Business Tools
    'Excel', 'PowerPoint', 'Tableau', 'Power BI', 'Salesforce', 'SAP', 'Slack', 'Confluence',
    
    # Security
    'Cybersecurity', 'Encryption', 'OAuth', 'JWT', 'SSL', 'Firewall', 'Penetration Testing',
    
    # Mobile Development
    'iOS', 'Android', 'React Native', 'Flutter', 'Xamarin',
    
    # Testing
    'Unit Testing', 'Integration Testing', 'Test Automation', 'Selenium', 'Jest', 'PyTest',
    'JUnit', 'TestNG',
    
    # Other Technologies
    'Microservices', 'API Development', 'Blockchain', 'IoT', 'AR/VR', 'Linux', 'Unix',
    'Windows Server', 'Networking', 'TCP/IP'
]


# Function to clean resume text
def cleanResume(txt):
    cleanText = re.sub(r'http\S+\s', ' ', txt)
    cleanText = re.sub(r'RT|cc', ' ', cleanText)
    cleanText = re.sub(r'#\S+\s', ' ', cleanText)
    cleanText = re.sub(r'@\S+', '  ', cleanText)
    cleanText = re.sub('[%s]' % re.escape(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', cleanText)
    cleanText = re.sub(r'[^\x00-\x7f]', ' ', cleanText)
    cleanText = re.sub(r'\s+', ' ', cleanText)
    return cleanText


# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text


# Function to extract text from TXT with explicit encoding handling
def extract_text_from_txt(file):
    # Try using utf-8 encoding for reading the text file
    try:
        text = file.read().decode('utf-8')
    except UnicodeDecodeError:
        # In case utf-8 fails, try 'latin-1' encoding as a fallback
        text = file.read().decode('latin-1')
    return text


# Function to handle file upload and extraction
def handle_file_upload(uploaded_file):
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension == 'pdf':
        text = extract_text_from_pdf(uploaded_file)
    elif file_extension == 'docx':
        text = extract_text_from_docx(uploaded_file)
    elif file_extension == 'txt':
        text = extract_text_from_txt(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF, DOCX, or TXT file.")
    return text


# Function to predict the category of a resume
def pred(input_resume):
    # Preprocess the input text (e.g., cleaning, etc.)
    cleaned_text = cleanResume(input_resume)

    # Vectorize the cleaned text using the same TF-IDF vectorizer used during training
    vectorized_text = tfidf.transform([cleaned_text])

    # Convert sparse matrix to dense
    vectorized_text = vectorized_text.toarray()

    # Prediction
    predicted_category = svc_model.predict(vectorized_text)

    # get name of predicted category
    predicted_category_name = le.inverse_transform(predicted_category)

    return predicted_category_name[0]  # Return the category name


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')


@st.cache_resource
def load_spacy_model():
    """Load spacy model for information extraction."""
    try:
        return spacy.load('en_core_web_sm')
    except OSError:
        st.error("spaCy model 'en_core_web_sm' not found. Please install it using: python -m spacy download en_core_web_sm")
        return None


def extract_candidate_info(raw_text):
    """
    Extract candidate information from raw resume text.
    
    Args:
        raw_text: Raw resume text before cleaning
        
    Returns:
        dict with keys: 'name', 'email', 'phone'
    """
    info = {'name': None, 'email': None, 'phone': None}
    
    # Extract email using regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, raw_text)
    if email_matches:
        info['email'] = email_matches[0]  # Take the first email found
    
    # Extract phone number using regex (supports formats like (555) 123-4567 and (555) 987 -6543)
    phone_pattern = r'\(?\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}'
    phone_matches = re.findall(phone_pattern, raw_text)
    # Filter to get likely phone numbers (at least 10 digits)
    for match in phone_matches:
        digits_only = re.sub(r'\D', '', match)
        if len(digits_only) >= 10:
            info['phone'] = match.strip()
            break
    
    # Extract name using spaCy PERSON entity from the beginning
    nlp = load_spacy_model()
    if nlp:
        # Process first 500 characters to focus on header/contact section
        doc = nlp(raw_text[:500])
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                info['name'] = ent.text
                break  # Take the first PERSON entity
    
    return info


def calculate_match_score(cleaned_resume_text, jd_text):
    embedding_model = load_embedding_model()
    resume_embedding = embedding_model.encode(cleaned_resume_text, convert_to_tensor=True)
    jd_embedding = embedding_model.encode(jd_text, convert_to_tensor=True)

    similarity = float(util.cos_sim(resume_embedding, jd_embedding)[0][0])
    similarity = max(0.0, min(1.0, similarity))
    return similarity


def generate_candidate_summary(text):
    """
    Generate an AI summary of a candidate resume using a fast summarization model.

    Args:
        text: Cleaned resume text

    Returns:
        string summary
    """
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    tokenizer = summarizer.tokenizer

    tokens = tokenizer(text, truncation=True, max_length=1024, return_tensors="pt")
    truncated_text = tokenizer.decode(tokens["input_ids"][0], skip_special_tokens=True)

    summary = summarizer(truncated_text, max_length=150, min_length=30, do_sample=False)
    return summary[0]["summary_text"]


def scale_match_score(raw_score):
    """
    Scale raw cosine similarity (0-1) to user-friendly 0-100% using Min-Max normalization.
    
    raw_score: float between 0 and 1
    Returns: scaled percentage (0-100)
    """
    min_realistic_score = 0.20
    max_realistic_score = 0.60
    
    if raw_score >= max_realistic_score:
        return 100.0
    elif raw_score <= min_realistic_score:
        return 0.0
    else:
        scaled = (raw_score - min_realistic_score) / (max_realistic_score - min_realistic_score)
        return scaled * 100.0


def get_match_category(scaled_percentage):
    """
    Categorize match score into 4 tiers.
    
    scaled_percentage: float between 0 and 100
    Returns: tuple (category_name, color_function)
    """
    if scaled_percentage >= 80:
        return "Excellent Match", "success"
    elif scaled_percentage >= 50:
        return "Moderate Match", "warning"
    elif scaled_percentage >= 20:
        return "Poor Match", "error"
    else:
        return "No Match", "error"


def extract_skills_from_text(text):
    """
    Extract skills from text by matching against the common skills list.
    
    Args:
        text: Text to search for skills (should be lowercase)
        
    Returns:
        set of found skills
    """
    text_lower = text.lower()
    found_skills = set()
    
    for skill in COMMON_SKILLS:
        # Use word boundaries to avoid partial matches
        # e.g., "Java" should not match "JavaScript"
        skill_lower = skill.lower()
        
        # Create a regex pattern with word boundaries
        # Handle skills with spaces or special characters
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    
    return found_skills


def analyze_skill_gap(resume_text, jd_text):
    """
    Compare skills in resume vs job description to find matches and gaps.
    
    Args:
        resume_text: Cleaned resume text
        jd_text: Cleaned job description text
        
    Returns:
        dict with keys: 'matched_skills', 'missing_skills', 'resume_skills', 'jd_skills'
    """
    resume_skills = extract_skills_from_text(resume_text)
    jd_skills = extract_skills_from_text(jd_text)
    
    matched_skills = resume_skills.intersection(jd_skills)
    missing_skills = jd_skills - resume_skills
    
    return {
        'matched_skills': sorted(matched_skills),
        'missing_skills': sorted(missing_skills),
        'resume_skills': sorted(resume_skills),
        'jd_skills': sorted(jd_skills)
    }


def analyze_custom_skill_gap(raw_resume_text, custom_skills_input):
    """
    Analyze custom skills from comma-separated text input against raw resume text.

    Args:
        raw_resume_text: Raw resume text
        custom_skills_input: Comma-separated custom skills from st.text_input

    Returns:
        dict with keys: 'matched_skills', 'missing_skills', 'resume_skills', 'jd_skills'
    """
    resume_text_lower = raw_resume_text.lower()
    custom_skills = [skill.strip().lower() for skill in custom_skills_input.split(',') if skill.strip()]

    matched_skills = set()
    for skill in custom_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, resume_text_lower):
            matched_skills.add(skill)

    required_skills = set(custom_skills)
    missing_skills = required_skills - matched_skills

    return {
        'matched_skills': sorted(matched_skills),
        'missing_skills': sorted(missing_skills),
        'resume_skills': sorted(matched_skills),
        'jd_skills': sorted(required_skills)
    }


def analyze_career_progression(raw_text):
    """
    Analyze objective role progression from resume text.

    Args:
        raw_text: Raw resume text

    Returns:
        tuple: (total_promotions, progression_path)
    """
    # Seniority score map for objective progression checks
    level_scores = {
        'intern': 1,
        'trainee': 1,
        'entry': 2,
        'assistant': 2,
        'associate': 2,
        'junior': 2,
        'analyst': 3,
        'engineer': 3,
        'developer': 3,
        'consultant': 3,
        'specialist': 3,
        'coordinator': 3,
        'senior': 4,
        'lead': 5,
        'manager': 6,
        'head': 7,
        'director': 7,
        'vice president': 8,
        'vp': 8,
        'chief': 9,
        'cto': 9,
        'ceo': 9,
        'cfo': 9,
        'coo': 9
    }

    title_keywords_pattern = re.compile(
        r'\b(intern|trainee|entry|assistant|associate|junior|analyst|engineer|developer|consultant|specialist|'
        r'coordinator|senior|lead|manager|head|director|vice president|vp|chief|cto|ceo|cfo|coo)\b',
        re.IGNORECASE
    )

    org_suffix_pattern = re.compile(
        r'\b([A-Z][A-Za-z0-9&.,\- ]{2,}?(?:Inc|LLC|Ltd|Limited|Corp|Corporation|Company|Technologies|Systems|Solutions|Group))\b'
    )

    def clean_title_line(line):
        title = re.sub(r'\s+', ' ', line).strip(' -|:•\t')
        title = re.sub(r'\b(\d{4}\s*[-–]\s*\d{4}|\d{4}\s*[-–]\s*(Present|Current))\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip(' -|:•\t')
        words = title.split()
        if len(words) > 12:
            title = ' '.join(words[:12])
        return title

    def extract_company_from_line(line, nlp_model=None):
        at_match = re.search(r'\b(?:at|@)\s+([A-Z][A-Za-z0-9&.,\- ]{1,60})', line)
        if at_match:
            return at_match.group(1).strip(' -|:;,.')

        pipe_parts = re.split(r'\s[\-|\|]\s', line)
        if len(pipe_parts) > 1:
            for part in pipe_parts:
                if not title_keywords_pattern.search(part):
                    candidate = part.strip(' -|:;,.')
                    if candidate and len(candidate.split()) <= 8:
                        return candidate

        org_match = org_suffix_pattern.search(line)
        if org_match:
            return org_match.group(1).strip(' -|:;,.')

        if nlp_model:
            doc = nlp_model(line)
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    return ent.text.strip(' -|:;,.')

        return "Unknown Company"

    def get_level_score(title):
        title_lower = title.lower()
        found_scores = [score for keyword, score in level_scores.items() if re.search(rf'\b{re.escape(keyword)}\b', title_lower)]
        if not found_scores:
            return 0
        return max(found_scores)

    nlp = load_spacy_model()
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Fallback if text was extracted as one long block
    if len(lines) <= 1:
        lines = [seg.strip() for seg in re.split(r'(?<=[.!?])\s+|\s{2,}', raw_text) if seg.strip()]

    extracted_roles = []
    seen_titles = set()

    for line in lines:
        if not title_keywords_pattern.search(line):
            continue

        cleaned_title = clean_title_line(line)
        if not cleaned_title or len(cleaned_title) < 3:
            continue

        normalized_title = cleaned_title.lower()
        if normalized_title in seen_titles:
            continue

        level_score = get_level_score(cleaned_title)
        if level_score == 0:
            continue

        company = extract_company_from_line(line, nlp_model=nlp)
        extracted_roles.append({
            'title': cleaned_title,
            'company': company,
            'level': level_score
        })
        seen_titles.add(normalized_title)

    if len(extracted_roles) < 2:
        return 0, []

    def compute_progressions(sequence):
        promotions = 0
        path = []
        for i in range(1, len(sequence)):
            prev_role = sequence[i - 1]
            current_role = sequence[i]
            if current_role['level'] > prev_role['level']:
                promotions += 1
                path.append(f"From {prev_role['title']} ➔ To {current_role['title']}")
        return promotions, path

    # Resumes are commonly reverse-chronological; evaluate both directions.
    forward_promotions, forward_path = compute_progressions(extracted_roles)
    reverse_roles = list(reversed(extracted_roles))
    reverse_promotions, reverse_path = compute_progressions(reverse_roles)

    if reverse_promotions > forward_promotions:
        return reverse_promotions, reverse_path

    return forward_promotions, forward_path


def extract_career_timeline(raw_text):
    """
    Extract chronological career timeline entries from resume text using date-range regex patterns.

    Args:
        raw_text: Raw resume text

    Returns:
        list[dict]: [{'date': '<date range>', 'context': '<job/company context>'}, ...]
    """
    date_range_patterns = [
        # Jan 2020 - Dec 2022 / January 2020 to Present
        r'\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{4}\s*(?:-|–|to)\s*(?:(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{4}|Present|Current)\b',
        # 05/2019 - 08/2021 or 5/2019 to Present
        r'\b(?:0?[1-9]|1[0-2])\/\d{4}\s*(?:-|–|to)\s*(?:(?:0?[1-9]|1[0-2])\/\d{4}|Present|Current)\b',
        # 2015-2018 or 2018 to Present
        r'\b\d{4}\s*(?:-|–|to)\s*(?:\d{4}|Present|Current)\b'
    ]

    combined_pattern = re.compile('|'.join(date_range_patterns), re.IGNORECASE)
    lines = [line.strip() for line in raw_text.splitlines()]

    timeline = []
    seen = set()

    for i, line in enumerate(lines):
        if not line:
            continue

        matches = combined_pattern.findall(line)
        if not matches:
            continue

        for match in matches:
            date_text = match.strip()

            # Use same line by default; if it's mostly date-only, use previous line as context when available.
            context = line
            line_without_date = re.sub(re.escape(date_text), '', line, flags=re.IGNORECASE).strip(' -|:•\t')
            if (not line_without_date or len(line_without_date) < 4) and i > 0:
                previous_line = lines[i - 1].strip()
                if previous_line:
                    context = f"{previous_line} | {line}"

            normalized_key = (date_text.lower(), context.lower())
            if normalized_key in seen:
                continue

            timeline.append({
                'date': date_text,
                'context': context
            })
            seen.add(normalized_key)

    return timeline


# Streamlit app layout
def main():
    st.set_page_config(page_title="Enterprise ATS Dashboard", page_icon="💼", layout="wide")

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
    st.sidebar.markdown("Configure your screening parameters below:")
    
    # File uploader in sidebar - ACCEPTS MULTIPLE FILES
    uploaded_files = st.sidebar.file_uploader(
        "📤 Upload Candidate Resume(s)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload one or multiple resumes in PDF, DOCX, or TXT format"
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
                
                # Format the display
                display_df['Match Score'] = display_df['Match Score'].apply(lambda x: f"{x:.1f}%")
                display_df['Skill Coverage'] = display_df['Skill Coverage'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
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
                                progression_df = pd.DataFrame({
                                    'Progression Path': progression_path
                                })
                                st.table(progression_df)
                            else:
                                st.markdown("No objective upward role progression was detected from the extracted resume text.")

                        with tab4:
                            st.markdown("### ⏱️ Career Timeline")
                            timeline_entries = extract_career_timeline(row['Resume Text'])

                            if timeline_entries:
                                timeline_df = pd.DataFrame(timeline_entries)
                                timeline_df = timeline_df.rename(columns={'date': 'Date Range', 'context': 'Context'})
                                st.table(timeline_df)
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
