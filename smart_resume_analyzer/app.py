import io
import hashlib
import re

import streamlit as st
import pdfplumber
import docx2txt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from analyzer import (
    ResumeAnalyzer,
    ROLE_SKILLS,
    compare_roles,
    live_match_preview
)


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Smart Resume Analyzer",
    page_icon="✦",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #faf6f0;
    color: #183b2a;
}

header[data-testid="stHeader"] {
    background-color: #183b2a;
}

header[data-testid="stHeader"] * {
    color: #f7f4ed !important;
}

.stApp [data-testid="stTextArea"] textarea {
    background-color: #262730 !important;
    color: #f7f4ed !important;
    caret-color: #f7f4ed;
}

.stApp [data-testid="stTextArea"] textarea::placeholder {
    color: #b7cbbd !important;
    opacity: 1;
}

.stApp [data-testid="stFileUploaderDropzone"] {
    background-color: #fffdf9 !important;
    border: 1px dashed #8d9b8e !important;
}

.stApp [data-testid="stFileUploaderDropzone"] p,
.stApp [data-testid="stFileUploaderDropzone"] span {
    color: #183b2a !important;
}

.stApp [data-testid="stFileUploaderDropzone"] button {
    background-color: #183b2a !important;
    border-color: #183b2a !important;
}

.stApp [data-testid="stFileUploaderDropzone"] button * {
    color: #faf6f0 !important;
}

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp p,
.stApp label,
.stApp [data-testid="stMarkdownContainer"] {
    color: #183b2a;
}

.main-title {
    background-color: #183b2a;
    padding: 45px;
    border-radius: 0 0 20px 20px;
    margin-bottom: 30px;
}

.main-title h1 {
    color: #f4c45d;
    font-size: 48px;
}

.main-title p {
    color: #b7cbbd;
    font-size: 18px;
}

.section-title {
    color: #183b2a;
    font-size: 22px;
    font-weight: bold;
    margin-top: 20px;
}

