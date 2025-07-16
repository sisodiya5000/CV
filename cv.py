# import streamlit as st
# import pandas as pd
# import os
# import re
# from datetime import datetime
# import fitz  # PyMuPDF
# import concurrent.futures

# # Folders
# UPLOAD_FOLDER = "cv_uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Extract info from PDF
# def extract_cv_info_from_pdf(pdf_path):
#     try:
#         with fitz.open(pdf_path) as doc:
#             text = "\n".join([page.get_text() for page in doc])

#         name_match = re.search(r"(?i)([A-Z][a-z]+\s[A-Z][a-z]+)", text)
#         name = name_match.group(1) if name_match else os.path.basename(pdf_path).split("_")[0]

#         email = re.search(r"[\w\.-]+@[\w\.-]+", text)
#         phone = re.search(r"(?:(?:\+91[-\s]?)?|0)?[6-9]\d{9}", text)
#         exp = re.search(r"(\d+\+?\s*(?:years?|yrs?|yr|year|experience|exp))", text, re.IGNORECASE)
#         education = re.findall(r"(?i)(B\.?Tech|M\.?Tech|MBA|B\.?Sc|M\.?Sc|PGDC|Diploma|B\.?E|M\.?E)[^\n]{0,60}", text)

#         edu = ", ".join(set([e.strip() for e in education])) if education else "Not Found"
#         summary = f"{name} has experience in {edu.lower()} with approx. {exp.group(1).lower() if exp else 'unknown experience length'}. Contact: {email.group(0) if email else 'no email'}."

#         return {
#             "Name": name,
#             "Email": email.group(0) if email else "Not Found",
#             "Phone": phone.group(0) if phone else "Not Found",
#             "Experience": exp.group(1) if exp else "Not Found",
#             "Education": edu,
#             "Summary": summary
#         }
#     except Exception as e:
#         return {
#             "Name": "Error",
#             "Email": str(e),
#             "Phone": "-", "Experience": "-", "Education": "-", "Summary": "-"
#         }

# @st.cache_data
# def load_database():
#     if os.path.exists("cv_database.csv"):
#         return pd.read_csv("cv_database.csv")
#     return pd.DataFrame(columns=["Name", "Email", "Phone", "Experience", "Education", "Summary"])

# # Save uploaded files to disk
# def save_uploaded_files(uploaded_files):
#     saved_paths = []
#     for file in uploaded_files:
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         save_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{file.name}")
#         with open(save_path, "wb") as f:
#             f.write(file.read())
#         saved_paths.append(save_path)
#     return saved_paths

# # Use multiple threads for faster processing
# def process_files_parallel(file_paths, max_workers=8):
#     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#         results = list(executor.map(extract_cv_info_from_pdf, file_paths))
#     return results

# # Streamlit UI
# st.set_page_config(page_title="Optimized CV Uploader", layout="wide")
# st.title("⚡ Optimized CV Management Dashboard")

# # Sidebar for uploads
# with st.sidebar:
#     st.header("📤 Upload CVs")
#     uploaded_files = st.file_uploader("Upload CV Files (PDF only)", type=["pdf"], accept_multiple_files=True)

# df = load_database()

# if uploaded_files:
#     with st.status("🚀 Uploading and processing CVs...", expanded=True) as status:
#         paths = save_uploaded_files(uploaded_files)
#         st.write(f"📁 Saved {len(paths)} files to disk.")
        
#         results = process_files_parallel(paths)
#         new_df = pd.DataFrame(results)

#         df = pd.concat([df, new_df], ignore_index=True).drop_duplicates(subset="Email")
#         df = df.sort_values(by="Name").reset_index(drop=True)
#         df.to_csv("cv_database.csv", index=False)

#         status.update(label="✅ All CVs processed and saved!", state="complete")
#     st.success(f"{len(uploaded_files)} CVs uploaded and extracted successfully!")

# # Display the database
# st.subheader("📄 Extracted CV Data")
# if not df.empty:
#     st.dataframe(df, use_container_width=True)
#     st.download_button("📥 Download CSV", df.to_csv(index=False), "cv_database.csv")
# else:
#     st.info("No CVs available. Upload some to get started.")


import streamlit as st
import pandas as pd
import os
import re
import fitz  # PyMuPDF
import zipfile
import tempfile
import concurrent.futures
from datetime import datetime

# Set up folders
UPLOAD_FOLDER = "cv_uploads"
TRASH_FOLDER = "cv_trash"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

