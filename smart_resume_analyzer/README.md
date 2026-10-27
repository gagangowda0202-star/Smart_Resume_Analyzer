# Smart Resume Analyzer

A Streamlit app for comparing resume text with a target job description, highlighting skill gaps, and preparing a targeted resume draft and career plan.

---

## ✨ Features

| Feature | Description |
|---|---|
| Feature | Description |
|---|---|
| Resume input | Upload PDF, DOCX, or TXT files, or paste/edit resume text |
| Live matching | Update skill and keyword match previews as resume or job text changes |
| Semantic matching | Compare resume and job-description meaning with Sentence Transformers, with a TF-IDF fallback |
| Skill-gap heatmap | See matched and missing job skills at a glance |
| Job recommendations | View role-fit suggestions that respond to resume edits |
| Resume rewrite draft | Create and edit a local, evidence-based summary and experience highlights |
| Career roadmap | Get next-step suggestions based on missing role skills |
| Interview preparation | Review role-specific prompts based on matched and missing skills |
| Reports and history | Download a PDF report and review saved scores |

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 📁 Project Structure

```
smart_resume_analyzer/
├── app.py              # Streamlit UI
├── analyzer.py         # NLP engine (skill extraction + scoring)
├── requirements.txt    # Python dependencies
└── README.md
```

---

## How It Works

```
Resume text + job description
        │
        ├── Live skill and keyword preview
        ├── Role recommendations
        └── Full analysis on submit
               ├── Skill match (35%)
               ├── Semantic similarity (30%)
               ├── Keyword overlap (20%)
               └── ATS score (15%)
                        │
                        └── Heatmap, rewrite draft, roadmap,
                            interview prep, and downloadable report
```

---

## 🎯 Supported Job Roles

- Software Engineer
- Data Scientist
- Machine Learning Engineer
- Frontend Developer
- Backend Developer
- Full Stack Developer
- DevOps Engineer
- Cloud Architect
- Data Analyst
- Business Analyst
- Product Manager
- UI/UX Designer
- QA Engineer
- Database Administrator
- Mobile App Developer
- Cybersecurity Analyst

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `pdfplumber` | PDF text extraction |
| `docx2txt` | DOCX text extraction |
| `sentence-transformers` | Local semantic matching model |
| `scikit-learn` | TF-IDF fallback support |

Semantic matching uses the local `all-MiniLM-L6-v2` model when available and falls back to TF-IDF if it cannot be loaded. The first model use may require downloading model files. Basic skill and keyword matching does not depend on the model.

## Privacy

Resume and job-description text are processed by the app and are not sent to an external LLM. The rewrite draft uses only information extracted from the resume; review it for accuracy before use. Analysis history stores the filename, role, timestamp, and scores, not the resume text.

---

## 💡 Tips for Best Results

1. Upload a **text-based PDF** (not scanned image)
2. Paste the **full job description** including requirements
3. Select the closest **job role category**
4. Use the missing skills list to **update your resume**
5. Re-analyze after improvements to see your score rise!
