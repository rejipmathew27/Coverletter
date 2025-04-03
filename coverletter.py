import streamlit as st
import PyPDF2
import requests
import openai
import os
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
    Create a professional cover letter based on the following resume and job description.
    The cover letter should:
    - Be addressed to the hiring manager
    - Highlight relevant experience from the resume
    - Match qualifications to the job requirements
    - Maintain professional tone
    - Be approximately 3-4 paragraphs

    Resume:
    {resume_text[:3000]}  # Truncate to prevent context overflow

    Job Description:
    {job_description[:3000]}
    """

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",  # Or another suitable engine
            prompt=prompt,
            max_tokens=400,  # Adjust as needed
            temperature=0.7,  # Adjust for creativity
        )
        return response.choices[0].text.strip()
    except Exception as e:
        st.error(f"Error generating cover letter: {str(e)}")
        return None

def update_resume(resume_text, job_description, openai_api_key):
    """Update resume using OpenAI API"""
    openai.api_key = openai_api_key
    prompt = f"""
    Update the following resume based on the job description.
    Ensure the resume highlights relevant skills and experience for the job.
    Only add or modify details that are directly applicable to the job description.

    Resume:
    {resume_text[:3000]}

    Job Description:
    {job_description[:3000]}
    """

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",  # Or another suitable engine
            prompt=prompt,
            max_tokens=500,  # Adjust as needed
            temperature=0.6,  # Adjust for creativity
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
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return ""

if st.button("Generate Cover Letter and Update Resume"):
    if not openai_api_key:
        st.error("Please enter your OpenAI API key.")
    elif uploaded_file and job_description.strip():
        with st.spinner("Analyzing resume and generating cover letter/updated resume..."):
            # Extract text from PDF
            resume_text = extract_text_from_pdf(uploaded_file)

            # Generate cover letter
            cover_letter = generate_cover_letter(resume_text, job_description, openai_api_key)

            # Update resume
            updated_resume = update_resume(resume_text, job_description, openai_api_key)

            if cover_letter and updated_resume:
                st.success("Cover Letter and Updated Resume Generated Successfully!")
                st.markdown("---")
                # Display cover letter in a text area
                cover_letter_text = st.text_area("Generated Cover Letter", value=cover_letter, height=300)

                # Display updated resume
                updated_resume_text = st.text_area("Updated Resume", value=updated_resume, height=300)

                # Add download buttons
                st.download_button(
                    label="Download Cover Letter",
                    data=cover_letter_text,
                    file_name="generated_cover_letter.txt",
                    mime="text/plain"
                )

                resume_pdf = create_pdf_from_text(updated_resume)
                st.session_state['resume_pdf'] = resume_pdf #store the created pdf in session state

    else:
        missing = []
        if not uploaded_file: missing.append("resume")
        if not job_description.strip(): missing.append("job description")
        if not openai_api_key: missing.append("OpenAI API key")
        st.warning(f"Please provide: {', '.join(missing)}")

if 'resume_pdf' in st.session_state: #seperate button to download resume
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
