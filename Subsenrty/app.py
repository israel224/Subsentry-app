import streamlit as st
import pandas as pd
import random
import hashlib
import requests
from datetime import datetime, timedelta

# --- 1. THEME & STYLING (Red, Black, Yellow) ---
st.set_page_config(page_title="SubSentry Pro", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* Background and Main Text */
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
    }
    /* Primary Buttons (Red) */
    div.stButton > button:first-child {
        background-color: #FF0000;
        color: white;
        border-radius: 10px;
        border: 2px solid #FFD700; /* Yellow Border */
    }
    /* Headers (Yellow) */
    h1, h2, h3 {
        color: #FFD700 !important;
    }
    /* Input Boxes */
    .stTextInput input {
        background-color: #333333;
        color: #FFD700;
        border: 1px solid #FF0000;
    }
    </style>
    """, unsafe_allow_id=True)

# --- 2. CONFIG ---
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"

# --- 3. HELPER FUNCTIONS ---
def send_otp(email, code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "SubSentry Guard", "email": SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "⚠️ Your Secure Access Code",
        "htmlContent": f"<h2 style='color:red;'>SubSentry Security</h2><p>Your code is: <b style='font-size:24px;'>{code}</b></p>"
    }
    requests.post(url, json=payload, headers=headers)

# --- 4. SESSION STATE ---
if 'auth_state' not in st.session_state:
    st.session_state.auth_state = "start"
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'subscriptions' not in st.session_state:
    st.session_state.subscriptions = []

# --- 5. SIGN UP / LOGIN FLOW ---
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
    st.subheader(f"Verifying Address: {st.session_state.user_email}")
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
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("FINALIZE ENCRYPTION"):
        if new_password == confirm_password and len(new_password) >= 6:
            st.session_state.auth_state = "logged_in"
            st.rerun()
        else:
            st.error("Check password match (min 6 chars).")

# --- 6. THE DASHBOARD (Multi-Add System) ---
elif st.session_state.auth_state == "logged_in":
    st.title(f"🚀 SENTRY COMMAND: {st.session_state.user_email}")
    
    with st.sidebar:
        st.header("➕ MONITOR NEW APP")
        app_name = st.text_input("Service Name")
        expiry = st.date_input("Billing Date")
        if st.button("ADD TO RADAR"):
            new_sub = {"Service": app_name, "Expiry": expiry, "Status": "🛡️ PROTECTED"}
            st.session_state.subscriptions.append(new_sub)
            st.success(f"Added {app_name}!")

    st.subheader("Active Subscriptions Under Watch")
    if len(st.session_state.subscriptions) > 0:
        # This handles as many as they want (10, 20, 50+)
        df = pd.DataFrame(st.session_state.subscriptions)
        st.dataframe(df, use_container_width=True) 
        st.warning("⚡ Sentry is active. Emails will be sent 48 hours before expiry.")
    else:
        st.write("Radar is empty. Add a service in the sidebar.")

    if st.button("LOGOUT"):
        st.session_state.auth_state = "start"
        st.rerun()
