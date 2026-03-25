import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import random

# --- CONFIGURATION ---
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"

# --- FUNCTIONS ---
def send_email(target_email, subject, body):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "SubSentry", "email": SENDER_EMAIL},
        "to": [{"email": target_email}],
        "subject": subject,
        "htmlContent": f"<html><body>{body}</body></html>"
    }
    requests.post(url, json=payload, headers=headers)

# --- SESSION STATE (The App's Memory) ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'otp' not in st.session_state:
    st.session_state.otp = None

# --- PHASE 1: LOGIN SYSTEM ---
if not st.session_state.authenticated:
    st.header("🔒 Secure Login")
    user_email = st.text_input("Enter your email to receive a code")
    
    if st.button("Send Verification Code"):
        st.session_state.otp = str(random.randint(100000, 999999))
        send_email(user_email, "Your SubSentry Code", f"Your login code is: <b>{st.session_state.otp}</b>")
        st.info("Code sent! Check your inbox.")

    code_input = st.text_input("Enter the 6-digit code")
    if st.button("Verify & Enter"):
        if code_input == st.session_state.otp:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid code.")
    st.stop()

# --- PHASE 2: THE DASHBOARD (Only shows if logged in) ---
st.title("🛡️ Subscription Command Center")
menu = st.sidebar.radio("Menu", ["My Dashboard", "Add Subscription"])

if menu == "Add Subscription":
    name = st.text_input("App Name (e.g. Netflix)")
    date = st.date_input("Next Expiry Date")
    if st.button("Save Subscription"):
        # This is where the 2-day logic lives
        st.success(f"Sentry set for {name}!")
        # Automated check
        if date - timedelta(days=2) == datetime.now().date():
             send_email(user_email, "⚠️ 2-Day Warning", f"Your {name} sub expires in 2 days!")

elif menu == "My Dashboard":
    st.write("Welcome back! Your sentries are active.")
    # You can add a table here later to show saved subs
