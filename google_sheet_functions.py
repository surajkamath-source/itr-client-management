import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SPREADSHEET_NAME = "ITR_App"
CLIENT_SHEET = "Client_Data"
HISTORY_SHEET = "Update_History"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)


def get_client_sheet():
    return client.open(SPREADSHEET_NAME).worksheet(CLIENT_SHEET)


def get_history_sheet():
    return client.open(SPREADSHEET_NAME).worksheet(HISTORY_SHEET)


def load_client_data():

    sheet = get_client_sheet()

    data = sheet.get_all_records()

    return pd.DataFrame(data)


def save_dataframe(df):

    sheet = get_client_sheet()

    sheet.clear()

    sheet.update(
        [df.columns.values.tolist()] +
        df.values.tolist()
    )
from datetime import datetime

def add_history(
    user,
    client_id,
    client_name,
    field_changed,
    old_value,
    new_value
):

    sheet = get_history_sheet()

    sheet.append_row([
        datetime.now().strftime("%d-%m-%Y"),
        datetime.now().strftime("%H:%M:%S"),
        user,
        client_id,
        client_name,
        field_changed,
        old_value,
        new_value
    ])
def load_history_data():

    sheet = get_history_sheet()

    data = sheet.get_all_records()

    return pd.DataFrame(data)
def add_client_row(new_row):

    sheet = get_client_sheet()

    headers = sheet.row_values(1)

    row_data = []

    for col in headers:
        row_data.append(
            new_row.get(col, "")
        )

    sheet.append_row(row_data)