.metric-box {
    background-color: #183b2a;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}

.metric-number {
    color: #f4c45d;
    font-size: 32px;
    font-weight: bold;
}

.metric-label {
    color: white;
    font-size: 14px;
}

.skill-match {
    display: inline-block;
    background-color: #d8f0e4;
    color: #155c38;
    padding: 7px 12px;
    border-radius: 20px;
    margin: 4px;
}

.skill-missing {
    display: inline-block;
    background-color: #fde2e2;
    color: #8a2020;
    padding: 7px 12px;
    border-radius: 20px;
    margin: 4px;
}

.skill-learn {
    display: inline-block;
    background-color: #fff0c9;
    color: #765000;
    padding: 7px 12px;
    border-radius: 20px;
    margin: 4px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="main-title">

<h1>
Your Resume.<br>
Analyzed. Optimized.
</h1>

<p>
AI-powered resume analysis with semantic matching,
ATS scoring, skill-gap detection and career recommendations.
</p>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def extract_text(uploaded_file):

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):

        with pdfplumber.open(uploaded_file) as pdf:

            pages = []

            for page in pdf.pages:

                text = page.extract_text()

                if text:

                    pages.append(text)

            return "\n".join(pages)


    elif filename.endswith(".docx"):

        return docx2txt.process(
            uploaded_file
        )


    elif filename.endswith(".txt"):

        return uploaded_file.read().decode(
            "utf-8",
            errors="ignore"
        )


    return ""


# ============================================================
# SKILL DISPLAY
# ============================================================

def display_skills(
    skills,
    css_class
):

    if not skills:

        return "<p>No skills detected.</p>"

    html = ""

    for skill in skills:

        html += (
            f'<span class="{css_class}">'
            f'{skill}'
            f'</span>'
        )

    return html


def format_resume_draft(
    resume_text,
    result,
    target_role
):

    source_lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]
    contact_pattern = re.compile(
        r"[\w.+-]+@[\w-]+\.[a-z]{2,}"
        r"|(?:\+?\d[\d\s().-]{8,})"
        r"|(?:https?://|www\.|linkedin\.com|github\.com|gitlab\.com)",
        re.IGNORECASE
    )
    heading_map = {
        "summary": "EXISTING SUMMARY",
        "professional summary": "EXISTING SUMMARY",
        "objective": "EXISTING SUMMARY",
        "profile": "EXISTING SUMMARY",
        "experience": "EXPERIENCE",
        "professional experience": "EXPERIENCE",
        "work experience": "EXPERIENCE",
        "employment": "EXPERIENCE",
        "work history": "EXPERIENCE",
        "education": "EDUCATION",
        "skills": "SKILLS",
        "technical skills": "SKILLS",
        "projects": "PROJECTS",
        "certifications": "CERTIFICATIONS",
        "certificates": "CERTIFICATIONS",
        "awards": "AWARDS",
        "honors": "AWARDS",
        "languages": "LANGUAGES",
        "publications": "PUBLICATIONS",
        "volunteering": "VOLUNTEERING",
        "volunteer experience": "VOLUNTEERING",
        "interests": "ADDITIONAL INFORMATION",
        "additional information": "ADDITIONAL INFORMATION",
        "achievements": "ACHIEVEMENTS",
        "leadership": "LEADERSHIP",
    }
    sections = {}
    header_lines = []
    active_section = None

    for line in source_lines:
        heading = line.strip().rstrip(":").lower()
        if heading in heading_map:
            active_section = heading_map[heading]
            sections.setdefault(active_section, [])
        elif active_section is None:
            header_lines.append(line)
        else:
            sections[active_section].append(line)

    # Keep every unclassified line rather than dropping source resume content.
    if not sections:
        header_lines = []
        sections["EXPERIENCE"] = list(source_lines)

    lines = []
    if header_lines:
        lines.extend(header_lines)

    lines.extend([
        "",
        "TARGET ROLE",
        target_role,
        "",
        "PROFESSIONAL SUMMARY",
        result.get("resume_rewrite", {}).get(
            "summary",
            "Experienced professional seeking a relevant opportunity."
        ),
    ])

    original_summary = sections.get("EXISTING SUMMARY", [])
    if original_summary:
        lines.extend(["", "EXISTING SUMMARY DETAILS"])
        lines.extend(original_summary)

    section_order = [
        "SKILLS",
        "EXPERIENCE",
        "EDUCATION",
        "PROJECTS",
        "CERTIFICATIONS",
        "AWARDS",
        "ACHIEVEMENTS",
        "LANGUAGES",
        "PUBLICATIONS",
        "VOLUNTEERING",
        "LEADERSHIP",
        "ADDITIONAL INFORMATION",
    ]
    for section_name in section_order:
        content = sections.get(section_name, [])
        if section_name == "SKILLS":
            matched_skills = sorted(set(result.get("matched_skills", [])))
            if matched_skills:
                content = content + [
                    "Role-matched skills: " + ", ".join(matched_skills)
                ]
        if section_name == "EDUCATION" and not content:
            content = list(result.get("education", []))
        if content:
            lines.extend(["", section_name])
            lines.extend(content)

    unhandled = [
        section for section in sections
        if section not in section_order
        and section != "EXISTING SUMMARY"
    ]
    for section_name in unhandled:
        lines.extend(["", section_name])
        lines.extend(sections[section_name])

    return "\n".join(lines).strip()


# ============================================================
# PDF REPORT
# ============================================================

