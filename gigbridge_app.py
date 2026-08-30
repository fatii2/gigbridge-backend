"""
GigBridge — Streamlit Edition
Innovative UI · AI Gig Recommendations · Student Free + Premium · Business Pro
Run: streamlit run gigbridge_app.py
"""

import streamlit as st
import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

st.set_page_config(
    page_title="GigBridge",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DB = "gigbridge.db"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;}
:root{
  --void:#060C1A;--ink:#0A1628;--smoke:#0F1F38;--steel:#162844;--mist:#1E3554;
  --fog:#2D4A6E;--ash:#6B89A8;--silver:#A8BDD0;--snow:#E0EAF4;--pure:#FFFFFF;
  --spark:#E8700A;--spark-dim:rgba(232,112,10,0.15);--spark-glow:rgba(232,112,10,0.35);
  --lime:#00D4AA;--lime-dim:rgba(0,212,170,0.12);
  --cyan:#3B9EE8;--cyan-dim:rgba(59,158,232,0.15);
  --violet:#5B7FE8;--violet-dim:rgba(91,127,232,0.15);
  --gold:#E8A010;--gold-dim:rgba(232,160,16,0.15);
  --red:#E84040;--red-dim:rgba(232,64,64,0.12);
  --green:#00C878;--green-dim:rgba(0,200,120,0.12);
  --r:12px;--r2:18px;--r3:24px;
}
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
section[data-testid="stSidebar"]{display:none !important;}
.main .block-container{max-width:480px !important;padding:0 !important;margin:0 auto !important;background:#0A1628;min-height:100vh;}
body,.stApp{background:#060C1A !important;font-family:'DM Sans',sans-serif;color:var(--snow);}
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:var(--smoke);}
::-webkit-scrollbar-thumb{background:var(--mist);border-radius:4px;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{
  background:var(--smoke) !important;border:1.5px solid var(--steel) !important;
  border-radius:var(--r) !important;color:var(--snow) !important;
  font-family:'DM Sans',sans-serif !important;font-size:0.9rem !important;
  padding:0.6rem 0.9rem !important;transition:border-color 0.2s !important;
}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{
  border-color:var(--spark) !important;box-shadow:0 0 0 3px var(--spark-dim) !important;outline:none !important;
}
.stSelectbox>div>div>div{background:var(--smoke) !important;border:1.5px solid var(--steel) !important;border-radius:var(--r) !important;color:var(--snow) !important;}
[data-baseweb="select"]>div{background:var(--smoke) !important;border-color:var(--steel) !important;color:var(--snow) !important;}
[data-baseweb="popover"],[data-baseweb="menu"]{background:var(--smoke) !important;}
[data-baseweb="option"]{background:var(--smoke) !important;color:var(--snow) !important;}
[data-baseweb="option"]:hover{background:var(--steel) !important;}
.stTextInput label,.stSelectbox label,.stTextArea label,.stNumberInput label,.stCheckbox label,.stRadio label{
  color:var(--ash) !important;font-size:0.78rem !important;font-weight:600 !important;
  letter-spacing:0.05em !important;text-transform:uppercase !important;font-family:'DM Sans',sans-serif !important;
}
.stButton>button{
  background:#1A3A6E !important;color:#fff !important;border:1px solid #2A5298 !important;
  border-radius:var(--r) !important;font-family:'DM Sans',sans-serif !important;font-weight:700 !important;
  font-size:0.9rem !important;padding:0.65rem 1.4rem !important;width:100% !important;
  cursor:pointer !important;transition:all 0.2s !important;
}
.stButton>button:hover{background:#E8700A !important;border-color:#E8700A !important;transform:translateY(-1px) !important;box-shadow:0 8px 24px rgba(232,112,10,0.3) !important;}
.stTabs [data-baseweb="tab-list"]{background:var(--smoke) !important;border-radius:var(--r) !important;padding:4px !important;gap:4px !important;border:none !important;}
.stTabs [data-baseweb="tab"]{background:transparent !important;border-radius:8px !important;color:var(--ash) !important;font-family:'DM Sans',sans-serif !important;font-weight:600 !important;font-size:0.82rem !important;border:none !important;padding:0.45rem 1rem !important;transition:all 0.2s !important;}
.stTabs [aria-selected="true"]{background:var(--spark) !important;color:var(--pure) !important;}
.stTabs [data-baseweb="tab-border"]{display:none !important;}
.stTabs [data-baseweb="tab-panel"]{padding:0 !important;background:transparent !important;}
hr{border:none;border-top:1px solid var(--steel);margin:1.2rem 0;}
.stProgress>div>div>div>div{background:linear-gradient(90deg,var(--spark),var(--gold)) !important;border-radius:4px !important;}
.stProgress>div>div{background:var(--steel) !important;border-radius:4px !important;}
[data-testid="stFileUploader"]{background:var(--smoke) !important;border:2px dashed var(--steel) !important;border-radius:var(--r2) !important;}
div[data-testid="stVerticalBlock"]{gap:0 !important;}
.stMarkdown p{margin:0;}
.element-container{margin-bottom:0 !important;}
div[data-testid="stVerticalBlock"]{gap:0 !important;}
.stMarkdown p{margin:0;}
.element-container{margin-bottom:0 !important;}
.stButton>button{width:100% !important;}

</style>
""", unsafe_allow_html=True)

# ─── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        plan TEXT DEFAULT 'free',
        plan_expires TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL,
        university TEXT NOT NULL,
        cnic TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        skills TEXT DEFAULT '',
        interests TEXT DEFAULT '',
        wallet_method TEXT DEFAULT '',
        wallet_number TEXT DEFAULT '',
        bank_name TEXT DEFAULT '',
        bank_account TEXT DEFAULT '',
        bank_title TEXT DEFAULT '',
        total_gigs INTEGER DEFAULT 0,
        total_earned REAL DEFAULT 0,
        avg_rating REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        business_name TEXT NOT NULL,
        industry TEXT DEFAULT '',
        city TEXT DEFAULT '',
        ntn TEXT DEFAULT '',
        description TEXT DEFAULT '',
        website TEXT DEFAULT '',
        total_posted INTEGER DEFAULT 0,
        total_hired INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        job_type TEXT NOT NULL,
        location TEXT DEFAULT '',
        is_remote INTEGER DEFAULT 0,
        hours_per_day TEXT DEFAULT '',
        salary REAL NOT NULL,
        salary_period TEXT DEFAULT 'monthly',
        skills_required TEXT DEFAULT '',
        category TEXT DEFAULT '',
        is_urgent INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open',
        payment_method TEXT DEFAULT 'easypaisa',
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
        student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
        cover_note TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        applied_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        job_id INTEGER REFERENCES jobs(id),
        amount REAL NOT NULL,
        plan TEXT NOT NULL,
        method TEXT DEFAULT '',
        status TEXT DEFAULT 'completed',
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    db.commit()
    if not db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        _seed(db)
    db.close()

def _seed(db):
    db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
               ("admin@gigbridge.pk", generate_password_hash("admin123"), "admin", "admin"))
    for email, name, uni, skills, interests, bio in [
        ("sara@iba.edu.pk","Sara Ahmed","IBA Karachi","Social Media,Content Writing,Canva","Marketing,Content Creation,Design","Final year BBA student passionate about marketing."),
        ("hassan@fast.edu.pk","Hassan Raza","FAST NUCES","Python,Data Entry,Excel,SQL","Technology,Data,Programming","CS student interested in data and automation."),
        ("aimen@ned.edu.pk","Aimen Siddiqui","NED University","Communication,Customer Service","Customer Service,Communication,Admin","Engineering student with strong communication skills."),
    ]:
        db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
                   (email, generate_password_hash("password123"), "student", "free"))
        uid = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
        db.execute("INSERT INTO students (user_id,full_name,university,skills,interests,bio,wallet_method,wallet_number) VALUES (?,?,?,?,?,?,?,?)",
                   (uid, name, uni, skills, interests, bio, "easypaisa", "03001234567"))
    for email, bname, industry, city in [
        ("hr@brewbox.pk","BrewBox Café","Food & Beverage","Karachi"),
        ("jobs@techhive.pk","TechHive Solutions","Technology","Karachi"),
        ("careers@mediapulse.pk","MediaPulse PK","Media","Lahore"),
    ]:
        db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
                   (email, generate_password_hash("password123"), "business", "pro"))
        uid = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
        db.execute("INSERT INTO businesses (user_id,business_name,industry,city) VALUES (?,?,?,?)",
                   (uid, bname, industry, city))
    jobs_data = [
        (1,"Social Media Manager","Manage Instagram, TikTok and Facebook. Create engaging content and grow following.","Part-time","Clifton",0,"4 hrs/day",18000,"Social Media,Canva,Content Writing","Marketing,Content Creation",1,"easypaisa"),
        (2,"Junior Data Analyst","Analyze customer data, build Excel dashboards and present weekly reports.","Part-time","DHA",1,"5 hrs/day",25000,"Excel,SQL,Python","Technology,Data",0,"jazzcash"),
        (2,"Customer Support Rep","Handle inbound queries via chat and phone. CRM training provided.","Part-time","DHA",0,"5 hrs/day",22000,"Communication,CRM","Customer Service",1,"easypaisa"),
        (3,"Content Writer","Write SEO blog articles in Urdu and English. Portfolio required.","Freelance","Remote",1,"Project-based",3000,"Writing,SEO","Content Creation,Writing",0,"jazzcash"),
        (1,"Weekend Barista Assistant","Assist our head barista on weekends. No experience needed.","Weekend","Clifton",0,"Sat & Sun",10000,"Hospitality","Food,Hospitality",0,"easypaisa"),
        (2,"UI/UX Design Intern","Help design mobile app screens using Figma.","Internship","DHA",1,"3 hrs/day",15000,"Figma,Canva,Design","Design,Technology",1,"jazzcash"),
    ]
    for row in jobs_data:
        db.execute("INSERT INTO jobs (business_id,title,description,job_type,location,is_remote,hours_per_day,salary,skills_required,category,is_urgent,payment_method) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                   row)
        db.execute("UPDATE businesses SET total_posted=total_posted+1 WHERE id=?", (row[0],))
    db.commit()

# ─── Helpers ───────────────────────────────────────────────────────────────────

def ini(name):
    return "".join(p[0] for p in (name or "GB").split()[:2]).upper()

def av_color(name):
    cols = ["#FF4D00","#7C3AFF","#00CC66","#00D4FF","#FFB800","#FF3B3B"]
    return cols[sum(ord(c) for c in (name or "")) % len(cols)]

def fmt_sal(amt, period="monthly"):
    s = {"monthly":"/mo","weekly":"/wk","per project":"/proj"}.get(period,"")
    return f"PKR {int(amt):,}{s}"

def time_ago(ds):
    if not ds: return ""
    try:
        d = datetime.strptime(ds[:19],"%Y-%m-%d %H:%M:%S")
        m = int((datetime.utcnow()-d).total_seconds()/60)
        if m<60: return f"{m}m ago"
        if m<1440: return f"{m//60}h ago"
        return f"{m//1440}d ago"
    except: return ""

def get_student(uid=None):
    db = get_db()
    s = db.execute("SELECT s.*,u.email,u.plan,u.plan_expires FROM students s JOIN users u ON u.id=s.user_id WHERE s.user_id=?",
                   (uid or st.session_state.user_id,)).fetchone()
    db.close(); return s

def get_business(uid=None):
    db = get_db()
    b = db.execute("SELECT b.*,u.email,u.plan,u.plan_expires FROM businesses b JOIN users u ON u.id=b.user_id WHERE b.user_id=?",
                   (uid or st.session_state.user_id,)).fetchone()
    db.close(); return b

def is_premium(uid):
    db = get_db()
    u = db.execute("SELECT plan,plan_expires FROM users WHERE id=?", (uid,)).fetchone()
    db.close()
    if not u: return False
    if u["plan"] == "premium":
        exp = u["plan_expires"]
        return datetime.utcnow() < datetime.strptime(exp[:19],"%Y-%m-%d %H:%M:%S") if exp else True
    return False

# ─── AI Recommender ────────────────────────────────────────────────────────────

INTEREST_MAP = {
    "Marketing":["Marketing","Content Creation","Social Media","Writing"],
    "Technology":["Technology","Data","Programming","Software"],
    "Design":["Design","UI/UX","Creative","Art"],
    "Content Creation":["Content Creation","Writing","Media"],
    "Customer Service":["Customer Service","Communication","Admin","Support"],
    "Finance":["Finance","Accounting","Banking"],
    "Food":["Food","Hospitality","Events","Catering"],
    "Data":["Data","Analytics","Research","Statistics"],
    "Education":["Education","Teaching","Tutoring"],
}

def ai_rank(interests, skills, jobs):
    tags = []
    for interest in (interests or "").split(","):
        i = interest.strip()
        for cat, lst in INTEREST_MAP.items():
            if any(i.lower() in t.lower() or t.lower() in i.lower() for t in lst):
                tags.extend(lst)
    skill_words = [s.strip().lower() for s in (skills or "").split(",") if s.strip()]
    scored = []
    for job in jobs:
        score = 0
        jcat = (job["category"] or "").lower()
        jsk = (job["skills_required"] or "").lower()
        jtitle = (job["title"] or "").lower()
        for tag in tags:
            if tag.lower() in jcat or tag.lower() in jtitle: score += 3
        for sk in skill_words:
            if sk in jsk or sk in jtitle: score += 2
        if job["is_urgent"]: score += 1
        scored.append((score, job))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [j for _, j in scored]

# ─── UI Helpers ────────────────────────────────────────────────────────────────

def nb(subtitle=None):
    sub = f'<div style="font-size:0.66rem;color:#6B89A8;letter-spacing:0.08em;text-transform:uppercase;margin-top:1px">{subtitle}</div>' if subtitle else ''
    logo_html = '<img src="data:image/png;base64,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" style="height:36px;width:auto;object-fit:contain;margin-right:8px;vertical-align:middle">'
    st.markdown(f"""
    <div style="background:#0A1628;border-bottom:1px solid #162844;padding:0.7rem 1.2rem;
      display:flex;align-items:center;justify-content:center;flex-direction:column;
      position:sticky;top:0;z-index:100;backdrop-filter:blur(12px);text-align:center">
      <div style="display:flex;align-items:center;justify-content:center;gap:4px">
        {logo_html}
        <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;letter-spacing:-0.04em;color:#fff">
          Gig<span style="color:#E8700A">Bridge</span></div>
      </div>
      {sub}
    </div>""", unsafe_allow_html=True)

def badge(text, color="#8B8F9A", bg="#252831"):
    return f'<span style="display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;font-size:0.67rem;font-weight:700;background:{bg};color:{color};margin:2px 2px 0 0">{text}</span>'

def av_html(name, size=42, fsize="0.88rem"):
    c = av_color(name)
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{c};display:inline-flex;align-items:center;justify-content:center;font-family:\'Syne\',sans-serif;font-size:{fsize};font-weight:800;color:white;flex-shrink:0">{ini(name)}</div>'

def metric_card(val, lbl, color="#FF4D00"):
    return f"""<div style="background:#1A1D24;border:1px solid #252831;border-radius:12px;padding:1rem 0.5rem;text-align:center">
      <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:{color}">{val}</div>
      <div style="font-size:0.67rem;color:#8B8F9A;margin-top:3px;text-transform:uppercase;letter-spacing:0.05em">{lbl}</div>
    </div>"""

def sec(title, sub=None):
    s = f'<div style="font-size:0.74rem;color:#8B8F9A;margin-top:3px">{sub}</div>' if sub else ''
    st.markdown(f'<div style="margin:1.1rem 0 0.8rem"><div style="font-family:\'Syne\',sans-serif;font-size:1.05rem;font-weight:800;color:#fff">{title}</div>{s}</div>', unsafe_allow_html=True)

def job_card(job):
    typ_c = {"Part-time":"#AAFF00","Freelance":"#00D4FF","Weekend":"#FFB800","Internship":"#7C3AFF"}.get(job["job_type"],"#8B8F9A")
    typ_bg = {"Part-time":"rgba(170,255,0,0.12)","Freelance":"rgba(0,212,255,0.12)","Weekend":"rgba(255,184,0,0.15)","Internship":"rgba(124,58,255,0.15)"}.get(job["job_type"],"#252831")
    urg = badge("⚡ URGENT","#FF4D00","rgba(255,77,0,0.15)") if job["is_urgent"] else ""
    rem = badge("🌐 Remote","#00D4FF","rgba(0,212,255,0.12)") if job["is_remote"] else ""
    tyb = badge(job["job_type"], typ_c, typ_bg)
    col = av_color(job["business_name"] or "")
    logo = ini(job["business_name"] or "")
    return f"""<div style="background:linear-gradient(135deg,#1A1D24,#252831);border:1px solid #353840;border-radius:18px;padding:1.2rem;margin-bottom:0.8rem;position:relative;overflow:hidden;">
      <div style="position:absolute;top:0;right:0;width:120px;height:120px;background:radial-gradient({col}20,transparent 70%);border-radius:50%;transform:translate(30px,-30px)"></div>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.7rem">
        <div style="display:flex;gap:0.75rem;align-items:center;flex:1;min-width:0">
          <div style="width:40px;height:40px;border-radius:10px;background:{col};display:inline-flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:0.75rem;font-weight:800;color:white;flex-shrink:0">{logo}</div>
          <div style="min-width:0">
            <div style="font-family:'Syne',sans-serif;font-size:0.93rem;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{job['title']}</div>
            <div style="color:#8B8F9A;font-size:0.75rem;margin-top:1px">{job['business_name']} · {job['location'] or 'Remote'}</div>
          </div>
        </div>
        <div style="font-family:'Syne',sans-serif;font-size:0.93rem;font-weight:800;color:#FF4D00;white-space:nowrap;margin-left:0.5rem">{fmt_sal(job['salary'],job['salary_period'])}</div>
      </div>
      <div style="margin-bottom:0.65rem">{tyb}{urg}{rem}</div>
      <div style="font-size:0.79rem;color:#8B8F9A;line-height:1.5;margin-bottom:0.7rem">{(job['description'] or '')[:100]}…</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="font-size:0.7rem;color:#545861">⏱ {job['hours_per_day'] or 'Flexible'} · {time_ago(job['created_at'])}</div>
        <div style="font-size:0.7rem;color:#8B8F9A">💳 {'EasyPaisa' if job['payment_method']=='easypaisa' else 'JazzCash'}</div>
      </div>
    </div>"""

def _render_nav(tabs, active, prefix):
    n = len(tabs)
    st.markdown('<div style="height:68px"></div>', unsafe_allow_html=True)

    # Build button labels with icon + text combined so they show in one button
    # Use a unique wrapper div ID per nav instance
    nav_id = f"nav_{prefix}"

    st.markdown(f"""
    <style>
    #{nav_id} {{
      position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
      width: 100%; max-width: 480px;
      background: #0A1628;
      border-top: 1px solid #162844;
      z-index: 9999;
      display: grid;
      grid-template-columns: repeat({n}, 1fr);
    }}
    #{nav_id} .stButton > button {{
      background: transparent !important;
      border: none !important;
      border-radius: 0 !important;
      color: #4A6A88 !important;
      font-size: 0.55rem !important;
      font-weight: 700 !important;
      padding: 10px 2px 8px !important;
      width: 100% !important;
      height: 58px !important;
      letter-spacing: 0.04em !important;
      text-transform: uppercase !important;
      box-shadow: none !important;
      line-height: 1.4 !important;
      white-space: pre-line !important;
    }}
    #{nav_id} .stButton > button:hover,
    #{nav_id} .stButton > button:focus {{
      background: rgba(232,112,10,0.07) !important;
      color: #E8700A !important;
      transform: none !important;
      box-shadow: none !important;
    }}
    #{nav_id} .element-container {{ margin: 0 !important; padding: 0 !important; }}
    #{nav_id} [data-testid="column"] {{ padding: 0 !important; }}
    </style>
    <div id="{nav_id}">
    """, unsafe_allow_html=True)

    cols = st.columns(n)
    for col, (screen, icon, label) in zip(cols, tabs):
        with col:
            is_active = screen == active
            color = "#E8700A" if is_active else "#4A6A88"
            # Show active indicator dot above icon
            dot = "·" if is_active else " "
            st.markdown(f'<div style="text-align:center;font-size:1.15rem;padding-top:8px;color:{color};line-height:1">{icon}</div>', unsafe_allow_html=True)
            if st.button(label, key=f"{prefix}_{screen}"):
                st.session_state.screen = screen
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def snav(active):
    tabs = [
        ("student_home",         "🏠", "Home"),
        ("student_ai_chat",      "🤖", "GigBot"),
        ("student_jobs",         "🔍", "Gigs"),
        ("student_applications", "📋", "Applied"),
        ("student_profile",      "👤", "Profile"),
    ]
    _render_nav(tabs, active, "snav")


def bnav(active):
    tabs = [
        ("business_home",        "🏠", "Home"),
        ("business_post",        "➕", "Post"),
        ("business_applicants",  "👥", "Applicants"),
        ("business_profile",     "👤", "Profile"),
    ]
    _render_nav(tabs, active, "bnav")

# ═══════════════════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════════════════

def show_landing():
    st.markdown("""
    <div style="min-height:calc(100vh - 60px);background:radial-gradient(ellipse at 20% 50%,rgba(255,77,0,0.08),transparent 60%),radial-gradient(ellipse at 80% 20%,rgba(124,58,255,0.06),transparent 60%),#0F1117;padding:2.5rem 1.5rem 2rem;text-align:center;">
      <div style="margin-bottom:1rem">
        <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:#FF4D00;background:rgba(255,77,0,0.15);padding:4px 12px;border-radius:20px;border:1px solid rgba(255,77,0,0.2)">Pakistan's #1 Student Job Platform</span>
      </div>
      <div style="font-family:'Syne',sans-serif;font-size:3.2rem;font-weight:800;letter-spacing:-0.05em;color:#fff;margin:0.8rem 0 0.4rem;line-height:1.05">Gig<span style="color:#FF4D00">Bridge</span></div>
      <p style="color:#8B8F9A;font-size:0.88rem;max-width:280px;margin:0 auto 2.5rem;line-height:1.6">AI-powered gig matching for students.<br>Hire verified talent for businesses.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.markdown("""<div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.4rem 1rem;text-align:center;margin-bottom:0.5rem">
          <div style="font-size:1.8rem;margin-bottom:0.5rem">🎓</div>
          <div style="font-family:'Syne',sans-serif;font-size:0.93rem;font-weight:800;color:#fff">Student</div>
          <div style="color:#8B8F9A;font-size:0.7rem;margin-top:4px">Find gigs · AI match</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Student Portal", key="l_s"):
            st.session_state.screen = "auth"; st.session_state.auth_role = "student"; st.rerun()
    with c2:
        st.markdown("""<div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.4rem 1rem;text-align:center;margin-bottom:0.5rem">
          <div style="font-size:1.8rem;margin-bottom:0.5rem">🏢</div>
          <div style="font-family:'Syne',sans-serif;font-size:0.93rem;font-weight:800;color:#fff">Business</div>
          <div style="color:#8B8F9A;font-size:0.7rem;margin-top:4px">Post gigs · Hire</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Business Portal", key="l_b"):
            st.session_state.screen = "auth"; st.session_state.auth_role = "business"; st.rerun()

    st.markdown('<div style="text-align:center;margin-top:1.5rem;padding-bottom:2rem"><span style="font-size:0.7rem;color:#545861">⚡ Free for students &nbsp;·&nbsp; 💳 EasyPaisa & JazzCash &nbsp;·&nbsp; 🔒 Verified</span></div>', unsafe_allow_html=True)


def show_auth():
    role = st.session_state.get("auth_role","student")
    is_s = role == "student"
    nb(subtitle=("Student Portal" if is_s else "Business Portal"))
    st.markdown('<div style="padding:1.3rem 1.2rem 0">', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;margin-bottom:1.2rem"><div style="font-size:1.8rem">{("🎓" if is_s else "🏢")}</div><div style="font-family:\'Syne\',sans-serif;font-size:1.3rem;font-weight:800;color:#fff;margin-top:0.3rem">{"Student Portal" if is_s else "Business Portal"}</div></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    with tab1:
        st.markdown("<div style='padding:0.8rem 0'>", unsafe_allow_html=True)
        hint = "sara@iba.edu.pk" if is_s else "hr@brewbox.pk"
        email = st.text_input("Email", placeholder=hint, key="si_e")
        pw = st.text_input("Password", type="password", placeholder="••••••••", key="si_p")
        st.markdown(f'<div style="font-size:0.73rem;color:#8B8F9A;margin-bottom:0.8rem">Demo: <strong style="color:#FF4D00">{hint} / password123</strong></div>', unsafe_allow_html=True)
        if st.button("Sign In →", key="signin"):
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
            db.close()
            if not user: st.error("No account found.")
            elif not check_password_hash(user["password"], pw): st.error("Wrong password.")
            else:
                st.session_state.user_id = user["id"]
                st.session_state.role = user["role"]
                st.session_state.screen = {"student":"student_home","business":"business_home","admin":"admin"}.get(user["role"],"student_home")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div style='padding:0.8rem 0'>", unsafe_allow_html=True)
        if is_s:
            name = st.text_input("Full Name *", placeholder="Sara Ahmed", key="su_n")
            uni = st.selectbox("University *", ["IBA Karachi","FAST NUCES","NED University","SZABIST","Bahria University","UIT Karachi","Sir Syed University","Hamdard University","Other"], key="su_u")
            cnic = st.text_input("CNIC *", placeholder="42101-1234567-8", key="su_c")
            email2 = st.text_input("Email *", placeholder="sara@iba.edu.pk", key="su_e")
            pw2 = st.text_input("Password *", type="password", placeholder="Min 8 characters", key="su_p")
            if st.button("Create Profile →", key="s_signup"):
                if not all([name,uni,cnic,email2,pw2]): st.error("Fill all fields.")
                elif len(pw2)<8: st.error("Password min 8 chars.")
                else:
                    db = get_db()
                    if db.execute("SELECT 1 FROM users WHERE email=?", (email2.strip().lower(),)).fetchone():
                        st.error("Email already registered."); db.close()
                    else:
                        db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)", (email2.strip().lower(), generate_password_hash(pw2), "student", "free"))
                        uid = db.execute("SELECT id FROM users WHERE email=?", (email2.strip().lower(),)).fetchone()["id"]
                        db.execute("INSERT INTO students (user_id,full_name,university,cnic) VALUES (?,?,?,?)", (uid, name, uni, cnic))
                        db.commit(); db.close()
                        st.session_state.user_id = uid; st.session_state.role = "student"; st.session_state.screen = "student_onboarding"
                        st.success("Welcome! 🎉"); st.rerun()
        else:
            bname = st.text_input("Business Name *", placeholder="TechHive Solutions", key="bu_n")
            industry = st.selectbox("Industry *", ["Technology","Retail","Food & Beverage","Media","Logistics","Events","Other"], key="bu_i")
            city = st.selectbox("City *", ["Karachi","Lahore","Islamabad","Rawalpindi","Peshawar","Quetta"], key="bu_c")
            email2 = st.text_input("Email *", placeholder="hr@company.pk", key="bu_e")
            pw2 = st.text_input("Password *", type="password", placeholder="Min 8 characters", key="bu_p")
            if st.button("Register Business →", key="b_signup"):
                if not all([bname,email2,pw2]): st.error("Fill all fields.")
                elif len(pw2)<8: st.error("Password min 8 chars.")
                else:
                    db = get_db()
                    if db.execute("SELECT 1 FROM users WHERE email=?", (email2.strip().lower(),)).fetchone():
                        st.error("Email already registered."); db.close()
                    else:
                        db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)", (email2.strip().lower(), generate_password_hash(pw2), "business", "trial"))
                        uid = db.execute("SELECT id FROM users WHERE email=?", (email2.strip().lower(),)).fetchone()["id"]
                        db.execute("INSERT INTO businesses (user_id,business_name,industry,city) VALUES (?,?,?,?)", (uid, bname, industry, city))
                        db.commit(); db.close()
                        st.session_state.user_id = uid; st.session_state.role = "business"; st.session_state.screen = "business_home"
                        st.success("Registered! 🚀"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Home", key="auth_back"):
        st.session_state.screen = "landing"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── STUDENT ──────────────────────────────────────────────────────────────────

def show_student_home():
    s = get_student()
    db = get_db()
    app_count = db.execute("SELECT COUNT(*) FROM applications WHERE student_id=?", (s["id"],)).fetchone()[0]
    hired = db.execute("SELECT COUNT(*) FROM applications WHERE student_id=? AND status='hired'", (s["id"],)).fetchone()[0]
    db.close()
    prem = is_premium(st.session_state.user_id)
    comp = min(100, 20 + 15*bool(s["skills"]) + 15*bool(s["bio"]) + 20*bool(s["wallet_method"]) + 15*bool(s["interests"]) + 15)

    nb()
    st.markdown('<div style="padding:1.2rem 1.2rem 0.5rem">', unsafe_allow_html=True)

    col = av_color(s["full_name"])
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1A1D24,#1e1015);border:1px solid #353840;border-radius:24px;padding:1.4rem;margin-bottom:1rem;position:relative;overflow:hidden">
      <div style="position:absolute;top:-40px;right:-40px;width:150px;height:150px;background:radial-gradient({col}40,transparent 70%);border-radius:50%"></div>
      <div style="position:relative;z-index:1">
        <div style="font-size:0.7rem;color:#8B8F9A;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:3px">Welcome back 👋</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#fff">{s['full_name'].split()[0]}'s Dashboard</div>
        <div style="color:#8B8F9A;font-size:0.79rem;margin:3px 0 0">{s['university']} · <span style="color:#AAFF00">✓ Verified</span>{' · <span style="color:#FFB800">⭐ Premium</span>' if prem else ''}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(metric_card(app_count,"Applied","#00D4FF"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card(hired,"Hired","#AAFF00"), unsafe_allow_html=True)
    with c3: st.markdown(metric_card(f"PKR {int(s['total_earned']):,}","Earned","#FFB800"), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    sec("Profile Completion", f"{comp}% complete")
    st.progress(comp/100)

    if not prem:
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(255,184,0,0.08),rgba(124,58,255,0.08));border:1px solid rgba(255,184,0,0.3);border-radius:18px;padding:1rem 1.1rem;margin:0.8rem 0">
          <div style="font-family:'Syne',sans-serif;font-size:0.93rem;font-weight:800;color:#FFB800;margin-bottom:3px">⭐ Unlock Student Premium</div>
          <div style="font-size:0.77rem;color:#8B8F9A;line-height:1.5">AI-generated CV · Training programs · Priority profile — PKR 500/month</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Upgrade to Premium ⭐", key="home_upg"):
            st.session_state.screen = "student_premium"; st.rerun()

    sec("Quick Actions")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍 Browse All Gigs", key="h_browse"):
            st.session_state.screen = "student_jobs"; st.session_state.jobs_view = "all"; st.rerun()
    with c2:
        if st.button("🤖 Ask GigBot", key="h_ai"):
            st.session_state.screen = "student_ai_chat"; st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    snav("student_home")


def show_student_jobs():
    s = get_student()
    db = get_db()
    all_jobs = db.execute("SELECT j.*,b.business_name FROM jobs j JOIN businesses b ON b.id=j.business_id WHERE j.status='open' ORDER BY j.is_urgent DESC,j.created_at DESC").fetchall()
    db.close()

    # active filter from session
    active_filter = st.session_state.get("job_filter", "All")

    nb(subtitle="Find Your Next Gig")
    st.markdown('<div style="padding:0.9rem 1.2rem 0">', unsafe_allow_html=True)

    # Search bar
    search = st.text_input("", placeholder="🔍  Search gigs, companies, skills…", key="jsearch", label_visibility="collapsed")

    # ── Filter chip row ────────────────────────────────────────────────────
    FILTERS = [
        ("All",        "🌐"),
        ("Part-time",  "⏰"),
        ("🤖 For You", "🤖"),
    ]
    CHIP_COLORS = {
        "All":"#FF4D00",
        "Part-time":"#00D4FF",
        "🤖 For You":"#7C3AFF",
    }

    # CSS to style these specific buttons as chips (override orange default)
    chip_css = ""
    for label, _ in FILTERS:
        color = CHIP_COLORS[label]
        is_active = active_filter == label
        bg = color if is_active else "transparent"
        border = color
        text = "#fff" if is_active else "#8B8F9A"
        safe = label.replace(" ","_").replace("🤖","bot").replace("🌐","globe")
        chip_css += f"""
        div[data-testid="column"]:has(button[kind="secondary"][data-testid*="chip_{safe}"]) button,
        .chip-{safe} button {{
          background:{bg} !important;
          border:1.5px solid {border} !important;
          color:{text} !important;
          border-radius:30px !important;
          padding:6px 10px !important;
          font-size:0.72rem !important;
          font-weight:700 !important;
          width:100% !important;
        }}"""

    st.markdown(f"<style>{chip_css}</style>", unsafe_allow_html=True)

    # Render chips as actual Streamlit buttons in a row
    chip_cols = st.columns(len(FILTERS))
    for col, (label, icon) in zip(chip_cols, FILTERS):
        with col:
            safe = label.replace(" ","_").replace("🤖","bot").replace("🌐","globe")
            st.markdown(f'<div class="chip-{safe}">', unsafe_allow_html=True)
            if st.button(f"{icon}", key=f"chip_{safe}", help=label):
                st.session_state.job_filter = label
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Labels row under chips
    label_cols = st.columns(len(FILTERS))
    for col, (label, icon) in zip(label_cols, FILTERS):
        with col:
            color = CHIP_COLORS[label] if active_filter == label else "#545861"
            short = label.replace("🤖 ","").replace("Part-","Part-\n")
            st.markdown(f'<div style="text-align:center;font-size:0.58rem;font-weight:700;color:{color};margin-top:2px;line-height:1.2">{label.replace("🤖 For You","For You")}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # ── Filter logic ───────────────────────────────────────────────────────
    filtered = list(all_jobs)
    if search:
        q = search.lower()
        filtered = [j for j in filtered if q in j["title"].lower() or q in (j["business_name"] or "").lower() or q in (j["skills_required"] or "").lower() or q in j["description"].lower()]

    if active_filter == "🤖 For You":
        # Pure keyword match against live posted jobs — NO API
        filtered = ai_rank(s["interests"], s["skills"], filtered)
        interests_label = s["interests"] or s["skills"] or ""
        if interests_label:
            st.markdown(f'<div style="background:rgba(124,58,255,0.12);border:1px solid rgba(124,58,255,0.25);border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.7rem;font-size:0.79rem;color:#C4C7D0">🤖 Matched to your interests: <strong style="color:#7C3AFF">{interests_label}</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:rgba(124,58,255,0.12);border:1px solid rgba(124,58,255,0.25);border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.7rem;font-size:0.79rem;color:#C4C7D0">🤖 Set your interests in <strong style="color:#fff">Profile</strong> for better matches!</div>', unsafe_allow_html=True)
    elif active_filter != "All":
        filtered = [j for j in filtered if j["job_type"] == active_filter]

    st.markdown(f'<div style="font-size:0.72rem;color:#8B8F9A;margin-bottom:0.6rem">{len(filtered)} gig{"s" if len(filtered)!=1 else ""} found</div>', unsafe_allow_html=True)

    if not filtered:
        st.markdown('<div style="text-align:center;padding:2.5rem 1rem;color:#545861"><div style="font-size:2.2rem;margin-bottom:0.6rem">🔭</div><div style="font-family:\'Syne\',sans-serif;font-size:0.95rem;color:#fff">No gigs found</div><div style="font-size:0.78rem;margin-top:4px">Try a different filter or check back later</div></div>', unsafe_allow_html=True)
    else:
        for job in filtered:
            st.markdown(job_card(job), unsafe_allow_html=True)
            if st.button(f"View & Apply →", key=f"vjob_{job['id']}"):
                st.session_state.selected_job = job["id"]; st.session_state.screen = "job_detail"; st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    snav("student_jobs")


def show_job_detail():
    jid = st.session_state.get("selected_job")
    if not jid: st.session_state.screen = "student_jobs"; st.rerun()
    db = get_db()
    job = db.execute("SELECT j.*,b.business_name FROM jobs j JOIN businesses b ON b.id=j.business_id WHERE j.id=?", (jid,)).fetchone()
    s = db.execute("SELECT id FROM students WHERE user_id=?", (st.session_state.user_id,)).fetchone()
    already = bool(db.execute("SELECT 1 FROM applications WHERE job_id=? AND student_id=?", (jid, s["id"])).fetchone()) if s else False
    db.close()
    if not job: st.session_state.screen = "student_jobs"; st.rerun()

    nb(subtitle=job["title"])
    col = av_color(job["business_name"] or "")
    skills = [x.strip() for x in (job["skills_required"] or "").split(",") if x.strip()]

    st.markdown(f'<div style="padding:1.2rem 1.2rem 0">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:linear-gradient(160deg,#1A1D24,#252831);border:1px solid #353840;border-radius:24px;padding:1.4rem;margin-bottom:1rem;position:relative;overflow:hidden">
      <div style="position:absolute;top:0;right:0;width:180px;height:180px;background:radial-gradient({col}25,transparent 70%);border-radius:50%;transform:translate(60px,-60px)"></div>
      <div style="position:relative;z-index:1">
        <div style="display:flex;align-items:center;gap:0.9rem;margin-bottom:0.9rem">
          <div style="width:52px;height:52px;border-radius:14px;background:{col};display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:white;flex-shrink:0">{ini(job['business_name'])}</div>
          <div>
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:#fff">{job['title']}</div>
            <div style="color:#8B8F9A;font-size:0.78rem">{job['business_name']} · {job['location'] or 'Remote'}</div>
          </div>
        </div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:#FF4D00">{fmt_sal(job['salary'],job['salary_period'])}</div>
      </div>
    </div>
    <div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.2rem;margin-bottom:0.8rem">
      <div style="font-size:0.7rem;font-weight:700;color:#8B8F9A;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.6rem">About This Gig</div>
      <p style="font-size:0.84rem;color:#C4C7D0;line-height:1.7">{job['description']}</p>
    </div>
    <div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.2rem;margin-bottom:0.8rem">
      <div style="font-size:0.7rem;font-weight:700;color:#8B8F9A;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.6rem">Details</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.7rem;font-size:0.81rem">
        <div><span style="color:#8B8F9A">Type</span><br><strong style="color:#fff">{job['job_type']}</strong></div>
        <div><span style="color:#8B8F9A">Hours</span><br><strong style="color:#fff">{job['hours_per_day'] or 'Flexible'}</strong></div>
        <div><span style="color:#8B8F9A">Payment</span><br><strong style="color:#fff">{'EasyPaisa 🟢' if job['payment_method']=='easypaisa' else 'JazzCash 🔴'}</strong></div>
        <div><span style="color:#8B8F9A">Location</span><br><strong style="color:#fff">{'Remote 🌐' if job['is_remote'] else job['location']}</strong></div>
      </div>
      {"<div style='margin-top:0.8rem'><div style='font-size:0.7rem;font-weight:700;color:#8B8F9A;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.4rem'>Skills Required</div><div>" + "".join(badge(sk,"#00D4FF","rgba(0,212,255,0.12)") for sk in skills) + "</div></div>" if skills else ""}
    </div>
    <div style="background:rgba(255,184,0,0.07);border:1px solid rgba(255,184,0,0.2);border-radius:12px;padding:0.75rem 1rem;margin-bottom:1rem;font-size:0.78rem;color:#FFB800">⚡ 5% platform fee applies on salary payments</div>
    """, unsafe_allow_html=True)

    if already:
        st.markdown('<div style="background:rgba(0,204,102,0.1);border:1px solid rgba(0,204,102,0.3);border-radius:12px;padding:0.85rem;text-align:center;font-weight:700;color:#00CC66;font-size:0.88rem">✓ Already Applied</div>', unsafe_allow_html=True)
    else:
        cover = st.text_area("Cover Note (optional)", placeholder="Why are you a great fit?", key="cover")
        if st.button("Apply Now →", key="apply_btn"):
            db = get_db()
            sid = db.execute("SELECT id FROM students WHERE user_id=?", (st.session_state.user_id,)).fetchone()["id"]
            db.execute("INSERT INTO applications (job_id,student_id,cover_note) VALUES (?,?,?)", (jid, sid, cover))
            db.commit(); db.close()
            st.success("Applied! ✅")
            st.session_state.screen = "student_applications"; st.rerun()

    if st.button("← Back to Gigs", key="job_back"):
        st.session_state.screen = "student_jobs"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    snav("student_jobs")


def show_student_applications():
    s = get_student()
    db = get_db()
    apps = db.execute("""SELECT a.*,j.title as jt,j.salary,j.salary_period,j.job_type,b.business_name
        FROM applications a JOIN jobs j ON j.id=a.job_id JOIN businesses b ON b.id=j.business_id
        WHERE a.student_id=? ORDER BY a.applied_at DESC""", (s["id"],)).fetchall()
    db.close()

    nb(subtitle="My Applications")
    st.markdown('<div style="padding:1rem 1.2rem 0">', unsafe_allow_html=True)
    sec("Applications", f"{len(apps)} total")

    S = {"pending":("#8B8F9A","#252831","⏳ Pending"),"reviewed":("#00D4FF","rgba(0,212,255,0.12)","👁 Reviewed"),
         "hired":("#AAFF00","rgba(170,255,0,0.12)","✅ Hired"),"rejected":("#FF3B3B","rgba(255,59,59,0.12)","✗ Passed")}

    if not apps:
        st.markdown('<div style="text-align:center;padding:2.5rem 1rem"><div style="font-size:2.2rem;margin-bottom:0.6rem">📋</div><div style="font-family:\'Syne\',sans-serif;font-size:0.95rem;color:#fff">No applications yet</div><div style="font-size:0.78rem;color:#8B8F9A;margin-top:4px">Browse gigs and apply!</div></div>', unsafe_allow_html=True)
        if st.button("Find Gigs →", key="apps_find"):
            st.session_state.screen = "student_jobs"; st.rerun()
    else:
        for a in apps:
            sc,sbg,sl = S.get(a["status"],("#8B8F9A","#252831","●"))
            st.markdown(f"""
            <div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.1rem 1.2rem;margin-bottom:0.8rem">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.3rem">
                <div style="font-family:'Syne',sans-serif;font-size:0.88rem;font-weight:700;color:#fff;flex:1;margin-right:0.5rem">{a['jt']}</div>
                <span style="background:{sbg};color:{sc};font-size:0.63rem;font-weight:700;padding:3px 8px;border-radius:20px;white-space:nowrap">{sl}</span>
              </div>
              <div style="color:#8B8F9A;font-size:0.77rem">{a['business_name']} · {fmt_sal(a['salary'],a['salary_period'])}</div>
              <div style="color:#545861;font-size:0.71rem;margin-top:2px">{a['job_type']} · Applied {time_ago(a['applied_at'])}</div>
              {f'<div style="color:#8B8F9A;font-size:0.76rem;margin-top:0.5rem;font-style:italic;border-left:2px solid #252831;padding-left:0.7rem">{a["cover_note"]}</div>' if a.get("cover_note") else ''}
            </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    snav("student_applications")


def show_student_profile():
    s = get_student()
    prem = is_premium(st.session_state.user_id)
    col = av_color(s["full_name"])
    comp = min(100, 20 + 15*bool(s["skills"]) + 15*bool(s["bio"]) + 20*bool(s["wallet_method"]) + 15*bool(s["interests"]) + 15)

    nb(subtitle="My Profile")
    st.markdown('<div style="padding:1rem 1.2rem 0">', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1A1D24,#252831);border:1px solid #353840;border-radius:24px;padding:1.4rem;margin-bottom:1rem;display:flex;align-items:center;gap:1rem">
      {av_html(s['full_name'],56,"1.2rem")}
      <div>
        <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#fff">{s['full_name']}</div>
        <div style="color:#8B8F9A;font-size:0.77rem;margin-top:2px">{s['university']}</div>
        <div style="margin-top:5px">
          {badge("✓ Verified","#AAFF00","rgba(170,255,0,0.12)")}
          {badge("⭐ " + str(s['avg_rating'])[:3],"#FFB800","rgba(255,184,0,0.15)")}
          {badge("⭐ PREMIUM","#FFB800","rgba(255,184,0,0.15)") if prem else badge("Free","#8B8F9A","#252831")}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(comp/100)
    st.markdown(f'<div style="font-size:0.7rem;color:#8B8F9A;text-align:right;margin-top:2px;margin-bottom:0.5rem">{comp}% profile complete</div>', unsafe_allow_html=True)

    sec("Edit Profile")
    with st.form("pf"):
        interests = st.text_input("Interests (AI matching)", value=s["interests"] or "", placeholder="Marketing, Technology, Design, Writing…")
        skills = st.text_input("Skills", value=s["skills"] or "", placeholder="Excel, Social Media, Python…")
        bio = st.text_area("Bio", value=s["bio"] or "", placeholder="Tell businesses about yourself…")
        if st.form_submit_button("Save Profile →"):
            db = get_db()
            db.execute("UPDATE students SET interests=?,skills=?,bio=? WHERE user_id=?", (interests, skills, bio, st.session_state.user_id))
            db.commit(); db.close()
            st.success("Saved! ✅"); st.rerun()

    sec("💳 Payment Methods")
    with st.form("wf"):
        st.markdown('<div style="font-size:0.7rem;color:#8B8F9A;margin-bottom:0.6rem">Your salary will be sent to your chosen method when hired</div>', unsafe_allow_html=True)
        pay_tab = st.selectbox("Payment Type", ["📱 Mobile Wallet","🏦 Bank Account"], key="pay_type_sel")
        if "Mobile" in pay_tab:
            mlist = ["","easypaisa","jazzcash"]
            mlabels = ["Select wallet","EasyPaisa 🟢","JazzCash 🔴"]
            cur = mlist.index(s["wallet_method"]) if s["wallet_method"] in mlist else 0
            method = st.selectbox("Wallet", mlabels, index=cur)
            wnum = st.text_input("Mobile Number", value=s["wallet_number"] or "", placeholder="03XX-XXXXXXX")
            if st.form_submit_button("Save →"):
                mval = mlist[mlabels.index(method)] if method in mlabels else ""
                db = get_db()
                db.execute("UPDATE students SET wallet_method=?,wallet_number=? WHERE user_id=?", (mval, wnum, st.session_state.user_id))
                db.commit(); db.close()
                st.success("Wallet saved! 💳"); st.rerun()
        else:
            banks = ["Select bank","HBL","UBL","Meezan Bank","MCB","Allied Bank","Bank Alfalah","Faysal Bank","Standard Chartered","Habib Metro","Bank of Punjab","NBP","Askari Bank","Other"]
            cur_bank_idx = banks.index(s["bank_name"]) if s.get("bank_name") and s["bank_name"] in banks else 0
            bank = st.selectbox("Bank Name", banks, index=cur_bank_idx)
            acc_title = st.text_input("Account Title", value=s.get("bank_title") or "", placeholder="Your full name as on account")
            acc_num = st.text_input("Account / IBAN Number", value=s.get("bank_account") or "", placeholder="PK36XXXX000000000000000")
            if st.form_submit_button("Save →"):
                db = get_db()
                db.execute("UPDATE students SET bank_name=?,bank_account=?,bank_title=?,wallet_method=? WHERE user_id=?",
                           (bank, acc_num, acc_title, "bank", st.session_state.user_id))
                db.commit(); db.close()
                st.success("Bank account saved! 🏦"); st.rerun()

    # Show current saved method
    if s["wallet_method"] == "easypaisa":
        st.markdown(f'<div style="background:rgba(0,204,102,0.08);border:1px solid rgba(0,204,102,0.2);border-radius:10px;padding:0.65rem 0.9rem;font-size:0.79rem;color:#00CC66;margin-top:0.3rem">✓ EasyPaisa linked: {s["wallet_number"]}</div>', unsafe_allow_html=True)
    elif s["wallet_method"] == "jazzcash":
        st.markdown(f'<div style="background:rgba(255,184,0,0.08);border:1px solid rgba(255,184,0,0.2);border-radius:10px;padding:0.65rem 0.9rem;font-size:0.79rem;color:#FFB800;margin-top:0.3rem">✓ JazzCash linked: {s["wallet_number"]}</div>', unsafe_allow_html=True)
    elif s["wallet_method"] == "bank":
        st.markdown(f'<div style="background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.2);border-radius:10px;padding:0.65rem 0.9rem;font-size:0.79rem;color:#00D4FF;margin-top:0.3rem">✓ Bank account linked: {s.get("bank_name","")} — {s.get("bank_account","")[:12]}…</div>', unsafe_allow_html=True)

    if st.button("📜 View Transactions", key="view_txn"):
        st.session_state.screen = "student_transactions"; st.rerun()

    sec("⭐ Premium Features")
    if not prem:
        st.markdown("""<div style="background:linear-gradient(135deg,rgba(255,184,0,0.08),rgba(124,58,255,0.08));border:1px solid rgba(255,184,0,0.3);border-radius:18px;padding:1.2rem;margin-bottom:0.8rem">
          <div style="font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:800;color:#FFB800">Unlock for PKR 500/month</div>
          <div style="margin-top:0.7rem;font-size:0.8rem;color:#C4C7D0;line-height:1.8">✦ AI-Generated CV<br>✦ Free Training Programs<br>✦ Priority Profile<br>✦ Unlimited AI Recommendations</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Upgrade to Premium ⭐", key="pf_upg"):
            st.session_state.screen = "student_premium"; st.rerun()
    else:
        st.markdown('<div style="background:rgba(255,184,0,0.08);border:1px solid rgba(255,184,0,0.3);border-radius:12px;padding:0.85rem;font-size:0.8rem;color:#FFB800;margin-bottom:0.8rem">⭐ Premium active — enjoy all features!</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            if st.button("🤖 Generate CV", key="gen_cv"):
                st.session_state.screen = "student_cv"; st.rerun()
        with c2:
            if st.button("📚 Trainings", key="view_tr"):
                st.session_state.screen = "student_training"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sign Out", key="so_s"):
        for k in ["user_id","role","screen"]: st.session_state.pop(k, None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    snav("student_profile")


def show_student_premium():
    nb(subtitle="Student Premium")
    st.markdown('<div style="padding:1.2rem">', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:linear-gradient(160deg,#1a1200,#16001a);border:1px solid rgba(255,184,0,0.3);border-radius:24px;padding:2rem 1.5rem;text-align:center;margin-bottom:1.2rem;position:relative;overflow:hidden">
      <div style="position:absolute;top:-60px;left:50%;transform:translateX(-50%);width:200px;height:200px;background:radial-gradient(rgba(255,184,0,0.15),transparent 70%);border-radius:50%"></div>
      <div style="position:relative;z-index:1">
        <div style="font-size:2.5rem;margin-bottom:0.5rem">⭐</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;color:#FFB800">Student Premium</div>
        <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:#fff;margin:0.4rem 0">PKR 500<span style="font-size:0.88rem;color:#8B8F9A">/month</span></div>
        <div style="color:#8B8F9A;font-size:0.81rem">Everything a student needs to land their dream gig</div>
      </div>
    </div>""", unsafe_allow_html=True)

    features = [("🤖","AI-Generated CV","Auto-creates a professional CV tailored to each job based on your skills and profile"),
                ("📚","Training Programs","Curated free training: Excel, Canva, Social Media, Customer Service, Python basics"),
                ("🚀","Priority Profile","Your profile appears first when businesses search for candidates"),
                ("♾️","Unlimited AI Match","Personalized gig recommendations based on your interests — unlimited")]
    for icon, title, desc in features:
        st.markdown(f"""<div style="display:flex;gap:0.9rem;align-items:flex-start;background:#1A1D24;border:1px solid #252831;border-radius:12px;padding:1rem;margin-bottom:0.7rem">
          <div style="font-size:1.4rem;flex-shrink:0">{icon}</div>
          <div><div style="font-weight:700;font-size:0.86rem;color:#fff">{title}</div>
          <div style="font-size:0.76rem;color:#8B8F9A;margin-top:3px;line-height:1.5">{desc}</div></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    method = st.selectbox("Pay via", ["EasyPaisa 🟢","JazzCash 🔴"], key="pm_m")
    if st.button("Subscribe — PKR 500/month →", key="sub_prem"):
        mval = "easypaisa" if "EasyPaisa" in method else "jazzcash"
        expires = (datetime.utcnow()+timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        db = get_db()
        db.execute("UPDATE users SET plan='premium',plan_expires=? WHERE id=?", (expires, st.session_state.user_id))
        db.execute("INSERT INTO payments (user_id,amount,plan,method) VALUES (?,?,?,?)", (st.session_state.user_id, 500, "premium", mval))
        db.commit(); db.close()
        st.success("🎉 Premium activated!")
        st.session_state.screen = "student_profile"; st.rerun()
    if st.button("← Back", key="prem_back"):
        st.session_state.screen = "student_home"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_student_cv():
    s = get_student()
    nb(subtitle="AI CV Generator")
    st.markdown('<div style="padding:1.2rem">', unsafe_allow_html=True)
    st.markdown('<div style="background:rgba(124,58,255,0.12);border:1px solid rgba(124,58,255,0.3);border-radius:12px;padding:0.85rem 1rem;margin-bottom:1rem;font-size:0.8rem;color:#C4C7D0">🤖 <strong style="color:#fff">AI CV Generator</strong> — Premium Feature</div>', unsafe_allow_html=True)

    with st.form("cv_f"):
        job_title = st.text_input("Target Job Title", placeholder="e.g. Social Media Manager")
        extra = st.text_area("Extra experience / achievements?", placeholder="e.g. Won hackathon, managed a team…")
        gen = st.form_submit_button("Generate My CV →")

    if gen and job_title:
        skills_list = [x.strip() for x in (s["skills"] or "").split(",") if x.strip()]
        st.markdown(f"""
        <div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.4rem;margin-top:0.8rem;font-family:'Courier New',monospace;font-size:0.77rem;line-height:1.8;color:#C4C7D0">
          <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#fff;border-bottom:1px solid #252831;padding-bottom:0.5rem;margin-bottom:0.8rem">{s['full_name'].upper()}</div>
          <div style="color:#8B8F9A">{s['university']} · {s.get('email','')}</div><br>
          <strong style="color:#FF4D00">OBJECTIVE</strong><br>
          Motivated {s['university']} student seeking a {job_title} role. {s['bio'] or 'Eager to apply academic knowledge professionally.'}<br><br>
          <strong style="color:#FF4D00">SKILLS</strong><br>{' · '.join(skills_list) or 'To be added'}<br><br>
          <strong style="color:#FF4D00">INTERESTS</strong><br>{(s['interests'] or 'Various fields').replace(',',' · ')}<br><br>
          {f'<strong style="color:#FF4D00">EXPERIENCE</strong><br>{extra}<br><br>' if extra else ''}
          <strong style="color:#FF4D00">PAYMENT</strong><br>Available via {s['wallet_method'].title() if s['wallet_method'] else 'EasyPaisa/JazzCash'}<br><br>
          <div style="border-top:1px solid #252831;padding-top:0.5rem;color:#545861;font-size:0.68rem">Generated by GigBridge AI · {datetime.now().strftime('%B %Y')}</div>
        </div>""", unsafe_allow_html=True)

    if st.button("← Back to Profile", key="cv_back"):
        st.session_state.screen = "student_profile"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_student_training():
    nb(subtitle="Training Programs")
    st.markdown('<div style="padding:1.2rem">', unsafe_allow_html=True)
    sec("Free Training Programs", "Included with Premium")

    programs = [
        ("📊","Microsoft Excel Mastery","VLOOKUP, Pivot Tables, dashboards","6 modules · 4 hrs","#AAFF00"),
        ("🎨","Canva Design Essentials","Graphics, posts, presentations","5 modules · 3 hrs","#7C3AFF"),
        ("📱","Social Media Marketing","Instagram, TikTok growth strategies","8 modules · 5 hrs","#00D4FF"),
        ("🤝","Customer Service Pro","Communication, CRM, complaints","4 modules · 2.5 hrs","#FFB800"),
        ("🐍","Python for Beginners","Variables, loops, functions, automation","10 modules · 8 hrs","#FF4D00"),
        ("✍️","Content Writing & SEO","Blogging, Urdu/English, keywords","6 modules · 4 hrs","#AAFF00"),
    ]
    for icon, title, desc, meta, color in programs:
        st.markdown(f"""<div style="background:#1A1D24;border:1px solid #252831;border-left:3px solid {color};border-radius:18px;padding:1.1rem 1.2rem;margin-bottom:0.8rem;display:flex;align-items:center;gap:1rem">
          <div style="font-size:1.6rem;flex-shrink:0">{icon}</div>
          <div style="flex:1">
            <div style="font-weight:700;font-size:0.86rem;color:#fff">{title}</div>
            <div style="font-size:0.74rem;color:#8B8F9A;margin-top:2px">{desc}</div>
            <div style="font-size:0.69rem;color:{color};margin-top:4px">{meta}</div>
          </div>
          <div style="color:{color};font-size:0.73rem;font-weight:700">Start →</div>
        </div>""", unsafe_allow_html=True)

    if st.button("← Back to Profile", key="tr_back"):
        st.session_state.screen = "student_profile"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── BUSINESS ──────────────────────────────────────────────────────────────────

def show_business_home():
    b = get_business()
    db = get_db()
    my_jobs = db.execute("SELECT * FROM jobs WHERE business_id=? ORDER BY created_at DESC LIMIT 5", (b["id"],)).fetchall()
    recent = db.execute("""SELECT a.*,j.title as jt,s.full_name,s.university,s.avg_rating
        FROM applications a JOIN jobs j ON j.id=a.job_id JOIN students s ON s.id=a.student_id
        WHERE j.business_id=? ORDER BY a.applied_at DESC LIMIT 4""", (b["id"],)).fetchall()
    u = db.execute("SELECT plan FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()
    db.close()

    col = av_color(b["business_name"])
    nb()
    st.markdown('<div style="padding:1.2rem 1.2rem 0.5rem">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1A1D24,#0d1220);border:1px solid #252831;border-radius:24px;padding:1.4rem;margin-bottom:1rem;position:relative;overflow:hidden">
      <div style="position:absolute;top:-40px;right:-40px;width:150px;height:150px;background:radial-gradient({col}30,transparent 70%);border-radius:50%"></div>
      <div style="position:relative;z-index:1;display:flex;align-items:center;gap:1rem">
        {av_html(b['business_name'],48,"1rem")}
        <div>
          <div style="font-size:0.68rem;color:#8B8F9A;letter-spacing:0.08em;text-transform:uppercase">Business Dashboard</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:800;color:#fff">{b['business_name']}</div>
          <div style="color:#8B8F9A;font-size:0.76rem">{b['industry'] or ''} · {b['city'] or ''}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(metric_card(b["total_posted"],"Posted","#00D4FF"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card(b["total_hired"],"Hired","#AAFF00"), unsafe_allow_html=True)
    with c3: st.markdown(metric_card((u["plan"] or "trial").upper(),"Plan","#FF4D00"), unsafe_allow_html=True)

    st.markdown('</div><div style="padding:0 1.2rem">', unsafe_allow_html=True)
    if my_jobs:
        sec("Active Gigs")
        for j in my_jobs:
            sc = {"open":"#AAFF00","closed":"#8B8F9A","filled":"#FFB800"}.get(j["status"],"#8B8F9A")
            st.markdown(f"""<div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1rem 1.1rem;margin-bottom:0.6rem;display:flex;justify-content:space-between;align-items:center">
              <div><div style="font-weight:700;font-size:0.86rem;color:#fff">{j['title']}</div>
              <div style="color:#8B8F9A;font-size:0.74rem">PKR {int(j['salary']):,} · {j['job_type']} · {time_ago(j['created_at'])}</div></div>
              <span style="font-size:0.63rem;font-weight:700;color:{sc};background:{sc}22;padding:3px 8px;border-radius:20px">{j['status'].upper()}</span>
            </div>""", unsafe_allow_html=True)

    if recent:
        sec("Recent Applicants")
        for a in recent:
            st.markdown(f"""<div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1rem 1.1rem;margin-bottom:0.6rem;display:flex;align-items:center;gap:0.8rem">
              {av_html(a['full_name'],40,"0.82rem")}
              <div style="flex:1">
                <div style="font-weight:700;font-size:0.84rem;color:#fff">{a['full_name']}</div>
                <div style="color:#8B8F9A;font-size:0.74rem">{a['university']} · {a['jt']}</div>
                <div style="color:#FFB800;font-size:0.7rem">{"★"*int(a['avg_rating'])}{"☆"*(5-int(a['avg_rating']))} · {time_ago(a['applied_at'])}</div>
              </div>
              {'<span style="background:rgba(255,77,0,0.15);color:#FF4D00;font-size:0.62rem;font-weight:700;padding:2px 7px;border-radius:20px">NEW</span>' if a["status"]=="pending" else ''}
            </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    bnav("business_home")


def show_business_post():
    b = get_business()
    db2 = get_db()
    u = db2.execute("SELECT plan FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()
    db2.close()

    nb(subtitle="Post a New Gig")
    st.markdown('<div style="padding:1rem 1.2rem 0">', unsafe_allow_html=True)

    if u["plan"] in ("trial",):
        db3 = get_db()
        open_ct = db3.execute("SELECT COUNT(*) FROM jobs WHERE business_id=? AND status='open'", (b["id"],)).fetchone()[0]
        db3.close()
        if open_ct >= 2:
            st.warning("⚠️ Trial allows max 2 active gigs. Upgrade to Pro.")
            if st.button("Upgrade to Pro →", key="upg_post"):
                st.session_state.screen = "business_subscribe"; st.rerun()
            bnav("business_post"); return

    with st.form("post_form"):
        title = st.text_input("Job Title *", placeholder="e.g. Social Media Assistant")
        c1,c2 = st.columns(2)
        with c1: jtype = st.selectbox("Job Type *", ["Part-time"])
        with c2: location = st.text_input("Location *", placeholder="DHA, Karachi")
        c3,c4 = st.columns(2)
        with c3: salary = st.number_input("Salary (PKR) *", min_value=0, step=500)
        with c4: period = st.selectbox("Period", ["monthly","weekly","per project"])
        hours = st.text_input("Hours / Day", placeholder="4 hrs/day")
        description = st.text_area("Description *", placeholder="Role, responsibilities…")
        skills = st.text_input("Skills Required", placeholder="Excel, Communication…")
        category = st.text_input("Category", placeholder="Marketing, Technology…")
        c5,c6 = st.columns(2)
        with c5: pmethod = st.selectbox("Payment via", ["easypaisa","jazzcash"])
        with c6: is_urgent = st.checkbox("URGENT ⚡")
        is_remote = st.checkbox("Remote 🌐")
        if st.form_submit_button("Post This Gig →"):
            if not title or not description or salary <= 0:
                st.error("Fill all required fields.")
            else:
                db = get_db()
                db.execute("""INSERT INTO jobs (business_id,title,description,job_type,location,is_remote,hours_per_day,salary,salary_period,skills_required,category,is_urgent,payment_method) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (b["id"], title, description, jtype, location, 1 if is_remote else 0, hours, salary, period, skills, category, 1 if is_urgent else 0, pmethod))
                db.execute("UPDATE businesses SET total_posted=total_posted+1 WHERE id=?", (b["id"],))
                db.commit(); db.close()
                st.success("Gig posted! 🚀")
                st.session_state.screen = "business_home"; st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    bnav("business_post")


def show_business_applicants():
    b = get_business()
    db = get_db()
    apps = db.execute("""SELECT a.*,j.title as jt,s.full_name,s.university,s.avg_rating,s.total_gigs,s.skills,s.id as sid
        FROM applications a JOIN jobs j ON j.id=a.job_id JOIN students s ON s.id=a.student_id
        WHERE j.business_id=? ORDER BY a.applied_at DESC""", (b["id"],)).fetchall()
    db.close()

    nb(subtitle="Applicants")
    st.markdown('<div style="padding:1rem 1.2rem 0">', unsafe_allow_html=True)
    sec("Applicants", f"{len(apps)} total")
    S_COLOR = {"pending":"#8B8F9A","hired":"#AAFF00","rejected":"#FF3B3B","reviewed":"#00D4FF"}

    if not apps:
        st.markdown('<div style="text-align:center;padding:2.5rem 1rem"><div style="font-size:2.2rem;margin-bottom:0.6rem">📭</div><div style="font-family:\'Syne\',sans-serif;font-size:0.95rem;color:#fff">No applicants yet</div></div>', unsafe_allow_html=True)
        if st.button("Post a Gig →", key="pag"):
            st.session_state.screen = "business_post"; st.rerun()
    else:
        for a in apps:
            sc = S_COLOR.get(a["status"],"#8B8F9A")
            stags = "".join(badge(sk.strip(),"#545861","#252831") for sk in (a["skills"] or "").split(",") if sk.strip())
            st.markdown(f"""<div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.1rem;margin-bottom:0.8rem">
              <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.6rem">
                {av_html(a['full_name'],42,"0.84rem")}
                <div style="flex:1">
                  <div style="font-weight:700;font-size:0.86rem;color:#fff">{a['full_name']}</div>
                  <div style="color:#8B8F9A;font-size:0.74rem">{a['university']}</div>
                  <div style="color:#FFB800;font-size:0.7rem">{"★"*int(a['avg_rating'])}{"☆"*(5-int(a['avg_rating']))} · {a['total_gigs']} gigs · {time_ago(a['applied_at'])}</div>
                </div>
                <span style="color:{sc};font-size:0.63rem;font-weight:700;background:{sc}22;padding:3px 8px;border-radius:20px">{a['status'].upper()}</span>
              </div>
              <div style="color:#8B8F9A;font-size:0.74rem;margin-bottom:0.4rem">For: <strong style="color:#C4C7D0">{a['jt']}</strong></div>
              {f'<div style="color:#8B8F9A;font-size:0.74rem;font-style:italic;border-left:2px solid #252831;padding-left:0.7rem;margin-bottom:0.4rem">{a["cover_note"]}</div>' if a.get("cover_note") else ''}
              <div style="margin-bottom:0.5rem">{stags}</div>
            </div>""", unsafe_allow_html=True)
            c1,c2 = st.columns(2)
            with c1:
                if st.button("✓ Hire", key=f"hire_{a['id']}"):
                    db2 = get_db()
                    db2.execute("UPDATE applications SET status='hired' WHERE id=?", (a["id"],))
                    db2.execute("UPDATE businesses SET total_hired=total_hired+1 WHERE user_id=?", (st.session_state.user_id,))
                    db2.commit(); db2.close()
                    st.success("🎉 Hired!"); st.rerun()
            with c2:
                if st.button("✗ Pass", key=f"rej_{a['id']}"):
                    db2 = get_db()
                    db2.execute("UPDATE applications SET status='rejected' WHERE id=?", (a["id"],))
                    db2.commit(); db2.close()
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    bnav("business_applicants")


def show_business_profile():
    b = get_business()
    db2 = get_db()
    u = db2.execute("SELECT plan,plan_expires FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()
    db2.close()
    plan_color = {"pro":"#AAFF00","trial":"#FFB800","active":"#AAFF00"}.get(u["plan"],"#8B8F9A")

    nb(subtitle="Business Profile")
    st.markdown('<div style="padding:1rem 1.2rem 0">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1A1D24,#252831);border:1px solid #353840;border-radius:24px;padding:1.4rem;margin-bottom:1rem;display:flex;align-items:center;gap:1rem">
      {av_html(b['business_name'],56,"1.2rem")}
      <div>
        <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:800;color:#fff">{b['business_name']}</div>
        <div style="color:#8B8F9A;font-size:0.77rem">{b['industry']} · {b['city']}</div>
        <div style="margin-top:5px">
          {badge("✓ Verified","#AAFF00","rgba(170,255,0,0.12)")}
          {badge((u['plan'] or 'trial').upper(), plan_color, plan_color+"22")}
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1: st.markdown(metric_card(b["total_posted"],"Posted","#00D4FF"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card(b["total_hired"],"Hired","#AAFF00"), unsafe_allow_html=True)

    sec("Edit Profile")
    with st.form("bpf"):
        desc = st.text_area("Description", value=b["description"] or "", placeholder="Tell students about your company…")
        website = st.text_input("Website", value=b["website"] or "", placeholder="https://yourcompany.pk")
        if st.form_submit_button("Save Profile →"):
            db = get_db()
            db.execute("UPDATE businesses SET description=?,website=? WHERE user_id=?", (desc, website, st.session_state.user_id))
            db.commit(); db.close()
            st.success("Saved! ✅"); st.rerun()

    sec("Subscription")
    if st.button("🚀 Manage Plan", key="biz_plan"):
        st.session_state.screen = "business_subscribe"; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sign Out", key="so_b"):
        for k in ["user_id","role","screen"]: st.session_state.pop(k, None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    bnav("business_profile")


def show_business_subscribe():
    nb(subtitle="Business Plans")
    st.markdown('<div style="padding:1.2rem">', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#1A1D24;border:1px solid #252831;border-radius:18px;padding:1.2rem;margin-bottom:0.8rem">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:#fff">Free Trial</div>
        <div style="font-size:0.77rem;color:#8B8F9A;margin-top:2px">Post 2 gigs · Basic features</div></div>
        <div style="font-family:'Syne',sans-serif;font-weight:800;color:#8B8F9A">PKR 0</div>
      </div>
    </div>
    <div style="background:linear-gradient(135deg,rgba(255,77,0,0.08),rgba(124,58,255,0.08));border:2px solid #FF4D00;border-radius:18px;padding:1.2rem;margin-bottom:0.8rem">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem">
        <div><div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:#fff">Business Pro 🔥</div>
        <div style="font-size:0.77rem;color:#8B8F9A;margin-top:2px">Unlimited gigs · Priority listing · Filters</div></div>
        <div style="font-family:'Syne',sans-serif;font-weight:800;color:#FF4D00">PKR 2,999/mo</div>
      </div>
    </div>""", unsafe_allow_html=True)
    method = st.selectbox("Pay via", ["EasyPaisa 🟢","JazzCash 🔴"], key="bsub_m")
    if st.button("Subscribe — PKR 2,999/month →", key="bsub"):
        mval = "easypaisa" if "EasyPaisa" in method else "jazzcash"
        expires = (datetime.utcnow()+timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        db = get_db()
        db.execute("UPDATE users SET plan='pro',plan_expires=? WHERE id=?", (expires, st.session_state.user_id))
        db.execute("INSERT INTO payments (user_id,amount,plan,method) VALUES (?,?,?,?)", (st.session_state.user_id, 2999, "pro", mval))
        db.commit(); db.close()
        st.success("🎉 Pro activated!")
        st.session_state.screen = "business_home"; st.rerun()
    if st.button("← Back", key="bsub_back"):
        st.session_state.screen = "business_profile"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── ADMIN ─────────────────────────────────────────────────────────────────────

def show_admin():
    db = get_db()
    stats = {
        "students": db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "businesses": db.execute("SELECT COUNT(*) FROM businesses").fetchone()[0],
        "jobs": db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "apps": db.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
        "hired": db.execute("SELECT COUNT(*) FROM applications WHERE status='hired'").fetchone()[0],
        "revenue": db.execute("SELECT COALESCE(SUM(amount),0) FROM payments").fetchone()[0],
    }
    students = db.execute("SELECT s.full_name,s.university,u.email,u.plan,u.created_at FROM students s JOIN users u ON u.id=s.user_id ORDER BY u.created_at DESC LIMIT 15").fetchall()
    businesses = db.execute("SELECT b.business_name,b.city,u.email,u.plan FROM businesses b JOIN users u ON u.id=b.user_id ORDER BY u.created_at DESC LIMIT 10").fetchall()
    payments = db.execute("SELECT p.*,u.email FROM payments p JOIN users u ON u.id=p.user_id ORDER BY p.created_at DESC LIMIT 10").fetchall()
    db.close()

    nb(subtitle="Admin Dashboard")
    st.markdown('<div style="padding:1rem 1.2rem 0">', unsafe_allow_html=True)
    sec("Platform Overview")

    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(metric_card(stats["students"],"Students","#00D4FF"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card(stats["businesses"],"Businesses","#7C3AFF"), unsafe_allow_html=True)
    with c3: st.markdown(metric_card(stats["jobs"],"Gigs","#AAFF00"), unsafe_allow_html=True)
    c4,c5,c6 = st.columns(3)
    with c4: st.markdown(metric_card(stats["apps"],"Applications","#FFB800"), unsafe_allow_html=True)
    with c5: st.markdown(metric_card(stats["hired"],"Hired","#FF4D00"), unsafe_allow_html=True)
    with c6: st.markdown(metric_card(f"PKR {int(stats['revenue']):,}","Revenue","#AAFF00"), unsafe_allow_html=True)

    sec("Students")
    for s in students:
        pc = {"premium":"#FFB800","free":"#8B8F9A"}.get(s["plan"],"#545861")
        st.markdown(f"""<div style="background:#1A1D24;border:1px solid #252831;border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.35rem;display:flex;justify-content:space-between;align-items:center">
          <div><div style="font-weight:700;font-size:0.82rem;color:#fff">{s['full_name']}</div>
          <div style="color:#8B8F9A;font-size:0.7rem">{s['university']} · {s['email']}</div></div>
          <span style="color:{pc};font-size:0.63rem;font-weight:700;background:{pc}22;padding:2px 7px;border-radius:20px">{(s['plan'] or 'free').upper()}</span>
        </div>""", unsafe_allow_html=True)

    sec("Businesses")
    for b in businesses:
        st.markdown(f"""<div style="background:#1A1D24;border:1px solid #252831;border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.35rem;display:flex;justify-content:space-between;align-items:center">
          <div><div style="font-weight:700;font-size:0.82rem;color:#fff">{b['business_name']}</div>
          <div style="color:#8B8F9A;font-size:0.7rem">{b['city']} · {b['email']}</div></div>
          <span style="font-size:0.63rem;font-weight:700;color:#AAFF00;background:rgba(170,255,0,0.12);padding:2px 7px;border-radius:20px">{(b['plan'] or 'trial').upper()}</span>
        </div>""", unsafe_allow_html=True)

    if payments:
        sec("Payments")
        for p in payments:
            st.markdown(f"""<div style="background:#1A1D24;border:1px solid #252831;border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.35rem;display:flex;justify-content:space-between;align-items:center">
              <div><div style="font-size:0.8rem;color:#fff">{p['email']}</div>
              <div style="color:#8B8F9A;font-size:0.7rem">{p['plan']} · {p['method'] or '—'} · {p['created_at'][:10]}</div></div>
              <div style="font-family:'Syne',sans-serif;font-weight:800;color:#AAFF00">PKR {int(p['amount']):,}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sign Out (Admin)", key="adm_so"):
        for k in ["user_id","role","screen"]: st.session_state.pop(k, None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── ONBOARDING: Skill Picker (shown once after signup / if no interests set) ──

SKILL_CATEGORIES = {
    "💻 Tech & IT": ["Web Development","Mobile Apps","Data Entry","Python","Excel & Sheets","Graphic Design","UI/UX Design","Video Editing","WordPress"],
    "📢 Marketing": ["Social Media","Content Writing","SEO","Email Marketing","Canva Design","Photography","Copywriting"],
    "🤝 Sales & Support": ["Sales Person","Customer Service","Cold Calling","Lead Generation","Chat Support","Telemarketing"],
    "📚 Education": ["Online Tutoring","Assignment Help","Research","Translation","Urdu/English Writing"],
    "🏢 Admin & Office": ["Data Entry","Virtual Assistant","Scheduling","HR Support","Bookkeeping","Receptionist"],
    "🎨 Creative": ["Graphic Design","Logo Design","Video Editing","Photography","Animation","Illustration"],
    "🍔 Food & Events": ["Barista","Waiter","Event Helper","Food Delivery","Catering","Kitchen Assist"],
    "📦 Logistics": ["Delivery Rider","Warehouse Helper","Inventory","Packaging","Dispatch"],
}

def show_onboarding():
    s = get_student()
    nb(subtitle="Choose Your Skills")

    st.markdown("""
    <div style="padding:1.2rem 1.2rem 0;text-align:center">
      <div style="font-size:2rem;margin-bottom:0.4rem">🎯</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:800;color:#fff">What can you do?</div>
      <div style="color:#8B8F9A;font-size:0.82rem;margin-top:4px;margin-bottom:1.2rem">Pick your skills &amp; interests — we'll find the best gigs for you</div>
    </div>
    """, unsafe_allow_html=True)

    selected = st.session_state.get("onboard_selected", set())

    st.markdown('<div style="padding:0 1.2rem">', unsafe_allow_html=True)
    for cat, skills in SKILL_CATEGORIES.items():
        st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:0.82rem;font-weight:800;color:#8B8F9A;letter-spacing:0.06em;text-transform:uppercase;margin:0.9rem 0 0.45rem">{cat}</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, skill in enumerate(skills):
            with cols[i % 3]:
                is_sel = skill in selected
                color = "#FF4D00" if is_sel else "#252831"
                border = "#FF4D00" if is_sel else "#353840"
                text_color = "#fff" if is_sel else "#8B8F9A"
                st.markdown(f"""<div style="background:{color}22;border:1.5px solid {border};border-radius:10px;
                  padding:0.45rem 0.3rem;text-align:center;font-size:0.71rem;font-weight:600;color:{text_color};
                  cursor:pointer;margin-bottom:0.4rem;transition:all 0.15s">{skill}</div>""", unsafe_allow_html=True)
                btn_label = "✓" if is_sel else "+"
                if st.button(btn_label, key=f"ob_{skill.replace(' ','_')}"):
                    sel = st.session_state.get("onboard_selected", set())
                    if skill in sel: sel.discard(skill)
                    else: sel.add(skill)
                    st.session_state.onboard_selected = sel
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div style="padding:0.8rem 1.2rem 1rem">', unsafe_allow_html=True)
    count = len(selected)
    if count > 0:
        st.markdown(f'<div style="background:rgba(255,77,0,0.1);border:1px solid rgba(255,77,0,0.3);border-radius:12px;padding:0.7rem 1rem;margin-bottom:0.8rem;font-size:0.8rem;color:#FF4D00;text-align:center"><strong>{count} skill{"s" if count!=1 else ""}</strong> selected</div>', unsafe_allow_html=True)
    if st.button(f"Find My Gigs →  ({count} selected)" if count else "Skip for now →", key="ob_done"):
        if selected:
            db = get_db()
            db.execute("UPDATE students SET interests=?,skills=? WHERE user_id=?",
                       (", ".join(selected), ", ".join(selected), st.session_state.user_id))
            db.commit(); db.close()
        st.session_state.onboard_selected = set()
        st.session_state.screen = "student_ai_chat"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─── GIGBOT CHAT — 100% LOCAL, NO API ─────────────────────────────────────────

GIGBOT_RESPONSES = {
    "graphic design":   ("graphic design / logo / creative work", ["Graphic Design","Canva","Design","Logo","Illustration","Video Editing","Figma"]),
    "design":           ("design work", ["Graphic Design","Canva","Design","Logo","Figma","UI"]),
    "data entry":       ("data entry / Excel work", ["Data Entry","Excel","SQL","Data","Spreadsheet"]),
    "excel":            ("Excel & data work", ["Excel","Data Entry","SQL","Data","Spreadsheet"]),
    "social media":     ("social media management", ["Social Media","Instagram","TikTok","Content","Marketing"]),
    "marketing":        ("marketing & content", ["Marketing","Social Media","Content","SEO","Canva"]),
    "content":          ("content writing & creation", ["Content Writing","Writing","SEO","Copywriting","Blog"]),
    "writing":          ("writing & content creation", ["Writing","Content Writing","SEO","Blog","Urdu"]),
    "sales":            ("sales & lead generation", ["Sales","Lead Generation","Cold Calling","Telemarketing","CRM"]),
    "customer":         ("customer support", ["Customer Service","Support","CRM","Chat","Communication"]),
    "support":          ("customer support", ["Customer Service","Support","CRM","Communication"]),
    "python":           ("Python / programming", ["Python","Programming","Web","Developer","SQL"]),
    "web":              ("web development", ["Web","WordPress","Developer","HTML","CSS"]),
    "video":            ("video editing", ["Video Editing","Canva","Creative","Animation"]),
    "photography":      ("photography", ["Photography","Creative","Canva"]),
    "teaching":         ("tutoring / teaching", ["Tutoring","Teaching","Education","Research"]),
    "tutor":            ("tutoring", ["Tutoring","Teaching","Education"]),
    "admin":            ("admin / virtual assistant work", ["Admin","Virtual Assistant","Scheduling","HR","Receptionist"]),
    "hr":               ("HR support", ["HR","Admin","Scheduling","Receptionist"]),
    "delivery":         ("delivery / logistics", ["Delivery","Logistics","Rider","Dispatch"]),
    "food":             ("food & events", ["Barista","Waiter","Food","Catering","Events","Kitchen"]),
    "barista":          ("café / barista work", ["Barista","Food","Catering","Kitchen"]),
    "part":             ("part-time jobs", []),   # catch "part time"
    "internship":       ("internships", []),
    "freelance":        ("freelance gigs", []),
}

def _gigbot_match(query, jobs):
    """Match user query to live posted jobs — no API."""
    q = query.lower().strip()
    # find best category keywords
    match_tags = []
    matched_label = ""
    for kw, (label, tags) in GIGBOT_RESPONSES.items():
        if kw in q:
            match_tags = tags
            matched_label = label
            break
    # also grab raw words from query
    raw_words = [w for w in q.split() if len(w) >= 4]
    all_keywords = list(set([t.lower() for t in match_tags] + raw_words))

    # special: type filters
    type_filter = None
    if "part" in q or "part-time" in q: type_filter = "Part-time"
    elif "internship" in q: type_filter = "Internship"
    elif "freelance" in q: type_filter = "Freelance"
    elif "weekend" in q: type_filter = "Weekend"

    scored = []
    for j in jobs:
        haystack = (j["title"] + " " + j["description"] + " " + (j["skills_required"] or "") + " " + (j["category"] or "")).lower()
        score = 0
        for kw in all_keywords:
            if kw in haystack: score += 2
        if type_filter and j["job_type"] == type_filter: score += 3
        if j["is_urgent"]: score += 1
        if score > 0: scored.append((score, j))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [j for _, j in scored[:3]]

    if top:
        names = " · ".join(f"{j['title']} at {j['business_name']} (PKR {int(j['salary']):,}/mo)" for j in top)
        reply = f"Here are the best {matched_label or query} gigs right now:\n\n{names}\n\nTap a card below to view and apply! 👇"
    else:
        reply = f"No gigs for {query} posted yet — check back soon! Try browsing All gigs or tell me another skill."
    return reply, [str(j["id"]) for j in top]


def gigbot_reply(user_msg, student, jobs):
    """Generate a reply from GigBot without any API."""
    q = user_msg.lower().strip()

    # greetings
    greetings = ["hi","hello","hey","salam","assalam","aoa","hii","helo","sup","yo"]
    if any(q.startswith(g) for g in greetings) or q in greetings:
        name = student["full_name"].split()[0]
        interests = student["interests"]
        if interests:
            return f"Hey {name}! 👋 You're into {interests}. Want me to show you the latest matching gigs?", []
        else:
            return f"Hey {name}! 👋 Tell me what kind of work you want and I'll find the best gigs for you! e.g. graphic design, data entry, sales, social media…", []

    if any(w in q for w in ["help","kya kar","what can","how does","kaise"]):
        return "Just tell me a skill or field — like graphic design, data entry, sales, content writing — and I'll instantly show you matching jobs posted on GigBridge.", []

    if any(w in q for w in ["salary","kitna","pay","earn","income","paise"]):
        if jobs:
            min_s = min(j["salary"] for j in jobs)
            max_s = max(j["salary"] for j in jobs)
            return f"Current gigs pay between PKR {int(min_s):,} and PKR {int(max_s):,} per month. Want me to show you the highest-paying ones?", []
        return "Tell me which field you're interested in and I'll show you what's paying right now!", []

    if any(w in q for w in ["how many","kitne","available","list","show all","sab"]):
        return f"There are {len(jobs)} gigs live on GigBridge right now! Tell me your skill and I'll filter them for you.", []

    reply, ids = _gigbot_match(user_msg, jobs)
    return reply, ids


def show_ai_chat():
    s = get_student()
    db = get_db()
    jobs = db.execute("SELECT j.*,b.business_name FROM jobs j JOIN businesses b ON b.id=j.business_id WHERE j.status='open' ORDER BY j.is_urgent DESC,j.created_at DESC").fetchall()
    db.close()

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        st.session_state.rec_job_ids = []

    nb(subtitle="GigBot — Gig Advisor")

    # Header card
    st.markdown("""
    <div style="padding:1rem 1.2rem 0">
      <div style="background:linear-gradient(135deg,rgba(124,58,255,0.18),rgba(255,77,0,0.08));border:1px solid rgba(124,58,255,0.35);border-radius:18px;padding:1rem 1.2rem;margin-bottom:0.6rem;display:flex;align-items:center;gap:0.9rem">
        <div style="width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#7C3AFF,#FF4D00);display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0">🤖</div>
        <div style="flex:1">
          <div style="font-family:'Syne',sans-serif;font-size:0.9rem;font-weight:800;color:#fff">GigBot</div>
          <div style="font-size:0.7rem;color:#8B8F9A;margin-top:1px">Matches you to live jobs · No AI fees · Instant</div>
        </div>
        <span style="background:rgba(0,204,102,0.15);color:#00CC66;font-size:0.62rem;font-weight:700;padding:3px 9px;border-radius:20px;white-space:nowrap">● LIVE</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick interest chips (always show)
    # Quick-pick chips — 3 per row, styled as small pills
    QUICK = [
        ("🎨 Design","Graphic Design"), ("📊 Data","Data Entry"), ("📞 Sales","Sales"),
        ("📱 Social","Social Media"),   ("✍️ Writing","Content Writing"), ("🤝 Support","Customer Support"),
        ("💻 Web Dev","Web Dev"),        ("🎬 Video","Video Editing"), ("📚 Tutor","Tutoring"),
        ("🏢 Admin","Admin Work"),       ("☕ Food","Barista / Food"), ("🚚 Delivery","Delivery"),
    ]
    st.markdown("""<style>
    .chip-row .stButton>button{
      background:#0F1F38 !important;border:1px solid #1E3554 !important;
      border-radius:20px !important;color:#A8BDD0 !important;
      font-size:0.71rem !important;font-weight:600 !important;
      padding:6px 4px !important;height:32px !important;min-height:0 !important;
      width:100% !important;white-space:nowrap !important;
      box-shadow:none !important;letter-spacing:0 !important;text-transform:none !important;
    }
    .chip-row .stButton>button:hover{
      background:#E8700A !important;color:#fff !important;
      border-color:#E8700A !important;transform:none !important;box-shadow:none !important;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="chip-row" style="padding:2px 1.2rem 8px">', unsafe_allow_html=True)
    for i in range(0, len(QUICK), 3):
        row = st.columns(3)
        for col, (chip_label, full_label) in zip(row, QUICK[i:i+3]):
            with col:
                if st.button(chip_label, key=f"qc_{full_label.replace(' ','_')}"):
                    st.session_state.chat_messages.append({"role":"user","content": full_label})
                    reply, ids = gigbot_reply(full_label, s, jobs)
                    st.session_state.chat_messages.append({"role":"assistant","content": reply})
                    st.session_state.rec_job_ids = ids
                    if not s["interests"]:
                        db2 = get_db()
                        db2.execute("UPDATE students SET interests=? WHERE user_id=?", (full_label, st.session_state.user_id))
                        db2.commit(); db2.close()
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat window
    st.markdown('<div style="padding:0 1.2rem">', unsafe_allow_html=True)

    if not st.session_state.chat_messages:
        name = s["full_name"].split()[0]
        if s["interests"]:
            welcome = f"Hey {name}! 👋 You're into {s['interests']}. Tap a chip or type below and I'll find matching gigs instantly! 🚀"
        else:
            welcome = f"Hey {name}! 👋 I'm GigBot — tap a skill above or type what work you want, like graphic design, data entry or sales, and I'll match you with live jobs!"
        st.session_state.chat_messages.append({"role":"assistant","content": welcome})

    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f'<div style="display:flex;justify-content:flex-end;margin-bottom:0.65rem"><div style="background:#FF4D00;color:#fff;border-radius:18px 18px 4px 18px;padding:0.65rem 1rem;max-width:78%;font-size:0.82rem;line-height:1.5">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="display:flex;gap:0.55rem;margin-bottom:0.65rem;align-items:flex-end"><div style="width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#7C3AFF,#FF4D00);display:flex;align-items:center;justify-content:center;font-size:0.7rem;flex-shrink:0">🤖</div><div style="background:#1A1D24;border:1px solid #252831;color:#C4C7D0;border-radius:18px 18px 18px 4px;padding:0.65rem 1rem;max-width:84%;font-size:0.82rem;line-height:1.55">{msg["content"]}</div></div>', unsafe_allow_html=True)

    # Recommended job cards
    rids = st.session_state.get("rec_job_ids", [])
    rec_jobs = [j for j in jobs if str(j["id"]) in rids]
    if rec_jobs:
        st.markdown('<div style="background:rgba(124,58,255,0.07);border:1px solid rgba(124,58,255,0.2);border-radius:14px;padding:0.8rem 0.9rem;margin-bottom:0.7rem">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.68rem;font-weight:700;color:#7C3AFF;letter-spacing:0.07em;text-transform:uppercase;margin-bottom:0.5rem">🤖 Matched Gigs</div>', unsafe_allow_html=True)
        for rj in rec_jobs:
            c = av_color(rj["business_name"] or "")
            urg = ' <span style="background:rgba(255,77,0,0.15);color:#FF4D00;font-size:0.6rem;font-weight:700;padding:2px 6px;border-radius:10px">URGENT</span>' if rj["is_urgent"] else ""
            st.markdown(f'<div style="background:#1A1D24;border:1px solid #252831;border-radius:12px;padding:0.75rem;margin-bottom:0.45rem;display:flex;align-items:center;gap:0.6rem"><div style="width:34px;height:34px;border-radius:8px;background:{c};display:flex;align-items:center;justify-content:center;font-family:\'Syne\',sans-serif;font-size:0.65rem;font-weight:800;color:white;flex-shrink:0">{ini(rj["business_name"])}</div><div style="flex:1;min-width:0"><div style="font-weight:700;font-size:0.82rem;color:#fff">{rj["title"]}{urg}</div><div style="color:#8B8F9A;font-size:0.7rem">{rj["business_name"]} · PKR {int(rj["salary"]):,}/mo · {rj["job_type"]}</div></div></div>', unsafe_allow_html=True)
            if st.button(f"Apply to {rj['title'][:20]}… →", key=f"bot_apply_{rj['id']}"):
                st.session_state.selected_job = rj["id"]; st.session_state.screen = "job_detail"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Text input — full width, no separate send button
    st.markdown('<div style="padding:0.3rem 1.2rem 0.8rem">', unsafe_allow_html=True)
    user_input = st.text_input("", placeholder="Type a skill or job type, e.g. sales, design…", key="bot_input", label_visibility="collapsed")
    if user_input.strip():
        st.session_state.chat_messages.append({"role":"user","content": user_input.strip()})
        reply, ids = gigbot_reply(user_input.strip(), get_student(), jobs)
        st.session_state.chat_messages.append({"role":"assistant","content": reply})
        st.session_state.rec_job_ids = ids
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    snav("student_ai_chat")


def show_student_transactions():
    s = get_student()
    db = get_db()
    txns = db.execute("""SELECT p.*,j.title as jt,b.business_name
        FROM payments p
        LEFT JOIN jobs j ON j.id = p.job_id
        LEFT JOIN businesses b ON b.id = j.business_id
        WHERE p.user_id=? ORDER BY p.created_at DESC""", (st.session_state.user_id,)).fetchall()
    db.close()

    nb(subtitle="Transactions")
    st.markdown('<div style="padding:1rem 1.2rem 0">', unsafe_allow_html=True)

    # Payment method summary card
    method_html = ""
    if s["wallet_method"] == "easypaisa":
        method_html = f'<div style="display:flex;align-items:center;gap:0.6rem"><div style="width:34px;height:34px;border-radius:10px;background:rgba(0,204,102,0.15);display:flex;align-items:center;justify-content:center;font-size:1rem">📱</div><div><div style="font-size:0.83rem;font-weight:700;color:#fff">EasyPaisa</div><div style="font-size:0.71rem;color:#00CC66">{s["wallet_number"]}</div></div></div>'
    elif s["wallet_method"] == "jazzcash":
        method_html = f'<div style="display:flex;align-items:center;gap:0.6rem"><div style="width:34px;height:34px;border-radius:10px;background:rgba(255,184,0,0.15);display:flex;align-items:center;justify-content:center;font-size:1rem">📱</div><div><div style="font-size:0.83rem;font-weight:700;color:#fff">JazzCash</div><div style="font-size:0.71rem;color:#FFB800">{s["wallet_number"]}</div></div></div>'
    elif s["wallet_method"] == "bank":
        method_html = f'<div style="display:flex;align-items:center;gap:0.6rem"><div style="width:34px;height:34px;border-radius:10px;background:rgba(0,212,255,0.15);display:flex;align-items:center;justify-content:center;font-size:1rem">🏦</div><div><div style="font-size:0.83rem;font-weight:700;color:#fff">{s.get("bank_name","Bank")}</div><div style="font-size:0.71rem;color:#00D4FF">{(s.get("bank_account") or "")[:16]}…</div></div></div>'
    else:
        method_html = '<div style="font-size:0.8rem;color:#8B8F9A">No payment method linked yet</div>'

    total_earned = s["total_earned"] or 0
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1A1D24,#252831);border:1px solid #353840;border-radius:24px;padding:1.3rem;margin-bottom:1rem">
      <div style="font-size:0.68rem;color:#8B8F9A;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.4rem">Total Earned</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:#AAFF00">PKR {int(total_earned):,}</div>
      <div style="margin-top:0.8rem;padding-top:0.8rem;border-top:1px solid #252831">{method_html}</div>
    </div>
    """, unsafe_allow_html=True)

    sec("Transaction History", f"{len(txns)} records")

    STATUS_STYLE = {
        "completed": ("#AAFF00","rgba(170,255,0,0.12)","✓ Paid"),
        "pending":   ("#FFB800","rgba(255,184,0,0.12)","⏳ Pending"),
        "failed":    ("#FF3B3B","rgba(255,59,59,0.12)","✗ Failed"),
    }

    if not txns:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 1rem">
          <div style="font-size:2.2rem;margin-bottom:0.6rem">💸</div>
          <div style="font-family:'Syne',sans-serif;font-size:0.95rem;color:#fff">No transactions yet</div>
          <div style="font-size:0.78rem;color:#8B8F9A;margin-top:4px">Payments will appear here once you're hired</div>
        </div>""", unsafe_allow_html=True)
        # Show demo transaction cards
        st.markdown('<div style="font-size:0.72rem;color:#545861;text-align:center;margin-bottom:0.8rem">— Demo preview —</div>', unsafe_allow_html=True)
        demos = [
            ("Social Media Manager","BrewBox Café",18000,"easypaisa","completed","2025-04-15"),
            ("Customer Support Rep","TechHive Solutions",22000,"jazzcash","pending","2025-04-28"),
        ]
        for jt, biz, amt, method, status, date in demos:
            sc,sbg,sl = STATUS_STYLE.get(status,("#8B8F9A","#252831","●"))
            m_icon = "📱" if method in ("easypaisa","jazzcash") else "🏦"
            m_label = {"easypaisa":"EasyPaisa","jazzcash":"JazzCash"}.get(method, method.title())
            st.markdown(f"""
            <div style="background:#1A1D24;border:1px solid #252831;border-radius:16px;padding:1rem 1.1rem;margin-bottom:0.6rem;opacity:0.5">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.4rem">
                <div style="flex:1;min-width:0;margin-right:0.5rem">
                  <div style="font-weight:700;font-size:0.85rem;color:#fff">{jt}</div>
                  <div style="color:#8B8F9A;font-size:0.73rem">{biz}</div>
                </div>
                <div style="text-align:right">
                  <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:0.93rem;color:#AAFF00">PKR {int(amt):,}</div>
                  <span style="background:{sbg};color:{sc};font-size:0.6rem;font-weight:700;padding:2px 7px;border-radius:20px">{sl}</span>
                </div>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#545861">
                <span>{m_icon} {m_label}</span><span>{date}</span>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        for txn in txns:
            sc,sbg,sl = STATUS_STYLE.get(txn["status"],("#8B8F9A","#252831","●"))
            method = txn["method"] or ""
            m_icon = "🏦" if method == "bank" else "📱"
            m_label = {"easypaisa":"EasyPaisa","jazzcash":"JazzCash","bank":"Bank Transfer"}.get(method, method.title() or "—")
            job_label = txn["jt"] or txn["plan"] or "Payment"
            biz_label = txn["business_name"] or "GigBridge"
            st.markdown(f"""
            <div style="background:#1A1D24;border:1px solid #252831;border-radius:16px;padding:1rem 1.1rem;margin-bottom:0.6rem">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.4rem">
                <div style="flex:1;min-width:0;margin-right:0.5rem">
                  <div style="font-weight:700;font-size:0.85rem;color:#fff">{job_label}</div>
                  <div style="color:#8B8F9A;font-size:0.73rem">{biz_label}</div>
                </div>
                <div style="text-align:right">
                  <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:0.93rem;color:#AAFF00">PKR {int(txn['amount']):,}</div>
                  <span style="background:{sbg};color:{sc};font-size:0.6rem;font-weight:700;padding:2px 7px;border-radius:20px">{sl}</span>
                </div>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#545861">
                <span>{m_icon} {m_label}</span><span>{txn['created_at'][:10]}</span>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Profile", key="txn_back"):
        st.session_state.screen = "student_profile"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    snav("student_profile")


# ─── ROUTER ────────────────────────────────────────────────────────────────────

def main():
    init_db()
    if "screen" not in st.session_state:
        st.session_state.screen = "landing"

    screen = st.session_state.get("screen","landing")

    if "user_id" not in st.session_state:
        if screen == "auth": show_auth()
        else: show_landing()
        return

    role = st.session_state.get("role","")
    if role == "student":
        {
            "student_home": show_student_home,
            "student_onboarding": show_onboarding,
            "student_ai_chat": show_ai_chat,
            "student_jobs": show_student_jobs,
            "job_detail": show_job_detail,
            "student_applications": show_student_applications,
            "student_profile": show_student_profile,
            "student_premium": show_student_premium,
            "student_cv": show_student_cv,
            "student_training": show_student_training,
            "student_transactions": show_student_transactions,
        }.get(screen, show_student_home)()
    elif role == "business":
        {
            "business_home": show_business_home,
            "business_post": show_business_post,
            "business_applicants": show_business_applicants,
            "business_profile": show_business_profile,
            "business_subscribe": show_business_subscribe,
        }.get(screen, show_business_home)()
    elif role == "admin":
        show_admin()
    else:
        st.session_state.clear(); st.rerun()

if __name__ == "__main__":
    main()
