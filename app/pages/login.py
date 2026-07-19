"""Login page for secure user authentication."""

import re
import streamlit as st
from pfm.db import get_session
from pfm.db.models import User
from pfm.config import DB_PATH
from pfm.auth import hash_password, verify_password

def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

from theme.styles import inject_global_styles
if "light_mode" not in st.session_state:
    st.session_state.light_mode = False
inject_global_styles(light_mode=st.session_state.light_mode)

st.logo(":material/account_balance:")

st.title("Welcome to PFM Analytics")
st.markdown("Securely manage your personal finances and analyze transaction history.")

tab1, tab2 = st.tabs(["Log In", "Sign Up"])

with tab1:
    st.subheader("Log In to Your Account")
    with st.form("login_form"):
        login_email = st.text_input("Email Address", placeholder="your_email@example.com")
        login_password = st.text_input("Password", type="password", placeholder="Enter your password")
        login_submitted = st.form_submit_button("Log In", type="primary")

        if login_submitted:
            email_clean = login_email.strip().lower()
            if not email_clean or not login_password:
                st.error("Please enter both email and password.")
            else:
                session = get_session(DB_PATH)
                try:
                    user = session.query(User).filter(User.user_id == email_clean).first()
                    if user and verify_password(user.password_hash, login_password):
                        st.session_state["user_id"] = user.user_id
                        st.session_state["user_name"] = user.user_name
                        st.success(f"Welcome back, {user.user_name}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                except Exception as exc:
                    st.error(f"Database error: {str(exc)}")
                finally:
                    session.close()

    # Optional Google Login integration
    st.markdown("---")
    st.markdown("### Or authenticate with external providers:")
    if st.button(":material/key: Log In with Google (Demo Mode)", width="stretch"):
        st.session_state["user_id"] = "google_user@example.com"
        st.session_state["user_name"] = "Google Test User"
        
        # Seed Google user in DB if not exists
        session = get_session(DB_PATH)
        try:
            google_user = session.query(User).filter(User.user_id == "google_user@example.com").first()
            if not google_user:
                session.add(User(
                    user_id="google_user@example.com",
                    user_name="Google Test User",
                    password_hash=hash_password("google_dummy_pass")
                ))
                session.commit()
        finally:
            session.close()
            
        st.success("Logged in with Google Account!")
        st.rerun()

with tab2:
    st.subheader("Create a New Account")
    with st.form("signup_form"):
        signup_email = st.text_input("Email Address", placeholder="your_email@example.com")
        signup_name = st.text_input("Full Name", placeholder="e.g., Rajesh Sharma")
        signup_password = st.text_input("Password", type="password", placeholder="At least 6 characters")
        signup_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        signup_submitted = st.form_submit_button("Sign Up", type="primary")

        if signup_submitted:
            email_clean = signup_email.strip().lower()
            name_clean = signup_name.strip()
            
            if not email_clean or not name_clean or not signup_password:
                st.error("All fields are required.")
            elif not is_valid_email(email_clean):
                st.error("Please enter a valid email address.")
            elif len(signup_password) < 6:
                st.error("Password must be at least 6 characters long.")
            elif signup_password != signup_confirm:
                st.error("Passwords do not match.")
            else:
                session = get_session(DB_PATH)
                try:
                    exists = session.query(User).filter(User.user_id == email_clean).first() is not None
                    if exists:
                        st.error("An account with this email already exists.")
                    else:
                        new_user = User(
                            user_id=email_clean,
                            user_name=name_clean,
                            password_hash=hash_password(signup_password)
                        )
                        session.add(new_user)
                        session.commit()
                        
                        st.session_state["user_id"] = email_clean
                        st.session_state["user_name"] = name_clean
                        st.success(f"Account created successfully! Welcome, {name_clean}.")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Database error during registration: {str(exc)}")
                finally:
                    session.close()
