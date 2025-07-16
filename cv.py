import streamlit as st
import os
import sqlite3
from datetime import datetime
from datetime import date as dated

# ---------- CONFIG ----------
UPLOAD_FOLDER = "uploads"
ALLOWED_USERS = ["user1", "user2", "user3", "user4", "user5"]
COMMON_PASSWORD = "smart123"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- DB INIT ----------
def init_db():
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            uploader TEXT,
            filename TEXT,
            filepath TEXT,
            uploaded_on TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ---------- FILE FUNCTIONS ----------
def save_file(uploader, file):
    filepath = os.path.join(UPLOAD_FOLDER, f"{uploader}_{file.name}")
    with open(filepath, "wb") as f:
        f.write(file.getbuffer())
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("INSERT INTO documents VALUES (?, ?, ?, ?)", (
        uploader, file.name, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def list_all_files():
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("SELECT rowid, uploader, filename, filepath, uploaded_on FROM documents")
    files = c.fetchall()
    conn.close()
    return files

def delete_file(rowid, path):
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("DELETE FROM documents WHERE rowid=?", (rowid,))
    conn.commit()
    conn.close()

def replace_file(rowid, old_path, uploader, new_file):
    if os.path.exists(old_path):
        os.remove(old_path)
    new_path = os.path.join(UPLOAD_FOLDER, f"{uploader}_{new_file.name}")
    with open(new_path, "wb") as f:
        f.write(new_file.getbuffer())
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("""
        UPDATE documents 
        SET filename=?, filepath=?, uploaded_on=?
        WHERE rowid=?
    """, (new_file.name, new_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rowid))
    conn.commit()
    conn.close()

# ---------- MAIN ----------
def main():
    st.set_page_config("📂 Shared Document Dashboard")
    st.title("📂 Shared Document Dashboard (Only 5 Users Access)")

    init_db()

    # --- LOGIN ---
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username in ALLOWED_USERS and password == COMMON_PASSWORD:
            st.session_state["user"] = username
            st.success(f"✅ Welcome {username}!")
        else:
            st.error("❌ Invalid credentials")

    # --- MAIN DASHBOARD ---
    if "user" in st.session_state:
        user = st.session_state["user"]
        st.markdown(f"**🔓 Logged in as:** `{user}`")

        uploaded_file = st.file_uploader("📤 Upload a document (shared with all users)", type=None)
        if uploaded_file:
            save_file(user, uploaded_file)
            st.success("✅ File uploaded successfully!")
            st.experimental_rerun()

        st.markdown("### 🔍 Search & Filter Documents")

        # --- Filters ---
        all_files = list_all_files()
        search_query = st.text_input("Search by filename (partial match allowed)")
        min_date = st.date_input("From Date", value=dated(2024, 1, 1))
        max_date = st.date_input("To Date", value=dated.today())

        # --- Filter logic ---
        filtered_files = []
        for rowid, uploader, filename, path, uploaded_on in all_files:
            file_date = datetime.strptime(uploaded_on, "%Y-%m-%d %H:%M:%S").date()
            if (
                search_query.lower() in filename.lower()
                and min_date <= file_date <= max_date
            ):
                filtered_files.append((rowid, uploader, filename, path, uploaded_on))

        # --- Display filtered results ---
        st.markdown("### 📁 Filtered Files:")
        if filtered_files:
            for rowid, uploader, filename, path, date in filtered_files:
                with st.expander(f"📄 {filename} (by {uploader} on {date})"):
                    with open(path, "rb") as f:
                        st.download_button("⬇️ Download", f, file_name=filename)

                    col1, col2 = st.columns(2)
                    with col1:
                        new_file = st.file_uploader(f"Replace `{filename}`", key=f"replace_{rowid}")
                        if new_file:
                            replace_file(rowid, path, user, new_file)
                            st.success("✅ File replaced!")
                            st.experimental_rerun()
                    with col2:
                        if st.button(f"❌ Delete `{filename}`", key=f"delete_{rowid}"):
                            delete_file(rowid, path)
                            st.warning("🗑 File deleted")
                            st.experimental_rerun()
        else:
            st.info("🔎 No files match your filters.")

if __name__ == "__main__":
    main()
