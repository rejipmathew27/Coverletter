import streamlit as st
import PyPDF2
import requests
import openai
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class CoverLetterAI:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        self.resume_text = None
        self.job_description = None
        self.candidate_profile = None

    def read_resume(self, uploaded_file):
        """Reads the resume from a PDF file."""
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            self.resume_text = text
            return True
        except Exception as e:
            st.error(f"Error reading resume: {str(e)}")
            return False

    def profile_candidate(self):
        """Creates a candidate profile (JSON) from the resume text."""
        openai.api_key = self.openai_api_key
        prompt = f"""
        Analyze the following resume and create a JSON object containing key information like name, contact details, skills, experience, and education.

        Resume:
        {self.resume_text[:3000]}

        JSON:
        """
        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=800,
                temperature=0.5,
            )
            self.candidate_profile = json.loads(response.choices[0].text.strip())
            return True
        except Exception as e:
            st.error(f"Error creating candidate profile: {str(e)}")
            return False

    def set_job_description(self, job_description):
        """Sets the job description."""
        self.job_description = job_description

    def write_cover_letter(self):
        """Generates a cover letter based on the candidate profile and job description."""
        openai.api_key = self.openai_api_key
        prompt = f"""
        Write a cover letter based on the following candidate profile and job description.

        Candidate Profile:
        {json.dumps(self.candidate_profile, indent=4)}

        Job Description:
        {self.job_description[:3000]}

        Cover Letter:
        """
        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=600,
                temperature=0.7,
            )
            return response.choices[0].text.strip()
        except Exception as e:
            st.error(f"Error writing cover letter: {str(e)}")
            return None

def fetch_job_description(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return ""

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

# Streamlit UI
st.title("AI Cover Letter Generator ✨")
st.subheader("Upload your resume and provide job description (OpenAI API)")

openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")
uploaded_file = st.file_uploader("Upload PDF Resume", type="pdf")

input_method = st.radio("Job Description Input Method:", ["Paste Text", "Web Link"], horizontal=True)

job_description = ""
if input_method == "Paste Text":
    job_description = st.text_area("Paste Job Description", height=300, key="job_desc_text", placeholder="Enter job description...", help="Paste the job description here.")
    st.markdown("""<style>textarea[data-baseweb="base-input"] {background-color: #f0f8ff !important;}</style>""", unsafe_allow_html=True)
else:
    url = st.text_input("Enter Job Description URL")
    if url:
        with st.spinner("Fetching job description..."):
            job_description = fetch_job_description(url)

if st.button("Generate Cover Letter"):
    if not openai_api_key:
        st.error("Please enter your OpenAI API key.")
    elif uploaded_file and job_description.strip():
        with st.spinner("Analyzing resume and generating cover letter..."):
            ai = CoverLetterAI(openai_api_key)
            if ai.read_resume(uploaded_file) and ai.profile_candidate():
                ai.set_job_description(job_description)
                cover_letter = ai.write_cover_letter()
                if cover_letter:
                    st.success("Cover Letter Generated Successfully!")
                    st.markdown("---")
                    cover_letter_text = st.text_area("Generated Cover Letter", value=cover_letter, height=300)
                    st.download_button(label="Download Cover Letter", data=cover_letter_text, file_name="generated_cover_letter.txt", mime="text/plain")
    else:
        missing = []
        if not uploaded_file: missing.append("resume")
        if not job_description.strip(): missing.append("job description")
        if not openai_api_key: missing.append("OpenAI API key")
        st.warning(f"Please provide: {', '.join(missing)}")

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
