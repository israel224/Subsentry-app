import streamlit as st
from supabase import create_client, Client
import datetime
import requests

# --- CONFIG & DATABASE ---
# Ensure these secrets are set in your Streamlit Cloud dashboard
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- BREVO EMAIL FUNCTION ---
def send_email(to_email, subject, content):
    api_key = st.secrets["BREVO_API_KEY"]
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "SubSentry System", "email": "ekeledilichukwuisrael@gmail.com"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": f"<html><body><p>{content}</p></body></html>"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code

# --- APP SESSION STATE ---
if "flow" not in st.session_state:
    st.session_state.flow = "landing"

# --- PAGE: LANDING ---
if st.session_state.flow == "landing":
    st.title("🔔 SUBSENTRY ALERT")
    st.write("Manage your subscriptions and get alerted before you get debited.")
    if st.button("CREATE ACCOUNT"):
        st.session_state.flow = "signup"
        st.rerun()
    if st.button("LOG IN"):
        st.session_state.flow = "login"
        st.rerun()

# --- PAGE: SIGNUP ---
elif st.session_state.flow == "signup":
    st.title("Join the Empire")
    s_email = st.text_input("Email")
    s_pass = st.text_input("Password", type="password")
    if st.button("REGISTER"):
        try:
            res = supabase.auth.sign_up({"email": s_email, "password": s_pass})
            st.success("Registration successful! Check your email for a link.")
        except Exception as e:
            st.error(f"Error: {e}")
    if st.button("Back to Login"):
        st.session_state.flow = "login"
        st.rerun()

# --- PAGE: LOGIN ---
elif st.session_state.flow == "login":
    st.title("Welcome Back")
    l_email = st.text_input("Email")
    l_pass = st.text_input("Password", type="password")
    if st.button("LOG IN"):
        try:
            res = supabase.auth.sign_in_with_password({"email": l_email, "password": l_pass})
            st.session_state.user_id = res.user.id
            st.session_state.temp_email = l_email
            st.session_state.flow = "dashboard"
            st.rerun()
        except:
            st.error("Invalid credentials. Please try again.")

# --- PAGE: DASHBOARD (REMINDER ENGINE INCLUDED) ---
elif st.session_state.flow == "dashboard":
    st.title("🚀 Your Subscriptions")
    user_email = st.session_state.temp_email
    st.write(f"Logged in: {user_email}")

    today = datetime.date.today()
    current_hour = datetime.datetime.now().hour

    # --- THE REMINDER ENGINE ---
    # This scans the whole table to see who needs a message today
    res = supabase.table("subscriptions").select("*").execute()
    
    if res.data:
        for sub in res.data:
            # Date Math
            sub_date = datetime.datetime.strptime(sub['next_renewal_date'], '%Y-%m-%d').date()
            days_left = (sub_date - today).days
            
            # TRIGGER: Between 8 AM and 12 PM AND exactly 2 days left
            if 8 <= current_hour <= 12:
                if days_left == 2:
                    # Session-based safety to prevent duplicate emails on page refresh
                    sent_key = f"sent_{sub['id']}_{today}"
                    if sent_key not in st.session_state:
                        # Find the owner's email (In this case, we send to the registered user)
                        # For testing, it sends to the person currently logged in or the sub owner
                        target_email = sub.get('user_email', user_email) 
                        
                        msg = f"Hi there! Your {sub['service_name']} subscription of ₦{sub['price']} will renew on {sub['next_renewal_date']}."
                        subj = f"⚠️ SubSentry Alert: {sub['service_name']} renews in 2 days!"
                        
                        status = send_email(target_email, subj, msg)
                        if status == 201 or status == 200:
                            st.session_state[sent_key] = True
                            st.success(f"Reminder sent for {sub['service_name']} to {target_email}!")

    # --- DISPLAY SUBSCRIPTIONS ---
    st.subheader("Active Subscriptions")
    # Fetch specifically for THIS logged-in user to show on screen
    user_subs = supabase.table("subscriptions").select("*").eq("user_id", st.session_state.user_id).execute()
    
    if user_subs.data:
        for sub in user_subs.data:
            with st.container():
                st.write(f"*{sub['service_name']}*")
                st.write(f"Price: ₦{sub['price']} | Date: {sub['next_renewal_date']}")
                
                sub_date = datetime.datetime.strptime(sub['next_renewal_date'], '%Y-%m-%d').date()
                if (sub_date - today).days <= 2:
                    st.warning("⚠️ DUE SOON")
                st.divider()
    else:
        st.info("No subscriptions found. Add one below!")

    # --- ADD NEW SUBSCRIPTION ---
    with st.expander("➕ Add New Subscription"):
        name = st.text_input("Service Name (e.g. MTN, Spotify)")
        amt = st.number_input("Price (₦)", min_value=0.0)
        ren_date = st.date_input("Next Renewal Date")
        
        if st.button("SAVE"):
            new_sub = {
                "user_id": st.session_state.user_id,
                "service_name": name,
                "price": amt,
                "next_renewal_date": str(ren_date),
                "user_email": user_email # Storing email to make sure engine knows where to send
            }
            supabase.table("subscriptions").insert(new_sub).execute()
            st.success("Subscription saved successfully!")
            st.rerun()

    if st.button("LOG OUT"):
        st.session_state.clear()
        st.session_state.flow = "landing"
        st.rerun()
