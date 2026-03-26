import streamlit as st
import pandas as pd
import random
import requests
import hashlib

# --- 1. THEME STYLING ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    div.stButton > button:first-child { 
        background-color: #FF0000; color: white; 
        border-radius: 8px; border: 2px solid #FFD700;
        font-weight: bold; width: 100%;
    }
    h1, h2, h3 { color: #FFD700 !important; text-align: center; }
    .stTextInput input { background-color: #222222; color: #FFD700; border: 1px solid #FF0000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIG ---
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"

def send_otp(email, code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "SubSentry Alert", "email": SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "🔔 Your Verification Code",
        "htmlContent": f"<h2>SubSentry Alert</h2><p>Your verification code is: <b>{code}</b></p>"
    }
    requests.post(url, json=payload, headers=headers)

# --- 3. LOGIC FLOW ---
if 'flow' not in st.session_state:
    st.session_state.flow = "landing"

# --- SCREEN 1: LANDING ---
if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    st.write("Never miss a subscription renewal again.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("SIGN UP"):
            st.session_state.flow = "signup_email"
            st.rerun()
    with col2:
        if st.button("LOG IN"):
            st.session_state.flow = "login"
            st.rerun()

# --- SCREEN 2: SIGN UP EMAIL ---
elif st.session_state.flow == "signup_email":
    st.subheader("Step 1: Verify Email")
    email = st.text_input("Enter your email address")
    if st.button("SEND VERIFICATION CODE"):
        if email:
            st.session_state.temp_email = email
            st.session_state.otp = str(random.randint(100000, 999999))
            send_otp(email, st.session_state.otp)
            st.session_state.flow = "verify_code"
            st.rerun()

# --- SCREEN 3: VERIFY CODE ---
elif st.session_state.flow == "verify_code":
    st.subheader(f"Code sent to {st.session_state.temp_email}")
    code_in = st.text_input("Enter 6-digit code")
    if st.button("VERIFY & CONTINUE"):
        if code_in == st.session_state.otp:
            st.session_state.flow = "create_password"
            st.rerun()
        else:
            st.error("Incorrect code.")

# --- SCREEN 4: CREATE PASSWORD ---
elif st.session_state.flow == "create_password":
    st.subheader("Step 2: Create Password")
    st.write("Verify successful! Now set your login password.")
    new_pass = st.text_input("New Password", type="password")
    if st.button("FINISH SIGN UP"):
        if len(new_pass) >= 4:
            st.success("Account Created! You can now log in.")
            st.session_state.flow = "landing"
            st.rerun()

# --- SCREEN 5: DASHBOARD ---
elif st.session_state.flow == "dashboard":
    st.title(f"🚀 Dashboard: {st.session_state.temp_email}")
    st.write("Add your subscriptions below to receive alerts.")
    if st.button("LOGOUT"):
        st.session_state.flow = "landing"
        st.rerun()
