import pickle
import re
from pathlib import Path
import os
import spacy
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / 'models'

# Load models safely
svc_model = None
tfidf = None
le = None

def load_models():
    global svc_model, tfidf, le
    if not svc_model:
        try:
            with open(MODELS_DIR / 'clf.pkl', 'rb') as f:
                svc_model = pickle.load(f)
            with open(MODELS_DIR / 'tfidf.pkl', 'rb') as f:
                tfidf = pickle.load(f)
            with open(MODELS_DIR / 'encoder.pkl', 'rb') as f:
                le = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load ML models. {e}")

COMMON_SKILLS = [
    'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Go', 'Rust',
    'TypeScript', 'R', 'MATLAB', 'Scala', 'Perl', 'Shell', 'Bash',
    'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring',
    'Express.js', 'jQuery', 'Bootstrap', 'REST API', 'GraphQL', 'WebSocket',
    'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Oracle', 'SQL Server', 'Redis', 'Cassandra',
    'DynamoDB', 'ElasticSearch', 'Neo4j', 'SQLite',
    'AWS', 'Azure', 'Google Cloud', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD',
    'Terraform', 'Ansible', 'GitLab', 'CircleCI', 'Travis CI',
    'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'TensorFlow', 'PyTorch',
    'Scikit-learn', 'Keras', 'Pandas', 'NumPy', 'Matplotlib', 'Seaborn', 'Jupyter',
    'Data Analysis', 'Statistics', 'A/B Testing', 'Neural Networks', 'CNN', 'RNN', 'LSTM',
    'Hadoop', 'Spark', 'Kafka', 'Hive', 'Pig', 'ETL', 'Data Pipeline', 'Data Warehouse',
    'Airflow', 'Flink',
    'Git', 'GitHub', 'GitLab', 'Bitbucket', 'SVN', 'Mercurial',
    'Agile', 'Scrum', 'Kanban', 'JIRA', 'Project Management', 'Leadership', 'Communication',
    'Teamwork', 'Problem Solving', 'Critical Thinking', 'Time Management', 'Presentation',
    'Excel', 'PowerPoint', 'Tableau', 'Power BI', 'Salesforce', 'SAP', 'Slack', 'Confluence',
    'Cybersecurity', 'Encryption', 'OAuth', 'JWT', 'SSL', 'Firewall', 'Penetration Testing',
    'iOS', 'Android', 'React Native', 'Flutter', 'Xamarin',
    'Unit Testing', 'Integration Testing', 'Test Automation', 'Selenium', 'Jest', 'PyTest',
    'JUnit', 'TestNG',
    'Microservices', 'API Development', 'Blockchain', 'IoT', 'AR/VR', 'Linux', 'Unix',
    'Windows Server', 'Networking', 'TCP/IP'
]

