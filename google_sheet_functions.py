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


# ======================
# SHEETS
# ======================

def get_client_sheet():
    return client.open(SPREADSHEET_NAME).worksheet(
        CLIENT_SHEET
    )


def get_history_sheet():
    return client.open(SPREADSHEET_NAME).worksheet(
        HISTORY_SHEET
    )


# ======================
# CLIENT DATA
# ======================

def load_client_data():

    sheet = get_client_sheet()

    data = sheet.get_all_records()

    return pd.DataFrame(data)


def save_dataframe(df):

    if len(df) == 0:
        raise Exception(
            "Refusing to save empty dataframe."
        )

    sheet = get_client_sheet()

    values = (
        [df.columns.tolist()]
        + df.fillna("").values.tolist()
    )

    sheet.clear()

    sheet.update(values)


def add_client_row(new_row):

    sheet = get_client_sheet()

    headers = sheet.row_values(1)

    row_data = []

    for col in headers:
        row_data.append(
            new_row.get(col, "")
        )

    sheet.append_row(row_data)


# ======================
# HISTORY
# ======================

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
