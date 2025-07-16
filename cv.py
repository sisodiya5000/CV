import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import fitz  # PyMuPDF
import concurrent.futures

# Folders
UPLOAD_FOLDER = "cv_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extract info from PDF
def extract_cv_info_from_pdf(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            text = "\n".join([page.get_text() for page in doc])

        name_match = re.search(r"(?i)([A-Z][a-z]+\s[A-Z][a-z]+)", text)
        name = name_match.group(1) if name_match else os.path.basename(pdf_path).split("_")[0]

        email = re.search(r"[\w\.-]+@[\w\.-]+", text)
        phone = re.search(r"(?:(?:\+91[-\s]?)?|0)?[6-9]\d{9}", text)
        exp = re.search(r"(\d+\+?\s*(?:years?|yrs?|yr|year|experience|exp))", text, re.IGNORECASE)
        education = re.findall(r"(?i)(B\.?Tech|M\.?Tech|MBA|B\.?Sc|M\.?Sc|PGDC|Diploma|B\.?E|M\.?E)[^\n]{0,60}", text)

        edu = ", ".join(set([e.strip() for e in education])) if education else "Not Found"
        summary = f"{name} has experience in {edu.lower()} with approx. {exp.group(1).lower() if exp else 'unknown experience length'}. Contact: {email.group(0) if email else 'no email'}."

        return {
            "Name": name,
            "Email": email.group(0) if email else "Not Found",
            "Phone": phone.group(0) if phone else "Not Found",
            "Experience": exp.group(1) if exp else "Not Found",
            "Education": edu,
            "Summary": summary
        }
    except Exception as e:
        return {
            "Name": "Error",
            "Email": str(e),
            "Phone": "-", "Experience": "-", "Education": "-", "Summary": "-"
        }

@st.cache_data
def load_database():
    if os.path.exists("cv_database.csv"):
        return pd.read_csv("cv_database.csv")
    return pd.DataFrame(columns=["Name", "Email", "Phone", "Experience", "Education", "Summary"])

# Save uploaded files to disk
def save_uploaded_files(uploaded_files):
    saved_paths = []
    for file in uploaded_files:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{file.name}")
        with open(save_path, "wb") as f:
            f.write(file.read())
        saved_paths.append(save_path)
    return saved_paths

# Use multiple threads for faster processing
def process_files_parallel(file_paths, max_workers=8):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(extract_cv_info_from_pdf, file_paths))
    return results

# Streamlit UI
st.set_page_config(page_title="Optimized CV Uploader", layout="wide")
st.title("⚡ Optimized CV Management Dashboard")

# Sidebar for uploads
with st.sidebar:
    st.header("📤 Upload CVs")
    uploaded_files = st.file_uploader("Upload CV Files (PDF only)", type=["pdf"], accept_multiple_files=True)

df = load_database()

if uploaded_files:
    with st.status("🚀 Uploading and processing CVs...", expanded=True) as status:
        paths = save_uploaded_files(uploaded_files)
        st.write(f"📁 Saved {len(paths)} files to disk.")
        
        results = process_files_parallel(paths)
        new_df = pd.DataFrame(results)

        df = pd.concat([df, new_df], ignore_index=True).drop_duplicates(subset="Email")
        df = df.sort_values(by="Name").reset_index(drop=True)
        df.to_csv("cv_database.csv", index=False)

        status.update(label="✅ All CVs processed and saved!", state="complete")
    st.success(f"{len(uploaded_files)} CVs uploaded and extracted successfully!")

# Display the database
st.subheader("📄 Extracted CV Data")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.download_button("📥 Download CSV", df.to_csv(index=False), "cv_database.csv")
else:
    st.info("No CVs available. Upload some to get started.")
