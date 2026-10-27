import re
import math
import sqlite3
from datetime import datetime
from pathlib import Path
from collections import Counter
from functools import lru_cache


# ============================================================
# JOB ROLES AND REQUIRED SKILLS
# ============================================================

ROLE_SKILLS = {

    "Software Engineer": [
        "python", "java", "c++", "c#", "javascript", "typescript",
        "algorithms", "data structures", "object oriented programming",
        "oop", "sql", "nosql", "git", "github",
        "rest api", "docker", "kubernetes",
        "linux", "aws", "azure", "gcp",
        "react", "node.js", "django", "flask", "fastapi",
        "testing", "unit testing", "agile", "scrum"
    ],

    "Data Scientist": [
        "python", "r", "sql", "machine learning",
        "deep learning", "statistics", "numpy", "pandas",
        "scikit-learn", "tensorflow", "pytorch",
        "nlp", "computer vision", "data visualization",
        "matplotlib", "seaborn", "plotly",
        "tableau", "power bi", "regression",
        "classification", "clustering", "jupyter"
    ],

    "Machine Learning Engineer": [
        "python", "machine learning", "deep learning",
        "tensorflow", "pytorch", "keras",
        "scikit-learn", "mlops", "model deployment",
        "docker", "kubernetes", "aws",
        "azure", "gcp", "mlflow",
        "nlp", "transformers", "computer vision",
        "data pipelines", "feature engineering"
    ],

    "Frontend Developer": [
        "html", "css", "javascript", "typescript",
        "react", "vue", "angular", "next.js",
        "tailwind", "bootstrap", "responsive design",
        "figma", "rest api", "graphql",
        "redux", "jest", "cypress",
        "webpack", "vite", "npm"
    ],

    "Backend Developer": [
        "python", "java", "node.js", "go", "c#",
        "php", "sql", "mysql", "postgresql",
        "mongodb", "redis", "rest api",
        "graphql", "docker", "kubernetes",
        "aws", "azure", "linux",
        "django", "flask", "fastapi",
        "spring boot", "express",
        "authentication", "jwt"
    ],

    "Full Stack Developer": [
        "html", "css", "javascript", "typescript",
        "react", "node.js", "python",
        "sql", "mongodb", "postgresql",
        "rest api", "graphql", "docker",
        "git", "github", "aws",
        "next.js", "express", "django",
        "fastapi", "authentication",
        "jwt", "testing"
    ],

    "DevOps Engineer": [
        "docker", "kubernetes", "terraform",
        "ansible", "jenkins", "github actions",
        "gitlab ci", "aws", "azure", "gcp",
        "linux", "bash", "python",
        "prometheus", "grafana",
        "ci/cd", "infrastructure as code",
        "helm", "nginx", "monitoring"
    ],

    "Cybersecurity Analyst": [
        "network security", "penetration testing",
        "vulnerability assessment", "siem",
        "splunk", "wireshark", "nmap",
        "metasploit", "incident response",
        "threat intelligence", "python",
        "bash", "linux", "windows",
        "firewall", "ids", "ips",
        "cloud security", "owasp",
        "encryption", "soc"
    ],

    "Cloud Architect": [
        "aws", "azure", "gcp", "cloud architecture",
        "cloud computing", "terraform", "infrastructure as code",
        "kubernetes", "docker", "microservices",
        "serverless", "networking", "security",
        "iam", "high availability", "disaster recovery",
        "cost optimization", "monitoring"
    ],

    "Data Analyst": [
        "sql", "excel", "python", "r", "pandas",
        "data cleaning", "data analysis", "data visualization",
        "tableau", "power bi", "statistics",
        "dashboards", "reporting", "database",
        "business intelligence", "google analytics"
    ],

    "Business Analyst": [
        "requirements gathering", "business analysis",
        "stakeholder management", "process improvement",
        "business process", "documentation", "user stories",
        "use cases", "agile", "scrum", "jira",
        "sql", "excel", "data analysis",
        "communication", "project management"
    ],

    "Product Manager": [
        "product strategy", "product roadmap",
        "product management", "market research",
        "user research", "product requirements",
        "prioritization", "stakeholder management",
        "agile", "scrum", "jira", "analytics",
        "data analysis", "customer feedback",
        "go-to-market", "communication"
    ],

    "UI/UX Designer": [
        "ui design", "ux design", "figma",
        "wireframing", "prototyping", "user research",
        "usability testing", "interaction design",
        "visual design", "design systems",
        "information architecture", "accessibility",
        "adobe xd", "sketch", "html", "css"
    ],

    "QA Engineer": [
        "quality assurance", "software testing",
        "manual testing", "test automation",
        "selenium", "cypress", "playwright",
        "pytest", "jest", "test cases",
        "regression testing", "api testing",
        "postman", "jira", "bug tracking",
        "continuous integration", "python", "javascript"
    ],

    "Database Administrator": [
        "database administration", "sql", "mysql",
        "postgresql", "oracle", "sql server",
        "mongodb", "database design", "database security",
        "backup and recovery", "performance tuning",
        "database migration", "replication",
        "high availability", "linux", "monitoring"
    ],

    "Mobile App Developer": [
        "android", "ios", "swift", "kotlin",
        "java", "flutter", "dart", "react native",
        "mobile development", "rest api", "firebase",
        "git", "ui design", "testing",
        "app store", "google play", "javascript"
    ]
}