def create_pdf_report(
    result,
    filename,
    role
):

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    story = []


    # Title

    story.append(
        Paragraph(
            "Smart Resume Analyzer",
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 15)
    )


    # Basic information

    story.append(
        Paragraph(
            f"<b>Resume:</b> {filename}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Target Job:</b> {role}",
            styles["BodyText"]
        )
    )

    story.append(
        Spacer(1, 15)
    )


    # Score table

    score_data = [

        ["Metric", "Score"],

        [
            "Overall Match",
            f"{result['match_score']}%"
        ],

        [
            "ATS Compatibility",
            f"{result['ats_score']}%"
        ],

        [
            "Resume Quality",
            f"{result['quality_score']}%"
        ],

        [
            "Skill Match",
            f"{result['skill_score']}%"
        ],

        [
            "Semantic Match",
            f"{result['semantic_score']}%"
        ],

        [
            "Keyword Match",
            f"{result['keyword_score']}%"
        ]

    ]


    score_table = Table(
        score_data,
        colWidths=[250, 120]
    )


    score_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#183b2a")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])
    )


    story.append(
        score_table
    )

    story.append(
        Spacer(1, 20)
    )


    # Matched skills

    story.append(
        Paragraph(
            "Matched Skills",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            ", ".join(
                result["matched_skills"]
            )
            or "None",
            styles["BodyText"]
        )
    )


    story.append(
        Spacer(1, 12)
    )


    # Missing skills

    story.append(
        Paragraph(
            "Missing Skills",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            ", ".join(
                result["missing_skills"]
            )
            or "None",
            styles["BodyText"]
        )
    )


    story.append(
        Spacer(1, 12)
    )


    # Education

    story.append(
        Paragraph(
            "Education",
            styles["Heading2"]
        )
    )

    if result["education"]:

        for education in result["education"]:

            story.append(
                Paragraph(
                    "• " + education,
                    styles["BodyText"]
                )
            )

    else:

        story.append(
            Paragraph(
                "Education not detected.",
                styles["BodyText"]
            )
        )


    story.append(
        Spacer(1, 12)
    )


    # Experience

    story.append(
        Paragraph(
            "Experience",
            styles["Heading2"]
        )
    )

    experience = result[
        "experience"
    ]

    story.append(
        Paragraph(
            "<b>Job Titles:</b> "
            +
            (
                ", ".join(
                    experience["job_titles"]
                )
                or "Not detected"
            ),
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            "<b>Experience Duration:</b> "
            +
            (
                ", ".join(
                    experience[
                        "duration_mentions"
                    ]
                )
                or "Not detected"
            ),
            styles["BodyText"]
        )
    )


    story.append(
        Spacer(1, 12)
    )


    # Suggestions

    story.append(
        Paragraph(
            "Resume Improvement Suggestions",
            styles["Heading2"]
        )
    )

    for suggestion in result[
        "suggestions"
    ]:

        story.append(
            Paragraph(
                "• " + suggestion,
                styles["BodyText"]
            )
        )

        story.append(
            Spacer(1, 5)
        )


    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# MAIN INPUT AREA
# ============================================================

if "analysis_page" not in st.session_state:
    st.session_state["analysis_page"] = "input"

current_page = st.session_state["analysis_page"]
role_list = list(ROLE_SKILLS.keys())
other_role_option = "Other role"


def sync_selected_role_from_search():
    st.session_state["selected_role_value"] = st.session_state[
        "searched_role_input"
    ]


# ============================================================
# LEFT COLUMN
# ============================================================

