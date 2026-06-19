import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Hiring System",
    page_icon="",
    layout="wide"
)

st.title("AI Hiring System")
st.caption("Automated CV Analysis, AI Interviews & Candidate Ranking")

# ── Upload Section ─────────────────────────────────────────────
st.header(" Upload CVs")

job_description = st.text_area("Job Description", height=100)
uploaded_files = st.file_uploader("Upload CVs (PDF)", type="pdf", accept_multiple_files=True)

if st.button(" Start Analysis", type="primary"):
    if not job_description or not uploaded_files:
        st.error("Please add job description and CVs")
    else:
        with st.spinner("Uploading..."):
            files = [("files", (f.name, f.read(), "application/pdf")) for f in uploaded_files]
            response = requests.post(
                f"{API_URL}/upload-cvs",
                data={"job_description": job_description},
                files=files
            )
            session_id = response.json()["session_id"]
            st.session_state["session_id"] = session_id

            requests.post(f"{API_URL}/analyze/{session_id}")
            st.success(f" Analysis started!")
            st.info(f"Session ID: {session_id}")

# ── Status Section ─────────────────────────────────────────────
if "session_id" in st.session_state:
    st.header(" Results")
    
    if st.button("Check Status"):
        session_id = st.session_state["session_id"]
        status = requests.get(f"{API_URL}/status/{session_id}").json()
        
        if status["status"] == "complete":
            report = requests.get(f"{API_URL}/report/{session_id}").json()
            st.success("Analysis Complete!")
            if "report" in report and report["report"]:
             st.text(report["report"])
            else:
             st.json(report)
        elif status["status"] == "processing":
            st.warning(" Still processing, check again in 30 seconds")
        else:
            st.error(f" Failed: {status.get('error', 'Unknown error')}")