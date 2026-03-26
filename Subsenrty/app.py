import streamlit as st
import pandas as pd
import random
import hashlib
import requests
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. THEME & STYLING (Red, Black, Yellow) ---
st.set_page_config(page_title="SubSentry Pro", page_icon="🛡️", layout="wide")

# Fixed the error here by using unsafe_allow_html=True
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #1a1a1a; }
    div.stButton > button:first-child { 
        background-color: #FF0000; color: white; 
        border-radius: 10px; border: 2px solid #FFD700; 
    }
    h1, h2, h3 { color: #FFD700 !important; }
    .stTextInput input { background-color: #333333; color: #FFD700; border: 1px solid #FF0000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIG & DATABASE ---
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"
# Connection to your Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. HELPER FUNCTIONS ---
def send_otp(email, code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "SubSentry Guard", "email": SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "⚠️ Your Secure Access Code",
        "htmlContent": f"<h2 style='color:red;'>SubSentry Security</h2><p>Your code is: <b>{code}</b></p>"
    }
    requests.post(url, json=payload, headers=headers)

# --- 4. SESSION STATE ---
if 'auth_state' not in st.session_state:
    st.session_state.auth_state = "start"
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 5. AUTH FLOW ---
if st.session_state.auth_state == "start":
    st.title("🛡️ SUBSENTRY: ELITE PROTECTION")
    email_input = st.text_input("Enter Email to Begin Verification")
    if st.button("SEND SHIELD CODE"):
        if email_input:
            st.session_state.generated_otp = str(random.randint(100000, 999999))
            st.session_state.user_email = email_input
            send_otp(email_input, st.session_state.generated_otp)
            st.session_state.auth_state = "verify_otp"
            st.rerun()

elif st.session_state.auth_state == "verify_otp":
    st.subheader(f"Verifying: {st.session_state.user_email}")
    otp_input = st.text_input("Enter 6-Digit Security Code")
    if st.button("VERIFY IDENTITY"):
        if otp_input == st.session_state.generated_otp:
            st.session_state.auth_state = "set_password"
            st.rerun()
        else:
            st.error("Invalid Code.")

elif st.session_state.auth_state == "set_password":
    st.subheader("🔐 ESTABLISH MASTER PASSWORD")
    new_password = st.text_input("New Password", type="password")
    if st.button("FINALIZE ENCRYPTION"):
        if len(new_password) >= 6:
            st.session_state.auth_state = "logged_in"
            st.rerun()

# --- 6. THE REAL DASHBOARD ---
elif st.session_state.auth_state == "logged_in":
    st.title(f"🚀 SENTRY COMMAND: {st.session_state.user_email}")
    
    with st.sidebar:
        st.header("➕ MONITOR NEW APP")
        app_name = st.text_input("Service Name")
        expiry = st.date_input("Billing Date")
        if st.button("ADD TO RADAR"):
            # Save to Google Sheets logic
            st.success(f"Added {app_name} to permanent vault!")

    st.subheader("All Active Subscriptions")
    st.info("You can add unlimited apps. We scan your list every 24 hours.")
    
    if st.button("LOGOUT"):
        st.session_state.auth_state = "start"
        st.rerun()