# ============================================================
# COMMON SKILLS
# ============================================================

GENERIC_SKILLS = [
    "communication",
    "leadership",
    "teamwork",
    "problem solving",
    "critical thinking",
    "time management",
    "project management",
    "presentation",
    "documentation",
    "mentoring",
    "collaboration",
    "analytical",
    "attention to detail",
    "adaptability",
    "creativity"
]


# ============================================================
# EDUCATION KEYWORDS
# ============================================================

EDUCATION_TERMS = [
    "bca",
    "b.tech",
    "btech",
    "mca",
    "m.tech",
    "mtech",
    "b.sc",
    "bsc",
    "m.sc",
    "msc",
    "bachelor",
    "master",
    "phd",
    "ph.d",
    "mba",
    "diploma",
    "computer science",
    "information technology",
    "engineering"
]


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9 .+#/&-]",
        " ",
        text
    )

    return text


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skill_tokens(text, skill_list):

    text = normalize(text)

    found = set()

    for skill in skill_list:

        skill_lower = skill.lower()

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(skill_lower)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, text):

            found.add(skill)

    return found


# ============================================================
# TF-IDF STYLE TEXT SIMILARITY
# ============================================================

def tfidf_similarity(text1, text2):

    def tokenize(text):

        return re.findall(
            r"\b[a-z][a-z0-9+#.]{1,}\b",
            normalize(text)
        )

    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    vocabulary = set(tokens1) | set(tokens2)

    if not vocabulary:
        return 0.0

    def vector(tokens):

        counts = Counter(tokens)

        total = len(tokens) or 1

        return {
            word: counts[word] / total
            for word in vocabulary
        }

    vector1 = vector(tokens1)
    vector2 = vector(tokens2)

    dot_product = sum(
        vector1[word] * vector2[word]
        for word in vocabulary
    )

    magnitude1 = math.sqrt(
        sum(value ** 2 for value in vector1.values())
    )

    magnitude2 = math.sqrt(
        sum(value ** 2 for value in vector2.values())
    )

    if magnitude1 == 0 or magnitude2 == 0:

        return 0.0

    return dot_product / (
        magnitude1 * magnitude2
    )


# ============================================================
# AI SEMANTIC SIMILARITY
# ============================================================

@lru_cache(maxsize=1)
def _load_sentence_transformer():

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )


def semantic_similarity(text1, text2):

    try:

        model = _load_sentence_transformer()

        embeddings = model.encode(
            [text1, text2],
            normalize_embeddings=True
        )

        score = float(
            embeddings[0] @ embeddings[1]
        )

        score = max(
            0.0,
            min(score, 1.0)
        )

        return score, "AI Sentence Transformer"

    except Exception:

        score = tfidf_similarity(
            text1,
            text2
        )

        return score, "TF-IDF Fallback"


