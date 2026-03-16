import streamlit as st
from datetime import datetime
import json
import hashlib
import uuid
from pathlib import Path
import time

# Simple user store helpers (file-based)
def _users_file():
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "users.json"

def load_users():
    try:
        uf = _users_file()
        if uf.exists():
            with uf.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_users(users: dict):
    try:
        uf = _users_file()
        with uf.open("w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# Appliances store helpers (file-based)
def _user_dir(email: str):
    """Return a safe per-user data directory."""
    safe_name = "".join(c if c.isalnum() else "_" for c in (email or "").lower())
    user_dir = Path("data") / "users" / safe_name
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def _appliances_file(user_email: str = None):
    if user_email:
        return _user_dir(user_email) / "appliances.json"
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "appliances.json"

def load_appliances(user_email=None):
    try:
        af = _appliances_file(user_email)
        if af.exists():
            with af.open("r", encoding="utf-8") as f:
                appliances = json.load(f)
            # Ensure each appliance has a stable unique id for referencing from homes
            updated = False
            for a in appliances:
                if "id" not in a:
                    a["id"] = str(uuid.uuid4())
                    updated = True
            if updated:
                save_appliances(appliances, user_email)
            return appliances
    except Exception:
        pass
    return []

def save_appliances(appliances: list, user_email=None):
    try:
        af = _appliances_file(user_email)
        with af.open("w", encoding="utf-8") as f:
            json.dump(appliances, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

# Homes store helpers (file-based)
def _homes_file(user_email: str = None):
    if user_email:
        return _user_dir(user_email) / "homes.json"
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "homes.json"

def load_homes(user_email=None):
    try:
        hf = _homes_file(user_email)
        if hf.exists():
            with hf.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_homes(homes: list, user_email=None):
    try:
        hf = _homes_file(user_email)
        with hf.open("w", encoding="utf-8") as f:
            json.dump(homes, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def normalize_home_devices(homes: list, appliances: list):
    """Convert legacy index-based device references to stable appliance IDs."""
    appliance_by_id = {a.get("id"): a for a in appliances if a.get("id")}
    updated = False
    for home in homes:
        devices = home.get("devices", [])
        if not isinstance(devices, list):
            continue
        new_devices = []
        for d in devices:
            if isinstance(d, int):
                if 0 <= d < len(appliances):
                    aid = appliances[d].get("id")
                    if aid:
                        new_devices.append(aid)
                        updated = True
            elif isinstance(d, str):
                if d in appliance_by_id:
                    new_devices.append(d)
                else:
                    # Try to match by name (legacy or manual entries)
                    match = next((a for a in appliances if a.get("name") == d), None)
                    if match and match.get("id"):
                        new_devices.append(match["id"])
                        updated = True
            # ignore other types
        if new_devices != devices:
            home["devices"] = new_devices
            updated = True
    return updated

# Custom CSS for readable text in dark mode
st.markdown("""
    <style>
    /* Main background - black */
    .stApp {
        background-color: #000000 !important;
    }
    
    /* Main text - white and light gray for readability in dark mode */
    body, .stApp {
        color: #FFFFFF;
    }
    
    div, p, span, li {
        color: #D0D0D0;
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF;
        font-weight: 600 !important;
    }
    
    .stMarkdown, .stMarkdown p, .stMarkdown li {
        color: #D0D0D0;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #FFFFFF;
        font-weight: 600 !important;
    }
    
    /* Form labels */
    .stTextInput label, .stSelectbox label, .stCheckbox label, .stRadio label, .stMultiSelect label {
        color: #E8E8E8 !important;
        font-weight: 600 !important;
    }
    
    /* Form inputs */
    .stTextInput input, .stCheckbox, .stRadio, .stTextArea textarea {
        color: #FFFFFF !important;
        background-color: #2a2a2a !important;
    }
    /* Select dropdowns (Category / Current Status) should show black text for readability */
    .stSelectbox, .stSelectbox select, .stSelectbox div[data-baseweb="select"],
    .stSelectbox div[data-baseweb="select"] span {
        color: #000000 !important;
        background-color: #000000 !important;
    }
    /* Dropdown options list - black background with white text */
    .stSelectbox option, .stSelectbox [role="option"],
    .stSelectbox [data-baseweb="select"] [role="option"],
    .stSelectbox [data-baseweb="select"] .baseweb-select-option,
    .stSelectbox div[role="listbox"] div[role="option"] {
        color: #000000 !important;
        background-color: #000000 !important;
    }
    
    /* Buttons - black text */
    .stButton > button {
        color: #000000 !important;
        background-color: #222222 !important;
        border: 1px solid #444444 !important;
        font-weight: 700 !important;
    }

    
    /* Button hover state */
    .stButton > button:hover {
        color: #000000 !important;
        background-color: #333333 !important;
        border-color: #AAAAAA !important;
    }
    
    /* App branding */
    .app-name {
        color: #B0B0B0 !important;
        font-weight: 700 !important;
    }
    
    /* Links */
    .stMarkdown a, a {
        color: #B0B0B0 !important;
        text-decoration: underline;
    }
    
    /* Toggle switches */
    .stToggle label {
        color: #E8E8E8 !important;
        font-weight: 600 !important;
    }
    
    /* Form sections */
    .stForm, .stFormSubmitButton {
        color: #E8E8E8 !important;
    }
    
    /* Info/Alert boxes */
    .stAlert {
        background-color: #2a2a2a !important;
        color: #E8E8E8 !important;
    }
    
    /* Sidebar - dark gray */
    [data-testid="stSidebar"] {
        background-color: #333333 !important;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span {
        color: #D0D0D0 !important;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: ##B0B0B0 !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    /* Tabs */
    .stTabs [role="tab"] {
        color: #D0D0D0 !important;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        color: #B0B0B0 !important;
    }
    
    /* Tables and data */
    table {
        color: #D0D0D0 !important;
    }
    
    table th {
        color: #FFFFFF !important;
        background-color: #333333 !important;
    }
    
    /* Card/box elements */
    .css-1siy2j7, [data-testid="stVerticalBlock"] > [style*="border"] {
        color: #D0D0D0 !important;
    }
    
    /* Error and success messages */
    .stAlert > div {
        color: #E8E8E8 !important;
    }

    /* Ensure dark-background cards render light text */
    [style*="background:#1f1f1f"],
    [style*="background: #1f1f1f"],
    [style*="background:#1a1a1a"],
    [style*="background: #1a1a1a"],
    [style*="background:#2a2a2a"],
    [style*="background: #2a2a2a"] {
        color: #F5F5F5 !important;
    }

    /* Ensure light-background stat cards still keep readable light gray text */
    [style*="background: #1a1a1a"],
    [style*="background:#1a1a1a"],
    [style*="background: #1a1a1a"],
    [style*="background:#1a1a1a"],
    [style*="background: #1a1a1a"],
    [style*="background:#1a1a1a"],
    [style*="background: #1a1a1a"],
    [style*="background:#1a1a1a"],
    [style*="background: #111111"],
    [style*="background:#111111"] {
        color: #D0D0D0 !important;
    }

    /* Sidebar navigation buttons - visible text when not active */
    [data-testid="stSidebar"] .stButton > button:not(:disabled) {
        color: #000000 !important;
        background-color: #333333 !important;
        border: 1px solid #555555 !important;
        font-weight: 600 !important;
    }

    /* Sidebar navigation buttons - active/current page (disabled state) */
    [data-testid="stSidebar"] .stButton > button:disabled {
        color: #000000 !important;
        background-color: #444444 !important;
        border: 1px solid #444444 !important;
        opacity: 1 !important;
        cursor: default !important;
    }

    /* Sidebar navigation button hover state */
    [data-testid="stSidebar"] .stButton > button:not(:disabled):hover {
        color: #000000 !important;
        background-color: #555555 !important;
        border: 1px solid #777777 !important;
    }

    /* Metric cards - gray background */
    [data-testid="stMetric"] {
        background-color: #2a2a2a !important;
        border: 1px solid #444444 !important;
    }

    [data-testid="stMetric"] .css-1xarl3l, [data-testid="stMetric"] .css-10trblm {
        color: #FFFFFF !important;
    }

    /* Expander elements - gray background */
    [data-testid="stExpander"] {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
    }

    /* Columns and containers - subtle gray background */
    [data-testid="column"] {
        background-color: #111111 !important;
        border: 1px solid #222222 !important;
        padding: 10px !important;
        border-radius: 5px !important;
    }

    /* Dataframe and table containers */
    [data-testid="stDataFrame"] {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
    }

    /* Progress bars - gray background */
    .stProgress > div > div {
        background-color: #444444 !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #2a2a2a !important;
        border: 1px solid #444444 !important;
    }

    /* Slider and number input backgrounds */
    [data-testid="stSlider"], [data-testid="stNumberInput"] {
        background-color: #1a1a1a !important;
    }

    /* General container backgrounds for better contrast */
    .css-1r6slb0, .css-1d391kg, .css-12w0qpk {
        background-color: #111111 !important;
        border: 1px solid #222222 !important;
    }

    /* Chat messages and other dynamic content */
    [data-testid="stChatMessage"] {
        background-color: #2a2a2a !important;
        border: 1px solid #444444 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Helper functions for login persistence
def load_login_session():
    """Load login session from data/session.json"""
    try:
        session_file = Path("data") / "session.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_login_session(email, name):
    """Save login session to data/session.json"""
    try:
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        session_data = {"email": email, "name": name}
        with open(data_dir / "session.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def clear_login_session():
    """Clear login session"""
    try:
        session_file = Path("data") / "session.json"
        if session_file.exists():
            session_file.unlink()
    except Exception:
        pass

# Helper functions for admin login persistence
def load_admin_session():
    """Load admin session from data/admin_session.json"""
    try:
        session_file = Path("data") / "admin_session.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_admin_session(email):
    """Save admin session to data/admin_session.json"""
    try:
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        session_data = {"email": email}
        with open(data_dir / "admin_session.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def clear_admin_session():
    """Clear admin session"""
    try:
        session_file = Path("data") / "admin_session.json"
        if session_file.exists():
            session_file.unlink()
    except Exception:
        pass

# Initialize session state
if "logged_in" not in st.session_state:
    # Try to load from saved session
    saved_session = load_login_session()
    if saved_session:
        users = load_users()
        email = saved_session.get("email")
        # Only auto-login if user still exists
        if email and email in users:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.user_name = saved_session.get("name") or users[email].get("name")
        else:
            clear_login_session()
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.user_name = None
            for k in ["appliances", "homes", "current_page"]:
                st.session_state.pop(k, None)
    else:
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        for k in ["appliances", "homes", "current_page"]:
            st.session_state.pop(k, None)

if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "page" not in st.session_state:
    st.session_state.page = None
if "admin_logged_in" not in st.session_state:
    admin_session = load_admin_session()
    if admin_session:
        st.session_state.admin_logged_in = True
        st.session_state.admin_user = admin_session.get("email")
        st.session_state.page = "admin"
    else:
        st.session_state.admin_logged_in = False
if "admin_user" not in st.session_state:
    st.session_state.admin_user = None
if "logo_last_click" not in st.session_state:
    st.session_state.logo_last_click = 0.0
if "admin_nav" not in st.session_state:
    st.session_state.admin_nav = "overview"


def render_header():
    """Render UnplugGo header with logo and tagline. Double-tap logo to open admin dashboard."""

    def handle_logo_tap():
        now = time.time()
        last = st.session_state.get("logo_last_click", 0.0)
        if now - last < 2.5:
            st.session_state.page = "admin"
            st.session_state.logo_last_click = 0.0
        else:
            st.session_state.logo_last_click = now

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Visible logo button (double-tap to open admin dashboard)
        st.button(
            "⚡ UnplugGo",
            key="logo_tap_button",
            help="Double-tap to open admin dashboard",
            use_container_width=True,
            on_click=handle_logo_tap,
        )
        st.markdown(
            """
            <div style="text-align: center; padding: 6px 0 10px 0;">
                <p style="color: #B0B0B0; font-size: 1.1em; margin: 0;">Grab, Click and Go</p>
                <p style="color: #888; font-size: 0.9em; margin: 4px 0 0 0;">Fire Prevention for Cantilan, Surigao del Sur</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def sign_in_page():
    """Render the sign-in form inline."""
    st.markdown("---")
    st.markdown("### Welcome Back")
    st.markdown("Sign in to manage your appliances and stay safe")

    # Show flash message from signup and prefill email if provided
    if st.session_state.get("signup_success_message"):
        st.success(st.session_state.signup_success_message)
        st.session_state.signup_success_message = None
    if st.session_state.get("prefill_email"):
        st.session_state.signin_email = st.session_state.prefill_email
        st.session_state.prefill_email = None
    
    with st.form("sign_in_form"):
        email = st.text_input("Email", placeholder="you@example.com", key="signin_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="signin_password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        if submitted:
            if not (email and password):
                st.error("Please fill in all fields")
            else:
                users = load_users()
                user = users.get(email)
                if not user:
                    st.error("Account not found. Please sign up.")
                elif user.get("password") != hash_password(password):
                    st.error("Incorrect password")
                else:
                    name = user.get("name") or email.split("@")[0]
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.user_name = name
                    st.session_state.page = None

                    # Clear any previous session data so it reloads for this user
                    st.session_state.pop("appliances", None)
                    st.session_state.pop("homes", None)
                    st.session_state.pop("current_page", None)

                    save_login_session(email, name)
                    st.success(f"Welcome back, {name}!")
                    st.rerun()
    
    if st.button("Back to Home", key="back_from_signin"):
        st.session_state.page = None
        st.rerun()


def sign_up_page():
    """Render the sign-up form inline."""
    st.markdown("---")
    st.markdown("### Create Account")
    st.markdown("Sign up to start protecting your home from fire hazards")
    
    with st.form("sign_up_form"):
        full_name = st.text_input("Full Name", placeholder="Juan Dela Cruz", key="signup_name")
        email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="signup_password")
        submitted = st.form_submit_button("Sign Up", use_container_width=True)
        if submitted:
            if not (full_name and email and password):
                st.error("Please fill in all fields")
            else:
                users = load_users()
                if email in users:
                    st.error("Account already exists. Please sign in.")
                else:
                    users[email] = {"name": full_name, "password": hash_password(password)}
                    if save_users(users):
                        # Auto-login after signup
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.session_state.user_name = full_name
                        st.session_state.page = None

                        # Ensure new user starts with an empty appliance list and default homes
                        st.session_state.pop("appliances", None)
                        st.session_state.pop("homes", None)
                        st.session_state.pop("current_page", None)

                        save_login_session(email, full_name)
                        st.success("Account created! You're now signed in.")
                        st.rerun()
                    else:
                        st.error("Could not save your account. Please try again.")
    
    if st.button("Back to Home", key="back_from_signup"):
        st.session_state.page = None
        st.rerun()


def show_dashboard():
    """Render the main dashboard with fire prevention focus."""

    # Ensure appliances are loaded from disk (persisted per-user)
    if "appliances" not in st.session_state:
        st.session_state.appliances = load_appliances(st.session_state.user_email) or []
        save_appliances(st.session_state.appliances, st.session_state.user_email)

    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    # Ensure homes are loaded from disk (persisted per-user)
    if "homes" not in st.session_state:
        st.session_state.homes = load_homes(st.session_state.user_email) or [
            {"name": "Main House", "place": "Cantilan, Surigao del Sur", "active": True, "devices": []},
            {"name": "Vacation Home", "place": "Beach Area", "active": False, "devices": []},
        ]
        save_homes(st.session_state.homes, st.session_state.user_email)

    # Normalize legacy home device references (indexes -> appliance IDs)
    if normalize_home_devices(st.session_state.homes, st.session_state.appliances):
        save_homes(st.session_state.homes, st.session_state.user_email)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; padding: 20px 0;">
                <h2 class="app-name" style="font-size: 1.5em; margin: 0;">⚡ UnplugGo</h2>
                <p style="color: #AAAAAA; font-size: 0.9em; margin-top: 5px;">Fire Prevention</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        
        st.markdown("<p style='font-weight: bold; color: #B0B0B0;'>MENU</p>", unsafe_allow_html=True)
        
        nav_items = [
            ("home", "🏠 Home"),
            ("appliances", "📋 Appliances"),
            ("homes", "🏠 Homes"),
            ("adapters", "⚡ Adapters"),
            ("settings", "⚙️ Settings"),
        ]
        
        for page_key, label in nav_items:
            if st.button(label, use_container_width=True, key=f"nav_{page_key}", 
                        help=f"Go to {label.split()[-1]}", disabled=(st.session_state.current_page == page_key)):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"<p style='color: #AAAAAA; font-size: 0.85em;'>👤 {st.session_state.user_email}</p>", unsafe_allow_html=True)
        
        if st.button("🚪 Sign Out", use_container_width=True, key="signout_sidebar"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.session_state.current_page = None
            for k in ["appliances", "homes", "current_page"]:
                st.session_state.pop(k, None)
            clear_login_session()
            st.rerun()
    
    # Main content area
    # Get active home name
    active_home = next((h for h in st.session_state.homes if h.get("active", False)), {"name": "Main House"})
    active_home_name = active_home["name"]
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"<p style='font-size: 1.1em; font-weight: bold; margin: 0;'>UnplugGo<br><span style='font-size: 0.9em; color: #AAAAAA;'>{active_home_name}</span></p>", unsafe_allow_html=True)
    with col3:
        st.markdown("<p style='text-align: right; color: #B0B0B0; font-weight: bold;'>🔥 Fire Prevention</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Current page content
    if st.session_state.current_page == "home":
        render_home_page()
    elif st.session_state.current_page == "appliances":
        render_appliances_page()
    elif st.session_state.current_page == "homes":
        render_homes_page()
    elif st.session_state.current_page == "adapters":
        render_adapters_page()
    elif st.session_state.current_page == "settings":
        render_settings_page()


def render_home_page():
    """Render the home dashboard page."""

    # Determine which home is active and which appliances belong to it
    active_home = next((h for h in st.session_state.homes if h.get("active")), None)
    appliance_by_id = {a.get("id"): a for a in st.session_state.appliances if a.get("id")}
    if active_home:
        active_ids = set(active_home.get("devices", []))
        active_appliances = [appliance_by_id[i] for i in active_ids if i in appliance_by_id]
    else:
        active_appliances = st.session_state.appliances

    total_devices = len(active_appliances)
    plugged_in = sum(1 for a in active_appliances if a.get("plugged"))
    unplugged = total_devices - plugged_in
    smart_devices = sum(1 for a in active_appliances if a.get("smart"))
    power_usage = 0.0
    for a in active_appliances:
        if a.get("plugged"):
            # parse strings like "45W" or "45"
            p = str(a.get("power", "")).strip().upper().replace("W", "")
            try:
                power_usage += float(p)
            except Exception:
                pass
    power_usage_str = f"{int(power_usage)}W" if power_usage == int(power_usage) else f"{power_usage:.1f}W"

    # Status cards
    card_col1, card_col2 = st.columns(2)
    with card_col1:
        st.markdown(
            f'''<div style="background: #1a1a1a; padding: 20px; border-radius: 10px; border-left: 4px solid #555555;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="color: #D0D0D0 !important; font-weight: bold; font-size: 1.1em; margin: 0;">Plugged In</p>
                        <p style="color: #D0D0D0 !important; font-size: 2em; font-weight: bold; margin: 5px 0 0 0;">{plugged_in}</p>
                    </div>
                    <div style="font-size: 2em;">🔌</div>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )
    
    with card_col2:
        st.markdown(
            f'''<div style="background: #1a1a1a; padding: 20px; border-radius: 10px; border-left: 4px solid #555555;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="color: #D0D0D0 !important; font-weight: bold; font-size: 1.1em; margin: 0;">Unplugged</p>
                        <p style="color: #D0D0D0 !important; font-size: 2em; font-weight: bold; margin: 5px 0 0 0;">{unplugged}</p>
                    </div>
                    <div style="font-size: 2em;">✅</div>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )
    
    card_col3, card_col4 = st.columns(2)
    with card_col3:
        st.markdown(
            f'''<div style="background: #1a1a1a; padding: 20px; border-radius: 10px; border-left: 4px solid #555555;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="color: #D0D0D0 !important; font-weight: bold; font-size: 1.1em; margin: 0;">Smart Devices</p>
                        <p style="color: #D0D0D0 !important; font-size: 2em; font-weight: bold; margin: 5px 0 0 0;">{smart_devices}</p>
                    </div>
                    <div style="font-size: 2em;">📡</div>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )
    
    with card_col4:
        st.markdown(
            f'''<div style="background: #1a1a1a; padding: 20px; border-radius: 10px; border-left: 4px solid #555555;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="color: #D0D0D0 !important; font-weight: bold; font-size: 1.1em; margin: 0;">Power Usage</p>
                        <p style="color: #D0D0D0 !important; font-size: 2em; font-weight: bold; margin: 5px 0 0 0;">{power_usage_str}</p>
                    </div>
                    <div style="font-size: 2em;">⚡</div>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )
    
    st.markdown("")
    
    # Quick Actions
    st.markdown("<p style='font-weight: bold; font-size: 1.1em;'>Quick Actions</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #AAAAAA; margin-top: -10px;'>Manage your appliances and devices</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ Add Appliance", use_container_width=True, key="add_appliance"):
            st.session_state.current_page = "appliances"
            st.rerun()
    with col2:
        if st.button("📡 Connect Smart Adapter", use_container_width=True, key="connect_adapter"):
            st.session_state.current_page = "adapters"
            st.rerun()
    
    st.markdown("")
    
    # Currently Plugged In
    st.markdown("<p style='font-weight: bold; font-size: 1.1em;'>Currently Plugged In</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #AAAAAA; margin-top: -10px;'>Monitor these devices to prevent fire hazards</p>", unsafe_allow_html=True)
    
    for device in active_appliances:
        if device.get("plugged"):
            st.markdown(
                f'''<div style="background: #1a1a1a; padding: 15px; border-radius: 8px; border-left: 3px solid #555555; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <p style="font-weight: bold; margin: 0; font-size: 1em;">{device.get('name','')}</p>
                            <p style="color: #AAAAAA; margin: 5px 0 0 0; font-size: 0.9em;">{device.get('location','')}</p>
                        </div>
                        <div style="text-align: right;">
                            <p style="color: #CCCCCC; font-weight: bold; margin: 0;">{device.get('power','')}</p>
                            <p style="color: #CCCCCC; font-size: 0.85em; margin: 5px 0 0 0;">{device.get('status','')}</p>
                        </div>
                    </div>
                </div>''',
                unsafe_allow_html=True,
            )
    
    st.markdown("")
    
    # Fire Prevention Tips
    st.markdown("<p style='font-weight: bold; font-size: 1.1em;'>Fire Prevention Tips</p>", unsafe_allow_html=True)
    tips = [
        "Always unplug appliances when not in use, especially high-wattage devices like irons and rice cookers",
        "Never leave chargers plugged in overnight without supervision",
        "Check electrical cords regularly for damage or wear",
        "Use UnplugGo smart adapters for automatic monitoring and alerts",
    ]
    for tip in tips:
        st.markdown(f"• {tip}")


def render_appliances_page():
    """Render appliances management page with grouped cards and add modal."""
    active_home = next((h for h in st.session_state.homes if h.get("active")), {"name": "Main House"})
    active_home_name = active_home.get("name", "Main House")

    st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'>", unsafe_allow_html=True)
    st.markdown(f"<div><strong>My Appliances</strong><br><span style='color:#AAAAAA;'>Tracking devices at {active_home_name}</span></div>", unsafe_allow_html=True)
    add_col = st.empty()
    if add_col.button("+ Add", key="open_add"): 
        st.session_state.show_add = True
    st.markdown("</div>", unsafe_allow_html=True)

    # Show add form in-place when requested
    if st.session_state.get("show_add", False):
        with st.form("add_appliance_form"):
            device_name = st.text_input("Appliance Name", placeholder="e.g., Electric Fan, Rice Cooker")
            location = st.text_input("Location", placeholder="e.g., Living Room, Kitchen")
            category = st.selectbox("Category", options=["Other", "Kitchen", "Living Room", "Bedroom"], index=0)
            current_status = st.selectbox("Current Status", options=["Unplugged (Safe)", "Plugged In"], index=0)
            submitted = st.form_submit_button("Add Appliance")
            if submitted and device_name and location:
                now = datetime.now().strftime("%I:%M:%S %p")
                plugged = True if current_status == "Plugged In" else False
                new_appliance = {
                    "id": str(uuid.uuid4()),
                    "name": device_name,
                    "location": location,
                    "power": "0W" if not plugged else "5W",
                    "status": "Monitored" if plugged else "Manual",
                    "plugged": plugged,
                    "smart": False,
                    "last_updated": now,
                }
                st.session_state.appliances.append(new_appliance)

                # Assign to active home (so dashboard/home stats stay in sync)
                if active_home is not None:
                    active_home.setdefault("devices", []).append(new_appliance["id"])
                    save_homes(st.session_state.homes, st.session_state.user_email)

                save_appliances(st.session_state.appliances, st.session_state.user_email)
                st.session_state.show_add = False
                st.success(f"Added {device_name}!")
                st.rerun()
        if st.button("Cancel Add", key="cancel_add"):
            st.session_state.show_add = False
            st.rerun()

    st.markdown("---")
    # Group appliances by location
    locations = {}
    for idx, a in enumerate(st.session_state.appliances):
        locations.setdefault(a.get("location", "Unknown"), []).append((idx, a))

    for loc, items in locations.items():
        st.markdown(f"<div style='background:#111111; padding:12px; border-radius:10px; margin-bottom:12px;'><strong>{loc}</strong> <span style='background:#222222; border-radius:8px; padding:2px 6px; font-size:0.8em;'>{len(items)}</span></div>", unsafe_allow_html=True)
        for idx, device in items:
                device_key = device.get("id") or f"idx_{idx}"
                plugged = device.get("plugged", False)
                color = "#1a1a1a"
                action_label = "Unplug" if plugged else "Plug In"
                # Make action buttons very visible (black text)
                action_color = "background:#444444; color:#000000; padding:6px 10px; border-radius:6px;" if plugged else "background:#333333; color:#000000; padding:6px 10px; border-radius:6px;"
                smart_badge = "<span style='background:#222222; color:#D0D0D0; padding:4px 6px; border-radius:6px; font-size:0.8em; margin-left:8px;'>Smart</span>" if device.get("smart") else "<span style='background:#222222; color:#AAAAAA; padding:4px 6px; border-radius:6px; font-size:0.8em; margin-left:8px;'>Manual</span>"
                st.markdown(f'''<div style="background:{color}; padding:12px; border-radius:8px; margin-bottom:10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <div style="font-weight:600;">{device.get('name','')} {smart_badge}</div>
                                    <div style="color:#AAAAAA; font-size:0.9em;">{device.get('location','')}</div>
                                </div>
                                <div style="text-align:right;">
                                    <form>
                                    </form>
                                    <div style="margin-bottom:6px;"><button style='{action_color}' onclick=''>{action_label}</button></div>
                                    <div style='font-size:0.9em; color:#9CA3AF;'>{('Plugged In' if plugged else 'Unplugged')} &nbsp; <span style="color:#B0B0B0; font-weight:600;">{device.get('power','')}</span></div>
                                    <div style='font-size:0.8em; color:#9CA3AF;'>Last updated: {device.get('last_updated','')}</div>
                                </div>
                            </div>
                        </div>''', unsafe_allow_html=True)
                colA, colB = st.columns([5,1])
                with colB:
                    if st.button("🗑️", key=f"del_{device_key}"):
                        removed_id = device.get("id")
                        if removed_id:
                            idx_to_remove = next((i for i, a in enumerate(st.session_state.appliances) if a.get("id") == removed_id), None)
                        else:
                            idx_to_remove = idx if idx < len(st.session_state.appliances) else None
                        if idx_to_remove is not None:
                            st.session_state.appliances.pop(idx_to_remove)
                        if removed_id:
                            for h in st.session_state.homes:
                                if removed_id in h.get("devices", []):
                                    h["devices"].remove(removed_id)
                            save_homes(st.session_state.homes, st.session_state.user_email)
                        save_appliances(st.session_state.appliances, st.session_state.user_email)
                        st.success("Removed")
                        st.rerun()
                if st.button(action_label, key=f"toggle_{device_key}"):
                    toggle_id = device.get("id")
                    if toggle_id:
                        target = next((a for a in st.session_state.appliances if a.get("id") == toggle_id), None)
                    else:
                        target = st.session_state.appliances[idx] if idx < len(st.session_state.appliances) else None
                    if target:
                        target["plugged"] = not target.get("plugged", False)
                        target["last_updated"] = datetime.now().strftime("%I:%M:%S %p")
                        if target["plugged"]:
                            target["power"] = "45W"
                            target["status"] = "Monitored"
                        else:
                            target["power"] = "0W"
                            target["status"] = "Manual"
                        save_appliances(st.session_state.appliances, st.session_state.user_email)
                        st.rerun()


def render_homes_page():
    """Render the homes overview page to manage multiple properties."""
    if "homes" not in st.session_state:
        st.session_state.homes = []

    if "show_edit" not in st.session_state:
        st.session_state.show_edit = False
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None

    st.markdown(
        "<div style='display:flex; justify-content:space-between; align-items:center; background:#111111; padding:16px; border-radius:12px; border:2px solid #333333; margin-bottom:16px;'>"
        "<div><strong style='font-size:1.1em;'>🏠 My Homes</strong><br><span style=\"color:#888; font-size:0.9em;\">Manage multiple locations and get alerts for each</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    add_col1, add_col2 = st.columns([4,1])
    with add_col2:
        if st.button("+ Add Home", key="add_home", use_container_width=True):
            st.session_state.homes.append({"name": f"Home {len(st.session_state.homes)+1}", "place": "New Area", "active": False, "devices": []})
            if not save_homes(st.session_state.homes, st.session_state.user_email):
                st.error("Failed to save homes")
            else:
                st.success("Home added")
            st.rerun()

    current = next((h for h in st.session_state.homes if h.get("active")), None)
    if current:
        st.markdown(
            f"<div style='background:#111111; padding:14px; border-radius:10px; margin-bottom:16px; border-left:4px solid #B0B0B0;'>"
            f"<strong style='color:#B0B0B0;'>📍 Currently Viewing</strong><br><span style=\"color:#333; font-weight:600;\">{current['name']}</span><br><span style=\"color:#AAAAAA; font-size:0.9em;\">{current['place']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    appliance_by_id = {a.get("id"): a for a in st.session_state.appliances if a.get("id")}

    for i, home in enumerate(st.session_state.homes):
        device_ids = home.get("devices", []) if isinstance(home.get("devices", []), list) else []
        total = len(device_ids)
        plugged = sum(1 for did in device_ids if appliance_by_id.get(did, {}).get("plugged"))
        smart = sum(1 for did in device_ids if appliance_by_id.get(did, {}).get("smart"))

        if home.get("active"):
            border = "3px solid #B0B0B0"
            bg = "#111111"
        else:
            border = "1px solid #E5E7EB"
            bg = "#111111"
        active_badge = f"<span style=\"background:#B0B0B0; color:#111111; padding:3px 8px; border-radius:5px; font-size:0.75em; font-weight:600;\">Active</span>" if home.get("active") else ""
        st.markdown(
            f"<div style='background:{bg}; padding:16px; border-radius:12px; border:{border}; margin-bottom:16px;'>"
            f"<div style=\"display:flex; justify-content:space-between; align-items:flex-start;\">"
            f"<div style=\"flex:1;\">"
            f"<div style=\"display:flex; align-items:center; gap:8px; margin-bottom:4px;\">"
            f"<strong style=\"font-size:1.05em;\">{home['name']}</strong>"
            f"{active_badge}"
            f"</div>"
            f"<span style=\"color:#AAAAAA; font-size:0.9em;\">📍 {home['place']}</span>"
            f"</div>"
            f"</div>"
            f"<div style=\"display:flex; justify-content:space-between; margin-top:14px;\">"
            f"<div style=\"display:flex; gap:16px;\">"
            f"<div><strong style=\"color:#AAAAAA;\">Total</strong><br><span style=\"font-size:1.2em; font-weight:700;\">{total}</span></div>"
            f"<div><strong style=\"color:#B0B0B0;\">Plugged In</strong><br><span style=\"font-size:1.2em; font-weight:700; color:#B0B0B0;\">{plugged}</span></div>"
            f"<div><strong style=\"color:#B0B0B0;\">Smart</strong><br><span style=\"font-size:1.2em; font-weight:700; color:#B0B0B0;\">{smart}</span></div>"
            f"</div>"
            f"<div style=\"text-align:right;\">"
            f"<div style=\"background:#111111; color:#B0B0B0; padding:8px 12px; border-radius:8px; font-size:0.9em; font-weight:600;\">⚡ {plugged} plugged in</div>"
            f"</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1])
        with c1:
            if st.button("✏️ Edit", key=f"edit_home_{i}", use_container_width=True):
                st.session_state.edit_index = i
                st.session_state.show_edit = True
                st.rerun()
        with c2:
            if st.button("🗑️ Delete", key=f"del_home_{i}", use_container_width=True):
                st.session_state.homes.pop(i)
                if not save_homes(st.session_state.homes, st.session_state.user_email):
                    st.error("Failed to save homes")
                st.success("Home removed")
                st.rerun()
        with c3:
            if not home.get("active"):
                if st.button("🔄 Switch to This Home", key=f"switch_{i}", use_container_width=True):
                    for h in st.session_state.homes:
                        h["active"] = False
                    st.session_state.homes[i]["active"] = True
                    if not save_homes(st.session_state.homes, st.session_state.user_email):
                        st.error("Failed to save homes")
                    st.success(f"Switched to {home['name']}")
                    st.rerun()
            else:
                st.markdown("<div style='padding:8px;'><small style='color:#888;'>Currently active</small></div>", unsafe_allow_html=True)

    if st.session_state.get("show_edit") and st.session_state.get("edit_index") is not None:
        idx = st.session_state.edit_index
        if 0 <= idx < len(st.session_state.homes):
            home = st.session_state.homes[idx]
            with st.expander("✏️ Edit Home", expanded=True):
                st.markdown(f"<p style='font-size:1.2em; font-weight:bold; margin-bottom:16px;'>Edit Home</p>", unsafe_allow_html=True)
                new_name = st.text_input("Home Name", value=home.get("name", ""), key=f"edit_name_{idx}", placeholder="e.g., Main House")
                new_place = st.text_input("Location/Place", value=home.get("place", ""), key=f"edit_place_{idx}", placeholder="e.g., Cantilan, Surigao del Sur")
                st.markdown("<br>", unsafe_allow_html=True)
                col_ok, col_space, col_cancel = st.columns([1, 0.5, 1])
                with col_ok:
                    if st.button("✅ Save Changes", key=f"save_home_{idx}", use_container_width=True):
                        st.session_state.homes[idx]["name"] = new_name
                        st.session_state.homes[idx]["place"] = new_place
                        if not save_homes(st.session_state.homes, st.session_state.user_email):
                            st.error("Failed to save homes")
                        st.session_state.show_edit = False
                        st.session_state.edit_index = None
                        st.success("Home updated")
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key=f"cancel_edit_{idx}", use_container_width=True):
                        st.session_state.show_edit = False
                        st.session_state.edit_index = None
                        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style=\"background:#111111; padding:16px; border-radius:12px; border-left:4px solid #B0B0B0;\">"
        "<strong style=\"font-size:1.05em; color:#B0B0B0;\">ℹ️ About Home Sections</strong>"
        "<ul style=\"margin-top:12px; margin-bottom:0;\">"
        "<li style=\"margin-bottom:8px;\">Create separate sections for different properties (main house, vacation home, rental, etc.)</li>"
        "<li style=\"margin-bottom:8px;\">Each home has its own set of appliances and smart adapters</li>"
        "<li style=\"margin-bottom:8px;\">Receive alerts specific to each location</li>"
        "<li>Easily switch between homes to monitor all your properties</li>"
        "</ul></div>",
        unsafe_allow_html=True,
    )


def load_settings():
    """Load settings from data/settings.json."""
    try:
        settings_file = Path("data") / "settings.json"
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "push_notifications": True,
        "daily_reminders": True,
        "smart_adapter_alerts": True,
        "reminder_frequency": "Every 2 hours",
        "high_risk_start": "6:00 PM",
        "high_risk_end": "10:00 PM",
        "dark_mode": False,
    }


def save_settings(settings):
    """Save settings to data/settings.json."""
    try:
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        with open(data_dir / "settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Failed to save settings: {e}")


def render_settings_page():
    """Render settings page with notifications, safety, appearance, and about sections."""
    if "settings" not in st.session_state:
        st.session_state.settings = load_settings()

    st.markdown("<div style='background:#111111; padding:16px; border-radius:12px; margin-bottom:16px;'><strong style='font-size:1.05em;'>🔔 Notifications</strong><br><span style=\"color:#AAAAAA; font-size:0.9em;\">Configure how you receive safety alerts</span></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<div style='padding:12px 0;'><strong>Push Notifications</strong><br><span style=\"color:#AAAAAA; font-size:0.9em;\">Receive alerts when devices are left plugged in</span></div>", unsafe_allow_html=True)
    with col2:
        push_notif = st.toggle("Push Notifications", value=st.session_state.settings.get("push_notifications", True), key="push_notif_toggle")
        st.session_state.settings["push_notifications"] = push_notif

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<div style='padding:12px 0;'><strong>Daily Safety Reminders</strong><br><span style=\"color:#AAAAAA; font-size:0.9em;\">Get a daily reminder to check your appliances</span></div>", unsafe_allow_html=True)
    with col2:
        daily_reminders = st.toggle("Daily Reminders", value=st.session_state.settings.get("daily_reminders", True), key="daily_reminders_toggle")
        st.session_state.settings["daily_reminders"] = daily_reminders

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<div style='padding:12px 0;'><strong>Smart Adapter Alerts</strong><br><span style=\"color:#AAAAAA; font-size:0.9em;\">Instant alerts from connected smart adapters</span></div>", unsafe_allow_html=True)
    with col2:
        smart_alerts = st.toggle("Smart Alerts", value=st.session_state.settings.get("smart_adapter_alerts", True), key="smart_alerts_toggle")
        st.session_state.settings["smart_adapter_alerts"] = smart_alerts

    st.markdown("")

    st.markdown("<div style='background:#111111; padding:16px; border-radius:12px; margin-bottom:16px; border-top:3px solid #B0B0B0;'><strong style='font-size:1.05em;'>🛡️ Safety Settings</strong></div>", unsafe_allow_html=True)

    st.markdown("<div style='padding:12px 0;'><strong>Reminder Frequency</strong></div>", unsafe_allow_html=True)
    freq_options = ["Every 1 hour", "Every 2 hours", "Every 3 hours", "Every 6 hours", "Daily"]
    reminder_freq = st.selectbox("Reminder Frequency", options=freq_options, index=freq_options.index(st.session_state.settings.get("reminder_frequency", "Every 2 hours")), key="reminder_freq_select", label_visibility="collapsed")
    st.session_state.settings["reminder_frequency"] = reminder_freq

    st.markdown("<div style='padding:12px 0;'><strong>High-Risk Hours</strong><br><span style=\"color:#AAAAAA; font-size:0.9em;\">Receive extra alerts during these hours</span></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.selectbox("Start Time", options=["12:00 AM", "1:00 AM", "2:00 AM", "3:00 AM", "4:00 AM", "5:00 AM", "6:00 AM", "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM", "10:00 PM", "11:00 PM"], index=18, key="start_time_select", label_visibility="collapsed")
        st.session_state.settings["high_risk_start"] = start_time
    with col2:
        end_time = st.selectbox("End Time", options=["12:00 AM", "1:00 AM", "2:00 AM", "3:00 AM", "4:00 AM", "5:00 AM", "6:00 AM", "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM", "10:00 PM", "11:00 PM"], index=22, key="end_time_select", label_visibility="collapsed")
        st.session_state.settings["high_risk_end"] = end_time

    st.markdown("")

    st.markdown("<div style='background:#111111; padding:16px; border-radius:12px; margin-bottom:16px;'><strong style='font-size:1.05em;'>🌙 Appearance</strong></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<div style='padding:12px 0;'><strong>Dark Mode</strong><br><span style=\"color:#AAAAAA; font-size:0.9em;\">Use dark theme for the app</span></div>", unsafe_allow_html=True)
    with col2:
        dark_mode = st.toggle("Dark Mode", value=st.session_state.settings.get("dark_mode", False), key="dark_mode_toggle")
        st.session_state.settings["dark_mode"] = dark_mode

    st.markdown("")

    st.markdown("<div style='background:#111111; padding:16px; border-radius:12px; margin-bottom:16px;'><strong style='font-size:1.05em;'>ℹ️ About UnplugGo</strong></div>", unsafe_allow_html=True)

    st.markdown(
        "<div style='background:#f5f5f5; padding:16px; border-radius:10px; margin-bottom:12px;'>"
        "<p style='margin:0 0 8px 0; font-weight:600;'>UnplugGo is a fire prevention application designed to help residents of Cantilan, Surigao del Sur safely manage their electrical appliances and prevent fire incidents.</p>"
        "<p style='margin:8px 0; color:#AAAAAA;'><strong>Version:</strong> 1.0.0</p>"
        "<p style='margin:8px 0; color:#AAAAAA;'><strong>Location:</strong> Cantilan, Surigao del Sur</p>"
        "<p style='margin:8px 0; color:#AAAAAA;'><strong>Purpose:</strong> Fire Prevention & Safety</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<strong style='margin-top:16px;'>⚡ Quick Links</strong>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Emergency Contacts", use_container_width=True, key="emergency_btn"):
            st.info("📞 Emergency Fire Department: 911\n🚒 Local Fire Station: Cantilan Fire Department")
    with col2:
        if st.button("Privacy Policy", use_container_width=True, key="privacy_btn"):
            st.info("Your data is protected and only used for fire prevention purposes.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Terms of Service", use_container_width=True, key="terms_btn"):
            st.info("By using UnplugGo, you agree to our terms of service for fire prevention.")
    with col2:
        if st.button("Help & Support", use_container_width=True, key="help_btn"):
            st.info("For support, contact us at support@unpluggo.com or call our hotline.")

    st.markdown("")

    st.markdown(
        "<div style='background:#111111; padding:20px; border-radius:12px; border:2px solid #B0B0B0; text-align:center; margin-bottom:16px;'>"
        "<div style='font-size:1.5em; margin-bottom:8px;'>⚡</div>"
        "<strong style='font-size:1.05em; color:#B0B0B0;'>Emergency Fire Hotline</strong><br>"
        "<p style='margin:8px 0; color:#AAAAAA;'>📞 911 / Local Fire Station</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    save_settings(st.session_state.settings)


def render_adapters_page():
    """Render smart adapters page."""
    st.markdown("### Smart Adapters")
    st.markdown("Connect and manage your UnplugGo smart adapters.")
    st.info("Coming soon: Adapter pairing and management")


def render_admin_dashboard():
    """Admin dashboard with sidebar navigation and rich panels (previous design)."""

    # Ensure admin session
    if not st.session_state.get("admin_logged_in"):
        # Admin login form
        with st.form("admin_login_form"):
            admin_email = st.text_input("Admin Email", placeholder="admin@unpluggo.com", key="admin_email")
            admin_password = st.text_input("Admin Password", type="password", placeholder="••••••••", key="admin_password")
            submitted = st.form_submit_button("Sign In as Admin", use_container_width=True)
            if submitted:
                if admin_email == "admin@unpluggo.com" and admin_password == "admin123":
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = admin_email
                    save_admin_session(admin_email)
                    st.success("Admin login successful")
                    st.session_state.page = "admin"
                    st.rerun()
                else:
                    st.error("Invalid admin credentials")
        if st.button("← Back", key="admin_back_login", use_container_width=True):
            st.session_state.page = None
            st.rerun()
        return

    # Sidebar navigation
    with st.sidebar:
        st.markdown("<h3 style='color:#B0B0B0; text-align:center;'>⚡ Admin Panel</h3>", unsafe_allow_html=True)
        nav_items = [
            ("dashboard", "🏠 Overview"),
            ("users", "👥 Users"),
            ("auth", "🔐 Authenticate Users"),
            ("usage", "📊 Appliance Usage"),
            ("reports", "📄 Reports"),
            ("settings", "⚙️ System Settings"),
        ]
        current = st.session_state.get("admin_nav", "dashboard")
        for key, label in nav_items:
            if st.button(label, key=f"admin_nav_{key}", use_container_width=True):
                st.session_state.admin_nav = key
                st.rerun()
        st.markdown("---")
        if st.button("🚪 Sign Out", key="admin_signout_sidebar", use_container_width=True):
            st.session_state.admin_logged_in = False
            clear_admin_session()
            st.session_state.admin_user = None
            st.session_state.page = None
            st.rerun()

    st.markdown(f"**Signed in as:** {st.session_state.get('admin_user', '')}")
    nav = st.session_state.get("admin_nav", "dashboard")

    # Dashboard layout
    if nav == "dashboard":
        users = st.session_state.get("users_cache", {})
        total_users = len(users) if isinstance(users, dict) else 0
        total_appliances = len(st.session_state.get("appliances", []))
        plugged = sum(1 for a in st.session_state.get("appliances", []) if a.get("plugged"))
        smart = sum(1 for a in st.session_state.get("appliances", []) if a.get("smart"))

        st.markdown(
            """
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;">
                <div style="background:#1f1f1f;padding:12px 14px;border-radius:10px;border:1px solid #2d2d2d;">
                    <div style="color:#B0B0B0;font-weight:700;">Users</div>
                    <div style="font-size:1.6em;font-weight:800;color:#111111;">{users_count}</div>
                    <div style="color:#888;font-size:0.9em;">Total registered</div>
                </div>
                <div style="background:#1f1f1f;padding:12px 14px;border-radius:10px;border:1px solid #2d2d2d;">
                    <div style="color:#B0B0B0;font-weight:700;">Appliances</div>
                    <div style="font-size:1.6em;font-weight:800;color:#111111;">{appliances_count}</div>
                    <div style="color:#888;font-size:0.9em;">Tracked devices</div>
                </div>
                <div style="background:#1f1f1f;padding:12px 14px;border-radius:10px;border:1px solid #2d2d2d;">
                    <div style="color:#D0D0D0 !important;font-weight:700;">Plugged In</div>
                    <div style="font-size:1.6em;font-weight:800;color:#D0D0D0 !important;">{plugged_count}</div>
                    <div style="color:#888;font-size:0.9em;">Currently active</div>
                </div>
                <div style="background:#1f1f1f;padding:12px 14px;border-radius:10px;border:1px solid #2d2d2d;">
                    <div style="color:#9b59b6;font-weight:700;">Smart Devices</div>
                    <div style="font-size:1.6em;font-weight:800;color:#111111;">{smart_count}</div>
                    <div style="color:#888;font-size:0.9em;">With smart adapters</div>
                </div>
            </div>
            """.format(users_count=total_users, appliances_count=total_appliances, plugged_count=plugged, smart_count=smart),
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        cta1, cta2, cta3 = st.columns(3)
        with cta1:
            if st.button("👥 Manage Users", use_container_width=True):
                st.session_state.admin_nav = "users"; st.rerun()
        with cta2:
            if st.button("🔐 Authenticate Users", use_container_width=True):
                st.session_state.admin_nav = "auth"; st.rerun()
        with cta3:
            if st.button("📄 Reports", use_container_width=True):
                st.session_state.admin_nav = "reports"; st.rerun()

    elif nav == "users":
        st.markdown("### Manage Users")
        users = load_users()
        st.session_state.users_cache = users
        search = st.text_input("Search users", key="admin_user_search", placeholder="Search by name or email")
        st.markdown("---")
        if not users:
            st.info("No users found.")
        else:
            for email, data in users.items():
                if search and search.lower() not in email.lower() and search.lower() not in data.get("full_name", "").lower():
                    continue
                with st.container():
                    c1, c2, c3 = st.columns([3, 2, 1])
                    with c1:
                        st.markdown(f"**{data.get('full_name','N/A')}**<br><span style='color:#888;'>{email}</span>", unsafe_allow_html=True)
                    with c2:
                        created = data.get("created_at", "Unknown")
                        st.markdown(f"<span style='color:#888;'>Created: {created[:10] if len(created)>10 else created}</span>", unsafe_allow_html=True)
                    with c3:
                        if st.button("🗑️", key=f"del_user_{email}"):
                            users.pop(email)
                            save_users(users)
                            st.success(f"Deleted {email}")
                            st.rerun()

    elif nav == "auth":
        st.markdown("### Authenticate Users")
        users = load_users()
        if not users:
            st.info("No users to authenticate.")
        else:
            for email, data in users.items():
                with st.expander(f"👤 {data.get('full_name','N/A')} - {email}"):
                    st.write(f"Email: {email}")
                    st.write(f"Name: {data.get('full_name','N/A')}")
                    st.write(f"Created: {data.get('created_at','Unknown')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Approve", key=f"approve_{email}"):
                            st.success(f"Approved {email}")
                    with col2:
                        if st.button("❌ Reject", key=f"reject_{email}"):
                            st.warning(f"Rejected {email}")

    elif nav == "usage":
        st.markdown("### Appliance Usage")
        total = len(st.session_state.get("appliances", []))
        plugged = sum(1 for a in st.session_state.get("appliances", []) if a.get("plugged"))
        smart = sum(1 for a in st.session_state.get("appliances", []) if a.get("smart"))
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Appliances", total)
        c2.metric("Currently Plugged", plugged)
        c3.metric("Smart Devices", smart)
        st.info("Detailed usage analytics coming soon.")

    elif nav == "reports":
        st.markdown("### Reports")
        report_type = st.selectbox("Report Type", ["Usage Summary", "Alerts", "User Activity"], key="admin_report_type")
        date_range = st.date_input("Date Range", [])
        if st.button("Generate Report", key="admin_generate_report", use_container_width=True):
            st.success(f"Generated {report_type} report (placeholder)")

    elif nav == "settings":
        st.markdown("### System Settings")
        st.toggle("Maintenance Mode", key="admin_maintenance")
        st.toggle("Enable Email Alerts", value=True, key="admin_email_alerts")
        st.selectbox("Default Reminder Frequency", ["Every 1 hour", "Every 2 hours", "Every 6 hours"], key="admin_reminder_default")

    st.markdown("---")
    if st.button("← Back", key="admin_back_btn", use_container_width=True):
        st.session_state.page = None
        st.rerun()


def main():
    st.set_page_config(page_title="UnplugGo", layout="wide", initial_sidebar_state="expanded")
    
    render_header()
    
    # Admin path when explicitly triggered
    if st.session_state.page == "admin":
        render_admin_dashboard()
        return
    
    if st.session_state.logged_in:
        show_dashboard()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sign In", use_container_width=True, key="signin_btn"):
                st.session_state.page = "signin"
                st.rerun()
        with col2:
            if st.button("Sign Up", use_container_width=True, key="signup_btn"):
                st.session_state.page = "signup"
                st.rerun()
        
        if st.session_state.page == "signin":
            sign_in_page()
        elif st.session_state.page == "signup":
            sign_up_page()
        else:
            st.markdown("---")
            st.markdown(
                """
                <div style="display: flex; justify-content: space-around; padding: 20px; text-align: center;">
                    <div>
                        <div style="font-size: 2em;">⚡</div>
                        <p><strong>Smart Monitoring</strong></p>
                    </div>
                    <div>
                        <div style="font-size: 2em;">🔥</div>
                        <p><strong>Fire Prevention</strong></p>
                    </div>
                    <div>
                        <div style="font-size: 2em;">📊</div>
                        <p><strong>Real-time Alerts</strong></p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
