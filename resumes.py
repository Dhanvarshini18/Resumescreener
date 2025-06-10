import streamlit as st
import PyPDF2
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import google.generativeai as genai
import os

# Configure Gemini API key from Streamlit secrets
genai.configure(api_key="AIzaSyBYTDmlXHHg9SGYDBA-mimwffrYuSruLZc")

# Initialize session state
if "resumes" not in st.session_state:
    st.session_state.resumes = []
if "criteria" not in st.session_state:
    st.session_state.criteria = ""
if "analysis_depth" not in st.session_state:
    st.session_state.analysis_depth = "Basic"
if "report" not in st.session_state:
    st.session_state.report = None

# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return None

# Function to generate screening report using Gemini API
def generate_screening_report(resume_text, criteria, depth):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Analyze the following resume against the provided job criteria and generate a screening report.
    Resume: {resume_text}
    Job Criteria: {criteria}
    Analysis Depth: {depth}
    Provide a structured report with:
    - Candidate Summary (if name is available)
    - Match Score (0-100)
    - Strengths
    - Gaps
    Return the report in markdown format.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return None

# Function to create PDF from report
def create_pdf_report(report_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Resume Screening Report", styles["Title"]))
    story.append(Spacer(1, 12))
    for line in report_text.split("\n"):
        story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 12))
    doc.build(story)
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Resume Screening Application")
st.markdown("""
Upload one or more resumes and specify job criteria to generate a screening report.
Select the analysis depth and download the report as a PDF.
""")

# Resume upload
uploaded_files = st.file_uploader("Upload Resumes (PDF or Text)", accept_multiple_files=True, type=["pdf", "txt"])
if uploaded_files:
    st.session_state.resumes = []
    for file in uploaded_files:
        if file.type == "application/pdf":
            text = extract_text_from_pdf(file)
        else:
            text = file.read().decode("utf-8")
        if text:
            st.session_state.resumes.append({"name": file.name, "text": text})
    st.success(f"Uploaded {len(st.session_state.resumes)} resume(s)")

# Screening criteria input
st.subheader("Job Criteria")
st.session_state.criteria = st.text_area("Enter job requirements (e.g., skills, experience, education)", value=st.session_state.criteria)
skills = st.multiselect("Select required skills", ["Python", "Java", "SQL", "Project Management", "Communication"], default=[])
if skills:
    st.session_state.criteria += "\nRequired Skills: " + ", ".join(skills)

# Analysis depth
st.session_state.analysis_depth = st.selectbox("Analysis Depth", ["Basic", "Detailed"], index=["Basic", "Detailed"].index(st.session_state.analysis_depth))

# Generate report
if st.button("Generate Report") and st.session_state.resumes:
    with st.spinner("Generating screening report..."):
        reports = []
        for resume in st.session_state.resumes:
            report = generate_screening_report(resume["text"], st.session_state.criteria, st.session_state.analysis_depth)
            if report:
                reports.append(f"### Report for {resume['name']}\n{report}")
        st.session_state.report = "\n\n".join(reports)
        st.markdown(st.session_state.report)

# Regenerate report
if st.button("Regenerate Report") and st.session_state.resumes and st.session_state.report:
    with st.spinner("Regenerating screening report..."):
        reports = []
        for resume in st.session_state.resumes:
            report = generate_screening_report(resume["text"], st.session_state.criteria, st.session_state.analysis_depth)
            if report:
                reports.append(f"### Report for {resume['name']}\n{report}")
        st.session_state.report = "\n\n".join(reports)
        st.markdown(st.session_state.report)

# Download report as PDF
if st.session_state.report:
    pdf_buffer = create_pdf_report(st.session_state.report)
    st.download_button(
        label="Download Report as PDF",
        data=pdf_buffer,
        file_name="resume_screening_report.pdf",
        mime="application/pdf"
    )