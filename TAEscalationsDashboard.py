import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import io  # Use Python's built-in StringIO

# Google Sheets API setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = "secret.json"  # Replace with your JSON file path

# Authenticate and connect to Google Sheets
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
client = gspread.authorize(creds)

# Google Sheet details
SHEET_ID = "11FoqJicHt3BGpzAmBnLi1FQFN-oeTxR_WGKszARDcR4"
SHEET_NAME = "Sheet1"  # Change if needed

# Required columns to keep
REQUIRED_COLUMNS = [
    "Mode", "Type", "Escalation Date", "Domain", "BID", "Account name",
    "Subject line (Manual TA Escalation)", "Parent Category", "Case Category",
    "Escalated To", "Escalated By", "Status"
]


# Function to fetch and clean data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_data():
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_values()  # Get all data as a list of lists

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Use first row as headers
    df.columns = df.iloc[0]  # Assign first row as header
    df = df[1:]  # Remove first row from data
    df = df.reset_index(drop=True)

    # Fix duplicate column names
    df.columns = pd.read_csv(io.StringIO(",".join(df.columns))).columns

    # Keep only the required columns
    df = df[[col for col in REQUIRED_COLUMNS if col in df.columns]]

    return df


# Load filtered data
df = fetch_data()

# Streamlit Dashboard
st.title("📊 Escalation Dashboard")
st.write("Showing only relevant columns.")

# Display filtered data
st.dataframe(df)

# Create visualization
if not df.empty:
    st.subheader("Visualization")
    st.bar_chart(df.set_index(df.columns[0]))  # Uses first column as index

# Auto-refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()  # Clear cache to force update
    st.experimental_rerun()
