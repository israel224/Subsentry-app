import streamlit as st
import pandas as pd
import random
import requests
from streamlit_gsheets import GSheetsConnection

# --- 1. THEME STYLING (Back to White & Professional) ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    /* Buttons - Clean Blue/Grey style */
    div.stButton > button:first-child {
        background-color: #007BFF;
        color: white;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        width: 100%;
    }
    /* Input Boxes */
    .stTextInput input {
        background-color: #F8F9FA;
        color: #333333;
        border: 1px solid #CED4DA;
    }
    /* Headers */
    h1, h2, h3 {
        color: #333333 !important;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE & CONFIG ---
# This uses the secret you just saved in Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)
BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
SENDER_EMAIL = "ekeledilichukwuisrael@gmail.com"

def get_users():
    try:
        return conn.read(ttl=0)
    except:
        return pd.DataFrame(columns=["email", "password"])

def send_otp(email, code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "content-type": "application/json"}
    payload = {
        "sender": {"name": "SubSentry Alert", "email": SENDER_EMAIL},
        "to": [{"email": email}],
        "subject": "🔔 Your Verification Code",
        "htmlContent": f"<h3>SubSentry Alert</h3><p>Your code is: <b>{code}</b></p>"
    }
    requests.post(url, json=payload, headers=headers)

# --- 3. APP FLOW ---
if 'flow' not in st.session_state:
    st.session_state.flow = "landing"

# SCREEN: LANDING
if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    st.write("---")
    if st.button("CREATE ACCOUNT (SIGN UP)"):
        st.session_state.flow = "signup_email"
        st.rerun()
    if st.button("LOG IN TO DASHBOARD"):
        st.session_state.flow = "login_screen"
        st.rerun()

# SCREEN: SIGN UP EMAIL
elif st.session_state.flow == "signup_email":
    st.subheader("Step 1: Verify Email")
    email_in = st.text_input("Enter your email address")
    if st.button("SEND VERIFICATION CODE"):
        if "@" in email_in:
            st.session_state.temp_email = email_in
            st.session_state.otp = str(random.randint(100000, 999999))
            send_otp(email_in, st.session_state.otp)
            st.session_state.flow = "verify_code"
            st.rerun()
        else:
            st.error("Please enter a valid email.")

# SCREEN: VERIFY CODE
elif st.session_state.flow == "verify_code":
    st.subheader(f"Verification code sent to {st.session_state.temp_email}")
    code_in = st.text_input("Enter 6-digit code")
    if st.button("VERIFY"):
        if code_in == st.session_state.otp:
            st.session_state.flow = "create_password"
            st.rerun()
        else:
            st.error("Invalid code.")

# SCREEN: CREATE PASSWORD
elif st.session_state.flow == "create_password":
    st.subheader("Step 2: Create Your Password")
    p1 = st.text_input("Choose Password", type="password")
    if st.button("SAVE & FINISH"):
        if len(p1) >= 4:
            # SAVE TO GOOGLE SHEET
            df = get_users()
            new_user = pd.DataFrame([{"email": st.session_state.temp_email, "password": p1}])
            updated_df = pd.concat([df, new_user], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Account Created Successfully!")
            st.session_state.flow = "dashboard"
            st.rerun()

# SCREEN: LOGIN
elif st.session_state.flow == "login_screen":
    st.subheader("Login")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("LOG IN"):
        df = get_users()
        if l_email in df['email'].values:
            correct_pw = df[df['email'] == l_email]['password'].values[0]
            if str(l_pass) == str(correct_pw):
                st.session_state.temp_email = l_email
                st.session_state.flow = "dashboard"
                st.rerun()
            else:
                st.error("Incorrect Password")
        else:
            st.error("User not found. Please Sign Up.")

# SCREEN: DASHBOARD
elif st.session_state.flow == "dashboard":
    st.title(f"🚀 Welcome, {st.session_state.temp_email}")
    st.info("Your subscription alerts will appear here.")
    if st.button("LOGOUT"):
        st.session_state.flow = "landing"
        st.rerun()