if current_page == "input":

    st.markdown(
        '<div class="section-title">'
        '01 — Resume'
        '</div>',
        unsafe_allow_html=True
    )


    resume_file = st.file_uploader(
        "Upload your resume",
        type=[
            "pdf",
            "docx",
            "txt"
        ]
    )

    if resume_file is not None:
        resume_signature = (
            resume_file.name,
            hashlib.sha256(resume_file.getvalue()).hexdigest()
        )
        if resume_signature != st.session_state.get(
            "uploaded_resume_signature"
        ):
            st.session_state["resume_text_input"] = extract_text(
                resume_file
            )
            st.session_state["uploaded_resume_signature"] = (
                resume_signature
            )

    resume_text = st.text_area(
        "Paste or edit resume text",
        key="resume_text_input",
        height=250,
        placeholder="Upload a resume above or paste its text here."
    )


    st.markdown(
        '<div class="section-title">'
        '02 — Job Role'
        '</div>',
        unsafe_allow_html=True
    )


    current_role_option = st.session_state.get(
        "selected_role_value",
        role_list[0]
    )
    if not st.session_state.get("role_search_input", "").strip():
        current_role_option = st.session_state.get(
            "selected_role_input",
            current_role_option
        )
    st.session_state["selected_role_value"] = current_role_option
    current_role_label = (
        st.session_state.get("custom_role_input", "").strip()
        if current_role_option == other_role_option
        else current_role_option
    ) or other_role_option
    with st.popover(
        current_role_label,
        use_container_width=True
    ):
        role_search = st.text_input(
            "Search job roles",
            key="role_search_input",
            type="search",
            icon=":material/search:",
            placeholder="Search job roles",
            live=True,
            label_visibility="collapsed"
        ).strip().casefold()
        matching_roles = [
            role for role in role_list
            if role_search in role.casefold()
        ]
        if role_search and not matching_roles:
            st.info(
                "No saved roles match that search. Choose Other role to enter "
                "a custom job title."
            )
        role_options = matching_roles + [other_role_option]
        if role_search:
            current_selection = st.session_state.get(
                "selected_role_value",
                role_options[0]
            )
            if (
                "searched_role_input" in st.session_state
                and st.session_state["searched_role_input"] not in role_options
            ):
                if current_selection in role_options:
                    st.session_state["searched_role_input"] = current_selection
                else:
                    del st.session_state["searched_role_input"]
            selected_index = (
                role_options.index(current_selection)
                if current_selection in role_options
                else None
            )
            selected_role_option = st.radio(
                "Matching job roles",
                role_options,
                index=selected_index,
                key="searched_role_input",
                on_change=sync_selected_role_from_search,
                label_visibility="collapsed"
            )
            if selected_role_option is None:
                selected_role_option = current_selection
        else:
            current_selection = st.session_state.get(
                "selected_role_value",
                role_options[0]
            )
            if current_selection not in role_options:
                current_selection = role_options[0]
                st.session_state["selected_role_value"] = current_selection
            if (
                "selected_role_input" in st.session_state
                and st.session_state["selected_role_input"] not in role_options
            ):
                st.session_state["selected_role_input"] = role_options[0]

            if "selected_role_input" not in st.session_state:
                st.session_state["selected_role_input"] = current_selection
            selected_role_option = st.selectbox(
                "Job role",
                role_options,
                key="selected_role_input",
                label_visibility="collapsed"
            )
            st.session_state["selected_role_value"] = selected_role_option

        if selected_role_option == other_role_option:
            st.text_input(
                "Enter your job role",
                key="custom_role_input",
                placeholder="e.g. Robotics Engineer"
            )
            if st.session_state.get("custom_role_input", "").strip():
                st.caption(
                    "For a custom role, skill matching uses skills detected "
                    "from your job description across the supported skill library."
                )

    if selected_role_option == other_role_option:
        selected_role = st.session_state.get(
            "custom_role_input",
            ""
        ).strip()
    else:
        selected_role = selected_role_option


    st.markdown(
        '<div class="section-title">'
        '03 — Job Description'
        '</div>',
        unsafe_allow_html=True
    )


    job_description = st.text_area(

        "Paste the complete job description",

        height=250,
        key="job_description_input",

        placeholder=
        """
Example:

We are looking for a Software Engineer
with Python, SQL, Git, REST API and
machine learning knowledge.

Responsibilities:
Develop software applications,
work with APIs and databases,
test applications and collaborate
with the development team.
"""

    )

    if resume_text.strip() and job_description.strip():
        live_preview = live_match_preview(
            resume_text,
            job_description,
            selected_role
        )
        st.subheader("Live Resume / Job Match")
        st.caption(
            "Skill and keyword scores update as you edit. "
            "Semantic AI matching runs when you analyze."
        )
        preview_col1, preview_col2 = st.columns(2)
        preview_col1.metric(
            "Required skills matched",
            f"{live_preview['skill_score']}%"
        )
        preview_col2.metric(
            "Keyword overlap",
            f"{live_preview['keyword_score']}%"
        )

        heatmap_skills = (
            live_preview["matched_skills"]
            + live_preview["missing_skills"]
        )
        if heatmap_skills:
            matched_set = set(live_preview["matched_skills"])
            heatmap = go.Figure(
                data=go.Heatmap(
                    z=[[
                        1 if skill in matched_set else 0
                        for skill in heatmap_skills
                    ]],
                    x=heatmap_skills,
                    y=["Job requirements"],
                    text=[[
                        "Matched" if skill in matched_set else "Missing"
                        for skill in heatmap_skills
                    ]],
                    colorscale=[
                        [0, "#f3a6a6"],
                        [1, "#7fcca2"]
                    ],
                    zmin=0,
                    zmax=1,
                    showscale=False,
                    hovertemplate="%{x}: %{text}<extra></extra>"
                )
            )
            heatmap.update_traces(
                texttemplate="%{text}"
            )
            heatmap.update_layout(
                title="Live Skill-gap Heatmap",
                height=150,
                margin=dict(l=10, r=10, t=45, b=10)
            )
            st.plotly_chart(
                heatmap,
                use_container_width=True
            )

        live_recommendations = pd.DataFrame(
            live_preview["job_recommendations"][:5]
        )
        if not live_recommendations.empty:
            st.markdown("**Live role recommendations**")
            st.dataframe(
                live_recommendations[["role", "score"]],
                use_container_width=True,
                hide_index=True
            )


    analyze_button = st.button(

        "✦ Analyze Resume",

        type="primary",

        use_container_width=True

    )