# Extract info from PDF
def extract_cv_info_from_pdf_bytes(pdf_bytes, filename="Unknown"):
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = "\n".join([page.get_text() for page in doc])

        name_match = re.search(r"(?i)([A-Z][a-z]+\s[A-Z][a-z]+)", text)
        name = name_match.group(1) if name_match else filename.split("_")[0]

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

# Process ZIP
def process_pdf_files_in_zip(zip_file):
    extracted_data = []
    with zipfile.ZipFile(zip_file, "r") as z:
        pdf_files = [f for f in z.namelist() if f.lower().endswith(".pdf")]

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(extract_cv_info_from_pdf_bytes, z.read(pdf), os.path.basename(pdf)) for pdf in pdf_files]
            for f in concurrent.futures.as_completed(futures):
                extracted_data.append(f.result())

    return extracted_data

@st.cache_data
def load_database():
    if os.path.exists("cv_database.csv"):
        return pd.read_csv("cv_database.csv")
    return pd.DataFrame(columns=["Name", "Email", "Phone", "Experience", "Education", "Summary"])

st.set_page_config(page_title="CV Dashboard", layout="wide")
st.title("📄 CV Management Dashboard with ZIP Support")

# Sidebar: Upload
with st.sidebar:
    st.header("📤 Upload CVs")
    zip_file = st.file_uploader("Upload a ZIP file of PDF CVs", type=["zip"])

df = load_database()
last_deleted_row = st.session_state.get("last_deleted", None)
trash_df = st.session_state.get("trash_bin", pd.DataFrame(columns=["Name", "Email", "Phone", "Experience", "Education", "Summary", "Deleted At"]))

# Process uploaded ZIP
if zip_file:
    with st.status("🧠 Processing ZIP file...", expanded=True) as status:
        extracted_data = process_pdf_files_in_zip(zip_file)
        new_df = pd.DataFrame(extracted_data)
        df = pd.concat([df, new_df], ignore_index=True).drop_duplicates(subset="Email")
        df = df.sort_values(by="Name").reset_index(drop=True)
        df.to_csv("cv_database.csv", index=False)
        status.update(label="✅ Extraction complete and database updated!", state="complete")
    st.success(f"{len(new_df)} CVs extracted successfully!")

# Display section
st.subheader("📄 Extracted CV Data")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("No CVs available. Upload a ZIP to begin.")

# Deletion options
st.subheader("🗑️ Delete CV")
if not df.empty:
    selected_index = st.number_input("Enter row number to delete:", min_value=0, max_value=len(df)-1, step=1)
    if st.checkbox("Confirm deletion of selected CV"):
        if st.button("Delete Selected CV"):
            try:
                row_data = df.loc[selected_index].copy()
                row_data["Deleted At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state["last_deleted"] = row_data
                trash_df = pd.concat([trash_df, pd.DataFrame([row_data])], ignore_index=True)
                df = df.drop(index=selected_index).reset_index(drop=True)
                df.to_csv("cv_database.csv", index=False)
                st.session_state["trash_bin"] = trash_df
                st.success("CV moved to Trash Bin!")
            except Exception as e:
                st.error(f"Error: {e}")

# Undo delete
if last_deleted_row is not None:
    if st.button("♻️ Undo Last Delete"):
        df = pd.concat([df, pd.DataFrame([last_deleted_row.drop("Deleted At", errors="ignore")])], ignore_index=True)
        df = df.drop_duplicates(subset="Email").sort_values(by="Name").reset_index(drop=True)
        df.to_csv("cv_database.csv", index=False)
        st.session_state["last_deleted"] = None
        st.success("Last deleted CV restored!")

# Trash bin
with st.expander("🗑️ Trash Bin"):
    if not trash_df.empty:
        st.dataframe(trash_df, use_container_width=True)
        restore_index = st.number_input("Restore row number from trash:", min_value=0, max_value=len(trash_df)-1, step=1)
        if st.button("🔄 Restore from Trash"):
            row = trash_df.loc[restore_index]
            df = pd.concat([df, pd.DataFrame([row.drop("Deleted At", errors="ignore")])], ignore_index=True)
            df = df.drop_duplicates(subset="Email").sort_values(by="Name").reset_index(drop=True)
            trash_df = trash_df.drop(index=restore_index).reset_index(drop=True)
            st.session_state["trash_bin"] = trash_df
            df.to_csv("cv_database.csv", index=False)
            st.success("CV restored!")
    else:
        st.info("Trash bin is empty.")

# Download button
with st.expander("📥 Download Extracted Data"):
    st.download_button("Download as CSV", df.to_csv(index=False), "cv_database.csv")