def clean_resume(txt):
    cleanText = re.sub(r'http\S+\s', ' ', txt)
    cleanText = re.sub(r'RT|cc', ' ', cleanText)
    cleanText = re.sub(r'#\S+\s', ' ', cleanText)
    cleanText = re.sub(r'@\S+', '  ', cleanText)
    cleanText = re.sub('[%s]' % re.escape(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', cleanText)
    cleanText = re.sub(r'[^\x00-\x7f]', ' ', cleanText)
    cleanText = re.sub(r'\s+', ' ', cleanText)
    return cleanText

def predict_category(resume_text):
    load_models()
    if not svc_model:
        return "Unknown Category (Models not found)"
    
    cleaned = clean_resume(resume_text)
    vectorized = tfidf.transform([cleaned]).toarray()
    prediction_id = svc_model.predict(vectorized)[0]
    category = le.inverse_transform([prediction_id])[0]
    return category

@lru_cache(maxsize=None)
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

@lru_cache(maxsize=None)
def load_spacy_model():
    try:
        return spacy.load('en_core_web_sm')
    except OSError:
        print("spaCy model not found. Please install it.")
        return None

def extract_candidate_info(raw_text):
    info = {'name': None, 'email': None, 'phone': None}
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, raw_text)
    if email_matches:
        info['email'] = email_matches[0]
    
    phone_pattern = r'\(?\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}'
    phone_matches = re.findall(phone_pattern, raw_text)
    for match in phone_matches:
        digits_only = re.sub(r'\D', '', match)
        if len(digits_only) >= 10:
            info['phone'] = match.strip()
            break
    
    nlp = load_spacy_model()
    if nlp:
        doc = nlp(raw_text[:500])
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                info['name'] = ent.text
                break
    
    return info

def calculate_match_score(cleaned_resume_text, jd_text):
    embedding_model = load_embedding_model()
    resume_embedding = embedding_model.encode(cleaned_resume_text, convert_to_tensor=True)
    jd_embedding = embedding_model.encode(jd_text, convert_to_tensor=True)

    similarity = float(util.cos_sim(resume_embedding, jd_embedding)[0][0])
    similarity = max(0.0, min(1.0, similarity))
    return similarity

def scale_match_score(raw_score):
    min_realistic_score = 0.20
    max_realistic_score = 0.60
    
    if raw_score >= max_realistic_score:
        return 100.0
    elif raw_score <= min_realistic_score:
        return 0.0
    else:
        scaled = (raw_score - min_realistic_score) / (max_realistic_score - min_realistic_score)
        return round(scaled * 100.0, 1)

def extract_skills_from_text(text):
    text_lower = text.lower()
    found_skills = set()
    for skill in COMMON_SKILLS:
        skill_lower = skill.lower()
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    return found_skills

def analyze_skill_gap(resume_text, jd_text):
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
    resume_text_lower = raw_resume_text.lower()
    custom_skills = [skill.strip() for skill in custom_skills_input.split(',') if skill.strip()]

    matched_skills = set()
    for skill in custom_skills:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
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

def extract_career_timeline(raw_text):
    date_range_patterns = [
        r'\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{4}\s*(?:-|–|to)\s*(?:(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{4}|Present|Current)\b',
        r'\b(?:0?[1-9]|1[0-2])\/\d{4}\s*(?:-|–|to)\s*(?:(?:0?[1-9]|1[0-2])\/\d{4}|Present|Current)\b',
        r'\b\d{4}\s*(?:-|–|to)\s*(?:\d{4}|Present|Current)\b'
    ]
    combined_pattern = re.compile('|'.join(date_range_patterns), re.IGNORECASE)
    lines = [line.strip() for line in raw_text.splitlines()]

    timeline = []
    seen = set()

    for i, line in enumerate(lines):
        if not line: continue
        matches = combined_pattern.findall(line)
        if not matches: continue

        for match in matches:
            date_text = match.strip()
            context = line
            line_without_date = re.sub(re.escape(date_text), '', line, flags=re.IGNORECASE).strip(' -|:•\t')
            if (not line_without_date or len(line_without_date) < 4) and i > 0:
                previous_line = lines[i - 1].strip()
                if previous_line:
                    context = f"{previous_line} | {line}"

            normalized_key = (date_text.lower(), context.lower())
            if normalized_key in seen: continue

            timeline.append({'date': date_text, 'context': context})
            seen.add(normalized_key)
            
    # Sort timeline: most recent first (Descending)
    def get_sort_key(item):
        # Use regex to find years in the date string
        years = [int(y) for y in re.findall(r'\d{4}', item['date'])]
        if not years:
            return (0, 0)
        
        # End year: If 'Present' or 'Current' is mentioned, it's 9999
        if re.search(r'Present|Current', item['date'], re.I):
            end_year = 9999
        else:
            end_year = max(years)
            
        # Start year: The earliest year in the string
        start_year = min(years)
        
        # Returning a tuple allows primary sort on end_year, secondary on start_year
        return (end_year, start_year)

    timeline.sort(key=get_sort_key, reverse=True)
    return timeline

def extract_evidence_and_keywords(resume_text: str) -> dict:
    import re
    cleaned = clean_resume(resume_text)
    resume_text_lower = resume_text.lower()
    
    # 1. Extract potential certification mentions
    certs_found = []
    cert_keywords = ['certificat', 'certified', 'credential', 'courseera', 'coursera', 'udemy', 'edx', 'nptel']
    for line in resume_text.splitlines():
        line_strip = line.strip()
        if not line_strip:
            continue
        if any(kw in line_strip.lower() for kw in cert_keywords):
            if len(line_strip) < 200:
                certs_found.append(line_strip)
                
    # 2. Extract potential awards / achievements
    awards_found = []
    award_keywords = ['award', 'honor', 'placed', 'rank', 'winner', 'achievement', 'medal', 'hackathon']
    for line in resume_text.splitlines():
        line_strip = line.strip()
        if not line_strip:
            continue
        if any(kw in line_strip.lower() for kw in award_keywords):
            if len(line_strip) < 200:
                awards_found.append(line_strip)

    # 3. Domain keyword mapping matches
    domain_keywords = {
        "Machine Learning & AI": ["machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch", "scikit-learn", "keras", "neural networks", "artificial intelligence", "cnn", "rnn", "llm", "transformers", "generative ai"],
        "Web Frontend": ["react", "angular", "vue", "javascript", "typescript", "html", "css", "next.js", "frontend", "bootstrap", "tailwind", "jquery"],
        "Backend & APIs": ["node.js", "django", "flask", "fastapi", "spring boot", "express.js", "backend", "rest api", "graphql", "apis", "microservices", "spring", "express"],
        "Databases & Data Engineering": ["sql", "mysql", "postgresql", "mongodb", "redis", "cassandra", "database", "oracle", "spark", "hadoop", "kafka", "etl", "data warehouse"],
        "Cloud & DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible", "cloud", "devops"],
        "Mobile Development": ["android", "ios", "react native", "flutter", "swift", "kotlin", "mobile app"]
    }
    
    domain_matches = {}
    for domain, keywords in domain_keywords.items():
        found = []
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, resume_text_lower):
                found.append(kw)
        if found:
            domain_matches[domain] = found
            
    return {
        "certifications": certs_found[:10],
        "awards": awards_found[:10],
        "domain_matches": domain_matches
    }

