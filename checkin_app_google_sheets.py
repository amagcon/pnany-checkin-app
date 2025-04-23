
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe
import json
from google.oauth2.service_account import Credentials

# ----------------- AUTHENTICATION -----------------
creds_dict = st.secrets["GOOGLE_CREDENTIALS"]
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)

# ----------------- CONFIG -----------------
st.set_page_config(
    page_title="PNANY 2025 Check-In",
    layout="wide",
    page_icon="📝"
)

# Background image
background_image = '''
<style>
body {
    background-image: url('https://images.unsplash.com/photo-1581092580331-4b94e43b8c97?auto=format&fit=crop&w=1950&q=80');
    background-size: cover;
    background-attachment: fixed;
}
</style>
'''
st.markdown(background_image, unsafe_allow_html=True)

# PNANY Logo
st.image("https://i.imgur.com/QjLFALD.png", width=180)  # Replace with actual PNANY logo link

# ----------------- SHEET SETUP -----------------
sheet_name = "PNANY 2025 Check-In Log"
worksheet = gc.open(sheet_name).sheet1
existing_data = worksheet.get_all_records()
checkin_log = pd.DataFrame(existing_data)

log_columns = [
    "Timestamp", "Name", "Email", "Credentials",
    "Status", "Membership Status", "Interested in Membership", "Affiliation"
]
for col in log_columns:
    if col not in checkin_log.columns:
        checkin_log[col] = ""

# Registration list fallback (optional)
registration_file = "registration_list.csv"
if os.path.exists(registration_file):
    registration_list = pd.read_csv(registration_file)
    registration_list["Name"] = registration_list["Name"].astype(str)
    registration_list["Email"] = registration_list["Email"].astype(str)
else:
    registration_list = pd.DataFrame(columns=["Name", "Email", "Credentials"])

# ----------------- LANDING PAGE -----------------
st.markdown("<h1 style='text-align: center; color: navy;'>👋 Welcome to PNANY 2025 Spring Educational Conference</h1>", unsafe_allow_html=True)

# Add custom CSS to enlarge buttons
st.markdown("""
    <style>
    div.stButton > button {
        font-size: 24px !important;
        padding: 1em 2em;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Custom CSS to enlarge buttons
st.markdown("""
    <style>
    div.stButton > button {
        font-size: 40px !important;
        padding: 1.2em 2em;
        border-radius: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


col1, col2 = st.columns(2)
with col1:
    attendee_clicked = st.button("🙋 Attendee Check-In", use_container_width=True)
with col2:
    organizer_clicked = st.button("🛠 Organizer View", use_container_width=True)

selection = None
if attendee_clicked:
    selection = "Attendee Check-In"
elif organizer_clicked:
    selection = "Organizer View"
else:
    st.info("Please select an option to begin.")
    st.stop()


if selection == "⬇️ Select Option":
    st.info("Please select an option to begin.")
    st.stop()

# ----------------- ATTENDEE CHECK-IN -----------------
elif selection == "Attendee Check-In":
    tab1, tab2 = st.tabs(["🧾 Pre-Registered Check-In", "📝 Manual Check-In"])

    with tab1:
        st.header("🧾 Pre-Registered Attendee Check-In")
        if registration_list.empty:
            st.warning("⚠️ Please upload a registration list to begin.")
        else:
            attendee_name = st.selectbox("Select your name", options=[""] + sorted(registration_list["Name"].unique()))
            if attendee_name:
                attendee = registration_list[registration_list["Name"] == attendee_name].iloc[0]
                email = attendee["Email"]
                existing_cred = attendee["Credentials"]

                if pd.isna(existing_cred) or existing_cred.strip() == "":
                    credentials = st.text_input("✍️ Enter your credentials")
                else:
                    credentials = existing_cred
                    st.markdown(f"**Pre-registered credentials:** `{credentials}`")

                if st.button("✅ Check In"):
                    name_lower = attendee_name.lower()
                    email_lower = email.lower()
                    log_names = checkin_log["Name"].astype(str).str.lower()
                    log_emails = checkin_log["Email"].astype(str).str.lower()

                    if name_lower in log_names.values or email_lower in log_emails.values:
                        st.warning(f"🚫 {attendee_name} has already checked in.")
                    else:
                        new_entry = pd.DataFrame([[
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            attendee_name,
                            email,
                            credentials,
                            "Preregistered", "", "", ""
                        ]], columns=log_columns)
                        checkin_log = pd.concat([checkin_log, new_entry], ignore_index=True)
                        set_with_dataframe(worksheet, checkin_log)
                        st.success(f"🎉 {attendee_name} has been checked in.")

    with tab2:
        st.header("📝 Manual Attendee Check-In")
        name_input = st.text_input("Full Name")
        email_input = st.text_input("Email")
        credentials_input = st.text_input("Credentials (optional)")
        membership_status = st.radio("Are you a PNANY member?", ["Yes", "No"], horizontal=True)

        interested = ""
        if membership_status == "No":
            interested = st.radio("Would you like to become a member?", ["Yes", "No"], horizontal=True)

        affiliation = st.text_input("Workplace or Affiliation")

        if st.button("➕ Submit Manual Check-In"):
            if not name_input or not email_input:
                st.warning("⚠️ Name and Email are required.")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email_input):
                st.error("❌ Please enter a valid email address.")
            else:
                name_lower = name_input.lower()
                email_lower = email_input.lower()
                log_names = checkin_log["Name"].astype(str).str.lower()
                log_emails = checkin_log["Email"].astype(str).str.lower()

                if name_lower in log_names.values or email_lower in log_emails.values:
                    st.warning(f"🚫 {name_input} has already checked in.")
                else:
                    new_entry = pd.DataFrame([[
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        name_input,
                        email_input,
                        credentials_input,
                        "Manual",
                        membership_status,
                        interested if membership_status == "No" else "",
                        affiliation
                    ]], columns=log_columns)
                    checkin_log = pd.concat([checkin_log, new_entry], ignore_index=True)
                    set_with_dataframe(worksheet, checkin_log)
                    st.success(f"✅ {name_input} has been manually checked in.")

# ----------------- ORGANIZER VIEW -----------------
elif selection == "Organizer View":
    st.header("📄 Checked-In Attendees Log")
    if not checkin_log.empty:
        st.dataframe(checkin_log)
    else:
        st.info("ℹ️ No attendees have checked in yet.")

    st.header("🌟 Interested in Membership")
    interested_df = checkin_log[
        (checkin_log["Membership Status"].str.lower() == "no") &
        (checkin_log["Interested in Membership"].str.lower() == "yes")
    ]
    if not interested_df.empty:
        st.dataframe(interested_df[["Timestamp", "Name", "Email", "Affiliation"]])
    else:
        st.info("ℹ️ No one has expressed interest in joining yet.")
