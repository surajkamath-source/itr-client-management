import streamlit as st
import gspread
import pandas as pd

from google.oauth2.service_account import Credentials
from datetime import datetime

SPREADSHEET_NAME = "ITR_App"
CLIENT_SHEET = "Client_Data"
HISTORY_SHEET = "Update_History"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
