import streamlit as st
import requests
from datetime import datetime


# API Base URL
API_URL = "http://127.0.0.1:8001"


# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Career Compass - AI Career Navigator",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== SESSION STATE INITIALIZATION ====================
session_defaults = {
    'authenticated': False,
    'access_token': None,
    'user_data': None,
    'resume_id': None,
    'resume_data': None,
    'current_page': "🏠 Home",
    'messages': [],
    'job_match_result': None,
    'show_loader': False,
    'advice_count': 0,
    'match_count': 0,
    'match_scores': [],           # ✅ NEW: Track all match scores
    'best_match_score': 0,        # ✅ NEW: Best match achieved
    'avg_match_score': 0,         # ✅ NEW: Average match score
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================== MODERN THEME STYLING ====================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-dark: #0f172a;
        --bg-card: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #334155;
    }
    
    body, .stApp {
        background-color: var(--bg-dark) !important;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.05) 0%, transparent 50%);
    }
    
    /* ✅ HIDE STREAMLIT BRANDING & DEFAULT MENU */
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    
    /* ✅ HIDE STREAMLIT'S DEFAULT HAMBURGER MENU */
    button[kind="header"],
    button[kind="headerNoPadding"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* ✅ HAMBURGER BUTTON - When sidebar is OPEN (close button) */
    [data-testid="stSidebarCollapseButton"] {
        position: fixed !important;
        top: 1rem !important;
        left: 1rem !important;
        z-index: 9999999 !important;
        background: linear-gradient(135deg, #6366f1, #ec4899) !important;
        border-radius: 12px !important;
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        max-width: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.6) !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        padding: 0 !important;
        opacity: 1 !important;
        visibility: visible !important;
        pointer-events: all !important;
    }

    /* ✅ HAMBURGER BUTTON - When sidebar is CLOSED (open button) */
    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 1rem !important;
        left: 1rem !important;
        z-index: 9999999 !important;
        background: linear-gradient(135deg, #6366f1, #ec4899) !important;
        border-radius: 12px !important;
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        max-width: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.6) !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        padding: 0 !important;
        opacity: 1 !important;
        visibility: visible !important;
        pointer-events: all !important;
    }

    /* ✅ Hover effect */
    [data-testid="collapsedControl"]:hover,
    [data-testid="stSidebarCollapseButton"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 6px 30px rgba(99, 102, 241, 0.8) !important;
        background: linear-gradient(135deg, #4f46e5, #db2777) !important;
    }
    /* ✅ IMPORTANT: Allow button content to be clickable */
    [data-testid="collapsedControl"] *,
    [data-testid="stSidebarCollapseButton"] * {
        pointer-events: none !important; /* Disable pointer events on children only */
}

    /* ✅ Hide default content but KEEP button clickable */
    [data-testid="collapsedControl"] > div,
    [data-testid="stSidebarCollapseButton"] > div {
        pointer-events: none !important;
    }

    [data-testid="collapsedControl"] span,
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] svg {
        display: none !important;
    }

    /* ✅ Custom hamburger icon ☰ */
    [data-testid="collapsedControl"]::before,
    [data-testid="stSidebarCollapseButton"]::before {
        content: "☰" !important;
        font-size: 24px !important;
        color: white !important;
        font-family: Arial, sans-serif !important;
        font-weight: bold !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        pointer-events: none !important;
        width: 100% !important;
        height: 100% !important;
    }
    /* ✅ HIDE "Press Enter to submit form" instruction */
[data-testid="InputInstructions"] {
    display: none !important;
    visibility: hidden !important;
}

/* Also hide for text input */
.stTextInput [data-testid="InputInstructions"],
.stTextArea [data-testid="InputInstructions"] {
    display: none !important;
}

    /* ✅ SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.98), rgba(10, 14, 39, 0.98)) !important;
        border-right: 1px solid var(--border-color) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
    }
    
    /* Force sidebar content visible */
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    
    p, span, label {
        color: var(--text-secondary) !important;
    }
    
    /* Modern Cards */
    .modern-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.4));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .modern-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 20px 25px rgba(99, 102, 241, 0.1);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4) !important;
    }
    
    /* Input Fields */
    .stTextInput input, .stTextArea textarea {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 12px !important;
        padding: 2rem !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--primary) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.9rem !important;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(99, 102, 241, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 102, 241, 0.3);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.5);
    }

    /* ✅ FIX EXPANDER ARROWS */
    [data-testid="stExpander"] summary span[data-testid="stIconMaterial"] {
        display: inline-flex !important;
        visibility: visible !important;
        font-size: 1.2rem !important;
        color: var(--text-primary) !important;
        font-family: 'Material Icons' !important;
    }
    
    [data-testid="stExpander"] summary span[data-testid="stIconMaterial"] {
        font-size: 0 !important;
        line-height: 0 !important;
    }
    
    [data-testid="stExpander"] summary span[data-testid="stIconMaterial"]::before {
        font-size: 1rem !important;
        line-height: normal !important;
        color: var(--primary) !important;
        display: inline-block !important;
    }
    
    [data-testid="stExpander"] summary {
        cursor: pointer !important;
        padding: 1rem !important;
        background: rgba(99, 102, 241, 0.05) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stExpander"] summary:hover {
        background: rgba(99, 102, 241, 0.1) !important;
    }

    </style>
