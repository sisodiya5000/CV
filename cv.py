import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta
import fitz  # PyMuPDF

# Folder to store uploaded CV files
UPLOAD_FOLDER = "cv_uploads"
TRASH_FOLDER = "cv_trash"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

# Function to extract real info from PDF using regex
def extract_cv_info_from_pdf(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            text = "\n".join([page.get_text() for page in doc])

        name_match = re.search(r"(?i)([A-Z][a-z]+\s[A-Z][a-z]+)", text)
        name = name_match.group(1) if name_match else os.path.basename(pdf_path).split("_")[0]

        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
        phone_match = re.search(r"(?:(?:\+91[-\s]?)?|0)?[6-9]\d{9}", text)
        exp_match = re.search(r"(\d+\+?\s*(?:years?|yrs?|yr|year|experience|exp))", text, re.IGNORECASE)

        education_match = re.findall(r"(?i)(B\.?Tech|M\.?Tech|MBA|B\.?Sc|M\.?Sc|PGDC|Diploma|B\.?E|M\.?E)[^\n]{0,60}", text)
        education = ", ".join(set([e.strip() for e in education_match])) if education_match else "Not Found"

        summary = f"{name} has experience in {education.lower()} with approx. {exp_match.group(1).lower() if exp_match else 'unknown experience length'}. Contact: {email_match.group(0) if email_match else 'no email found'}."

        return {
            "Name": name,
            "Email": email_match.group(0) if email_match else "Not Found",
            "Phone": phone_match.group(0) if phone_match else "Not Found",
            "Experience": exp_match.group(1) if exp_match else "Not Found",
            "Education": education,
            "Summary": summary,
            
        }
    except Exception as e:
        return {"Name": "Error", "Email": str(e), "Phone": "-", "Experience": "-", "Education": "-", "Summary": "-"}

@st.cache_data
def load_database():
    if os.path.exists("cv_database.csv"):
        df = pd.read_csv("cv_database.csv")
        if "Summary" not in df.columns or df["Summary"].isnull().all():
            df["Summary"] = df.apply(
                lambda row: f"{row['Name']} has experience in {row['Education'].lower()} with approx. {row['Experience'].lower() if row['Experience'] != 'Not Found' else 'unknown experience length'}. Contact: {row['Email']}.",
                axis=1
            )
            df.to_csv("cv_database.csv", index=False)
        return df
    return pd.DataFrame(columns=["Name", "Email", "Phone", "Experience", "Education", "Summary"])

st.set_page_config(page_title="CV Dashboard", layout="wide")
st.title("📄 CV Management Dashboard")

# Upload Section
st.sidebar.header("📤 Upload CVs")
uploaded_files = st.sidebar.file_uploader("Upload CV Files (PDF only)", type=["pdf"], accept_multiple_files=True)

df = load_database()
# Ensure File Name column is never shown
if "File Name" in df.columns:
    df = df.drop(columns=["File Name"])
last_deleted_row = st.session_state.get("last_deleted", None)
trash_df = st.session_state.get("trash_bin", pd.DataFrame(columns=["Name", "Email", "Phone", "Experience", "Education", "Summary", "Deleted At"]))

if uploaded_files:
    st.sidebar.success(f"Uploaded {len(uploaded_files)} file(s). Extracting...")
    for uploaded_file in uploaded_files:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{uploaded_file.name}")
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        info = extract_cv_info_from_pdf(save_path)
        df = pd.concat([df, pd.DataFrame([info])], ignore_index=True)

    df = df.drop_duplicates(subset="Email")
    df = df.sort_values(by="Name").reset_index(drop=True)
    df = df[["Name", "Email", "Phone", "Experience", "Education", "Summary"]]
    df.to_csv("cv_database.csv", index=False)
    st.sidebar.success("✅ CVs Extracted, Saved, and Database Updated!")

# Display Section
st.subheader("🧾 Extracted CV Details")
selected_index = st.number_input("Enter row number to delete (starting from 0):", min_value=0, max_value=len(df)-1 if len(df) > 0 else 0, step=1)
delete_confirm = st.checkbox("Confirm deletion of selected CV")

if st.button("🗑️ Delete Selected CV"):
    if delete_confirm:
        try:
            row_data = df.loc[selected_index].copy()
            file_to_delete = None  # File Name removed
            row_data["Deleted At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state["last_deleted"] = row_data
            trash_df = pd.concat([trash_df, pd.DataFrame([row_data])], ignore_index=True)
            df = df.drop(index=selected_index).reset_index(drop=True)
            df.to_csv("cv_database.csv", index=False)
            st.session_state["trash_bin"] = trash_df
            st.success("CV moved to Trash Bin!")
        except Exception as e:
            st.error(f"Error deleting CV: {e}")
    else:
        st.warning("Please confirm deletion before proceeding.")

if last_deleted_row is not None:
    if st.button("♻️ Undo Last Delete"):
        df = pd.concat([df, pd.DataFrame([last_deleted_row.drop("Deleted At") if "Deleted At" in last_deleted_row else last_deleted_row])], ignore_index=True)
        df = df.drop_duplicates(subset="Email")
        df = df.sort_values(by="Name").reset_index(drop=True)
        df.to_csv("cv_database.csv", index=False)
        st.session_state["last_deleted"] = None
        st.success("Last deleted CV restored!")

# Only show non-deleted CVs
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("No CVs available. Upload new ones or restore from trash.")

with st.expander("🗑️ Trash Bin History"):
    if not trash_df.empty:
        st.dataframe(trash_df, use_container_width=True)
        restore_index = st.number_input("Enter row number from trash to restore:", min_value=0, max_value=len(trash_df)-1, step=1)
        if st.button("🔄 Restore from Trash"):
            row_to_restore = trash_df.loc[restore_index].copy()
            trash_df = trash_df.drop(index=restore_index).reset_index(drop=True)
            df = pd.concat([df, pd.DataFrame([row_to_restore.drop("Deleted At") if "Deleted At" in row_to_restore else row_to_restore])], ignore_index=True)
            df = df.drop_duplicates(subset="Email")
            df = df.sort_values(by="Name").reset_index(drop=True)
            df.to_csv("cv_database.csv", index=False)
            restored_file = None  # File Name removed
            st.session_state["trash_bin"] = trash_df
            st.success("CV restored from Trash!")
    else:
        st.info("Trash bin is empty.")

# Auto-delete trash older than 10 days
now = datetime.now()
for filename in os.listdir(TRASH_FOLDER):
    file_path = os.path.join(TRASH_FOLDER, filename)
    if os.path.isfile(file_path):
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if (now - file_time).days > 10:
            os.remove(file_path)

with st.expander("📥 Download Extracted Data"):
    st.download_button("Download as CSV", df.to_csv(index=False), "cv_database.csv")
