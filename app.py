import streamlit as st
import pdfplumber
import pandas as pd
import altair as alt
from PyPDF2 import PdfReader
from pdfminer.pdfparser import PDFSyntaxError
import io
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env into environment

CLIENT_SECRET_FILE = os.getenv("GOOGLE_CLIENT_SECRET_PATH")

# ----------------------------- HELPER FUNCTIONS -----------------------------

def is_pdf_encrypted(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        return reader.is_encrypted
    except Exception:
        return False

def extract_text_from_pdf(uploaded_file, password=None):
    try:
        if password:
            with pdfplumber.open(uploaded_file, password=password) as pdf:
                return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        else:
            with pdfplumber.open(uploaded_file) as pdf:
                return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    except PDFSyntaxError:
        st.error("Unable to read the PDF. It might be corrupted or improperly decrypted.")
        return None
    except Exception as e:
        st.error(f"PDF error: {e}")
        return None

def parse_transactions(text):
    # Dummy parser – replace with your custom regex/logic
    lines = text.splitlines()
    data = []
    for line in lines:
        if any(char.isdigit() for char in line):  # crude filter
            parts = line.split()
            if len(parts) >= 3:
                date = parts[0]
                description = " ".join(parts[1:-1])
                amount = parts[-1]
                try:
                    amount = float(amount.replace(",", "").replace("₦", ""))
                    category = categorize_transaction(description)
                    data.append({"Date": date, "Description": description, "Amount": amount, "Category": category})
                except ValueError:
                    continue
    return pd.DataFrame(data)

def categorize_transaction(description):
    desc = description.lower()
    if "supermarket" in desc or "grocery" in desc:
        return "Groceries"
    elif "salary" in desc or "income" in desc:
        return "Income"
    elif "restaurant" in desc or "eat" in desc:
        return "Dining"
    elif "transfer" in desc:
        return "Transfers"
    else:
        return "Uncategorized"

def upload_to_google_sheets(df, sheet_name, creds_json):
    try:
        credentials = Credentials.from_service_account_info(creds_json)
        client = gspread.authorize(credentials)
        sheet = client.open(sheet_name).sheet1
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("Uploaded to Google Sheets!")
    except Exception as e:
        st.error(f"Upload failed: {e}")

# ----------------------------- STREAMLIT APP -----------------------------

st.title("📄 Bank Statement Analyzer")

uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type=["pdf"])

if uploaded_file:
    uploaded_file.seek(0)
    if is_pdf_encrypted(uploaded_file):
        password = st.text_input("🔐 Enter PDF password", type="password")
    else:
        password = None

    if st.button("🔍 Extract Transactions"):
        uploaded_file.seek(0)
        text = extract_text_from_pdf(uploaded_file, password)
        if text:
            df = parse_transactions(text)

            if df.empty:
                st.warning("No transactions found.")
            else:
                st.success(f"{len(df)} transactions extracted.")

                # Filtering
                category_filter = st.selectbox("📂 Filter by Category", ["All"] + sorted(df["Category"].unique().tolist()))
                if category_filter != "All":
                    df = df[df["Category"] == category_filter]

                st.dataframe(df)

                # Chart
                chart = alt.Chart(df).mark_bar().encode(
                    x='Category',
                    y='sum(Amount)',
                    color='Category'
                ).properties(title="Total Spending by Category")
                st.altair_chart(chart, use_container_width=True)

                # Export CSV
                filename = st.text_input("💾 Enter filename for CSV export (without extension)", value="transactions")
                if st.button("Export CSV Locally"):
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{filename}.csv",
                        mime='text/csv'
                    )

                # Upload to Google Sheets
with st.expander("☁️ Upload to Google Sheets"):
    sheet_name = st.text_input("Google Sheet Name", value="Bank Transactions")
    if st.button("Upload to Google Sheets"):
        try:
            credentials = Credentials.from_service_account_file(CLIENT_SECRET_FILE)
            client = gspread.authorize(credentials)
            st.text("✅ Authorized service account")

            sheet = client.open(sheet_name).sheet1
            st.text("✅ Opened sheet")

            sheet.clear()
            sheet.update([df.columns.values.tolist()] + df.values.tolist())
            st.success("Uploaded to Google Sheets!")
        except Exception as e:
            st.error(f"Upload failed: {e}")