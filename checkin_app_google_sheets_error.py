import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe
import json
from google.oauth2.service_account import Credentials

# Setup
st.set_page_config(page_title='Event Check-In', layout='centered')
sheet_name = 'PNANY 2025 Check-In Log'
creds_dict = st.secrets['GOOGLE_CREDENTIALS']
scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
worksheet = gc.open(sheet_name).sheet1
existing_data = worksheet.get_all_records()
checkin_log = pd.DataFrame(existing_data)
log_columns = ['Timestamp', 'Name', 'Email', 'Credentials', 'Status', 'Membership Status', 'Interested in Membership', 'Affiliation']
for col in log_columns:
    if col not in checkin_log.columns:
        checkin_log[col] = ''

# Background image
background_image = '''
<style>
body {
    background-image: url("https://images.unsplash.com/photo-1581092580331-4b94e43b8c97?auto=format&fit=crop&w=1950&q=80");
    background-size: cover;
    background-attachment: fixed;
}
</style>
'''
st.markdown(background_image, unsafe_allow_html=True)

# PNANY Logo
st.image("https://i.imgur.com/QjLFALD.png", width=180)

# Landing Page Navigation
if "view" not in st.session_state:
    st.session_state.view = None

st.markdown("""
    <style>
    div.stButton > button {
        font-size: 28px !important;
        padding: 1.5em 2em !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("🙋 Attendee Check-In"):
        st.session_state.view = "attendee"
with col2:
    if st.button("🛠 Organizer View"):
        st.session_state.view = "organizer"

if st.session_state.view is None:
    st.stop()
