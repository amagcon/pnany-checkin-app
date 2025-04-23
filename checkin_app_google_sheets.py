#import os
#st.write("File exists?", os.path.exists("google_credentials.json"))

import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe

# Setup
st.set_page_config(page_title="Event Check-In", layout="centered")
credentials_file = r"C:\Users\aubre\OneDrive\Visual Studio Code Folder\New App Attendee Checkin\google_credentials.json"  # Your downloaded JSON key
sheet_name = "PNANY 2025 Check-In Log"

# Authenticate and load Google Sheet
gc = gspread.service_account(filename=credentials_file)
worksheet = gc.open(sheet_name).sheet1
existing_data = worksheet.get_all_records()
checkin_log = pd.DataFrame(existing_data)

# Ensure required columns exist
log_columns = [
    "Timestamp", "Name", "Email", "Credentials",
    "Status", "Membership Status", "Interested in Membership", "Affiliation"
]
for col in log_columns:
    if col not in checkin_log.columns:
        checkin_log[col] = ""

# Sidebar (manual fallback CSV registration list)
registration_file = "registration_list.csv"
if os.path.exists(registration_file):
    registration_list = pd.read_csv(registration_file)
    registration_list["Name"] = registration_list["Name"].astype(str)
    registration_list["Email"] = registration_list["Email"].astype(str)
else:
    registration_list = pd.DataFrame(columns=["Name", "Email", "Credentials"])

st.sidebar.header("📋 Upload Registration List")
if registration_list.empty:
    uploaded_file = st.sidebar.file_uploader("Upload CSV (Name, Email, Credentials)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        required = {"Name", "Email", "Credentials"}
        if required.issubset(df.columns):
            df["Name"] = df["Name"].astype(str).str.strip()
            df["Email"] = df["Email"].astype(str).str.strip()
            df["Credentials"] = df["Credentials"].fillna("").astype(str).str.strip()
            df.to_csv(registration_file, index=False)
            st.sidebar.success("✅ Registration list saved. Please refresh the page.")
        else:
            st.sidebar.error("CSV must include: Name, Email, Credentials.")
else:
    st.sidebar.write("✅ Registration list loaded.")

# Header
st.markdown(
    "<h2 style='text-align: center; color: navy;'>👋 Welcome to PNANY 2025 Spring Educational Conference</h2>",
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4 = st.tabs([
    "🧾 Pre-Registered Check-In",
    "📝 Manual Check-In",
    "📄 View Check-In Log",
    "🌟 Interested in Membership"
])

# Pre-Registered Check-In
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

# Manual Check-In
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

# View Log
with tab3:
    st.header("📄 Checked-In Attendees Log")
    if not checkin_log.empty:
        st.dataframe(checkin_log)
    else:
        st.info("ℹ️ No attendees have checked in yet.")

# View Interested Members
with tab4:
    st.header("🌟 Attendees Interested in PNANY Membership")
    if not checkin_log.empty:
        interested_df = checkin_log[
            (checkin_log["Membership Status"].str.lower() == "no") &
            (checkin_log["Interested in Membership"].str.lower() == "yes")
        ]
        if not interested_df.empty:
            st.dataframe(interested_df[["Timestamp", "Name", "Email", "Affiliation"]])
        else:
            st.info("No non-members have indicated interest in joining yet.")
    else:
        st.info("ℹ️ No check-ins recorded.")