def live_match_preview(
    resume_text,
    job_description,
    job_role
):

    is_custom_role = job_role not in ROLE_SKILLS
    role_skills = ROLE_SKILLS.get(job_role, [])
    all_skills = skills_for_role(job_role) + GENERIC_SKILLS

    resume_skills = extract_skill_tokens(
        resume_text,
        all_skills
    )
    job_skills = extract_skill_tokens(
        job_description,
        all_skills
    )

    if not job_skills and not is_custom_role:
        job_skills = set(role_skills)

    matched_skills = resume_skills & job_skills
    missing_skills = job_skills - resume_skills
    skill_score = round(
        len(matched_skills) / len(job_skills) * 100
    ) if job_skills else 0
    keyword_score = round(
        keyword_overlap(resume_text, job_description) * 100
    ) if job_description.strip() else 0

    return {
        "skill_score": skill_score,
        "keyword_score": keyword_score,
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills),
        "job_recommendations": role_recommendations(
            resume_text
        ) if resume_text.strip() else []
    }


# ============================================================
# KEYWORD MATCHING
# ============================================================

def keyword_overlap(text1, text2):

    stopwords = {
        "and",
        "the",
        "or",
        "of",
        "in",
        "to",
        "a",
        "an",
        "is",
        "are",
        "for",
        "with",
        "on",
        "at",
        "by",
        "as",
        "be",
        "will",
        "should",
        "have",
        "has",
        "their",
        "your",
        "our",
        "this",
        "that",
        "which",
        "from",
        "into",
        "we",
        "you",
        "they",
        "it",
        "its"
    }

    def keywords(text):

        words = re.findall(
            r"\b[a-z][a-z0-9+#.]{1,}\b",
            text.lower()
        )

        return {
            word
            for word in words
            if word not in stopwords
            and len(word) > 2
        }

    set1 = keywords(text1)
    set2 = keywords(text2)

    union = set1 | set2

    if not union:

        return 0.0

    return len(set1 & set2) / len(union)


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

