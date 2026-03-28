import streamlit as st
import pandas as pd
import random
import requests
from streamlit_gsheets import GSheetsConnection

# --- 1. THEME STYLING ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔")
st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    div.stButton > button:first-child { 
        background-color: #007BFF; color: white; 
        border-radius: 5px; border: none; font-weight: bold; width: 100%;
    }
    .stTextInput input { background-color: #F8F9FA; color: #333333; border: 1px solid #CED4DA; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_users():
    try:
        # Specifically reading from 'Sheet1'
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        return pd.DataFrame(columns=["email", "password"])

# --- 3. EMAIL CONFIG ---
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"

def send_otp(email, code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "SubSentry", "email": SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "Verification Code",
        "htmlContent": f"Your code is: <b>{code}</b>"
    }
    requests.post(url, json=payload, headers=headers)

# --- 4. APP FLOW ---
if 'flow' not in st.session_state:
    st.session_state.flow = "landing"

if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    if st.button("CREATE ACCOUNT"):
        st.session_state.flow = "signup_email"
        st.rerun()
    if st.button("LOG IN"):
        st.session_state.flow = "login_screen"
        st.rerun()

elif st.session_state.flow == "signup_email":
    st.subheader("Sign Up")
    email_in = st.text_input("Enter Email")
    if st.button("SEND CODE"):
        st.session_state.temp_email = email_in
        st.session_state.otp = str(random.randint(1000, 9999))
        send_otp(email_in, st.session_state.otp)
        st.session_state.flow = "verify_code"
        st.rerun()

elif st.session_state.flow == "verify_code":
    st.subheader("Verify Email")
    code_in = st.text_input("Enter 4-digit code")
    if st.button("VERIFY"):
        if code_in == st.session_state.otp:
            st.session_state.flow = "create_password"
            st.rerun()
        else:
            st.error("Invalid code.")

elif st.session_state.flow == "create_password":
    st.subheader("Set Password")
    p1 = st.text_input("New Password", type="password")
    if st.button("SAVE & FINISH"):
        # READ, UPDATE, AND PUSH
        df = get_users()
        new_user = pd.DataFrame([{"email": st.session_state.temp_email, "password": p1}])
        updated_df = pd.concat([df, new_user], ignore_index=True)
        
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Account Secured!")
        st.session_state.flow = "dashboard"
        st.rerun()

elif st.session_state.flow == "login_screen":
    st.subheader("Login")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("LOG IN"):
        df = get_users()
        if not df.empty and l_email in df['email'].values:
            correct_p = df[df['email'] == l_email]['password'].values[0]
            if str(l_pass) == str(correct_p):
                st.session_state.temp_email = l_email
                st.session_state.flow = "dashboard"
                st.rerun()
            else: st.error("Wrong password")
        else: st.error("Email not found")

elif st.session_state.flow == "dashboard":
    st.title(f"🚀 Dashboard: {st.session_state.temp_email}")
    st.write("Welcome to your secure subscription manager.")
    if st.button("LOGOUT"):
        st.session_state.flow = "landing"
        st.rerun()
