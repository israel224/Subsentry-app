import streamlit as st
from supabase import create_client, Client
import datetime
import requests
import json

# --- 1. CONFIGURATION & SECRETS ---
# This ensures we connect to your specific database
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Missing Database Secrets! Check Streamlit Cloud.")

# --- 2. BREVO EMAIL ENGINE ---
def send_email(to_email, subject, content):
    """Sends high-priority transactional emails via Brevo API"""
    try:
        api_key = st.secrets["BREVO_API_KEY"]
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }
        payload = {
            "sender": {"name": "SubSentry AI", "email": "ekeledilichukwuisrael@gmail.com"},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": f"<html><body style='font-family: Arial;'><h2>SubSentry Notification</h2><p>{content}</p></body></html>"
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code
    except Exception as e:
        st.sidebar.error(f"Email Engine Error: {e}")
        return 500

# --- 3. SESSION MANAGEMENT ---
if "flow" not in st.session_state:
    st.session_state.flow = "landing"
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# --- 4. NAVIGATION FLOW ---

# --- PAGE: LANDING ---
if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT SYSTEM")
    st.subheader("Never get debited by surprise again.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 GET STARTED"):
            st.session_state.flow = "signup"
            st.rerun()
    with col2:
        if st.button("🔑 LOGIN"):
            st.session_state.flow = "login"
            st.rerun()

# --- PAGE: SIGNUP ---
elif st.session_state.flow == "signup":
    st.title("Create Emperor Account")
    with st.form("signup_form"):
        s_email = st.text_input("Email Address")
        s_pass = st.text_input("Choose Password", type="password")
        submit = st.form_submit_button("CREATE ACCOUNT")
        
        if submit:
            try:
                supabase.auth.sign_up({"email": s_email, "password": s_pass})
                st.success("Success! Now go to Supabase and Confirm this user.")
            except Exception as e:
                st.error(f"Signup failed: {e}")
    if st.button("Already have an account? Log in"):
        st.session_state.flow = "login"
        st.rerun()

# --- PAGE: LOGIN ---
elif st.session_state.flow == "login":
    st.title("Welcome Back, Emperor")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    
    if st.button("SECURE LOG IN"):
        try:
            # STRIP spaces to prevent "Invalid Credentials"
            response = supabase.auth.sign_in_with_password({
                "email": l_email.strip(), 
                "password": l_pass
            })
            if response.user:
                st.session_state.user_id = response.user.id
                st.session_state.temp_email = l_email.strip()
                st.session_state.flow = "dashboard"
                st.rerun()
        except Exception as e:
            st.error(f"AUTHENTICATION ERROR: {str(e)}")
            st.info("Tip: If you keep seeing this, click 'Confirm User' in your Supabase Auth dashboard.")

# --- PAGE: DASHBOARD (THE MASTER ENGINE) ---
elif st.session_state.flow == "dashboard":
    st.title("🚀 SubSentry Dashboard")
    curr_user = st.session_state.temp_email
    st.info(f"User: {curr_user}")

    # DATE & TIME CALCULATIONS
    today = datetime.date.today()
    current_hour = datetime.datetime.now().hour
    
    # --- AUTOMATED REMINDER ENGINE ---
    # This runs for EVERYONE in the database every time the dashboard loads
    try:
        all_subs = supabase.table("subscriptions").select("*").execute()
        if all_subs.data:
            for s in all_subs.data:
                # Calculate renewal gap
                target_date = datetime.datetime.strptime(s['next_renewal_date'], '%Y-%m-%d').date()
                gap = (target_date - today).days
                
                # TRIGGER: 8:00 AM to 12:00 PM Window + 2 Days Left
                if 8 <= current_hour <= 12:
                    if gap == 2:
                        # Prevent duplicate emails within the same hour
                        lock_key = f"sent_{s['id']}_{today}"
                        if lock_key not in st.session_state:
                            email_dest = s.get('user_email', curr_user)
                            subject = f"⚠️ RENEWAL ALERT: {s['service_name']}"
                            body = f"Your {s['service_name']} sub of ₦{s['price']} renews on {s['next_renewal_date']} (2 days!)."
                            
                            status = send_email(email_dest, subject, body)
                            if status in [200, 201]:
                                st.session_state[lock_key] = True
                                st.toast(f"✅ Reminder sent for {s['service_name']}!")
    except Exception as e:
        st.error(f"Engine Error: {e}")

    # --- SUBSCRIPTION LIST UI ---
    st.subheader("Your Monitored Services")
    my_subs = supabase.table("subscriptions").select("*").eq("user_id", st.session_state.user_id).execute()
    
    if my_subs.data:
        for sub in my_subs.data:
            with st.expander(f"📦 {sub['service_name']} - ₦{sub['price']}"):
                st.write(f"*Renewal Date:* {sub['next_renewal_date']}")
                days_to_go = (datetime.datetime.strptime(sub['next_renewal_date'], '%Y-%m-%d').date() - today).days
                st.write(f"*Countdown:* {days_to_go} days left")
                if days_to_go <= 2:
                    st.warning("Action Required: Renewal approaching!")
    else:
        st.write("No active subscriptions. Add your first one below!")

    # --- ADD NEW SUBSCRIPTION FORM ---
    st.divider()
    with st.expander("➕ REGISTER NEW SUBSCRIPTION"):
        with st.form("add_sub"):
            n_name = st.text_input("Service Name (e.g. Netflix, MTN)")
            n_price = st.number_input("Monthly Cost (₦)", min_value=0.0)
            n_date = st.date_input("Next Billing Date")
            save = st.form_submit_button("ADD TO SYSTEM")
            
            if save:
                new_entry = {
                    "user_id": st.session_state.user_id,
                    "service_name": n_name,
                    "price": n_price,
                    "next_renewal_date": str(n_date),
                    "user_email": curr_user
                }
                supabase.table("subscriptions").insert(new_entry).execute()
                st.success("Added to database!")
                st.rerun()

    # --- LOGOUT ---
    if st.sidebar.button("🚪 LOGOUT"):
        st.session_state.clear()
        st.session_state.flow = "landing"
        st.rerun()
