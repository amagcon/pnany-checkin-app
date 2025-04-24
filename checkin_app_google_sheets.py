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

###

# Load pre-uploaded registration list
registration_file = "registration_list.csv"

if os.path.exists(registration_file):
    registration_list = pd.read_csv(registration_file)
    registration_list["Name"] = registration_list["Name"].astype(str).str.strip()
    registration_list["Email"] = registration_list["Email"].astype(str).str.strip()
    registration_list["Credentials"] = registration_list["Credentials"].fillna("").astype(str).str.strip()
    if "Membership Note" not in registration_list.columns:
        registration_list["Membership Note"] = ""
else:
    st.error("❌ 'registration_list.csv' not found. Please upload the file to the app directory.")
    st.stop()



# -------------------- ATTENDEE VIEW --------------------
if st.session_state.view == "attendee":
    st.markdown("<h2 style='text-align: center; color: navy;'>👋 Welcome to PNANY 2025 Spring Educational Conference</h2>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs([
        "🧾 Pre-Registered Check-In",
        "📝 Manual Check-In"
    ])

    with tab1:
        st.header("🧾 Pre-Registered Attendee Check-In")
        if registration_list.empty:
            st.warning("⚠️ Please upload a registration list to begin.")
        else:
            with st.form("pre_registered_form"):
                attendee_name = st.selectbox("Select your name", options=[""] + sorted(registration_list["Name"].unique()))
                credentials = ""
                email = ""
                missing_cred = False

                if attendee_name:
                    attendee = registration_list[registration_list["Name"] == attendee_name].iloc[0]
                    email = attendee["Email"]
                    existing_cred = attendee["Credentials"]

                    if not isinstance(existing_cred, str) or existing_cred.strip().lower() in ["", "nan", "none"]:
                        credentials = st.text_input("✍️ Enter your credentials")
                        missing_cred = True
                    else:
                        credentials = existing_cred
                        st.markdown(f"**Pre-registered credentials:** `{credentials}`")

                membership_status = st.radio("Are you a PNANY member?", ["Yes", "No"], horizontal=True)
                interested = ""
                if membership_status == "No":
                    interested = st.radio("Would you like to become a member?", ["Yes", "No"], horizontal=True)

                # Show Membership Note if available
                note = attendee.get("Membership Note", "")
                if isinstance(note, str) and note.strip() != "":
                    st.markdown(f"""
                        <div style='
                            background-color:#fff3cd;
                            padding:10px 15px;
                            margin-top:15px;
                            border-left:6px solid #ffc107;
                            border-radius:4px;
                            font-weight:bold;
                            font-size:16px;
                        '>
                        📢 {note}
                        </div>
                    """, unsafe_allow_html=True)
                ###
                
                submitted = st.form_submit_button("✅ Check In")

            if submitted:
                if missing_cred and not credentials.strip():
                    st.warning("⚠️ Credentials are required for check-in.")
                elif attendee_name:
                    name_lower = attendee_name.lower()
                    email_lower = email.lower()
                    log_names = checkin_log["Name"].astype(str).str.lower()
                    log_emails = checkin_log["Email"].astype(str).str.lower()

                    if name_lower in log_names.values or email_lower in log_emails.values:
                        st.warning(f"🚫 {attendee_name} has already checked in.")
                    else:
                        new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                   attendee_name, email, credentials, "Preregistered",
                                                   membership_status,
                                                   interested if membership_status == "No" else "",
                                                   ""]], columns=log_columns)
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
                    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                               name_input, email_input, credentials_input, "Manual",
                                               membership_status,
                                               interested if membership_status == "No" else "",
                                               affiliation]], columns=log_columns)
                    checkin_log = pd.concat([checkin_log, new_entry], ignore_index=True)
                    set_with_dataframe(worksheet, checkin_log)
                    st.success(f"✅ {name_input} has been manually checked in.")

# -------------------- ORGANIZER VIEW --------------------
elif st.session_state.view == "organizer":
    st.markdown("<h2 style='text-align: center; color: navy;'>🛠 Organizer View</h2>", unsafe_allow_html=True)
    tab3, tab4 = st.tabs(["📄 View Check-In Log", "🌟 Interested in Membership"])

    with tab3:
        st.header("📄 Checked-In Attendees Log")
        total_checked_in = len(checkin_log)
        st.subheader(f"✅ Total Checked-In: {total_checked_in}")

        if not checkin_log.empty:
            st.dataframe(checkin_log)

            # Export as CSV
            csv = checkin_log.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name="PNANY_checkin_log.csv",
                mime="text/csv"
            )

            # Export as Excel
            excel_writer = pd.ExcelWriter("checkin_export.xlsx", engine="xlsxwriter")
            checkin_log.to_excel(excel_writer, index=False, sheet_name="CheckIns")
            excel_writer.close()
            with open("checkin_export.xlsx", "rb") as f:
                st.download_button(
                    label="⬇️ Download Excel",
                    data=f.read(),
                    file_name="PNANY_checkin_log.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("ℹ️ No attendees have checked in yet.")

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