# ============================================================
# ANALYZE OR DISPLAY RESULTS
# ============================================================

if current_page == "input":

    if analyze_button:

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not resume_text.strip():
            st.error(
                "Please upload a resume or paste its text."
            )

            st.stop()


        if not job_description.strip():

            st.error(
                "Please enter the job description."
            )

            st.stop()

        if not selected_role:
            st.error(
                "Select a job role or enter a name for your custom role."
            )
            st.stop()


        # ----------------------------------------------------
        # RESUME TEXT
        # ----------------------------------------------------

        with st.spinner(
            "Analyzing your resume..."
        ):
            resume_text = resume_text.strip()


        # ----------------------------------------------------
        # ANALYZE
        # ----------------------------------------------------

        analyzer = ResumeAnalyzer()


        with st.spinner(
            "Running AI semantic analysis..."
        ):

            result = analyzer.analyze(

                resume_text,

                job_description,

                selected_role

            )


        # ----------------------------------------------------
        # SAVE HISTORY
        # ----------------------------------------------------

        analyzer.save_history(

            resume_file.name if resume_file else "pasted_resume.txt",

            selected_role,

            result

        )

        st.session_state["analysis_result"] = result
        st.session_state["analysis_filename"] = (
            resume_file.name if resume_file else "pasted_resume.txt"
        )
        st.session_state["analysis_role"] = selected_role
        st.session_state["analysis_resume_text"] = resume_text
        st.session_state["resume_rewrite_editor"] = format_resume_draft(
            resume_text,
            result,
            selected_role
        )
        st.session_state["analysis_page"] = "results"
        st.rerun()

