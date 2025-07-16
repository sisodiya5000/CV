# CV Management Dashboard

This is a **CV Management Dashboard** built using **Streamlit**, **Pandas**, and **PyMuPDF**. The application allows users to upload, view, and manage CVs in PDF format. It extracts relevant details from the uploaded CVs (such as Name, Email, Phone, Experience, and Education), stores them in a CSV file, and displays them in an interactive web interface. Users can also delete and restore CVs, as well as manage a trash bin for deleted files.

## Features

- **Upload CVs**: Users can upload CVs in PDF format.
- **Extract Information**: Extracts key information like Name, Email, Phone, Experience, and Education from the CVs.
- **View and Manage Data**: Displays the extracted CV data in an interactive table. The data is saved to a CSV file for persistence.
- **Delete and Restore CVs**: Users can delete CVs, and the deleted entries are stored in a trash bin for potential restoration.
- **Trash Bin**: CVs moved to the trash bin can be restored back to the main database.
- **Automatic Cleanup**: Old files in the trash bin (older than 10 days) are automatically deleted.
- **Download Extracted Data**: Option to download the extracted data as a CSV file.

## Requirements

Before you begin, ensure you have met the following requirements:

- **Python 3.7+** is installed on your system.
- **Streamlit**, **Pandas**, and **PyMuPDF** libraries are installed.

To install the required libraries, run:

```bash
pip install streamlit pandas PyMuPDF
