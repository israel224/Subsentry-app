import streamlit as st
import pandas as pd
import random
import requests
import hashlib

# --- 1. THEME STYLING ---
st.set_page_config(page_title="SubSentry Alert", page_icon="🔔", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    div.stButton > button:first-child { 
        background-color: #FF0000; color: white; 
        border-radius: 8px; border: 2px solid #FFD700;
        font-weight: bold; width: 100%;
    }
    h1, h2, h3 { color: #FFD700 !important; text-align: center; }
    .stTextInput input { background-color: #222222; color: #FFD700 !important; border: 1px solid #FF0000; }
    section[data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #FF0000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIG & SECRETS ---
try:
    BREVO_API_KEY = st.secrets["BREVO_API_KEY"]
except:
    st.error("❌ BREVO_API_KEY missing in Streamlit Secrets!")
    st.stop()

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
    return requests.post(url, json=payload, headers=headers)

# --- 3. SESSION STATE ---
if 'flow' not in st.session_state:
    st.session_state.flow = "landing"
if 'subs' not in st.session_state:
    st.session_state.subs = []

# --- 4. APP FLOW ---

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
    email = st.text_input("Enter Email")
    if st.button("SEND CODE"):
        st.session_state.temp_email = email
        st.session_state.otp = str(random.randint(100000, 999999))
        send_otp(email, st.session_state.otp)
        st.session_state.flow = "verify_code"
        st.rerun()

# SCREEN: VERIFY CODE
elif st.session_state.flow == "verify_code":
    st.subheader(f"Code sent to {st.session_state.temp_email}")
    code_in = st.text_input("6-Digit Code")
    if st.button("VERIFY"):
        if code_in == st.session_state.otp:
            st.session_state.flow = "create_password"
            st.rerun()
        else:
            st.error("Wrong code.")

# SCREEN: CREATE PASSWORD
elif st.session_state.flow == "create_password":
    st.subheader("Step 2: Set Password")
    p1 = st.text_input("Password", type="password")
    if st.button("COMPLETE SIGN UP"):
        st.session_state.password = p1 # In a real site, we save this to a database
        st.session_state.flow = "dashboard"
        st.rerun()

# SCREEN: LOGIN
elif st.session_state.flow == "login_screen":
    st.subheader("Login to SubSentry")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("ENTER"):
        st.session_state.temp_email = l_email
        st.session_state.flow = "dashboard"
        st.rerun()

# SCREEN: THE REAL DASHBOARD
elif st.session_state.flow == "dashboard":
    st.title(f"🚀 COMMAND CENTER: {st.session_state.temp_email}")
    
    with st.sidebar:
        st.header("➕ Add Subscription")
        name = st.text_input("App Name (e.g. Netflix)")
        price = st.text_input("Price ($/₦)")
        date = st.date_input("Renewal Date")
        if st.button("SET ALERT"):
            st.session_state.subs.append({"App": name, "Price": price, "Date": date})
            st.success(f"Added {name}!")

    st.subheader("Your Active Alerts")
    if st.session_state.subs:
        df = pd.DataFrame(st.session_state.subs)
        st.table(df) # This handles 10+ subscriptions easily
    else:
        st.info("No subscriptions added yet. Use the sidebar to add some!")

    if st.button("LOGOUT"):
        st.session_state.flow = "landing"
        st.rerun()
