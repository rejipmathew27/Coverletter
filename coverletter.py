import streamlit as st
import PyPDF2
import requests
import openai
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Streamlit UI
st.title("AI Cover Letter and Resume Updater ✨")
st.subheader("Upload your resume and provide job description (OpenAI API)")

# Input for OpenAI API Key
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")

# File upload section
uploaded_file = st.file_uploader("Upload PDF Resume", type="pdf")

# Job description input method
input_method = st.radio("Job Description Input Method:",
                        ["Paste Text", "Web Link"],
                        horizontal=True)

job_description = ""
if input_method == "Paste Text":
    job_description = st.text_area("Paste Job Description", height=300,
                                   help="Paste the job description here.",
                                   key="job_desc_text",
                                   placeholder="Enter job description...",
                                   )
    st.markdown("""
    <style>
        textarea[data-baseweb="base-input"] {
            background-color: #f0f8ff !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    url = st.text_input("Enter Job Description URL")
    if url:
        with st.spinner("Fetching job description..."):
            job_description = fetch_job_description(url)

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF resume"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def generate_cover_letter(resume_text, job_description, openai_api_key):
    """Generate cover letter using OpenAI API"""
    openai.api_key = openai_api_key
    prompt = f"""
    Write a cover letter based on this resume and job description.

    Resume:
    {resume_text[:3000]}

    Job Description:
    {job_description[:3000]}

    Cover Letter:
    """

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        st.error(f"Error generating cover letter: {str(e)}")
        return None

def update_resume(resume_text, job_description, openai_api_key):
    """Update resume using OpenAI API"""
    openai.api_key = openai_api_key
    prompt = f"""
    Update the resume based on the job description, highlighting relevant skills and experiences.

    Resume:
    {resume_text[:3000]}

    Job Description:
    {job_description[:3000]}

    Updated Resume:
    """

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=600,
            temperature=0.6,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        st.error(f"Error updating resume: {str(e)}")
        return None

def create_pdf_from_text(text):
    """Create a PDF from the given text."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    textobject = p.beginText(50, 750)
    textobject.setFont("Helvetica", 12)
    lines = text.split('\n')
    for line in lines:
        textobject.textLine(line)
    p.drawText(textobject)
    p.save()
    buffer.seek(0)
    return buffer

def fetch_job_description(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return ""

if st.button("Generate Cover Letter and Update Resume"):
    if not openai_api_key:
        st.error("Please enter your OpenAI API key.")
    elif uploaded_file and job_description.strip():
        with st.spinner("Analyzing resume and generating cover letter/updated resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            cover_letter = generate_cover_letter(resume_text, job_description, openai_api_key)
            updated_resume = update_resume(resume_text, job_description, openai_api_key)

            if cover_letter and updated_resume:
                st.success("Cover Letter and Updated Resume Generated Successfully!")
                st.markdown("---")
                cover_letter_text = st.text_area("Generated Cover Letter", value=cover_letter, height=300)
                updated_resume_text = st.text_area("Updated Resume", value=updated_resume, height=300)

                st.download_button(
                    label="Download Cover Letter",
                    data=cover_letter_text,
                    file_name="generated_cover_letter.txt",
                    mime="text/plain"
                )

                resume_pdf = create_pdf_from_text(updated_resume)
                st.session_state['resume_pdf'] = resume_pdf

    else:
        missing = []
        if not uploaded_file: missing.append("resume")
        if not job_description.strip(): missing.append("job description")
        if not openai_api_key: missing.append("OpenAI API key")
        st.warning(f"Please provide: {', '.join(missing)}")

if 'resume_pdf' in st.session_state:
    st.download_button(
        label="Download Updated Resume (PDF)",
        data=st.session_state['resume_pdf'],
        file_name="updated_resume.pdf",
        mime="application/pdf"
    )

# Add some styling
st.markdown("""
<style>
    .stTextArea [data-baseweb=base-input] {
        background-color: #f5f5f5;
    }
    .stDownloadButton button {
        background-color: #4CAF50;
        color: white;
    }
    div[data-baseweb="radio"] label {
        padding: 8px;
        border-radius: 4px;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)