""", unsafe_allow_html=True)


# ==================== HELPER FUNCTIONS ====================
def get_auth_headers():
    """Get authorization headers"""
    if st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}


def smooth_transition(page_name):
    """Navigate to a page smoothly"""
    st.session_state.current_page = page_name
    st.rerun()


def api_call(method, endpoint, **kwargs):
    """Centralized API call handler"""
    try:
        url = f"{API_URL}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers.update(get_auth_headers())
        
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
        
        if method == "GET":
            response = requests.get(url, headers=headers, **kwargs)
        elif method == "POST":
            response = requests.post(url, headers=headers, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, **kwargs)
        
        return response
    except Exception as e:
        st.error(f"❌ Connection error: {str(e)}")
        return None


# ==================== LANDING PAGE ====================
def show_landing_page():
    """Landing page with authentication"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 3rem 0 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🧭</div>
                <h1 style="font-size: 3.5rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, #6366f1, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Career Compass
                </h1>
                <p style="font-size: 1.2rem; color: var(--text-muted); margin-bottom: 3rem;">
                    Your AI-Powered Career Navigator
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3, gap="medium")
    
    features = [
        ("🔍", "Smart Resume Analysis", "AI-powered analysis with RAG technology"),
        ("⚡", "Instant Job Matching", "Real-time comparison with job descriptions"),
        ("💬", "Career Guidance", "24/7 AI advisor for career questions"),
    ]
    
    for idx, (icon, title, desc) in enumerate(features):
        with [col1, col2, col3][idx]:
            st.markdown(f"""
                <div class="modern-card" style="text-align: center;">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">{icon}</div>
                    <h3 style="margin: 1rem 0 0.5rem; font-size: 1.1rem;">{title}</h3>
                    <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0;">{desc}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=True):
                email = st.text_input("📧 Email", placeholder="your@email.com")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
                submit = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
                
                if submit:
                    if not email or not password:
                        st.error("❌ Please fill in all fields")
                    else:
                        with st.spinner("Authenticating..."):
                            response = api_call("POST", "/login", 
                                              data={"username": email, "password": password})
                            
                            if response and response.status_code == 200:
                                data = response.json()
                                st.session_state.authenticated = True
                                st.session_state.access_token = data.get('access_token')
                                st.session_state.user_data = {
                                    'user_id': data.get('user_id'),
                                    'username': data.get('username'),
                                    'email': data.get('email')
                                }
                                st.success("✅ Login successful!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Invalid email or password")
        
        with tab2:
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=True):
                reg_email = st.text_input("📧 Email", placeholder="your@email.com", key="reg_email")
                reg_username = st.text_input("👤 Username", placeholder="Choose username", key="reg_username")
                reg_password = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters", key="reg_password")
                reg_confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm")
                
                submit = st.form_submit_button("🎉 Create Account", use_container_width=True, type="primary")
                
                if submit:
                    if not reg_email or not reg_username or not reg_password:
                        st.error("❌ Please fill in all required fields")
                    elif reg_password != reg_confirm:
                        st.error("❌ Passwords don't match")
                    elif len(reg_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        with st.spinner("Creating account..."):
                            response = api_call("POST", "/register",
                                              json={
                                                  "email": reg_email,
                                                  "username": reg_username,
                                                  "password": reg_password
                                              })
                            
                            if response and response.status_code == 200:
                                data = response.json()
                                st.session_state.authenticated = True
                                st.session_state.access_token = data.get('access_token')
                                st.session_state.user_data = {
                                    'user_id': data.get('user_id'),
                                    'username': data.get('username'),
                                    'email': data.get('email')
                                }
                                st.success("🎉 Account created!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Registration failed. Email may already exist.")


# ==================== HOME PAGE ====================
def show_home_page():
    """Dashboard home page with gamified scoring"""
    
    st.markdown(f"""
        <div style="margin-bottom: 3rem;">
            <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">
                👋 Welcome back, <span style="color: var(--primary);">{st.session_state.user_data['username']}</span>
            </h1>
            <p style="color: var(--text-muted); font-size: 1.05rem;">
                Let's advance your career journey today.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # ✅ Fetch real counts from database
    resume_count = 0
    match_count = 0
    advice_count = 0
    best_match_score = 0
    total_skills = 0
    total_domains = 0
    
    # Get resume count
    resumes_response = api_call("GET", "/my-resumes")
    if resumes_response and resumes_response.status_code == 200:
        resumes_data = resumes_response.json()
        resume_count = resumes_data.get("count", 0)
        
        # Get skills/domains from first resume if available
        resumes_list = resumes_data.get("resumes", [])
        if resumes_list and len(resumes_list) > 0:
            first_resume = resumes_list[0]
            total_skills = first_resume.get("skills_count", 0)
    
    # Get match history count
    match_response = api_call("GET", "/match-history")
    if match_response and match_response.status_code == 200:
        matches_data = match_response.json()
        matches_list = matches_data.get("matches", [])
        match_count = len(matches_list)
        
        # Get best match score
        if matches_list:
            best_match_score = max([m.get('match_score', 0) for m in matches_list])
    
    # Get chat history count
    chat_response = api_call("GET", "/chat-history")
    if chat_response and chat_response.status_code == 200:
        chats_data = chat_response.json()
        advice_count = len(chats_data.get("chats", []))
    
    # ==================== GAMIFIED CAREER READINESS SCORE ====================
    profile_score = 0
    tier = "🌱 Beginner"
    tier_color = "#94a3b8"
    tier_emoji = "🌱"
    next_goal = "Upload your first resume to begin your journey"

    # Level 1: Getting Started (0-25)
    if resume_count > 0:
        profile_score = 15
        tier = "🌱 Getting Started"
        tier_color = "#94a3b8"
        tier_emoji = "🌱"
        next_goal = "Complete 1 job match to reach Active Job Seeker"
        
        if total_skills >= 5:
            profile_score = 25
            next_goal = "Complete 3 job matches to reach Active Job Seeker"

    # Level 2: Active Job Seeker (26-50)
    if match_count > 0:
        profile_score = 35
        tier = "📈 Active Job Seeker"
        tier_color = "#6366f1"
        tier_emoji = "📈"
        next_goal = "Complete 3 career advice queries to reach Career Optimizer"
        
        if match_count >= 3:
            profile_score = 45
            next_goal = "Use career advice 3 times to level up"
        if match_count >= 5:
            profile_score = 50
            next_goal = "Keep exploring career advice to level up"

    # Level 3: Career Optimizer (51-75)
    if advice_count > 0:
        profile_score = max(profile_score, 55)
        tier = "⭐ Career Optimizer"
        tier_color = "#06b6d4"
        tier_emoji = "⭐"
        next_goal = "Upload 2+ resumes and complete 5+ matches to reach Power User"
        
        if advice_count >= 3:
            profile_score = 65
            next_goal = "Complete 5 job matches to reach Power User"
        if advice_count >= 5:
            profile_score = 75
            next_goal = "Upload multiple resumes and get 5+ job matches"

    # Level 4: Power User (76-100)
    if resume_count >= 2 and match_count >= 5 and advice_count >= 5:
        profile_score = 85
        tier = "🔥 Power User"
        tier_color = "#f59e0b"
        tier_emoji = "🔥"
        next_goal = "Get 15+ skills to reach Expert"
        
        # Bonus: High quality resume
        if total_skills >= 15:
            profile_score = 95
            tier = "🚀 Career Expert"
            tier_color = "#10b981"
            tier_emoji = "🚀"
            next_goal = "Achieve 80%+ job match score to reach Master"
        
        # Ultimate bonus: Strong job matches
        if best_match_score >= 80:
            profile_score = 100
            tier = "🏆 Career Master"
            tier_color = "gold"
            tier_emoji = "🏆"
            next_goal = "You've mastered Career Compass! 🎉"

    profile_score = round(profile_score, 1)
    
    # ==================== DASHBOARD METRICS ====================
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown(f"""
            <div class="modern-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0 0 0.5rem 0;">Total Resumes</p>
                        <h2 style="color: var(--primary); font-size: 2.5rem; margin: 0;">{resume_count}</h2>
                    </div>
                    <div style="font-size: 2rem;">📄</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="modern-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0 0 0.5rem 0;">Career Readiness</p>
                        <h2 style="color: {tier_color}; font-size: 2.5rem; margin: 0 0 0.5rem 0;">{profile_score}</h2>
                        <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 8px; overflow: hidden;">
                            <div style="background: {tier_color}; height: 100%; width: {profile_score}%; transition: width 0.3s ease;"></div>
                        </div>
                        <p style="color: {tier_color}; font-size: 0.85rem; margin: 0.5rem 0 0 0; font-weight: 600;">{tier}</p>
                    </div>
                    <div style="font-size: 2rem;">{tier_emoji}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        ai_sessions = match_count + advice_count
        st.markdown(f"""
            <div class="modern-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0 0 0.5rem 0;">AI Sessions</p>
                        <h2 style="color: var(--success); font-size: 2.5rem; margin: 0;">{ai_sessions}</h2>
                    </div>
                    <div style="font-size: 2rem;">💬</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ✅ Progress to Next Level
    if profile_score < 100:
        st.markdown(f"""
            <div class="modern-card" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.1));">
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <div style="font-size: 2rem;">🎯</div>
                    <div>
                        <p style="color: var(--text-muted); font-size: 0.85rem; margin: 0;">Next Goal</p>
                        <p style="color: var(--text-primary); font-size: 1rem; margin: 0.3rem 0 0 0; font-weight: 500;">{next_goal}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="modern-card" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(245, 158, 11, 0.2)); text-align: center;">
                <h3 style="margin: 0; color: gold;">🏆 Congratulations! You're a Career Master! 🏆</h3>
                <p style="margin: 0.5rem 0 0 0; color: var(--text-muted);">You've mastered all features of Career Compass!</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("<h3 style='margin: 0 0 1rem 0;'>⚡ Quick Start</h3>", unsafe_allow_html=True)
        if st.button("📄 Upload Resume", use_container_width=True):
            smooth_transition("📄 Upload Resume")
        if st.button("🎯 Find Jobs", use_container_width=True):
            smooth_transition("🎯 Job Match")
        if st.button("💬 Ask AI Advisor", use_container_width=True):
            smooth_transition("💬 Career Advice")
    
    with col2:
        st.markdown("<h3 style='margin: 0 0 1rem 0;'>📊 Tips</h3>", unsafe_allow_html=True)
        st.markdown("""
            <div class="modern-card">
                <p style="margin: 0.5rem 0; font-size: 0.9rem;">• Keep your resume updated regularly</p>
                <p style="margin: 0.5rem 0; font-size: 0.9rem;">• Match with multiple job descriptions</p>
                <p style="margin: 0.5rem 0; font-size: 0.9rem;">• Ask specific career questions</p>
            </div>
        """, unsafe_allow_html=True)

# ==================== UPLOAD RESUME PAGE ====================
def show_upload_page():
    """Resume upload page"""
    
    st.markdown("<h1 style='margin-bottom: 1rem;'>📄 Upload Your Resume</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted); margin-bottom: 2rem;'>Upload a PDF or DOCX file for AI-powered analysis.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose file", type=['pdf', 'docx'], help="Max 10MB")
    
    if uploaded_file:
        st.markdown(f"""
            <div class="modern-card">
                <p style="margin: 0; color: var(--text-muted);"><strong>Selected:</strong> {uploaded_file.name}</p>
                <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.9rem;">{uploaded_file.size / 1024:.1f} KB</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Analyze Resume", use_container_width=True, type="primary"):
            with st.spinner("🤖 AI is analyzing your resume..."):
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = api_call("POST", "/upload-resume", files=files)
                
                if response and response.status_code == 200:
                    data = response.json()
                    st.session_state.resume_id = data.get('resume_id')
                    st.session_state.resume_data = data
                    st.success("✅ Resume analyzed successfully!")
                    st.balloons()
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("🎯 Skills Found", len(data.get('skills', [])))
                    
                    with col2:
                        st.metric("🏢 Career Domains", len(data.get('domains', [])))
                    
                    with col3:
                        st.metric("📝 Text Length", f"{len(data.get('extracted_text', ''))} chars")
                    
                    if data.get('skills'):
                        st.markdown("<br><h3>💼 Extracted Skills</h3>", unsafe_allow_html=True)
                        skills_html = " ".join([
                            f"<span style='display: inline-block; background: rgba(99, 102, 241, 0.2); color: var(--primary); padding: 0.4rem 0.8rem; border-radius: 20px; margin: 0.2rem; font-size: 0.9rem; border: 1px solid var(--primary);'>{skill}</span>"
                            for skill in data.get('skills', [])
                        ])
                        st.markdown(skills_html, unsafe_allow_html=True)
                    
                    if data.get('domains'):
                        st.markdown("<br><h3>🎯 Career Domains</h3>", unsafe_allow_html=True)
                        for domain in data.get('domains', []):
                            st.success(f"✓ {domain.replace('_', ' ').title()}")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🎯 Match with Jobs", use_container_width=True):
                            smooth_transition("🎯 Job Match")
                    with col2:
                        if st.button("💬 Get Career Advice", use_container_width=True):
                            smooth_transition("💬 Career Advice")
                else:
                    st.error("❌ Failed to analyze resume. Please try again.")


# ==================== JOB MATCH PAGE ====================
def show_job_match_page():
    """Job matching page"""
    
    st.markdown("<h1 style='margin-bottom: 1rem;'>🎯 Job Match Analysis</h1>", unsafe_allow_html=True)
    
    if not st.session_state.resume_id:
        st.warning("⚠️ Please upload a resume first to use this feature.")
        if st.button("📄 Go to Upload Resume"):
            smooth_transition("📄 Upload Resume")
        st.stop()
    
    st.markdown(f"""
        <div class="modern-card">
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div style="background: rgba(99, 102, 241, 0.1); padding: 0.8rem; border-radius: 10px; font-size: 1.5rem;">📄</div>
                <div>
                    <p style="margin: 0; color: var(--text-muted); font-size: 0.9rem;">Active Resume</p>
                    <p style="margin: 0; color: var(--text-primary); font-weight: 600;">Resume ID: {st.session_state.resume_id[:16]}...</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    job_desc = st.text_area(
        "📋 Job Description",
        height=250,
        placeholder="Paste the complete job description here including:\n- Job title\n- Required skills\n- Responsibilities\n- Qualifications",
        help="The more details you provide, the better the match analysis"
    )
    
    if st.button("🚀 Analyze Match", use_container_width=True, type="primary"):
        if not job_desc or len(job_desc.strip()) < 50:
            st.error("❌ Please provide a detailed job description (at least 50 characters)")
        else:
            with st.spinner("⚙️ AI is comparing your profile with the job..."):
                payload = {
                    "resume_id": st.session_state.resume_id,
                    "job_description": job_desc.strip()
                }
                response = api_call("POST", "/job-match", json=payload)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.session_state.job_match_result = result
                    st.session_state.match_count += 1
                    
                    # ✅ Track match scores for gamification
                    match_score = result.get('match_score', 0)
                    st.session_state.match_scores.append(match_score)
                    st.session_state.avg_match_score = sum(st.session_state.match_scores) / len(st.session_state.match_scores)
                    st.session_state.best_match_score = max(st.session_state.match_scores)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if match_score >= 80:
                        score_color = "var(--success)"
                        score_message = "🎉 Excellent Match! You're a strong candidate."
                    elif match_score >= 60:
                        score_color = "#06b6d4"
                        score_message = "👍 Good Match! Some skill gaps to address."
                    else:
                        score_color = "var(--warning)"
                        score_message = "📝 Partial Match. Consider upskilling."
                    
                    st.markdown(f"""
                        <div class="modern-card" style="text-align: center; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.1));">
                            <h2 style="margin: 0 0 1rem 0;">Match Score</h2>
                            <div style="font-size: 4rem; color: {score_color}; font-weight: 800; margin: 1rem 0;">{match_score}%</div>
                            <p style="margin: 0; font-size: 1.1rem;">{score_message}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2, gap="large")
                    
                    with col1:
                        st.markdown("<h3>✅ Matching Skills</h3>", unsafe_allow_html=True)
                        matching = result.get('matched_skills', [])
                        if matching:
                            for skill in matching:
                                st.markdown(f"""
                                    <div style='background: rgba(16, 185, 129, 0.1); padding: 0.5rem 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 3px solid var(--success);'>
                                        ✓ {skill}
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No exact skill matches found")
                    
                    with col2:
                        st.markdown("<h3>📚 Skills to Develop</h3>", unsafe_allow_html=True)
                        missing = result.get('missing_skills', [])
                        if missing:
                            for skill in missing:
                                st.markdown(f"""
                                    <div style='background: rgba(245, 158, 11, 0.1); padding: 0.5rem 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 3px solid var(--warning);'>
                                        ○ {skill}
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("🎉 All required skills matched!")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("💡 AI Recommendations", expanded=True):
                        st.markdown(f"""
                            <div style='background: rgba(99, 102, 241, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid var(--primary);'>
                                <p style='margin: 0; line-height: 1.8;'>{result.get('recommendations', 'No recommendations available.')}</p>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("❌ Failed to analyze match. Please try again.")


# ==================== CAREER ADVICE PAGE ====================
def show_career_advice_page():
    """Career advice page with chat history"""
    
    st.markdown("<h1 style='margin-bottom: 1rem;'>💬 Career Advice</h1>", unsafe_allow_html=True)
    
    # ✅ Fetch user's resumes from database instead of relying on session state
    resumes_response = api_call("GET", "/my-resumes")
    
    if not resumes_response or resumes_response.status_code != 200:
        st.error("❌ Failed to load resumes")
        return
    
    resumes_data = resumes_response.json()
    resumes_list = resumes_data.get('resumes', [])
    
    # ✅ Check if user has any resumes
    if not resumes_list or len(resumes_list) == 0:
        st.warning("⚠️ Please upload a resume first to get personalized advice.")
        if st.button("📄 Go to Upload Resume", use_container_width=True):
            smooth_transition("📄 Upload Resume")
        
        # ✅ Still show chat history even without resumes
        st.markdown("<br><hr style='border: none; border-top: 1px solid rgba(128, 128, 128, 0.2);'><br>", unsafe_allow_html=True)
        st.markdown("### 📜 Previous Conversations")
        
        chat_response = api_call("GET", "/chat-history")
        if chat_response and chat_response.status_code == 200:
            chats = chat_response.json().get('chats', [])
            if chats:
                st.info("You can view your previous conversations below.")
                for chat in chats:
                    from datetime import datetime
                    created_date = datetime.fromisoformat(chat['created_at'].replace('Z', '+00:00'))
                    date_str = created_date.strftime("%b %d, %Y • %I:%M %p")
                    question_preview = chat['user_query'][:80] + "..." if len(chat['user_query']) > 80 else chat['user_query']
                    
                    with st.expander(f"💬 {question_preview}", expanded=False):
                        st.markdown(f"<p style='color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;'>{date_str}</p>", unsafe_allow_html=True)
                        st.markdown(f"""
                            <div style="background: rgba(99, 102, 241, 0.08); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                                <p style="margin: 0 0 0.5rem 0; color: var(--primary); font-weight: 600; font-size: 0.85rem;">YOUR QUESTION</p>
                                <p style="margin: 0; line-height: 1.7; color: var(--text-primary);">{chat['user_query']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f"""
                            <div style="background: rgba(16, 185, 129, 0.08); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                                <p style="margin: 0 0 0.5rem 0; color: var(--success); font-weight: 600; font-size: 0.85rem;">AI RESPONSE</p>
                                <p style="margin: 0; line-height: 1.8; color: var(--text-primary);">{chat['ai_response']}</p>
                            </div>
                        """, unsafe_allow_html=True)
        return
    
    # ✅ User has resumes - show resume selector
    resume_options = {r['filename']: r['resume_id'] for r in resumes_list}
    selected_filename = st.selectbox(
        "📄 Select Resume for Advice",
        options=list(resume_options.keys()),
        key="career_advice_resume_select"
    )
    selected_resume_id = resume_options[selected_filename]
    
    # Active Resume Card
    st.markdown(f"""
        <div class="modern-card">
            <div style="display: flex; gap: 1rem; align-items: center;">
                <div style="background: rgba(99, 102, 241, 0.1); padding: 0.8rem; border-radius: 10px; font-size: 1.5rem;">📄</div>
                <div>
                    <p style="margin: 0; color: var(--text-muted); font-size: 0.9rem;">Selected Resume</p>
                    <p style="margin: 0; color: var(--text-primary); font-weight: 600;">{selected_filename}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Ask Question Section
    st.markdown("### 🤖 Ask AI Anything")
    st.markdown("<p style='color: var(--text-muted); margin-bottom: 1rem;'>Get personalized career advice based on your resume</p>", unsafe_allow_html=True)
    
    query = st.text_area(
        "Your Question",
        height=120,
        placeholder="Examples:\n• How can I improve my resume?\n• What jobs suit my skills?\n• Should I add certifications?\n• Career growth tips for my profile?",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        ask_button = st.button("🚀 Get Advice", use_container_width=True, type="primary")
    
    # ✅ Show response immediately after asking
    if ask_button:
        if not query or len(query.strip()) < 10:
            st.error("❌ Please ask a detailed question (at least 10 characters)")
        else:
            with st.spinner("🤔 AI is analyzing your profile..."):
                payload = {
                    "resume_id": selected_resume_id,  # ✅ Use selected resume
                    "query": query.strip()
                }
                response = api_call("POST", "/career-advice", json=payload)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    # ✅ Display response immediately
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.success("✅ Got your answer!")
                    
                    st.markdown(f"""
                        <div style="background: rgba(16, 185, 129, 0.08); padding: 1.5rem; border-radius: 12px; border-left: 4px solid var(--success); margin-top: 1rem;">
                            <p style="margin: 0 0 0.5rem 0; color: var(--success); font-weight: 600; font-size: 0.9rem;">💡 AI RESPONSE</p>
                            <p style="margin: 0; line-height: 1.8; color: var(--text-primary); font-size: 1rem;">{result.get('answer', 'No response available.')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Optional: Show button to view in history
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📜 View All Conversations", use_container_width=False):
                        st.rerun()
                    
                else:
                    st.error("❌ Failed to get advice. Please try again.")
    
    # Divider
    st.markdown("<br><hr style='border: none; border-top: 1px solid rgba(128, 128, 128, 0.2);'><br>", unsafe_allow_html=True)
    
    # Chat History Section
    st.markdown("### 📜 Previous Conversations")
    st.markdown("<p style='color: var(--text-muted); margin-bottom: 1.5rem;'>Click on any conversation to view details</p>", unsafe_allow_html=True)
    
    # Fetch chat history
    response = api_call("GET", "/chat-history")
    
    if response and response.status_code == 200:
        data = response.json()
        chats = data.get('chats', [])
        
        if not chats:
            st.info("📭 No conversations yet. Ask your first question above!")
        else:
            # Show total count
            st.markdown(f"<p style='color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;'>Total: {len(chats)} conversations</p>", unsafe_allow_html=True)
            
            # Show each chat in expander (collapsed by default)
            for chat in chats:
                from datetime import datetime
                created_date = datetime.fromisoformat(chat['created_at'].replace('Z', '+00:00'))
                date_str = created_date.strftime("%b %d, %Y • %I:%M %p")
                
                # Truncate question for preview (first 80 chars)
                question_preview = chat['user_query'][:80] + "..." if len(chat['user_query']) > 80 else chat['user_query']
                
                # ✅ Use expander - shows only question by default
                with st.expander(f"💬 {question_preview}", expanded=False):
                    st.markdown(f"<p style='color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1rem;'>{date_str}</p>", unsafe_allow_html=True)
                    
                    # Full Question
                    st.markdown(f"""
                        <div style="background: rgba(99, 102, 241, 0.08); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                            <p style="margin: 0 0 0.5rem 0; color: var(--primary); font-weight: 600; font-size: 0.85rem;">YOUR QUESTION</p>
                            <p style="margin: 0; line-height: 1.7; color: var(--text-primary);">{chat['user_query']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Full Answer
                    st.markdown(f"""
                        <div style="background: rgba(16, 185, 129, 0.08); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                            <p style="margin: 0 0 0.5rem 0; color: var(--success); font-weight: 600; font-size: 0.85rem;">AI RESPONSE</p>
                            <p style="margin: 0; line-height: 1.8; color: var(--text-primary);">{chat['ai_response']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Delete button inside expander
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col2:
                        if st.button(f"🗑️ Delete", key=f"del_chat_{chat['id']}", use_container_width=True):
                            del_response = api_call("DELETE", f"/chat-history/{chat['id']}")
                            if del_response and del_response.status_code == 200:
                                st.success("✅ Deleted!")
                                st.rerun()
    else:
        st.error("❌ Failed to load chat history")

# ==================== MY RESUMES PAGE ====================
def show_resumes_page():
    """Resume history page"""
    
    st.markdown("<h1 style='margin-bottom: 1rem;'>📁 My Resumes</h1>", unsafe_allow_html=True)
    
    if not st.session_state.access_token:
        st.warning("🔒 Please login to view your resumes")
        if st.button("🔑 Go to Login", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        return
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    response = api_call("GET", "/my-resumes")
    
    if response and response.status_code == 200:
        resumes = response.json().get('resumes', [])
        
        st.metric("📊 Total Resumes", len(resumes))
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not resumes:
            st.info("📭 No resumes uploaded yet. Start by uploading your first resume!")
            if st.button("📄 Upload Resume", use_container_width=True):
                smooth_transition("📄 Upload Resume")
        else:
            for resume in resumes:
                st.markdown(f"""
                    <div class="modern-card">
                        <div style="display: flex; gap: 1.5rem; align-items: center;">
                            <div style="background: rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 12px; font-size: 1.5rem;">📄</div>
                            <div style="flex: 1;">
                                <h4 style="margin: 0 0 0.3rem 0;">{resume.get('filename', 'Resume')}</h4>
                                <p style="margin: 0; font-size: 0.85rem; color: var(--text-muted);">
                                    Uploaded: {resume.get('uploaded_at', 'N/A').split('T')[0]} • 
                                    {resume.get('skills_count', 0)} skills
                                </p>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                
                with col1:
                    view_url = f"{API_URL}/resume/{resume.get('resume_id')}/view?token={st.session_state.access_token}"
                    st.markdown(f"""
                        <a href="{view_url}" target="_blank" style="
                            display: block;
                            padding: 0.5rem 1rem;
                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                            color: white;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: 600;
                            text-align: center;
                            transition: transform 0.2s, box-shadow 0.2s;
                            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(16, 185, 129, 0.4)'" 
                           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(16, 185, 129, 0.3)'">
                            👁️ View
                        </a>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🎯 Use", key=f"use_{resume.get('resume_id')}", use_container_width=True):
                        st.session_state.resume_id = resume.get('resume_id')
                        st.session_state.resume_data = resume
                        st.success("✅ Resume selected!")
                        smooth_transition("🎯 Job Match")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{resume.get('resume_id')}", use_container_width=True, type="secondary"):
                        del_response = api_call("DELETE", f"/resume/{resume.get('resume_id')}")
                        if del_response and del_response.status_code == 200:
                            st.success("✅ Deleted!")
                            st.rerun()
                
                with col4:
                    st.write("")
                
                st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
    
    elif response and response.status_code == 401:
        st.error("🔒 Session expired. Please login again.")
        if st.button("🔑 Go to Login", use_container_width=True):
            st.session_state.authenticated = False
            for key in session_defaults.keys():
                st.session_state[key] = session_defaults[key]
            st.rerun()
    else:
        st.error("❌ Failed to load resumes.")

# ==================== MATCH HISTORY PAGE ====================
def show_match_history_page():
    """Display job match history"""
    
    st.markdown("<h1 style='margin-bottom: 1rem;'>📊 Match History</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted); margin-bottom: 2rem;'>View your previous job match analyses.</p>", unsafe_allow_html=True)
    
    response = api_call("GET", "/match-history")
    
    if response and response.status_code == 200:
        data = response.json()
        matches = data.get('matches', [])
        
        if not matches:
            st.info("📭 No match history yet. Start by matching your resume with a job!")
            if st.button("🎯 Match with Jobs", use_container_width=True):
                smooth_transition("🎯 Job Match")
            return
        
        st.metric("📊 Total Matches", len(matches))
        st.markdown("<br>", unsafe_allow_html=True)
        
        for match in matches:
            match_score = match['match_score']
            
            # Score color
            if match_score >= 80:
                score_color = "var(--success)"
                score_emoji = "🎉"
            elif match_score >= 60:
                score_color = "#06b6d4"
                score_emoji = "👍"
            else:
                score_color = "var(--warning)"
                score_emoji = "📝"
            
            # Format date
            from datetime import datetime
            created_date = datetime.fromisoformat(match['created_at'].replace('Z', '+00:00'))
            date_str = created_date.strftime("%b %d, %Y at %I:%M %p")
            
            st.markdown(f"""
                <div class="modern-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <div>
                            <h3 style="margin: 0 0 0.3rem 0;">{score_emoji} {match['job_title']}</h3>
                            <p style="margin: 0; color: var(--text-muted); font-size: 0.85rem;">{date_str}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 2rem; color: {score_color}; font-weight: 800;">{match_score}%</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"📋 View Details", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ✅ Matched Skills")
                    if match['matched_skills']:
                        for skill in match['matched_skills'][:10]:
                            st.markdown(f"""
                                <div style='background: rgba(16, 185, 129, 0.1); padding: 0.3rem 0.8rem; border-radius: 8px; margin: 0.3rem 0; border-left: 3px solid var(--success);'>
                                    ✓ {skill}
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No matched skills")
                
                with col2:
                    st.markdown("### 📚 Missing Skills")
                    if match['missing_skills']:
                        for skill in match['missing_skills'][:10]:
                            st.markdown(f"""
                                <div style='background: rgba(245, 158, 11, 0.1); padding: 0.3rem 0.8rem; border-radius: 8px; margin: 0.3rem 0; border-left: 3px solid var(--warning);'>
                                    ○ {skill}
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("🎉 All skills matched!")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 💡 Recommendations")
                st.markdown(f"""
                    <div style='background: rgba(99, 102, 241, 0.05); padding: 1rem; border-radius: 12px; border-left: 4px solid var(--primary);'>
                        <p style='margin: 0; line-height: 1.8;'>{match['recommendations']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📄 Job Description")
                st.text_area("", match['job_description'], height=150, key=f"jd_{match['id']}", disabled=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([2, 1, 1])
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_match_{match['id']}", use_container_width=True):
                        del_response = api_call("DELETE", f"/match-history/{match['id']}")
                        if del_response and del_response.status_code == 200:
                            st.success("✅ Deleted!")
                            st.rerun()
            
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
    
    else:
        st.error("❌ Failed to load match history")


# ==================== DELETE ACCOUNT PAGE ====================
def show_delete_account_modal():
    """Show delete account confirmation modal"""
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="modern-card" style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05)); border-color: rgba(239, 68, 68, 0.3);">
            <h2 style="color: var(--danger); margin: 0 0 1rem 0;">⚠️ Delete Account</h2>
            <p style="margin: 0 0 1rem 0;">This action is <strong>permanent</strong> and cannot be undone!</p>
            <p style="margin: 0; color: var(--text-muted); font-size: 0.9rem;">
                All your data will be permanently deleted:
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="modern-card">
                <h4 style="margin: 0 0 0.5rem 0;">❌ What will be deleted:</h4>
                <ul style="margin: 0; padding-left: 1.5rem; color: var(--text-muted);">
                    <li>All uploaded resumes</li>
                    <li>Job match history</li>
                    <li>Career advice conversations</li>
                    <li>Your account credentials</li>
                    <li>All personal data</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="modern-card">
                <h4 style="margin: 0 0 0.5rem 0;">💡 Before you go:</h4>
                <ul style="margin: 0; padding-left: 1.5rem; color: var(--text-muted);">
                    <li>Download any resumes you need</li>
                    <li>Save important career advice</li>
                    <li>Consider logging out instead</li>
                    <li>You can create a new account anytime</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Confirmation checkbox
    confirm = st.checkbox(
        f"I understand that deleting my account '{st.session_state.user_data['username']}' is permanent and cannot be undone",
        key="delete_confirm"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Go Back", use_container_width=True):
            smooth_transition("🏠 Home")
    
    with col3:
        if st.button("🗑️ Delete My Account", use_container_width=True, type="primary", disabled=not confirm):
            if confirm:
                with st.spinner("Deleting your account..."):
                    response = api_call("DELETE", "/delete-account")
                    
                    if response and response.status_code == 200:
                        st.success("✅ Account deleted successfully")
                        st.balloons()
                        
                        # Clear session and logout
                        for key in session_defaults.keys():
                            st.session_state[key] = session_defaults[key]
                        
                        st.info("Redirecting to login page...")
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete account. Please try again or contact support.")




# ==================== MAIN APP ====================
if not st.session_state.authenticated:
    show_landing_page()
else:
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; padding: 1.5rem 0; border-bottom: 1px solid var(--border-color);">
                <div style="background: linear-gradient(135deg, var(--primary), var(--primary-dark)); width: 50px; height: 50px; border-radius: 12px; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5rem;">
                    {st.session_state.user_data['username'][0].upper()}
                </div>
                <h4 style="margin: 0 0 0.3rem 0;">{st.session_state.user_data['username']}</h4>
                <p style="margin: 0; color: var(--text-muted); font-size: 0.85rem;">{st.session_state.user_data['email']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        menu_items = [
            ("🏠 Home", "🏠 Home"),
            ("📄 Upload Resume", "📄 Upload Resume"),
            ("🎯 Job Match", "🎯 Job Match"),
            ("💬 Career Advice", "💬 Career Advice"),
            ("📁 My Resumes", "📁 My Resumes"),
            ("📊 Match History", "📊 Match History"),
        ]
        
        for label, page in menu_items:
            is_active = st.session_state.current_page == page
            button_style = """
                background: linear-gradient(135deg, var(--primary), var(--primary-dark));
                color: white;
                border-left: 4px solid rgba(99, 102, 241, 0.8);
            """ if is_active else """
                background: transparent;
                color: var(--text-secondary);
            """
            
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                smooth_transition(page)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            for key in session_defaults.keys():
                st.session_state[key] = session_defaults[key]
            st.rerun()

        # ✅ DELETE ACCOUNT BUTTON - KEEP THIS
        if st.button("🗑️ Delete Account", use_container_width=True, key="delete_account_btn"):
            smooth_transition("⚙️ Delete Account")

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);'>
            <p style='color: var(--text-muted); font-size: 0.75rem; margin: 0;'>
                Built by Pavithra R S
            </p>
            
        </div>
    """, unsafe_allow_html=True)
    
        st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.current_page == "🏠 Home":
        show_home_page()
    elif st.session_state.current_page == "📄 Upload Resume":
        show_upload_page()
    elif st.session_state.current_page == "🎯 Job Match":
        show_job_match_page()
    elif st.session_state.current_page == "💬 Career Advice":
        show_career_advice_page()
    elif st.session_state.current_page == "📁 My Resumes":
        show_resumes_page()
    elif st.session_state.current_page == "📊 Match History": 
        show_match_history_page()
    elif st.session_state.current_page == "⚙️ Delete Account":  
        show_delete_account_modal()
    