else:

    with st.container():

        result = st.session_state["analysis_result"]
        resume_filename = st.session_state["analysis_filename"]
        selected_role = st.session_state["analysis_role"]
        resume_text = st.session_state["analysis_resume_text"]

        if st.button("Start New Analysis", key="start_new_analysis"):
            for key in (
                "analysis_result",
                "analysis_filename",
                "analysis_role",
                "analysis_resume_text",
                "resume_text_input",
                "selected_role_input",
                "job_description_input",
                "uploaded_resume_signature",
                "resume_rewrite_editor",
            ):
                st.session_state.pop(key, None)
            st.session_state["analysis_page"] = "input"
            st.rerun()

        st.success(
            "Resume analysis completed successfully."
        )


        # ====================================================
        # SCORE CARDS
        # ====================================================

        st.subheader(
            "Resume Analysis"
        )


        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.markdown(

                f"""
<div class="metric-box">

<div class="metric-number">
{result['match_score']}%
</div>

<div class="metric-label">
Overall Match
</div>

</div>
""",

                unsafe_allow_html=True
            )


        with col2:

            st.markdown(

                f"""
<div class="metric-box">

<div class="metric-number">
{result['ats_score']}%
</div>

<div class="metric-label">
ATS Score
</div>

</div>
""",

                unsafe_allow_html=True
            )


        with col3:

            st.markdown(

                f"""
<div class="metric-box">

<div class="metric-number">
{result['quality_score']}%
</div>

<div class="metric-label">
Resume Quality
</div>

</div>
""",

                unsafe_allow_html=True
            )


        with col4:

            st.markdown(

                f"""
<div class="metric-box">

<div class="metric-number">
{len(result['matched_skills'])}
</div>

<div class="metric-label">
Matched Skills
</div>

</div>
""",

                unsafe_allow_html=True
            )

        # ====================================================
        # SCORE BREAKDOWN
        # ====================================================

        st.subheader(
            "Score Breakdown"
        )


        score_data = pd.DataFrame({

            "Category": [

                "Technical Skills",
                "Semantic Match",
                "Keyword Match",
                "ATS Compatibility"

            ],

            "Score": [

                result["skill_score"],

                result["semantic_score"],

                result["keyword_score"],

                result["ats_score"]

            ]

        })


        chart = px.bar(

            score_data,

            x="Category",

            y="Score",

            range_y=[0, 100],

            text="Score",

            title="Resume Analysis Scores"

        )


        chart.update_layout(
            height=400
        )


        st.plotly_chart(
            chart,
            use_container_width=True
        )


        # ====================================================
        # SKILL ANALYSIS
        # ====================================================

        st.subheader(
            "Skill Gap Analysis"
        )

        heatmap_skills = (
            result["matched_skills"]
            + result["missing_skills"]
        )
        if heatmap_skills:
            matched_set = set(result["matched_skills"])
            skill_heatmap = go.Figure(
                data=go.Heatmap(
                    z=[[
                        1 if skill in matched_set else 0
                        for skill in heatmap_skills
                    ]],
                    x=heatmap_skills,
                    y=["Job requirements"],
                    text=[[
                        "Matched" if skill in matched_set else "Missing"
                        for skill in heatmap_skills
                    ]],
                    colorscale=[
                        [0, "#f3a6a6"],
                        [1, "#7fcca2"]
                    ],
                    zmin=0,
                    zmax=1,
                    showscale=False,
                    hovertemplate="%{x}: %{text}<extra></extra>"
                )
            )
            skill_heatmap.update_traces(
                texttemplate="%{text}"
            )
            skill_heatmap.update_layout(
                title="Required Skill Coverage",
                height=150,
                margin=dict(l=10, r=10, t=45, b=10)
            )
            st.plotly_chart(
                skill_heatmap,
                use_container_width=True
            )


        skill_col1, skill_col2 = st.columns(2)


        with skill_col1:

            st.markdown(
                "### ✓ Matched Skills"
            )

            st.markdown(

                display_skills(

                    result[
                        "matched_skills"
                    ],

                    "skill-match"

                ),

                unsafe_allow_html=True

            )


        with skill_col2:

            st.markdown(
                "### ✕ Missing Skills"
            )

            st.markdown(

                display_skills(

                    result[
                        "missing_skills"
                    ],

                    "skill-missing"

                ),

                unsafe_allow_html=True

            )


        # ====================================================
        # EDUCATION
        # ====================================================

        st.subheader(
            "Education Extraction"
        )


        if result["education"]:

            for education in result[
                "education"
            ]:

                st.write(
                    "🎓",
                    education
                )

        else:

            st.warning(
                "No education information detected."
            )


        # ====================================================
        # EXPERIENCE
        # ====================================================

        st.subheader(
            "Experience Extraction"
        )


        experience = result[
            "experience"
        ]


        exp_col1, exp_col2 = st.columns(2)


        with exp_col1:

            st.markdown(
                "**Job Titles**"
            )

            if experience[
                "job_titles"
            ]:

                for title in experience[
                    "job_titles"
                ]:

                    st.write(
                        "💼",
                        title
                    )

            else:

                st.write(
                    "Not detected"
                )


        with exp_col2:

            st.markdown(
                "**Experience Duration**"
            )

            if experience[
                "duration_mentions"
            ]:

                for duration in experience[
                    "duration_mentions"
                ]:

                    st.write(
                        "⏱️",
                        duration
                    )

            else:

                st.write(
                    "Not detected"
                )


        # ====================================================
        # STRENGTHS / WEAKNESSES
        # ====================================================

        st.subheader(
            "Strengths and Weaknesses"
        )

        strengths_col, weaknesses_col = st.columns(2)

        with strengths_col:
            st.markdown("### Strengths")
            for item in result.get("strengths", []):
                st.success(item)

        with weaknesses_col:
            st.markdown("### Weaknesses")
            for item in result.get("weaknesses", []):
                st.warning(item)

        # ====================================================
        # JOB RECOMMENDATIONS
        # ====================================================

        st.subheader(
            "Recommended Job Roles"
        )


        recommendations = pd.DataFrame(

            result[
                "job_recommendations"
            ]

        )


        if not recommendations.empty:

            recommendation_chart = px.bar(

                recommendations,

                x="score",

                y="role",

                orientation="h",

                range_x=[0, 100],

                text="score",

                title="Career Role Compatibility"

            )


            recommendation_chart.update_layout(
                height=450
            )


            st.plotly_chart(

                recommendation_chart,

                use_container_width=True

            )


            st.dataframe(

                recommendations[
                    [
                        "role",
                        "score"
                    ]
                ],

                use_container_width=True,

                hide_index=True

            )

        # ====================================================
        # PERSONALIZED RECOMMENDATIONS
        # ====================================================

        st.subheader(
            "Personalized Recommendations"
        )

        for number, item in enumerate(result.get("personalized_recommendations", []), start=1):
            st.info(f"{number}. {item}")

        # ====================================================
        # INTERVIEW QUESTIONS
        # ====================================================

        st.subheader(
            "Interview Questions"
        )

        for number, item in enumerate(result.get("interview_questions", []), start=1):
            st.info(f"{number}. {item}")

        # ====================================================
        # LEARNING ROADMAP
        # ====================================================

        st.subheader(
            "Skill Learning Roadmap"
        )

        for number, item in enumerate(result.get("learning_roadmap", []), start=1):
            st.warning(f"{number}. {item}")

        # ====================================================
        # RESUME IMPROVEMENT
        # ====================================================

        st.subheader(
            "Resume Improvement Suggestions"
        )


        for number, suggestion in enumerate(

            result[
                "suggestions"
            ],

            start=1

        ):

            st.info(

                f"{number}. {suggestion}"

            )

        # ====================================================
        # RESUME REWRITE DRAFT
        # ====================================================

        st.subheader(
            "Resume Rewrite Draft"
        )
        st.caption(
            "Generated locally from details already present in your resume. "
            "No resume text is sent to an external service; verify the draft "
            "and edit it before using."
        )
        rewrite_text = st.text_area(
            "Edit and copy your tailored draft",
            key="resume_rewrite_editor",
            height=260
        )
        st.download_button(
            "Download resume rewrite draft",
            data=rewrite_text,
            file_name="resume_rewrite_draft.txt",
            mime="text/plain"
        )


        # ====================================================
        # AI METHOD
        # ====================================================

        st.caption(

            "Semantic analysis method: "
            + result[
                "semantic_method"
            ]

        )


        # ====================================================
        # PDF DOWNLOAD
        # ====================================================

        st.subheader(
            "Download Report"
        )


        pdf_file = create_pdf_report(

            result,

            resume_filename,

            selected_role

        )


        st.download_button(

            label=
            "⬇ Download Complete PDF Report",

            data=pdf_file,

            file_name=
            "resume_analysis_report.pdf",

            mime=
            "application/pdf",

            use_container_width=True

        )


        # ====================================================
        # MULTIPLE JOB ROLE COMPARISON
        # ====================================================

        st.subheader(
            "Compare Multiple Job Roles"
        )


        comparison_role_options = role_list + (
            [selected_role]
            if selected_role not in role_list
            else []
        )
        compare_roles_list = st.multiselect(

            "Select job roles to compare",

            comparison_role_options,

            default=[
                selected_role
            ]

        )


        if compare_roles_list:

            comparison = compare_roles(

                resume_text,

                compare_roles_list

            )


            comparison_df = pd.DataFrame(
                comparison
            )


            st.dataframe(

                comparison_df[
                    [
                        "role",
                        "score"
                    ]
                ],

                use_container_width=True,

                hide_index=True

            )


# ============================================================
# ANALYSIS HISTORY
# ============================================================

if current_page == "results":

    st.divider()

    st.subheader(
        "Analysis History"
    )

    history_analyzer = ResumeAnalyzer()
    history = history_analyzer.get_history()

    if history:

        history_df = pd.DataFrame(
            history,
            columns=[
                "Date",
                "Resume",
                "Job Role",
                "Match Score",
                "ATS Score",
                "Quality Score"
            ]
        )
        history_df.insert(
            0,
            "Sl No.",
            range(1, len(history_df) + 1)
        )

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No previous analysis found."
        )