def extract_education(text):

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]

    education = []

    for line in lines:

        lower_line = line.lower()

        if any(
            term in lower_line
            for term in EDUCATION_TERMS
        ):

            if (
                4 <= len(line) <= 180
                and line not in education
            ):

                education.append(line)

    return education[:10]


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience(text):

    duration_mentions = re.findall(
        r"\b\d+(?:\.\d+)?\+?\s*(?:years?|yrs?)\b",
        text,
        re.IGNORECASE
    )

    job_titles = []

    patterns = [

        r"\bsoftware engineer\b",

        r"\bsoftware developer\b",

        r"\bfrontend developer\b",

        r"\bbackend developer\b",

        r"\bfull stack developer\b",

        r"\bdata scientist\b",

        r"\bdata analyst\b",

        r"\bmachine learning engineer\b",

        r"\bdevops engineer\b",

        r"\bproject manager\b",

        r"\bproduct manager\b",

        r"\bui/ux designer\b",

        r"\bcybersecurity analyst\b",

        r"\bintern\b",

        r"\bdeveloper\b",

        r"\bengineer\b",

        r"\banalyst\b",

        r"\bmanager\b",

        r"\bdesigner\b"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        job_titles.extend(matches)

    return {

        "duration_mentions": sorted(
            set(duration_mentions)
        )[:10],

        "job_titles": sorted(
            set(job_titles),
            key=str.lower
        )[:10]
    }


# ============================================================
# ATS SCORE
# ============================================================

def ats_score(text):

    return ats_score_breakdown(text)["score"]


def ats_score_breakdown(text):

    lower = text.lower()
    word_count = len(text.split())

    if 300 <= word_count <= 1000:
        length_points = 20
        length_guidance = ""
    elif 180 <= word_count <= 1300:
        length_points = 15
        length_guidance = (
            "Aim for 300–1,000 words when relevant to your experience."
        )
    elif word_count >= 100:
        length_points = 8
        length_guidance = (
            "Add relevant detail; the preferred range is 300–1,000 words."
        )
    else:
        length_points = 0
        length_guidance = (
            "Add relevant experience, projects, skills, and achievements."
        )

    checks = [
        {
            "check": "Resume length",
            "earned": length_points,
            "possible": 20,
            "guidance": length_guidance
        }
    ]

    sections = [
        ["summary", "objective", "profile"],
        ["experience", "employment", "work history"],
        ["education"],
        ["skills", "technical skills"],
        ["projects"],
        ["certifications", "certificates"]
    ]
    section_names = [
        "Summary",
        "Experience",
        "Education",
        "Skills",
        "Projects",
        "Certifications"
    ]

    for section_group, section_name in zip(sections, section_names):
        found = any(section in lower for section in section_group)
        checks.append({
            "check": f"{section_name} section",
            "earned": 10 if found else 0,
            "possible": 10,
            "guidance": (
                "" if found
                else f"Add a clearly labeled {section_name} section if relevant."
            )
        })

    criteria = [
        (
            "Email address",
            bool(re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", lower)),
            8,
            "Add a professional email address."
        ),
        (
            "Professional profile link",
            bool(re.search(r"(linkedin\.com|github\.com|gitlab\.com)", lower)),
            7,
            "Add a LinkedIn, GitHub, or GitLab profile link if relevant."
        ),
        (
            "Phone number",
            bool(re.search(r"(?:\+?\d[\d\s().-]{8,})", text)),
            5,
            "Add a contact phone number if you want employers to reach you by phone."
        ),
        (
            "Bullet points",
            bool(re.search(r"•|▪|●|\n[-*]\s", text)),
            5,
            "Use concise bullet points for experience and project descriptions."
        ),
        (
            "Dates",
            bool(re.search(r"\b(?:19|20)\d{2}\b", text)),
            5,
            "Include dates for relevant education and work experience."
        ),
        (
            "Quantified achievements",
            bool(re.search(r"\b\d+(?:%|x)\b", lower)),
            5,
            "Add truthful, measurable outcomes where available."
        )
    ]

    for label, passed, points, guidance in criteria:
        checks.append({
            "check": label,
            "earned": points if passed else 0,
            "possible": points,
            "guidance": "" if passed else guidance
        })

    earned_points = sum(
        item["earned"] for item in checks
    )

    return {
        "score": min(earned_points, 100),
        "earned_points": earned_points,
        "possible_points": sum(
            item["possible"] for item in checks
        ),
        "checks": checks
    }


# ============================================================
# RESUME QUALITY SCORE
# ============================================================

def resume_quality_score(
    text,
    ats,
    skill_score
):

    word_count = len(
        text.split()
    )

    if 300 <= word_count <= 1000:

        length_score = 100

    elif 150 <= word_count <= 1300:

        length_score = 75

    else:

        length_score = 45

    quality = (
        ats * 0.45
        + skill_score * 0.30
        + length_score * 0.25
    )

    return round(
        min(quality, 100)
    )


# ============================================================
# JOB ROLE RECOMMENDATIONS
# ============================================================

def role_recommendations(
    resume_text,
    limit=5
):

    results = []

    for role, skills in ROLE_SKILLS.items():

        matched = extract_skill_tokens(
            resume_text,
            skills
        )

        score = round(
            len(matched)
            / max(len(skills), 1)
            * 100
        )

        results.append({

            "role": role,

            "score": score,

            "matched_skills": sorted(
                matched
            )
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:limit]


def skills_for_role(job_role):

    if job_role in ROLE_SKILLS:
        return ROLE_SKILLS[job_role]

    return list(dict.fromkeys(
        skill
        for skills in ROLE_SKILLS.values()
        for skill in skills
    ))


# ============================================================
# DATABASE
# ============================================================

class ResumeAnalyzer:

    def __init__(
        self,
        database="resume_history.db"
    ):

        self.database = Path(
            database
        )

        self.initialize_database()


    def initialize_database(self):

        with sqlite3.connect(
            self.database
        ) as connection:

            connection.execute("""

                CREATE TABLE IF NOT EXISTS analyses (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    created_at TEXT,

                    file_name TEXT,

                    job_role TEXT,

                    match_score INTEGER,

                    ats_score INTEGER,

                    quality_score INTEGER

                )

            """)


    def save_history(
        self,
        file_name,
        job_role,
        result
    ):

        with sqlite3.connect(
            self.database
        ) as connection:

            connection.execute("""

                INSERT INTO analyses

                (
                    created_at,
                    file_name,
                    job_role,
                    match_score,
                    ats_score,
                    quality_score
                )

                VALUES (?, ?, ?, ?, ?, ?)

            """,

            (

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                file_name,

                job_role,

                result["match_score"],

                result["ats_score"],

                result["quality_score"]

            ))


    def get_history(
        self,
        limit=20
    ):

        with sqlite3.connect(
            self.database
        ) as connection:

            rows = connection.execute("""

                SELECT

                    created_at,
                    file_name,
                    job_role,
                    match_score,
                    ats_score,
                    quality_score

                FROM analyses

                ORDER BY id DESC

                LIMIT ?

            """, (limit,)).fetchall()

        return rows


    # ========================================================
    # MAIN ANALYSIS
    # ========================================================

    def analyze(
        self,
        resume_text,
        job_description,
        job_role
    ):

        is_custom_role = job_role not in ROLE_SKILLS
        role_skills = ROLE_SKILLS.get(job_role, [])
        all_skills = skills_for_role(job_role) + GENERIC_SKILLS

        # Resume skills

        resume_skills = extract_skill_tokens(
            resume_text,
            all_skills
        )

        # Job description skills

        job_skills = extract_skill_tokens(
            job_description,
            all_skills
        )

        # If job description has no detected skills,
        # use the selected role's skills.

        if not job_skills and not is_custom_role:

            job_skills = set(
                role_skills
            )

        matched_skills = (
            resume_skills
            & job_skills
        )

        missing_skills = (
            job_skills
            - resume_skills
        )

        # Skill score

        if job_skills:

            skill_score = round(

                len(matched_skills)
                / len(job_skills)
                * 100

            )

        else:

            skill_score = 0


        # AI semantic similarity

        semantic_score, method = (
            semantic_similarity(
                resume_text,
                job_description
            )
        )

        semantic_percentage = round(
            semantic_score * 100
        )


        # Keyword score

        keyword_score = round(

            keyword_overlap(
                resume_text,
                job_description
            ) * 100

        )


        # ATS

        ats_breakdown = ats_score_breakdown(
            resume_text
        )
        ats = ats_breakdown["score"]


        # Resume quality

        quality = resume_quality_score(
            resume_text,
            ats,
            skill_score
        )


        # Final match score

        final_score = round(

            skill_score * 0.35

            + semantic_percentage * 0.30

            + keyword_score * 0.20

            + ats * 0.15

        )

        final_score = max(
            0,
            min(final_score, 100)
        )


        # Education

        education = extract_education(
            resume_text
        )


        # Experience

        experience = extract_experience(
            resume_text
        )


        # Job recommendations

        recommendations = (
            role_recommendations(
                resume_text
            )
        )

        # Strengths and gaps

        strengths = self.generate_strengths(
            resume_text,
            matched_skills,
            semantic_percentage,
            keyword_score,
            ats
        )

        weaknesses = self.generate_weaknesses(
            missing_skills,
            ats,
            quality,
            semantic_percentage,
            keyword_score
        )

        personalized_recommendations = (
            self.generate_personalized_recommendations(
                resume_text,
                matched_skills,
                missing_skills,
                ats,
                quality,
                semantic_percentage,
                keyword_score
            )
        )

        interview_questions = (
            self.generate_interview_questions(
                job_role,
                matched_skills,
                missing_skills
            )
        )

        learning_roadmap = (
            self.generate_learning_roadmap(
                job_role,
                missing_skills
            )
        )

        resume_rewrite = self.generate_resume_rewrite(
            resume_text,
            job_description,
            job_role,
            matched_skills
        )

        # Improvement suggestions

        suggestions = (
            self.generate_suggestions(

                resume_text,

                job_description,

                matched_skills,

                missing_skills,

                ats,

                quality,

                semantic_percentage,

                keyword_score

            )
        )


        return {

            "match_score":
                final_score,

            "skill_score":
                skill_score,

            "semantic_score":
                semantic_percentage,

            "keyword_score":
                keyword_score,

            "ats_score":
                ats,

            "ats_breakdown":
                ats_breakdown,

            "quality_score":
                quality,

            "matched_skills":
                sorted(
                    matched_skills
                ),

            "missing_skills":
                sorted(
                    missing_skills
                ),

            "education":
                education,

            "experience":
                experience,

            "job_recommendations":
                recommendations,

            "strengths":
                strengths,

            "weaknesses":
                weaknesses,

            "personalized_recommendations":
                personalized_recommendations,

            "interview_questions":
                interview_questions,

            "learning_roadmap":
                learning_roadmap,

            "resume_rewrite":
                resume_rewrite,

            "suggestions":
                suggestions,

            "resume_improvement":
                suggestions,

            "semantic_method":
                method

        }


    # ========================================================
    # IMPROVEMENT SUGGESTIONS
    # ========================================================

    def generate_strengths(
        self,
        resume,
        matched_skills,
        semantic_score,
        keyword_score,
        ats
    ):

        strengths = []

        if matched_skills:
            strengths.append(
                "Strong skill alignment with the target role: "
                + ", ".join(sorted(matched_skills)[:6])
            )

        if semantic_score >= 60:
            strengths.append(
                "Your resume content aligns well with the job description's core responsibilities."
            )

        if keyword_score >= 50:
            strengths.append(
                "Relevant job keywords are already present throughout the resume."
            )

        if ats >= 75:
            strengths.append(
                "The resume structure is ATS-friendly and easy for recruiters to scan."
            )

        if not strengths:
            strengths.append(
                "The current resume demonstrates foundational experience and a clear career direction."
            )

        return strengths[:5]


    def generate_weaknesses(
        self,
        missing_skills,
        ats,
        quality,
        semantic_score,
        keyword_score
    ):

        weaknesses = []

        if missing_skills:
            missing = ", ".join(sorted(missing_skills)[:5])
            weaknesses.append(
                "Missing role-critical skills: " + missing
            )

        if ats < 70:
            weaknesses.append(
                "ATS structure can be improved with clearer headings and standard resume sections."
            )

        if quality < 70:
            weaknesses.append(
                "Resume quality would improve with stronger achievement statements and better formatting."
            )

        if semantic_score < 50:
            weaknesses.append(
                "The summary and experience sections do not yet strongly match the job's core responsibilities."
            )

        if keyword_score < 50:
            weaknesses.append(
                "The resume is missing some important employer keywords from the job description."
            )

        if not weaknesses:
            weaknesses.append(
                "No major gaps detected, but there is room to strengthen impact statements and keyword coverage."
            )

        return weaknesses[:5]


    def generate_personalized_recommendations(
        self,
        resume,
        matched_skills,
        missing_skills,
        ats,
        quality,
        semantic_score,
        keyword_score
    ):

        recommendations = []

        if missing_skills:
            recommendations.append(
                "Prioritize adding the missing skills that are most relevant to your target role, especially if you have hands-on experience with them."
            )

        if ats < 80:
            recommendations.append(
                "Use a consistent section layout with Summary, Skills, Experience, Projects, and Education to improve ATS readability."
            )

        if quality < 75:
            recommendations.append(
                "Replace generic task statements with quantified impact statements, such as percentage gains, delivery scale, or performance improvement."
            )

        if semantic_score < 60:
            recommendations.append(
                "Rewrite your profile summary so it mirrors the employer's language and major responsibilities."
            )

        if keyword_score < 60:
            recommendations.append(
                "Integrate role-specific keywords naturally into bullet points, project summaries, and skills sections."
            )

        if not recommendations:
            recommendations.append(
                "Continue refining the resume with targeted metrics and job-specific phrasing to keep it competitive."
            )

        return recommendations[:5]


    def generate_interview_questions(
        self,
        job_role,
        matched_skills,
        missing_skills
    ):

        core = sorted(matched_skills)[:4]
        gaps = sorted(missing_skills)[:4]

        questions = []

        if core:
            questions.append(
                "Be ready to discuss your experience with " + ", ".join(core) + " and how you applied them in real projects."
            )

        if gaps:
            questions.append(
                "Prepare for questions on " + ", ".join(gaps) + " in case the interviewer tests your familiarity with those areas."
            )

        questions.append(
            "Be ready to explain your approach to problem solving, trade-offs, and collaboration in a " + job_role.lower() + " role."
        )

        return questions[:5]


    def generate_learning_roadmap(
        self,
        job_role,
        missing_skills
    ):

        gaps = sorted(missing_skills)[:5]

        roadmap = []

        if gaps:
            for skill in gaps:
                roadmap.append(
                    f"Learn {skill} by building a small project or completing a guided hands-on exercise."
                )

        roadmap.append(
            "Practice explaining projects, metrics, and trade-offs clearly for interviews in a " + job_role.lower() + " role."
        )

        return roadmap[:6]


    def generate_resume_rewrite(
        self,
        resume,
        job_description,
        job_role,
        matched_skills
    ):

        experience = extract_experience(resume)
        summary_parts = [
            f"Professional targeting {job_role} opportunities."
        ]

        if experience["duration_mentions"]:
            summary_parts.append(
                "The resume indicates "
                + ", ".join(experience["duration_mentions"][:2])
                + " of experience."
            )

        if experience["job_titles"]:
            summary_parts.append(
                "Relevant titles listed include "
                + ", ".join(experience["job_titles"][:3])
                + "."
            )

        if matched_skills:
            summary_parts.append(
                "Relevant skills evidenced in the resume include "
                + ", ".join(sorted(matched_skills)[:8])
                + "."
            )

        resume_lines = [
            re.sub(r"^\s*[•▪●*-]\s*", "", line).strip()
            for line in resume.splitlines()
            if line.strip()
        ]
        evidence = []

        for line in resume_lines:
            if re.search(
                r"[\w.+-]+@[\w-]+\.[a-z]{2,}"
                r"|(?:\+?\d[\d\s().-]{8,})"
                r"|(?:https?://|linkedin\.com|github\.com)",
                line,
                re.IGNORECASE
            ):
                continue

            line_skills = extract_skill_tokens(
                line,
                list(matched_skills)
            )
            relevance = keyword_overlap(
                line,
                job_description
            )

            if line_skills or re.search(r"\d", line) or relevance >= 0.12:
                evidence.append(
                    (relevance, line_skills, line)
                )

        evidence.sort(
            key=lambda item: (item[0], len(item[1]), len(item[2])),
            reverse=True
        )

        return {
            "summary": " ".join(summary_parts),
            "bullets": [
                line
                for _, _, line in evidence[:5]
            ]
        }


    def generate_suggestions(

        self,

        resume,

        job_description,

        matched_skills,

        missing_skills,

        ats,

        quality,

        semantic_score,

        keyword_score

    ):

        suggestions = []


        # Missing skills

        if missing_skills:

            missing = ", ".join(
                list(missing_skills)[:8]
            )

            suggestions.append(

                "Consider adding these relevant "
                "skills if you genuinely have them: "
                + missing

            )


        # Semantic score

        if semantic_score < 50:

            suggestions.append(

                "Improve semantic alignment by "
                "rewriting your professional summary "
                "and experience bullets to better match "
                "the target job responsibilities."

            )


        # Keyword score

        if keyword_score < 50:

            suggestions.append(

                "Use important keywords from the "
                "job description naturally in your "
                "resume where they accurately describe "
                "your experience."

            )


        # ATS

        if ats < 70:

            suggestions.append(

                "Improve ATS compatibility by using "
                "standard headings such as Summary, "
                "Skills, Experience, Education and Projects."

            )


        # Quality

        if quality < 70:

            suggestions.append(

                "Improve resume quality by using "
                "clear bullet points, consistent formatting "
                "and measurable achievements."

            )


        # Resume length

        word_count = len(
            resume.split()
        )

        if word_count < 300:

            suggestions.append(

                "Your resume is quite short. "
                "Add relevant projects, experience, "
                "technical skills and achievements."

            )


        if word_count > 1200:

            suggestions.append(

                "Your resume is lengthy. "
                "Remove outdated or irrelevant "
                "information and focus on important achievements."

            )


        # Email

        if not re.search(

            r"[\w.+-]+@[\w-]+\.[a-z]{2,}",

            resume,

            re.IGNORECASE

        ):

            suggestions.append(

                "Add a professional email address."

            )


        # GitHub / LinkedIn

        if not re.search(

            r"github|linkedin|portfolio|gitlab",

            resume,

            re.IGNORECASE

        ):

            suggestions.append(

                "Add your GitHub, LinkedIn or portfolio "
                "link if relevant."

            )


        # Quantified achievements

        numbers = re.findall(

            r"\b\d+(?:\.\d+)?%?\b",

            resume

        )

        if len(numbers) < 3:

            suggestions.append(

                "Add measurable achievements such as "
                "percentage improvements, project size, "
                "users served or performance improvements."

            )


        if not suggestions:

            suggestions.append(

                "Your resume is well aligned. "
                "Continue using measurable achievements "
                "and job-specific keywords."

            )


        return suggestions[:10]


# ============================================================
# MULTIPLE JOB ROLE COMPARISON
# ============================================================

def compare_roles(
    resume_text,
    selected_roles
):

    results = []

    for role in selected_roles:

        skills = skills_for_role(role)

        matched = extract_skill_tokens(
            resume_text,
            skills
        )

        if skills:

            score = round(

                len(matched)
                / len(skills)
                * 100

            )

        else:

            score = 0


        results.append({

            "role":
                role,

            "score":
                score,

            "matched":
                sorted(matched)

        })


    results.sort(

        key=lambda x: x["score"],

        reverse=True

    )

    return results