# Bank Statements Analyzer

This Streamlit app extracts transaction data from bank statement PDFs, analyzes the data, and uploads it to a Google Sheet.

## 🔧 Features
- Extracts transactions using `pdfplumber`
- Parses dates, descriptions, and amounts with regex
- Visualizes spending using Altair charts
- Uploads data to a Google Sheet via Google Sheets API

## 🚀 How to Run the App

1. **Clone this repo**  
   ```bash
   git clone https://github.com/your-username/bank-statements-analyzer.git
   cd bank-statements-analyzer