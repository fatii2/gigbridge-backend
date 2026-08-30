"""
GigBridge — Complete Python/Flask Web App v2
Fixes: sign-in bug, file uploads displayed, subscription/trial system, admin dashboard
Run:  python app.py
Open: http://localhost:5000
"""

from flask import (Flask, request, redirect, url_for, session,
                   flash, send_from_directory, abort)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os, uuid
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "gigbridge-secret-2026-change-in-prod"

DB            = "gigbridge.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_IMG   = {"png", "jpg", "jpeg", "webp"}
ALLOWED_DOC   = {"png", "jpg", "jpeg", "pdf"}

for d in [UPLOAD_FOLDER, f"{UPLOAD_FOLDER}/ids", f"{UPLOAD_FOLDER}/logos"]:
    os.makedirs(d, exist_ok=True)

TRIAL_DAYS              = 5
BIZ_FREE_JOB_LIMIT      = 2

# ── Pricing (all PKR) ────────────────────────────────────────────────────────
STUDENT_FREE_PRICE      = 0
STUDENT_PREMIUM_PRICE   = 750      # mid-range of 500–1000
BIZ_STARTER_PRICE       = 0
BIZ_PRO_PRICE_PKR       = 5000     # mid-range of 5000–8000
BIZ_ENTERPRISE_PRICE    = 8000

# ── Cancellation: 15% × PKR 250 = PKR 37.50, floored to PKR 38 ──────────────
CANCELLATION_FEE_RATE   = 0.15
CANCELLATION_FEE_BASE   = 250
CANCELLATION_FEE        = int(CANCELLATION_FEE_RATE * CANCELLATION_FEE_BASE)  # = 37
CANCELLATION_WINDOW_DAYS= 7

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _migrate(db):
    """Safely add any missing columns/tables to an existing database."""
    migrations = [
        ("users",    "premium_tier",       "TEXT DEFAULT 'free'"),
        ("payments", "payment_type",        "TEXT DEFAULT 'subscription'"),
        ("jobs",     "booked_student_id",   "INTEGER DEFAULT NULL"),
        ("jobs",     "booked_at",           "TEXT DEFAULT NULL"),
    ]
    for table, col, col_def in migrations:
        existing = [r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()]
        if col not in existing:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")

    # Create cancellations table if missing
    db.execute("""
        CREATE TABLE IF NOT EXISTS cancellations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id         INTEGER REFERENCES jobs(id),
            cancelled_by   INTEGER REFERENCES users(id),
            cancelled_role TEXT,
            fee_charged    REAL DEFAULT 0,
            reason         TEXT DEFAULT '',
            created_at     TEXT DEFAULT (datetime('now'))
        )""")
    db.commit()

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        email      TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        role       TEXT NOT NULL CHECK(role IN ('student','business','admin')),
        trial_start TEXT DEFAULT (datetime('now')),
        plan       TEXT DEFAULT 'trial',
        plan_expires TEXT,
        premium_tier TEXT DEFAULT 'free',
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS students (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        full_name    TEXT NOT NULL,
        date_of_birth TEXT,
        cnic         TEXT UNIQUE NOT NULL,
        university   TEXT NOT NULL,
        id_card_path TEXT,
        skills       TEXT DEFAULT '',
        bio          TEXT DEFAULT '',
        wallet_method TEXT,
        wallet_number TEXT,
        total_gigs   INTEGER DEFAULT 0,
        total_earned REAL DEFAULT 0,
        avg_rating   REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS businesses (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
        business_name TEXT NOT NULL,
        industry      TEXT,
        ntn           TEXT,
        city          TEXT,
        logo_path     TEXT,
        description   TEXT DEFAULT '',
        website       TEXT DEFAULT '',
        total_posted  INTEGER DEFAULT 0,
        total_hired   INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id    INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
        title          TEXT NOT NULL,
        description    TEXT NOT NULL,
        job_type       TEXT NOT NULL,
        location       TEXT,
        is_remote      INTEGER DEFAULT 0,
        hours_per_day  TEXT,
        salary         REAL NOT NULL,
        salary_period  TEXT DEFAULT 'monthly',
        skills_required TEXT DEFAULT '',
        is_urgent      INTEGER DEFAULT 0,
        status         TEXT DEFAULT 'open',
        payment_method TEXT,
        booked_student_id INTEGER DEFAULT NULL,
        booked_at      TEXT DEFAULT NULL,
        created_at     TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS applications (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id     INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
        student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
        cover_note TEXT DEFAULT '',
        status     TEXT DEFAULT 'pending',
        applied_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS payments (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER REFERENCES users(id),
        amount       REAL NOT NULL,
        plan         TEXT NOT NULL,
        method       TEXT,
        payment_type TEXT DEFAULT 'subscription',
        status       TEXT DEFAULT 'completed',
        created_at   TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS cancellations (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id         INTEGER REFERENCES jobs(id),
        cancelled_by   INTEGER REFERENCES users(id),
        cancelled_role TEXT,
        fee_charged    REAL DEFAULT 0,
        reason         TEXT DEFAULT '',
        created_at     TEXT DEFAULT (datetime('now'))
    );
    """)
    db.commit()
    _migrate(db)   # safely add any new columns to existing databases
    if not db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        _seed(db)
    db.close()

def _seed(db):
    # Admin
    db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
               ("admin@gigbridge.pk", generate_password_hash("admin123"), "admin", "admin"))

    # Students
    for email, name, dob, cnic, uni, skills, bio, method, wallet in [
        ("sara@iba.edu.pk","Sara Ahmed","2002-03-15","42101-1234567-8","IBA Karachi","Social Media, Content Writing, Microsoft Office","Final year BBA student passionate about marketing.","easypaisa","03001234567"),
        ("hassan@fast.edu.pk","Hassan Raza","2001-07-22","42201-9876543-2","FAST NUCES","Python, Data Entry, Excel, SQL","CS student interested in data and automation.","jazzcash","03321234567"),
        ("aimen@ned.edu.pk","Aimen Siddiqui","2000-11-05","42301-5551234-9","NED University","Communication, Customer Service, Urdu Typing","Engineering student with strong communication skills.","easypaisa","03111234567"),
    ]:
        db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
                   (email, generate_password_hash("password123"), "student", "active"))
        uid = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
        db.execute("INSERT INTO students (user_id,full_name,date_of_birth,cnic,university,skills,bio,wallet_method,wallet_number) VALUES (?,?,?,?,?,?,?,?,?)",
                   (uid, name, dob, cnic, uni, skills, bio, method, wallet))

    # Businesses
    for email, bname, industry, ntn, city in [
        ("hr@brewbox.pk","BrewBox Café","Food & Beverage","NTN-1001001","Karachi"),
        ("jobs@techhive.pk","TechHive Solutions","Technology","NTN-2002002","Karachi"),
        ("careers@mediapulse.pk","MediaPulse PK","Media","NTN-3003003","Lahore"),
    ]:
        db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
                   (email, generate_password_hash("password123"), "business", "pro"))
        uid = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
        db.execute("INSERT INTO businesses (user_id,business_name,industry,ntn,city) VALUES (?,?,?,?,?)",
                   (uid, bname, industry, ntn, city))

    # Jobs
    for biz_id, title, desc, jtype, loc, remote, hours, salary, skills, urgent, pmethod in [
        (1,"Social Media Manager","Manage our Instagram, TikTok and Facebook. Create engaging content and grow our following.","Part-time","Clifton, Karachi",0,"4 hrs/day",18000,"Social Media, Canva, Content Writing",1,"easypaisa"),
        (2,"Junior Data Analyst","Analyze customer data, build Excel dashboards and present weekly reports.","Part-time","DHA, Karachi",1,"5 hrs/day",25000,"Excel, SQL, Python",0,"jazzcash"),
        (2,"Customer Support Rep","Handle inbound queries via chat and phone. CRM training provided.","Part-time","DHA, Karachi",0,"5 hrs/day",22000,"Communication, CRM",1,"easypaisa"),
        (3,"Content Writer (Urdu/English)","Write SEO blog articles in Urdu and English. Portfolio required.","Freelance","Remote",1,"Project-based",3000,"Writing, SEO, Urdu",0,"jazzcash"),
        (1,"Weekend Barista Assistant","Assist our head barista on weekends. No experience needed.","Weekend","Clifton, Karachi",0,"Sat & Sun",10000,"Hospitality, Punctuality",0,"easypaisa"),
        (2,"UI/UX Design Intern","Help design mobile app screens using Figma.","Internship","DHA, Karachi",1,"3 hrs/day",15000,"Figma, Canva, Design",1,"jazzcash"),
    ]:
        db.execute("INSERT INTO jobs (business_id,title,description,job_type,location,is_remote,hours_per_day,salary,skills_required,is_urgent,payment_method) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   (biz_id, title, desc, jtype, loc, remote, hours, salary, skills, urgent, pmethod))
        db.execute("UPDATE businesses SET total_posted=total_posted+1 WHERE id=?", (biz_id,))
    db.commit()

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def trial_days_left(user):
    try:
        start = datetime.strptime(user["trial_start"][:19], "%Y-%m-%d %H:%M:%S")
        ends  = start + timedelta(days=TRIAL_DAYS)
        left  = (ends - datetime.utcnow()).days
        return max(0, left)
    except:
        return 0

def is_subscription_active(user):
    plan = user["plan"]
    if plan in ("active", "pro", "admin", "trial"):
        if plan == "trial":
            return trial_days_left(user) > 0
        if plan in ("active", "pro"):
            exp = user["plan_expires"]
            if exp:
                return datetime.utcnow() < datetime.strptime(exp[:19], "%Y-%m-%d %H:%M:%S")
            return True   # no expiry = lifetime (seeded accounts)
        return True
    return False

def save_file(file_obj, subfolder, allowed_exts):
    if not file_obj or not file_obj.filename:
        return None
    ext = file_obj.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_exts:
        return None
    fname = f"{uuid.uuid4().hex}.{ext}"
    file_obj.save(os.path.join(UPLOAD_FOLDER, subfolder, fname))
    return fname

def get_user():
    if "user_id" not in session:
        return None
    db  = get_db()
    u   = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    db.close()
    return u

def get_student(uid=None):
    db = get_db()
    s  = db.execute("SELECT s.*,u.email,u.trial_start,u.plan,u.plan_expires FROM students s JOIN users u ON u.id=s.user_id WHERE s.user_id=?",
                    (uid or session["user_id"],)).fetchone()
    db.close()
    return s

def get_business(uid=None):
    db = get_db()
    b  = db.execute("SELECT b.*,u.email,u.trial_start,u.plan,u.plan_expires FROM businesses b JOIN users u ON u.id=b.user_id WHERE b.user_id=?",
                    (uid or session["user_id"],)).fetchone()
    db.close()
    return b

def initials(name):
    return "".join(p[0] for p in (name or "GB").split()[:2]).upper()

def avatar_bg(name):
    cols = ["#FF6B2B","#1B6FD4","#1A9E5E","#6B3BD4","#D43B1B","#B8860B"]
    return cols[sum(ord(c) for c in (name or "")) % len(cols)]

def fmt_salary(amt, period="monthly"):
    s = {"monthly":"/mo","weekly":"/wk","per project":"/project"}.get(period,"")
    return f"PKR {int(amt):,}{s}"

def time_ago(ds):
    if not ds: return ""
    try:
        d = datetime.strptime(ds[:19], "%Y-%m-%d %H:%M:%S")
        m = int((datetime.utcnow()-d).total_seconds()/60)
        if m < 60: return f"{m}m ago"
        if m < 1440: return f"{m//60}h ago"
        return f"{m//1440}d ago"
    except: return ""

def status_badge(s):
    M = {"pending":("b-gray","⏳ Pending"),"reviewed":("b-blue","👁 Reviewed"),
         "hired":("b-green","✅ Hired"),"rejected":("b-red","❌ Rejected"),
         "open":("b-green","🟢 Open"),"closed":("b-gray","Closed"),"filled":("b-orange","Filled")}
    c, l = M.get(s,("b-gray",s))
    return f'<span class="badge {c}">{l}</span>'

# ══════════════════════════════════════════════════════════════════════════════
# DECORATORS
# ══════════════════════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def d(*a,**k):
        if "user_id" not in session: return redirect(url_for("landing"))
        return f(*a,**k)
    return d

def student_required(f):
    @wraps(f)
    def d(*a,**k):
        if session.get("role") != "student": return redirect(url_for("landing"))
        return f(*a,**k)
    return d

def business_required(f):
    @wraps(f)
    def d(*a,**k):
        if session.get("role") != "business": return redirect(url_for("landing"))
        return f(*a,**k)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a,**k):
        if session.get("role") != "admin": return redirect(url_for("landing"))
        return f(*a,**k)
    return d

def subscription_required(f):
    """Redirect to paywall if trial expired and no active plan."""
    @wraps(f)
    def d(*a,**k):
        u = get_user()
        if u and u["role"] != "admin" and not is_subscription_active(u):
            return redirect(url_for("paywall"))
        return f(*a,**k)
    return d

# ══════════════════════════════════════════════════════════════════════════════
# SHARED HTML
# ══════════════════════════════════════════════════════════════════════════════

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --or:#FF6B2B;--orl:#FFF0E8;--dk:#0F0E0C;--wh:#FAFAF8;
  --gy:#6B6860;--lt:#F5F4F0;--bd:#E8E6E0;
  --gn:#1A9E5E;--gnl:#E4F7EE;--bl:#1B6FD4;--bll:#E4EEFF;
  --rd:#D43B1B;--rdl:#FEE8E4;--am:#B8860B;--aml:#FFF8E4;
  --fh:'Syne',sans-serif;--fb:'DM Sans',sans-serif;
}
html{font-size:15px}
body{font-family:var(--fb);background:var(--lt);color:var(--dk);min-height:100vh;-webkit-font-smoothing:antialiased}
.wrap{max-width:480px;margin:0 auto;min-height:100vh;background:var(--wh);box-shadow:0 0 60px rgba(0,0,0,.12);position:relative}

/* Navbar */
.nb{background:var(--wh);border-bottom:1px solid var(--bd);padding:.9rem 1.2rem;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.nb-logo{font-family:var(--fh);font-size:1.4rem;font-weight:800;letter-spacing:-1px;text-decoration:none;color:var(--dk)}
.nb-logo span{color:var(--or)}
.nb-av{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.78rem;color:#fff;text-decoration:none;flex-shrink:0}

/* Bottom nav */
.bn{background:var(--wh);border-top:1px solid var(--bd);display:flex;position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:480px;z-index:99}
.ni{flex:1;padding:.7rem .5rem;display:flex;flex-direction:column;align-items:center;gap:.18rem;color:var(--gy);font-size:.65rem;font-weight:600;text-decoration:none;transition:color .15s}
.ni.active{color:var(--or)}
.ni-icon{font-size:1.3rem;line-height:1}

/* Screen */
.sc{padding:1.2rem;padding-bottom:90px;background:var(--lt);min-height:calc(100vh - 58px)}

/* Buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:.4rem;padding:.6rem 1.2rem;border-radius:10px;border:none;font-family:var(--fb);font-size:.85rem;font-weight:600;cursor:pointer;transition:all .15s;text-decoration:none;white-space:nowrap}
.btn:hover{transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.bp{background:var(--or);color:#fff}.bp:hover{background:#e55a20}
.bo{background:transparent;border:1.5px solid var(--bd);color:var(--dk)}.bo:hover{border-color:var(--or);color:var(--or)}
.bs{background:var(--gnl);color:var(--gn);border:none}
.bd2{background:var(--rdl);color:var(--rd);border:none}
.bdk{background:var(--dk);color:#fff}.bdk:hover{background:#222}
.blg{padding:.85rem 2rem;font-size:1rem;border-radius:12px}
.bsm{padding:.38rem .85rem;font-size:.78rem}
.bbl{width:100%;margin-bottom:.7rem}
.btn[disabled]{opacity:.5;pointer-events:none}

/* Forms */
.fg{margin-bottom:1rem}
.fl{display:block;font-size:.79rem;font-weight:600;margin-bottom:.32rem}
.fi{width:100%;padding:.65rem .9rem;border:1.5px solid var(--bd);border-radius:10px;font-family:var(--fb);font-size:.88rem;color:var(--dk);background:var(--wh);transition:border .15s;-webkit-appearance:none}
.fi:focus{outline:none;border-color:var(--or)}
.fi::placeholder{color:#bbb}
.frow{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
select.fi{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236B6860' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right .9rem center;padding-right:2.5rem;background-color:var(--wh)}
textarea.fi{resize:vertical;min-height:85px}
.upload-z{border:2px dashed var(--bd);border-radius:12px;padding:1.3rem;text-align:center;cursor:pointer;transition:all .15s;background:var(--lt);display:block}
.upload-z:hover{border-color:var(--or);background:var(--orl)}
.upload-z.done{border-color:var(--gn);background:var(--gnl)}

/* Cards */
.card{background:var(--wh);border:1px solid var(--bd);border-radius:14px;padding:1.25rem;margin-bottom:.9rem}
.card-a{cursor:pointer;transition:all .2s}.card-a:hover{border-color:var(--or);box-shadow:0 4px 20px rgba(255,107,43,.1);transform:translateY(-2px)}
.card-a:hover .card-title{color:var(--or)}

/* Badges */
.badge{display:inline-flex;align-items:center;padding:.23rem .62rem;border-radius:20px;font-size:.71rem;font-weight:700}
.b-orange{background:var(--orl);color:var(--or)}
.b-green{background:var(--gnl);color:var(--gn)}
.b-blue{background:var(--bll);color:var(--bl)}
.b-gray{background:var(--lt);color:var(--gy);border:1px solid var(--bd)}
.b-red{background:var(--rdl);color:var(--rd)}
.b-amber{background:var(--aml);color:var(--am)}
.b-urg{background:var(--or);color:#fff;font-size:.61rem;padding:.12rem .4rem;margin-left:.25rem}

/* Stats */
.sg{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin-bottom:1.2rem}
.sc2{background:var(--wh);border:1px solid var(--bd);border-radius:14px;padding:1rem;text-align:center}
.sn{font-family:var(--fh);font-size:1.55rem;font-weight:800;color:var(--or)}
.sl{font-size:.72rem;color:var(--gy);margin-top:.12rem}

/* Hero */
.hero{background:var(--dk);border-radius:14px;padding:1.5rem;color:#fff;margin-bottom:1.2rem;position:relative;overflow:hidden}
.hero::after{content:'';position:absolute;right:-50px;top:-50px;width:180px;height:180px;background:var(--or);opacity:.12;border-radius:50%}
.hero h2{font-family:var(--fh);font-size:1.35rem;position:relative;z-index:1}
.hero p{color:#9E9C96;font-size:.81rem;margin-top:.2rem;position:relative;z-index:1}
.hero .btn{position:relative;z-index:1;margin-top:.85rem}

/* Rating */
.rb{background:var(--lt);border-radius:10px;height:7px;margin-top:.3rem}
.rf{background:var(--or);border-radius:10px;height:7px}

/* Talent card */
.tb{display:inline-flex;align-items:center;gap:.3rem;background:var(--orl);color:var(--or);font-size:.71rem;font-weight:700;padding:.25rem .62rem;border-radius:20px;margin-top:.3rem}
.stag{background:var(--lt);border:1px solid var(--bd);border-radius:20px;padding:.22rem .6rem;font-size:.71rem;font-weight:600;color:var(--gy);display:inline-block;margin:.2rem .2rem 0 0}

/* Flash */
.flash{padding:.75rem 1rem;border-radius:10px;font-size:.83rem;font-weight:500;margin:.5rem 1.2rem 0}
.f-success{background:var(--gnl);color:var(--gn)}
.f-error{background:var(--rdl);color:var(--rd)}
.f-info{background:var(--bll);color:var(--bl)}
.f-warning{background:var(--aml);color:var(--am)}

/* Trial banner */
.trial-bar{background:var(--aml);border-bottom:1px solid #e0cc8a;padding:.6rem 1.2rem;font-size:.8rem;font-weight:600;color:var(--am);display:flex;align-items:center;justify-content:space-between;gap:.5rem}

/* File preview */
.file-preview{display:flex;align-items:center;gap:.8rem;background:var(--lt);border:1px solid var(--bd);border-radius:10px;padding:.75rem 1rem;margin-top:.5rem}
.file-preview img{width:48px;height:48px;object-fit:cover;border-radius:8px;border:1px solid var(--bd)}
.file-icon{width:48px;height:48px;background:var(--rdl);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.4rem}

/* Misc */
.st{font-family:var(--fh);font-size:1.1rem;font-weight:700;margin-bottom:.85rem}
.av{border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-weight:800;color:#fff;flex-shrink:0}
.empty{text-align:center;padding:3rem 1rem;color:var(--gy)}
.ei{font-size:2.8rem;margin-bottom:.8rem}
.co-logo{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:#fff;flex-shrink:0}
.sal{font-family:var(--fh);font-size:1rem;font-weight:800;color:var(--or)}
.aw{padding:.75rem 1rem;border-radius:10px;background:var(--aml);color:var(--am);font-size:.81rem;margin-bottom:1rem}
hr{border:none;border-top:1px solid var(--bd);margin:1rem 0}
@keyframes fi{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.fade{animation:fi .3s ease}

/* Admin */
.adm-table{width:100%;border-collapse:collapse;font-size:.82rem}
.adm-table th{text-align:left;padding:.6rem .8rem;background:var(--lt);color:var(--gy);font-weight:700;font-size:.73rem;letter-spacing:.04em;border-bottom:1px solid var(--bd)}
.adm-table td{padding:.65rem .8rem;border-bottom:1px solid var(--bd);vertical-align:middle}
.adm-table tr:hover td{background:var(--lt)}
</style>
"""

def flashes_html():
    from flask import get_flashed_messages
    html = ""
    for cat, msg in get_flashed_messages(with_categories=True):
        html += f'<div class="flash f-{cat}">{msg}</div>'
    return html

def page(body, title="GigBridge"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="theme-color" content="#0F0E0C">
<title>{title} — GigBridge</title>
{CSS}
</head>
<body>
<div class="wrap">
{flashes_html()}
{body}
</div>
</body>
</html>"""

def navbar(back=None, profile_url=None, logo_url="/", ini="", color="#FF6B2B"):
    back_btn = f'<a href="{back}" style="color:var(--gy);font-size:1.2rem;text-decoration:none;padding:.2rem .5rem">←</a>' if back else '<div style="width:36px"></div>'
    av = f'<a class="nb-av" href="{profile_url}" style="background:{color}">{ini}</a>' if profile_url else '<div style="width:36px"></div>'
    return f"""<div class="nb">{back_btn}<a class="nb-logo" href="{logo_url}">Gig<span>Bridge</span></a>{av}</div>"""

def trial_banner(user):
    if user["plan"] != "trial": return ""
    left = trial_days_left(user)
    if left <= 0: return ""
    return f'<div class="trial-bar"><span>⏱ Free trial: <strong>{left} day{"s" if left!=1 else ""} left</strong></span><a href="/subscribe" class="btn bp bsm">Upgrade →</a></div>'

def snav(active):
    tabs = [("home","🏠","Home","/student/home"),("jobs","💼","Gigs","/student/jobs"),
            ("applications","📋","Applied","/student/applications"),("profile","👤","Profile","/student/profile")]
    return '<div class="bn">'+"".join(f'<a class="ni {"active" if t==active else ""}" href="{u}"><span class="ni-icon">{ic}</span>{lb}</a>' for t,ic,lb,u in tabs)+'</div>'

def bnav(active):
    tabs = [("home","🏠","Home","/business/home"),("post","➕","Post Gig","/business/post"),
            ("applicants","👥","Applicants","/business/applicants"),("profile","🏢","Profile","/business/profile")]
    return '<div class="bn">'+"".join(f'<a class="ni {"active" if t==active else ""}" href="{u}"><span class="ni-icon">{ic}</span>{lb}</a>' for t,ic,lb,u in tabs)+'</div>'

def file_preview_html(path, subfolder):
    if not path: return ""
    ext = path.rsplit(".",1)[-1].lower()
    url = f"/uploads/{subfolder}/{path}"
    if ext in ("jpg","jpeg","png","webp"):
        return f'<div class="file-preview"><img src="{url}" alt="uploaded"><div style="font-size:.82rem"><div style="font-weight:600">Uploaded ✓</div><div style="color:var(--gy);font-size:.76rem">{path[:30]}</div></div></div>'
    return f'<div class="file-preview"><div class="file-icon">📄</div><div style="font-size:.82rem"><div style="font-weight:600">Document uploaded ✓</div><div style="color:var(--gy);font-size:.76rem">{path[:30]}</div></div></div>'

# ══════════════════════════════════════════════════════════════════════════════
# UPLOADS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/uploads/<subfolder>/<filename>")
@login_required
def serve_upload(subfolder, filename):
    if subfolder not in ("ids","logos"): abort(404)
    # Students can only see their own ID; businesses can see logos; admins see all
    role = session.get("role","")
    if subfolder == "ids" and role not in ("admin",):
        # Only owner or business reviewing applicant
        db = get_db()
        s  = db.execute("SELECT id_card_path FROM students WHERE user_id=?", (session["user_id"],)).fetchone()
        db.close()
        if not (s and s["id_card_path"] == filename):
            abort(403)
    return send_from_directory(os.path.join(UPLOAD_FOLDER, subfolder), filename)

# ══════════════════════════════════════════════════════════════════════════════
# LANDING
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def landing():
    if "user_id" in session:
        r = session.get("role","")
        if r == "student":   return redirect(url_for("student_home"))
        if r == "business":  return redirect(url_for("business_home"))
        if r == "admin":     return redirect(url_for("admin_dashboard"))
    body = f"""
{navbar(logo_url="/")}
<div style="min-height:calc(100vh - 58px);background:var(--dk);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem;text-align:center;position:relative;overflow:hidden">
  <div style="position:absolute;top:-100px;right:-100px;width:360px;height:360px;background:var(--or);opacity:.1;border-radius:50%"></div>
  <div style="position:absolute;bottom:-80px;left:-80px;width:260px;height:260px;background:var(--or);opacity:.07;border-radius:50%"></div>
  <div style="position:relative;z-index:1;width:100%;max-width:340px">
    <div style="font-family:var(--fh);font-size:2.9rem;font-weight:800;letter-spacing:-2px;color:#fff;margin-bottom:.3rem">Gig<span style="color:var(--or)">Bridge</span></div>
    <p style="color:#9E9C96;font-size:.88rem;margin-bottom:2.5rem">Pakistan's smartest part-time job platform for students</p>
    <div style="display:flex;flex-direction:column;gap:1rem">
      <a href="/login?role=student" style="background:rgba(255,255,255,.06);border:1.5px solid rgba(255,255,255,.12);color:#fff;padding:1.4rem;border-radius:18px;display:flex;flex-direction:column;align-items:center;gap:.45rem;text-decoration:none">
        <span style="font-size:2.2rem">🎓</span>
        <span style="font-family:var(--fh);font-size:1.15rem;font-weight:700">I'm a Student</span>
        <span style="color:#9E9C96;font-size:.79rem">Find gigs, earn money, build your profile</span>
      </a>
      <a href="/login?role=business" style="background:rgba(255,255,255,.06);border:1.5px solid rgba(255,255,255,.12);color:#fff;padding:1.4rem;border-radius:18px;display:flex;flex-direction:column;align-items:center;gap:.45rem;text-decoration:none">
        <span style="font-size:2.2rem">🏢</span>
        <span style="font-family:var(--fh);font-size:1.15rem;font-weight:700">I'm a Business</span>
        <span style="color:#9E9C96;font-size:.79rem">Post gigs, hire verified students</span>
      </a>
    </div>
    <p style="color:#444;font-size:.73rem;margin-top:1.8rem">🔒 Verified students only &nbsp;·&nbsp; 💳 EasyPaisa & JazzCash &nbsp;·&nbsp; {TRIAL_DAYS}-day free trial</p>
  </div>
</div>"""
    return page(body, "Welcome")

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET","POST"])
def login():
    role = request.args.get("role","student")
    tab  = request.args.get("tab","signin")

    if request.method == "POST":
        action = request.form.get("action","")
        db = get_db()

        # ── Sign in ──────────────────────────────────────────────────────────
        if action == "signin":
            email = request.form.get("email","").strip().lower()
            pw    = request.form.get("password","")
            user  = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            db.close()
            if not user:
                flash("No account found with that email", "error")
                return redirect(url_for("login", role=role, tab="signin"))
            if not check_password_hash(user["password"], pw):
                flash("Incorrect password", "error")
                return redirect(url_for("login", role=role, tab="signin"))
            session["user_id"] = user["id"]
            session["role"]    = user["role"]
            flash(f"Welcome back! 👋", "success")
            if user["role"] == "admin":   return redirect(url_for("admin_dashboard"))
            if user["role"] == "student": return redirect(url_for("student_home"))
            return redirect(url_for("business_home"))

        # ── Student signup ───────────────────────────────────────────────────
        elif action == "student_signup":
            email = request.form.get("email","").strip().lower()
            pw    = request.form.get("password","")
            cnic  = request.form.get("cnic","").strip()
            name  = request.form.get("name","").strip()
            uni   = request.form.get("university","").strip()
            dob   = request.form.get("dob","")

            if not all([email, pw, cnic, name, uni]):
                flash("Please fill in all required fields", "error")
                db.close(); return redirect(url_for("login", role="student", tab="signup"))
            if len(pw) < 8:
                flash("Password must be at least 8 characters", "error")
                db.close(); return redirect(url_for("login", role="student", tab="signup"))
            if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
                flash("Email already registered — please sign in", "error")
                db.close(); return redirect(url_for("login", role="student", tab="signin"))
            if db.execute("SELECT 1 FROM students WHERE cnic=?", (cnic,)).fetchone():
                flash("CNIC already registered", "error")
                db.close(); return redirect(url_for("login", role="student", tab="signup"))

            id_card = save_file(request.files.get("id_card"), "ids", ALLOWED_DOC)
            if not id_card:
                flash("Please upload your university ID card (JPG, PNG or PDF)", "error")
                db.close(); return redirect(url_for("login", role="student", tab="signup"))

            db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
                       (email, generate_password_hash(pw), "student", "trial"))
            uid = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
            db.execute("INSERT INTO students (user_id,full_name,date_of_birth,cnic,university,id_card_path) VALUES (?,?,?,?,?,?)",
                       (uid, name, dob, cnic, uni, id_card))
            db.commit(); db.close()

            session["user_id"] = uid
            session["role"]    = "student"
            flash(f"Welcome to GigBridge! 🎉 Your {TRIAL_DAYS}-day free trial has started.", "success")
            return redirect(url_for("student_home"))

        # ── Business signup ──────────────────────────────────────────────────
        elif action == "biz_signup":
            email  = request.form.get("email","").strip().lower()
            pw     = request.form.get("password","")
            bname  = request.form.get("biz_name","").strip()
            industry = request.form.get("industry","")
            ntn    = request.form.get("ntn","").strip()
            city   = request.form.get("city","")

            if not all([email, pw, bname]):
                flash("Please fill in all required fields", "error")
                db.close(); return redirect(url_for("login", role="business", tab="signup"))
            if len(pw) < 8:
                flash("Password must be at least 8 characters", "error")
                db.close(); return redirect(url_for("login", role="business", tab="signup"))
            if db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
                flash("Email already registered — please sign in", "error")
                db.close(); return redirect(url_for("login", role="business", tab="signin"))

            logo = save_file(request.files.get("logo"), "logos", ALLOWED_IMG)

            db.execute("INSERT INTO users (email,password,role,plan) VALUES (?,?,?,?)",
                       (email, generate_password_hash(pw), "business", "trial"))
            uid = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
            db.execute("INSERT INTO businesses (user_id,business_name,industry,ntn,city,logo_path) VALUES (?,?,?,?,?,?)",
                       (uid, bname, industry, ntn, city, logo or ""))
            db.commit(); db.close()

            session["user_id"] = uid
            session["role"]    = "business"
            flash(f"Business registered! 🚀 Your {TRIAL_DAYS}-day free trial has started.", "success")
            return redirect(url_for("business_home"))

        db.close()
        return redirect(url_for("login", role=role, tab=tab))

    # ── GET: render form ──────────────────────────────────────────────────────
    is_s  = (role == "student")
    icon  = "🎓" if is_s else "🏢"
    label = "Student Portal" if is_s else "Business Portal"
    hint  = (f"sara@iba.edu.pk" if is_s else "hr@brewbox.pk") + " / password123"

    signin_form = f"""
<form method="POST" action="/login?role={role}&tab=signin">
  <input type="hidden" name="action" value="signin">
  <div class="fg"><label class="fl">Email</label><input class="fi" type="email" name="email" placeholder="{'student@uni.edu.pk' if is_s else 'hr@company.pk'}" required autocomplete="email"></div>
  <div class="fg"><label class="fl">Password</label><input class="fi" type="password" name="password" placeholder="••••••••" required autocomplete="current-password"></div>
  <button type="submit" class="btn bp blg bbl">Sign In →</button>
  <p style="text-align:center;font-size:.79rem;color:var(--gy);margin-top:.5rem">Demo: <strong>{hint}</strong></p>
</form>"""

    student_form = f"""
<form method="POST" action="/login?role=student&tab=signup" enctype="multipart/form-data">
  <input type="hidden" name="action" value="student_signup">
  <div class="frow">
    <div class="fg"><label class="fl">Full Name *</label><input class="fi" name="name" placeholder="Sara Ahmed" required></div>
    <div class="fg"><label class="fl">Date of Birth *</label><input class="fi" type="date" name="dob" required></div>
  </div>
  <div class="fg"><label class="fl">University Email *</label><input class="fi" type="email" name="email" placeholder="sara@iba.edu.pk" required autocomplete="email"></div>
  <div class="fg"><label class="fl">CNIC Number *</label><input class="fi" name="cnic" placeholder="42101-1234567-8" maxlength="15" required></div>
  <div class="fg"><label class="fl">University *</label>
    <select class="fi" name="university" required>
      <option value="">Select university</option>
      {''.join(f'<option>{u}</option>' for u in ["IBA Karachi","FAST NUCES","NED University","SZABIST","Bahria University","UIT Karachi","Sir Syed University","Hamdard University","Aga Khan University","Other"])}
    </select></div>
  <div class="fg"><label class="fl">Password *</label><input class="fi" type="password" name="password" placeholder="Min 8 characters" minlength="8" required autocomplete="new-password"></div>
  <div class="fg">
    <label class="fl">University ID Card * <span style="color:var(--gy);font-weight:400">(JPG/PNG/PDF)</span></label>
    <label class="upload-z" for="id_card" id="id_lbl">
      <div style="font-size:2rem;margin-bottom:.35rem">🪪</div>
      <div style="font-size:.82rem;color:var(--gy)">Click to upload · Max 5MB</div>
    </label>
    <input type="file" id="id_card" name="id_card" accept="image/*,.pdf" required style="display:none"
      onchange="let l=document.getElementById('id_lbl');l.className='upload-z done';l.innerHTML='<div style=\\'font-size:2rem\\'>✅</div><div style=\\'font-size:.82rem;color:var(--gn);font-weight:600\\'>' + this.files[0].name + '</div>'">
  </div>
  <button type="submit" class="btn bp blg bbl">Create My Profile →</button>
  <p style="text-align:center;font-size:.78rem;color:var(--gy);margin-top:.4rem">{TRIAL_DAYS}-day free trial · No credit card needed</p>
</form>"""

    biz_form = f"""
<form method="POST" action="/login?role=business&tab=signup" enctype="multipart/form-data">
  <input type="hidden" name="action" value="biz_signup">
  <div class="fg"><label class="fl">Business Name *</label><input class="fi" name="biz_name" placeholder="TechHive Solutions" required></div>
  <div class="frow">
    <div class="fg"><label class="fl">Industry *</label>
      <select class="fi" name="industry">{''.join(f'<option>{i}</option>' for i in ["Technology","Retail","Food & Beverage","Media","Logistics","Events","Other"])}</select></div>
    <div class="fg"><label class="fl">City *</label>
      <select class="fi" name="city">{''.join(f'<option>{c}</option>' for c in ["Karachi","Lahore","Islamabad","Rawalpindi","Peshawar","Quetta"])}</select></div>
  </div>
  <div class="fg"><label class="fl">Business Email *</label><input class="fi" type="email" name="email" placeholder="hr@company.pk" required autocomplete="email"></div>
  <div class="fg"><label class="fl">NTN Number</label><input class="fi" name="ntn" placeholder="NTN-1234567"></div>
  <div class="fg"><label class="fl">Password *</label><input class="fi" type="password" name="password" placeholder="Min 8 characters" minlength="8" required autocomplete="new-password"></div>
  <div class="fg">
    <label class="fl">Business Logo <span style="color:var(--gy);font-weight:400">(optional)</span></label>
    <label class="upload-z" for="logo" id="logo_lbl">
      <div style="font-size:2rem;margin-bottom:.35rem">🏢</div>
      <div style="font-size:.82rem;color:var(--gy)">Click to upload · PNG/JPG</div>
    </label>
    <input type="file" id="logo" name="logo" accept="image/*" style="display:none"
      onchange="let l=document.getElementById('logo_lbl');l.className='upload-z done';l.innerHTML='<div style=\\'font-size:2rem\\'>✅</div><div style=\\'font-size:.82rem;color:var(--gn);font-weight:600\\'>' + this.files[0].name + '</div>'">
  </div>
  <button type="submit" class="btn bp blg bbl">Register My Business →</button>
  <p style="text-align:center;font-size:.78rem;color:var(--gy);margin-top:.4rem">{TRIAL_DAYS}-day free trial · No credit card needed</p>
</form>"""

    form = signin_form if tab == "signin" else (student_form if is_s else biz_form)
    tab_style = lambda t: "background:var(--wh);color:var(--dk);box-shadow:0 1px 4px rgba(0,0,0,.08)" if tab==t else "background:transparent;color:var(--gy)"

    body = f"""
{navbar(back="/")}
<div style="padding:1.3rem;background:var(--lt);min-height:calc(100vh - 58px)">
  <div style="background:var(--wh);border:1px solid var(--bd);border-radius:14px;padding:1.7rem">
    <div style="text-align:center;margin-bottom:1.4rem">
      <div style="font-size:2.1rem;margin-bottom:.35rem">{icon}</div>
      <h2 style="font-family:var(--fh);font-size:1.45rem;font-weight:800">{label}</h2>
      <p style="color:var(--gy);font-size:.83rem">Join Pakistan's top student gig platform</p>
    </div>
    <div style="display:flex;gap:.4rem;background:var(--lt);padding:.3rem;border-radius:10px;margin-bottom:1.25rem">
      <a href="/login?role={role}&tab=signin" style="flex:1;padding:.5rem;border-radius:8px;text-align:center;text-decoration:none;font-size:.81rem;font-weight:600;transition:all .15s;{tab_style('signin')}">Sign In</a>
      <a href="/login?role={role}&tab=signup" style="flex:1;padding:.5rem;border-radius:8px;text-align:center;text-decoration:none;font-size:.81rem;font-weight:600;transition:all .15s;{tab_style('signup')}">Sign Up</a>
    </div>
    {form}
    <p style="text-align:center;margin-top:.8rem;font-size:.8rem;color:var(--gy)"><a href="/" style="color:var(--or)">← Back to home</a></p>
  </div>
</div>"""
    return page(body, label)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

# ══════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION / PAYWALL
# ══════════════════════════════════════════════════════════════════════════════


def _paywall_plans(role):
    """Build subscription plan cards — new tiered pricing."""
    is_student = (role == "student")

    def card(border, bg, name, price, feats, plan_val, highlight=False):
        badge = '<span style="background:var(--or);color:#fff;font-size:.66rem;font-weight:700;padding:.18rem .55rem;border-radius:20px;margin-left:.4rem">POPULAR</span>' if highlight else ''
        feat_html = "".join(f'<div style="display:flex;gap:.4rem;align-items:flex-start;margin-bottom:.25rem"><span style="color:var(--gn);flex-shrink:0">✓</span><span>{f}</span></div>' for f in feats)
        pay_btns = (
            f'<form method="POST" action="/subscribe" style="display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.8rem">'
            f'<input type="hidden" name="plan" value="{plan_val}">'
            f'<button name="method" value="easypaisa" type="submit" class="btn bp bsm">EasyPaisa</button>'
            f'<button name="method" value="jazzcash"  type="submit" class="btn bo bsm">JazzCash</button>'
            f'</form>'
        ) if plan_val != "free" else (
            f'<form method="POST" action="/subscribe" style="margin-top:.8rem">'
            f'<input type="hidden" name="plan" value="free">'
            f'<button type="submit" class="btn bs bbl">Continue Free →</button>'
            f'</form>'
        )
        return (
            f'<div style="border:{border};border-radius:14px;padding:1.2rem;margin-bottom:.9rem;background:{bg}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.55rem">'
            f'<strong style="font-family:var(--fh);font-size:1rem">{name}{badge}</strong>'
            f'<span style="font-weight:800;color:{"var(--or)" if highlight else "var(--dk)"}">{price}</span></div>'
            f'<div style="font-size:.8rem;color:var(--gy);line-height:1.9">{feat_html}</div>'
            f'{pay_btns}</div>'
        )

    if is_student:
        return (
            card("1px solid var(--bd)", "var(--wh)", "Free",
                 "PKR 0",
                 ["Browse 3 gigs/day", "Apply to 1 gig/day", "Basic profile"],
                 "free") +
            card("2px solid var(--or)", "var(--orl)", "Student Premium 🔥",
                 f"PKR {STUDENT_PREMIUM_PRICE:,}/month",
                 ["Unlimited browsing & applications",
                  "Priority matching — appear first to employers",
                  "CV optimisation tools",
                  "Access to training programs",
                  "Premium verified badge on profile",
                  "Early access to urgent high-pay gigs"],
                 "student_premium", highlight=True)
        )
    else:
        return (
            card("1px solid var(--bd)", "var(--wh)", "Starter Free",
                 "PKR 0",
                 [f"Post up to {BIZ_FREE_JOB_LIMIT} gigs/month", "Access basic student pool", "Standard matching"],
                 "free") +
            card("2px solid var(--or)", "var(--orl)", "Business Pro 🔥",
                 f"PKR {BIZ_PRO_PRICE_PKR:,}/month",
                 ["Unlimited gig postings",
                  "Full student pool access with filters",
                  "Priority listing — gigs shown first",
                  "Applicant shortlisting tools",
                  "Dedicated support channel"],
                 "biz_pro", highlight=True) +
            card("1px solid var(--bd)", "var(--wh)", "Business Enterprise",
                 f"PKR {BIZ_ENTERPRISE_PRICE:,}/month",
                 ["Everything in Pro",
                  "Bulk hiring — post unlimited urgent gigs",
                  "Dedicated account manager",
                  "Monthly talent pipeline reports",
                  "Custom SLA & invoice billing"],
                 "biz_enterprise")
        )

@app.route("/paywall")
@login_required
def paywall():
    u = get_user()
    role = u["role"]
    body = f"""
{navbar(back="/")}
<div style="padding:1.3rem;background:var(--lt);min-height:calc(100vh - 58px)">
  <div style="background:var(--dk);border-radius:14px;padding:2rem;text-align:center;margin-bottom:1.2rem;color:#fff">
    <div style="font-size:2.5rem;margin-bottom:.5rem">⏰</div>
    <h2 style="font-family:var(--fh);font-size:1.5rem;font-weight:800">Your free trial has ended</h2>
    <p style="color:#9E9C96;font-size:.85rem;margin-top:.4rem">Choose a plan to continue using GigBridge</p>
  </div>
  {_paywall_plans(role)}
  <div style="border:1px solid var(--bd);border-radius:14px;padding:1.2rem;margin-bottom:.9rem;background:var(--wh)">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem">
      <strong style="font-family:var(--fh)">Enterprise</strong>
      <span style="font-weight:800">Custom</span>
    </div>
    <div style="font-size:.8rem;color:var(--gy)">Everything in Pro + bulk hiring + account manager</div>
    <a href="mailto:hello@gigbridge.pk" class="btn bo bbl" style="margin-top:.8rem">Contact Sales →</a>
  </div>
  <div style="background:var(--lt);border-radius:12px;padding:1rem;font-size:.79rem;color:var(--gy);text-align:center;line-height:1.8">
    ⚠️ Cancellation policy: bookings cancelled within <strong>{CANCELLATION_WINDOW_DAYS} days</strong> incur a fee of PKR {CANCELLATION_FEE}
  </div>
</div>"""
    return page(body, "Choose a Plan")

@app.route("/subscribe", methods=["GET"])
@login_required
def subscribe_page():
    return redirect(url_for("paywall"))

@app.route("/subscribe", methods=["POST"])
@login_required
def subscribe():
    plan   = request.form.get("plan", "free")
    method = request.form.get("method", "easypaisa")
    u      = get_user()
    role   = u["role"]
    db     = get_db()

    # ── Price lookup ────────────────────────────────────────────────────────
    PRICES = {
        "free":             0,
        "student_premium":  STUDENT_PREMIUM_PRICE,
        "biz_pro":          BIZ_PRO_PRICE_PKR,
        "biz_enterprise":   BIZ_ENTERPRISE_PRICE,
    }
    amt = PRICES.get(plan, 0)

    # ── Plan label & tier mapping ────────────────────────────────────────────
    PLAN_STATUS = {
        "free":             "active",
        "student_premium":  "premium",
        "biz_pro":          "pro",
        "biz_enterprise":   "enterprise",
    }
    new_status = PLAN_STATUS.get(plan, "active")
    expires = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S") if amt > 0 else None

    db.execute("UPDATE users SET plan=?, plan_expires=?, premium_tier=? WHERE id=?",
               (new_status, expires, plan, u["id"]))

    if amt > 0:
        ptype = "student_premium" if role == "student" else "business_subscription"
        db.execute("INSERT INTO payments (user_id,amount,plan,method,payment_type) VALUES (?,?,?,?,?)",
                   (u["id"], amt, plan, method, ptype))
        db.commit(); db.close()
        flash(f"🎉 {plan.replace('_',' ').title()} activated! PKR {amt:,} paid via {method.title()}. Valid 30 days.", "success")
    else:
        db.commit(); db.close()
        flash("You're on the Free plan. Upgrade anytime for more features.", "info")

    return redirect(url_for("student_home" if role == "student" else "business_home"))

# ══════════════════════════════════════════════════════════════════════════════
# STUDENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/student/home")
@student_required
@subscription_required
def student_home():
    s  = get_student()
    u  = get_user()
    db = get_db()
    app_count  = db.execute("SELECT COUNT(*) FROM applications WHERE student_id=?", (s["id"],)).fetchone()[0]
    hired_count= db.execute("SELECT COUNT(*) FROM applications WHERE student_id=? AND status='hired'", (s["id"],)).fetchone()[0]
    urgent     = db.execute("SELECT j.*,b.business_name FROM jobs j JOIN businesses b ON b.id=j.business_id WHERE j.status='open' AND j.is_urgent=1 ORDER BY j.created_at DESC LIMIT 2").fetchall()
    db.close()

    skills = [x.strip() for x in (s["skills"] or "").split(",") if x.strip()]
    comp   = sum([20, 10*(bool(s["skills"])), 10*(bool(s["bio"])), 20*(bool(s["wallet_method"])),
                  10*(bool(s["id_card_path"])), 10, 10*(bool(s["date_of_birth"]))])
    comp   = min(comp, 100)

    urg_html = "".join(_job_card(j) for j in urgent)
    body = f"""
{navbar(profile_url="/student/profile", ini=initials(s['full_name']), color=avatar_bg(s['full_name']))}
{trial_banner(u)}
<div class="sc fade">
  <div class="hero">
    <p style="color:#9E9C96;font-size:.79rem;margin-bottom:.15rem">Welcome back 👋</p>
    <h2>{s['full_name'].split()[0]}'s Dashboard</h2>
    <p>{s['university']} · <span style="color:#4CAF50">✓ Verified</span></p>
    <a href="/student/jobs" class="btn bp bsm">Browse Gigs →</a>
  </div>
  <div class="sg">
    <div class="sc2"><div class="sn">{app_count}</div><div class="sl">Applied</div></div>
    <div class="sc2"><div class="sn">{hired_count}</div><div class="sl">Hired</div></div>
    <div class="sc2"><div class="sn">PKR {int(s['total_earned']):,}</div><div class="sl">Earned</div></div>
  </div>
  <div class="card">
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">
      <div class="av" style="width:54px;height:54px;font-size:1.1rem;background:{avatar_bg(s['full_name'])}">{initials(s['full_name'])}</div>
      <div>
        <div style="font-weight:700;font-size:1rem">{s['full_name']}</div>
        <div style="color:var(--gy);font-size:.81rem">{s['university']}</div>
        <div class="tb">⭐ Talent Card</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:.9rem">
      <div><div style="font-size:.73rem;color:var(--gy);margin-bottom:.22rem">Rating</div>
        <div style="font-weight:700;font-size:.87rem">{s['avg_rating']:.1f} / 5.0</div>
        <div class="rb"><div class="rf" style="width:{s['avg_rating']/5*100:.0f}%"></div></div></div>
      <div><div style="font-size:.73rem;color:var(--gy);margin-bottom:.22rem">Profile</div>
        <div style="font-weight:700;font-size:.87rem">{comp}%</div>
        <div class="rb"><div class="rf" style="width:{comp}%"></div></div></div>
    </div>
    <div style="font-size:.72rem;color:var(--gy);font-weight:700;letter-spacing:.05em;margin-bottom:.4rem">SKILLS</div>
    <div>{''.join(f'<span class="stag">{sk}</span>' for sk in skills[:5]) or '<a href="/student/profile" style="font-size:.82rem;color:var(--or)">Add your skills →</a>'}</div>
    <hr>
    <a href="/student/profile#wallet" class="btn bo bbl">💳 Link EasyPaisa / JazzCash</a>
  </div>
  {f'<div class="st">🔥 Urgent Gigs</div>{urg_html}' if urg_html else ''}
</div>
{snav("home")}"""
    return page(body, "Home")

def _job_card(j):
    COLORS = {"BrewBox":"#FF6B2B","TechHive":"#6B3BD4","MediaPulse":"#1B6FD4","Lenscraft":"#1A9E5E"}
    color  = next((v for k,v in COLORS.items() if k in (j["business_name"] or "")), avatar_bg(j["business_name"] or ""))
    logo   = initials(j["business_name"] or "")
    skills = [x.strip() for x in (j["skills_required"] or "").split(",") if x.strip()][:3]
    urg    = '<span class="badge b-urg">URGENT</span>' if j["is_urgent"] else ""
    return f"""
<div class="card card-a" onclick="location.href='/job/{j['id']}'">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.7rem">
    <div style="display:flex;gap:.8rem;align-items:center;flex:1;min-width:0">
      <div class="co-logo" style="background:{color}">{logo}</div>
      <div style="min-width:0">
        <div class="card-title" style="font-weight:700;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{j['title']} {urg}</div>
        <div style="color:var(--gy);font-size:.78rem">{j['business_name']} · {j['location'] or 'Remote'}</div>
      </div>
    </div>
    <div class="sal" style="white-space:nowrap;margin-left:.5rem">{fmt_salary(j['salary'], j['salary_period'])}</div>
  </div>
  <div style="display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:.7rem">
    <span class="badge b-blue">{j['job_type']}</span>
    <span class="badge b-gray">⏱ {j['hours_per_day'] or 'Flexible'}</span>
    {''.join(f'<span class="badge b-orange">{s}</span>' for s in skills)}
    <span class="badge b-gray">{time_ago(j['created_at'])}</span>
  </div>
  <p style="font-size:.81rem;color:var(--gy);line-height:1.5;margin-bottom:.7rem">{(j['description'] or '')[:110]}…</p>
  <a href="/job/{j['id']}" class="btn bp bsm" onclick="event.stopPropagation()">View & Apply →</a>
</div>"""

@app.route("/student/jobs")
@student_required
@subscription_required
def student_jobs():
    jtype  = request.args.get("type","All")
    search = request.args.get("q","").strip()
    db = get_db()
    q  = "SELECT j.*,b.business_name FROM jobs j JOIN businesses b ON b.id=j.business_id WHERE j.status='open'"
    p  = []
    if jtype != "All": q += " AND j.job_type=?"; p.append(jtype)
    if search: q += " AND (j.title LIKE ? OR j.description LIKE ?)"; p += [f"%{search}%",f"%{search}%"]
    q += " ORDER BY j.is_urgent DESC, j.created_at DESC"
    jobs = db.execute(q, p).fetchall()
    db.close()

    chips = "".join(f'<a href="/student/jobs?type={t}" style="padding:.38rem .9rem;border-radius:20px;border:1.5px solid {"var(--dk)" if t==jtype else "var(--bd)"};background:{"var(--dk)" if t==jtype else "var(--wh)"};color:{"#fff" if t==jtype else "var(--dk)"};font-size:.77rem;font-weight:600;white-space:nowrap;text-decoration:none">{t}</a>'
                for t in ["All","Part-time","Freelance","Weekend","Internship"])
    body = f"""
{navbar(profile_url="/student/profile", ini=initials(get_student()['full_name']), color=avatar_bg(get_student()['full_name']))}
<div class="sc fade">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem">
    <div class="st" style="margin-bottom:0">All Gigs</div>
    <span style="font-size:.79rem;color:var(--gy)">{len(jobs)} available</span>
  </div>
  <form method="GET" action="/student/jobs" style="margin-bottom:.9rem;display:flex;gap:.5rem">
    <input class="fi" name="q" value="{search}" placeholder="Search gigs…" style="flex:1">
    <button type="submit" class="btn bp bsm">Search</button>
  </form>
  <div style="display:flex;gap:.5rem;overflow-x:auto;padding-bottom:.3rem;margin-bottom:1rem;scrollbar-width:none">{chips}</div>
  {''.join(_job_card(j) for j in jobs) if jobs else '<div class="empty"><div class="ei">💼</div><p>No gigs found</p></div>'}
</div>
{snav("jobs")}"""
    return page(body, "Browse Gigs")

@app.route("/job/<int:jid>")
@login_required
@subscription_required
def job_detail(jid):
    db  = get_db()
    job = db.execute("SELECT j.*,b.business_name FROM jobs j JOIN businesses b ON b.id=j.business_id WHERE j.id=?", (jid,)).fetchone()
    if not job: db.close(); return redirect(url_for("student_jobs"))

    already = False
    if session.get("role") == "student":
        s = db.execute("SELECT id FROM students WHERE user_id=?", (session["user_id"],)).fetchone()
        if s: already = bool(db.execute("SELECT 1 FROM applications WHERE job_id=? AND student_id=?", (jid, s["id"])).fetchone())
    db.close()

    skills = [x.strip() for x in (job["skills_required"] or "").split(",") if x.strip()]
    COLORS = {"BrewBox":"#FF6B2B","TechHive":"#6B3BD4","MediaPulse":"#1B6FD4"}
    color  = next((v for k,v in COLORS.items() if k in (job["business_name"] or "")), avatar_bg(job["business_name"] or ""))
    back   = "/student/jobs" if session.get("role")=="student" else "/business/home"

    if session.get("role") == "student":
        if already:
            apply_html = '<button class="btn bs blg bbl" disabled>✓ Already Applied</button>'
        else:
            apply_html = f"""
<form method="POST" action="/job/{jid}/apply">
  <div class="fg"><label class="fl">Cover Note <span style="color:var(--gy);font-weight:400">(optional)</span></label>
    <textarea class="fi" name="cover_note" rows="3" placeholder="Tell them why you're a great fit…"></textarea></div>
  <button type="submit" class="btn bp blg bbl">Apply Now →</button>
</form>"""
    else:
        apply_html = f'<a href="{back}" class="btn bo bbl">← Back</a>'

    s = get_student() if session.get("role")=="student" else None
    nav_html = snav("jobs") if session.get("role")=="student" else bnav("home")
    nav_bar  = navbar(back=back, profile_url=("/student/profile" if session.get("role")=="student" else "/business/profile"),
                      ini=initials(s["full_name"] if s else get_business()["business_name"]),
                      color=avatar_bg(s["full_name"] if s else get_business()["business_name"]))
    body = f"""
{nav_bar}
<div style="padding:1.2rem;background:var(--lt);min-height:calc(100vh - 58px)">
  <div class="card fade">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;gap:.5rem">
      <div style="display:flex;gap:.8rem;align-items:center;flex:1;min-width:0">
        <div class="co-logo" style="background:{color};width:50px;height:50px;border-radius:14px">{initials(job['business_name'])}</div>
        <div style="min-width:0">
          <h2 style="font-family:var(--fh);font-size:1.15rem;font-weight:800;margin-bottom:.12rem">{job['title']}</h2>
          <div style="color:var(--gy);font-size:.81rem">{job['business_name']} · {job['location'] or 'Remote'}</div>
        </div>
      </div>
      <div class="sal" style="font-size:1.1rem;white-space:nowrap">{fmt_salary(job['salary'], job['salary_period'])}</div>
    </div>
    <div style="display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:1rem">
      <span class="badge b-blue">{job['job_type']}</span>
      <span class="badge b-gray">⏱ {job['hours_per_day'] or 'Flexible'}</span>
      {'<span class="badge b-urg">URGENT</span>' if job['is_urgent'] else ''}
      {status_badge(job['status'])}
    </div>
    <p style="font-size:.88rem;line-height:1.7;color:var(--gy);margin-bottom:1rem">{job['description']}</p>
    {('<div style="margin-bottom:1rem"><div style="font-size:.72rem;font-weight:700;color:var(--gy);letter-spacing:.05em;margin-bottom:.45rem">SKILLS REQUIRED</div><div>' + ''.join(f'<span class="stag">{s}</span>' for s in skills) + '</div></div>') if skills else ''}
    <div class="aw">💳 Salary paid via {'EasyPaisa' if job['payment_method']=='easypaisa' else 'JazzCash'} · 5% platform fee applies</div>
    {apply_html}
  </div>
</div>
{nav_html}"""
    return page(body, job["title"])

@app.route("/job/<int:jid>/apply", methods=["POST"])
@student_required
@subscription_required
def apply_job(jid):
    db = get_db()
    s  = db.execute("SELECT id FROM students WHERE user_id=?", (session["user_id"],)).fetchone()
    if db.execute("SELECT 1 FROM applications WHERE job_id=? AND student_id=?", (jid, s["id"])).fetchone():
        flash("You already applied for this job", "error")
    else:
        db.execute("INSERT INTO applications (job_id,student_id,cover_note) VALUES (?,?,?)",
                   (jid, s["id"], request.form.get("cover_note","")))
        db.commit()
        flash("Application submitted! ✅ The business will review your Talent Card.", "success")
    db.close()
    return redirect(url_for("student_applications"))

# ── Cancellation (within 7 days of booking) ──────────────────────────────────
@app.route("/job/<int:jid>/cancel", methods=["POST"])
@login_required
@subscription_required
def cancel_booking(jid):
    db  = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not job:
        db.close(); flash("Gig not found.", "error")
        return redirect(url_for("student_home" if session.get("role")=="student" else "business_home"))

    booked_at_str = job["booked_at"]
    if not booked_at_str:
        db.close(); flash("This gig has no active booking to cancel.", "error")
        return redirect(url_for("student_home" if session.get("role")=="student" else "business_home"))

    booked_at = datetime.strptime(booked_at_str[:19], "%Y-%m-%d %H:%M:%S")
    days_since = (datetime.utcnow() - booked_at).days
    u    = get_user()
    role = session.get("role")
    fee  = 0
    reason = request.form.get("reason", "")

    if days_since <= CANCELLATION_WINDOW_DAYS:
        fee = CANCELLATION_FEE
        db.execute("INSERT INTO payments (user_id,amount,plan,method,payment_type) VALUES (?,?,?,?,?)",
                   (u["id"], fee, "cancellation_fee", "platform", "cancellation"))
        db.execute("INSERT INTO cancellations (job_id,cancelled_by,cancelled_role,fee_charged,reason) VALUES (?,?,?,?,?)",
                   (jid, u["id"], role, fee, reason))
        db.execute("UPDATE jobs SET status='open', booked_student_id=NULL, booked_at=NULL WHERE id=?", (jid,))
        db.commit(); db.close()
        flash(f"⚠️ Booking cancelled within {CANCELLATION_WINDOW_DAYS} days. Cancellation fee of PKR {fee} has been charged.", "error")
    else:
        db.execute("INSERT INTO cancellations (job_id,cancelled_by,cancelled_role,fee_charged,reason) VALUES (?,?,?,?,?)",
                   (jid, u["id"], role, 0, reason))
        db.execute("UPDATE jobs SET status='open', booked_student_id=NULL, booked_at=NULL WHERE id=?", (jid,))
        db.commit(); db.close()
        flash("Booking cancelled. No fee charged (outside the 7-day window).", "success")

    return redirect(url_for("student_applications" if role=="student" else "business_applicants"))

@app.route("/student/applications")
@student_required
@subscription_required
def student_applications():
    s  = get_student()
    db = get_db()
    apps = db.execute("""SELECT a.*,j.title as jt,j.salary,j.salary_period,j.job_type,b.business_name
        FROM applications a JOIN jobs j ON j.id=a.job_id JOIN businesses b ON b.id=j.business_id
        WHERE a.student_id=? ORDER BY a.applied_at DESC""", (s["id"],)).fetchall()
    db.close()
    cards = "".join(f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem">
    <div style="font-weight:700">{a['jt']}</div>{status_badge(a['status'])}
  </div>
  <div style="color:var(--gy);font-size:.81rem">{a['business_name']} · {fmt_salary(a['salary'],a['salary_period'])}</div>
  <div style="color:var(--gy);font-size:.76rem;margin-top:.25rem">{a['job_type']} · Applied {time_ago(a['applied_at'])}</div>
  {f'<p style="font-size:.81rem;color:var(--gy);margin-top:.45rem;font-style:italic">"{a["cover_note"]}"</p>' if a['cover_note'] else ''}
  {f'''<details style="margin-top:.6rem"><summary style="font-size:.78rem;color:var(--rd);cursor:pointer;font-weight:600">Cancel Booking</summary>
  <div style="background:var(--rdl);border-radius:8px;padding:.7rem;margin-top:.4rem">
    <p style="font-size:.76rem;color:var(--rd);margin-bottom:.5rem">⚠️ Cancelling within 7 days of booking incurs a PKR {CANCELLATION_FEE} fee.</p>
    <form method="POST" action="/job/{a['job_id']}/cancel">
      <input class="fi" name="reason" placeholder="Reason for cancellation" style="font-size:.8rem;margin-bottom:.4rem">
      <button type="submit" class="btn bsm" style="background:var(--rd);color:#fff;border:none">Confirm Cancel</button>
    </form>
  </div></details>''' if a['status']=='hired' else ''}
</div>""" for a in apps)
    body = f"""
{navbar(profile_url="/student/profile", ini=initials(s['full_name']), color=avatar_bg(s['full_name']))}
<div class="sc fade">
  <div class="st">My Applications</div>
  {cards or '<div class="empty"><div class="ei">📋</div><p>No applications yet.<br>Browse gigs and apply!</p><a href="/student/jobs" class="btn bp" style="margin-top:1rem">Find Gigs →</a></div>'}
</div>
{snav("applications")}"""
    return page(body, "My Applications")

@app.route("/student/profile", methods=["GET","POST"])
@student_required
@subscription_required
def student_profile():
    s = get_student()
    u = get_user()
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "profile":
            db.execute("UPDATE students SET skills=?,bio=? WHERE user_id=?",
                       (request.form.get("skills",""), request.form.get("bio",""), session["user_id"]))
            flash("Profile saved! ✅", "success")
        elif action == "wallet":
            db.execute("UPDATE students SET wallet_method=?,wallet_number=? WHERE user_id=?",
                       (request.form.get("method",""), request.form.get("wallet_number",""), session["user_id"]))
            flash("Wallet linked! 💳", "success")
        db.commit(); db.close()
        return redirect(url_for("student_profile") + "#wallet" if request.form.get("action")=="wallet" else url_for("student_profile"))
    db.close()
    comp = min(100, sum([20, 10*(bool(s["skills"])), 10*(bool(s["bio"])), 20*(bool(s["wallet_method"])),
                         10*(bool(s["id_card_path"])), 10, 10*(bool(s["date_of_birth"]))]))
    plan_badge = {"trial": f'<span class="badge b-amber">⏱ Trial ({trial_days_left(u)}d left)</span>',
                  "active": '<span class="badge b-green">✅ Pro</span>',
                  "pro":    '<span class="badge b-green">✅ Pro</span>'}.get(u["plan"], '<span class="badge b-gray">Free</span>')
    body = f"""
{navbar(profile_url="/student/profile", ini=initials(s['full_name']), color=avatar_bg(s['full_name']))}
{trial_banner(u)}
<div class="sc fade">
  <div class="st">My Profile</div>
  <div class="card">
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">
      <div class="av" style="width:58px;height:58px;font-size:1.2rem;background:{avatar_bg(s['full_name'])}">{initials(s['full_name'])}</div>
      <div style="flex:1">
        <div style="font-weight:700;font-size:1.05rem">{s['full_name']}</div>
        <div style="color:var(--gy);font-size:.81rem">{s['university']}</div>
        <div style="display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.35rem">
          <span class="badge b-green">✓ Verified</span>
          <span class="badge b-orange">⭐ {s['avg_rating']:.1f}</span>
          {plan_badge}
        </div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.7rem;font-size:.82rem;margin-bottom:1rem">
      <div><span style="color:var(--gy)">Gigs Done:</span><br><strong>{s['total_gigs']}</strong></div>
      <div><span style="color:var(--gy)">Earned:</span><br><strong>PKR {int(s['total_earned']):,}</strong></div>
      <div><span style="color:var(--gy)">CNIC:</span><br><strong>***-****{s['cnic'][-4:]}</strong></div>
      <div><span style="color:var(--gy)">Member since:</span><br><strong>{(s['date_of_birth'] or '')[:10]}</strong></div>
    </div>
    <div style="font-size:.72rem;font-weight:700;color:var(--gy);letter-spacing:.04em;margin-bottom:.35rem">PROFILE COMPLETION</div>
    <div class="rb" style="margin-bottom:1rem"><div class="rf" style="width:{comp}%"></div></div>

    <!-- ID card preview -->
    {('<div style="margin-bottom:1rem"><div style="font-size:.72rem;font-weight:700;color:var(--gy);letter-spacing:.04em;margin-bottom:.35rem">UNIVERSITY ID CARD</div>' + file_preview_html(s["id_card_path"],"ids") + '</div>') if s["id_card_path"] else ''}

    <hr>
    <form method="POST">
      <input type="hidden" name="action" value="profile">
      <div class="fg"><label class="fl">Skills (comma-separated)</label>
        <input class="fi" name="skills" value="{s['skills'] or ''}" placeholder="Excel, Social Media, Writing"></div>
      <div class="fg"><label class="fl">Bio</label>
        <textarea class="fi" name="bio" rows="3" placeholder="Tell businesses about yourself…">{s['bio'] or ''}</textarea></div>
      <button type="submit" class="btn bp bbl">Save Profile</button>
    </form>
    <hr id="wallet">
    <div style="font-weight:700;font-size:.9rem;margin-bottom:.75rem">💳 Payment Account
      {('<span class="badge b-green" style="margin-left:.4rem">Linked ✓</span>' if s['wallet_method'] else '')}</div>
    <form method="POST">
      <input type="hidden" name="action" value="wallet">
      <div class="fg"><label class="fl">Payment Method</label>
        <select class="fi" name="method">
          <option value="">Select method</option>
          <option value="easypaisa" {'selected' if s['wallet_method']=='easypaisa' else ''}>EasyPaisa 🟢</option>
          <option value="jazzcash"  {'selected' if s['wallet_method']=='jazzcash'  else ''}>JazzCash 🔴</option>
        </select></div>
      <div class="fg"><label class="fl">Wallet Number</label>
        <input class="fi" name="wallet_number" value="{s['wallet_number'] or ''}" placeholder="03XX-XXXXXXX"></div>
      <button type="submit" class="btn bo bbl">Save Wallet</button>
    </form>
    <hr>
    <a href="/logout" class="btn bbl" style="color:var(--rd);border:1.5px solid var(--rd);background:var(--rdl)">Sign Out</a>
  </div>
</div>
{snav("profile")}"""
    return page(body, "My Profile")

# ══════════════════════════════════════════════════════════════════════════════
# BUSINESS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/business/home")
@business_required
@subscription_required
def business_home():
    b  = get_business()
    u  = get_user()
    db = get_db()
    my_jobs = db.execute("SELECT * FROM jobs WHERE business_id=? ORDER BY created_at DESC LIMIT 5", (b["id"],)).fetchall()
    recent  = db.execute("""SELECT a.*,j.title as jt,s.full_name,s.university,s.avg_rating,s.total_gigs
        FROM applications a JOIN jobs j ON j.id=a.job_id JOIN students s ON s.id=a.student_id
        WHERE j.business_id=? ORDER BY a.applied_at DESC LIMIT 4""", (b["id"],)).fetchall()
    db.close()

    jobs_html = "".join(f"""
<div class="card" style="display:flex;justify-content:space-between;align-items:center">
  <div><div style="font-weight:700;font-size:.9rem">{j['title']}</div>
    <div style="color:var(--gy);font-size:.79rem">PKR {int(j['salary']):,} · {j['job_type']}</div></div>
  {status_badge(j['status'])}
</div>""" for j in my_jobs)

    apps_html = "".join(f"""
<div class="card" style="display:flex;align-items:center;gap:.85rem">
  <div class="av" style="width:42px;height:42px;font-size:.86rem;background:{avatar_bg(a['full_name'])}">{initials(a['full_name'])}</div>
  <div style="flex:1">
    <div style="font-weight:700;font-size:.87rem">{a['full_name']} {'<span class="badge b-urg" style="font-size:.6rem">NEW</span>' if a['status']=='pending' else ''}</div>
    <div style="color:var(--gy);font-size:.77rem">{a['university']} · {a['jt']}</div>
    <div style="color:var(--or);font-size:.76rem">{'★'*int(a['avg_rating'])}{'☆'*(5-int(a['avg_rating']))} · {a['total_gigs']} gigs</div>
  </div>
  <div style="display:flex;gap:.35rem;flex-direction:column">
    <a href="/business/hire/{a['id']}" class="btn bs bsm">Hire</a>
    <a href="/business/reject/{a['id']}" class="btn bd2 bsm">Pass</a>
  </div>
</div>""" for a in recent)

    body = f"""
{navbar(profile_url="/business/profile", ini=initials(b['business_name']), color=avatar_bg(b['business_name']))}
{trial_banner(u)}
<div class="sc fade">
  <div class="hero">
    <p style="color:#9E9C96;font-size:.79rem">Business Dashboard</p>
    <h2>{b['business_name']}</h2>
    <p>{b['industry'] or ''} · {b['city'] or ''}</p>
    <a href="/business/post" class="btn bp bsm">+ Post a Gig</a>
  </div>
  <div class="sg">
    <div class="sc2"><div class="sn">{b['total_posted']}</div><div class="sl">Posted</div></div>
    <div class="sc2"><div class="sn">{b['total_hired']}</div><div class="sl">Hired</div></div>
    <div class="sc2"><div class="sn" style="font-size:1rem">{(u['plan'] or 'trial').upper()}</div><div class="sl">Plan</div></div>
  </div>
  {f'<div class="st">Active Gigs</div>{jobs_html}' if my_jobs else ''}
  {f'<div class="st">Recent Applicants</div>{apps_html}' if recent else ''}
</div>
{bnav("home")}"""
    return page(body, "Dashboard")

@app.route("/business/post", methods=["GET","POST"])
@business_required
@subscription_required
def business_post():
    b = get_business()
    u = get_user()
    if request.method == "POST":
        db = get_db()
        # Free/trial plan: max 2 open jobs
        if u["plan"] in ("trial","free"):
            open_ct = db.execute("SELECT COUNT(*) FROM jobs WHERE business_id=? AND status='open'", (b["id"],)).fetchone()[0]
            if open_ct >= BIZ_FREE_JOB_LIMIT:
                flash(f"Free/trial plan allows max {BIZ_FREE_JOB_LIMIT} active gigs. Upgrade to Pro for unlimited.", "error")
                db.close(); return redirect(url_for("business_post"))
        try:
            salary = float(request.form.get("salary",0) or 0)
        except ValueError:
            salary = 0
        db.execute("""INSERT INTO jobs (business_id,title,description,job_type,location,is_remote,hours_per_day,
            salary,salary_period,skills_required,is_urgent,payment_method) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (b["id"], request.form.get("title","").strip(), request.form.get("description","").strip(),
             request.form.get("job_type","Part-time"), request.form.get("location","").strip(),
             1 if request.form.get("is_remote") else 0, request.form.get("hours",""),
             salary, request.form.get("salary_period","monthly"), request.form.get("skills","").strip(),
             1 if request.form.get("is_urgent") else 0, request.form.get("payment_method","easypaisa")))
        db.execute("UPDATE businesses SET total_posted=total_posted+1 WHERE id=?", (b["id"],))
        db.commit(); db.close()
        flash("Gig posted! 🚀 Students can now apply.", "success")
        return redirect(url_for("business_home"))

    body = f"""
{navbar(profile_url="/business/profile", ini=initials(b['business_name']), color=avatar_bg(b['business_name']))}
{trial_banner(u)}
<div class="sc fade">
  <div class="st">Post a New Gig</div>
  <div class="card">
    <form method="POST">
      <div class="fg"><label class="fl">Job Title *</label><input class="fi" name="title" placeholder="e.g. Social Media Assistant" required></div>
      <div class="frow">
        <div class="fg"><label class="fl">Job Type *</label>
          <select class="fi" name="job_type">{''.join(f"<option>{t}</option>" for t in ["Part-time","Freelance","Weekend","Internship"])}</select></div>
        <div class="fg"><label class="fl">Location *</label><input class="fi" name="location" placeholder="DHA, Karachi" required></div>
      </div>
      <div class="frow">
        <div class="fg"><label class="fl">Salary (PKR) *</label><input class="fi" type="number" name="salary" placeholder="15000" min="1" required></div>
        <div class="fg"><label class="fl">Salary Period</label>
          <select class="fi" name="salary_period"><option value="monthly">Monthly</option><option value="weekly">Weekly</option><option value="per project">Per Project</option></select></div>
      </div>
      <div class="fg"><label class="fl">Hours / Day</label><input class="fi" name="hours" placeholder="4 hrs/day"></div>
      <div class="fg"><label class="fl">Description *</label><textarea class="fi" name="description" rows="4" placeholder="Role, responsibilities, requirements…" required></textarea></div>
      <div class="fg"><label class="fl">Skills Required</label><input class="fi" name="skills" placeholder="Excel, Communication, Social Media"></div>
      <div class="fg"><label class="fl">Payment Method</label>
        <select class="fi" name="payment_method">
          <option value="easypaisa">EasyPaisa 🟢</option>
          <option value="jazzcash">JazzCash 🔴</option>
        </select></div>
      <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:1rem">
        <input type="checkbox" id="urg" name="is_urgent" style="width:16px;height:16px;accent-color:var(--or)">
        <label for="urg" style="font-size:.85rem;font-weight:600;cursor:pointer">Mark as URGENT</label></div>
      <div class="aw">⚠️ GigBridge charges a 5% processing fee on all salary payments.</div>
      <button type="submit" class="btn bp blg bbl">Post This Gig →</button>
    </form>
  </div>
</div>
{bnav("post")}"""
    return page(body, "Post a Gig")

@app.route("/business/applicants")
@business_required
@subscription_required
def business_applicants():
    b  = get_business()
    db = get_db()
    apps = db.execute("""SELECT a.*,j.title as jt,s.full_name,s.university,s.avg_rating,s.total_gigs,s.skills,s.id as sid
        FROM applications a JOIN jobs j ON j.id=a.job_id JOIN students s ON s.id=a.student_id
        WHERE j.business_id=? ORDER BY a.applied_at DESC""", (b["id"],)).fetchall()
    db.close()

    cards = "".join(f"""
<div class="card">
  <div style="display:flex;align-items:center;gap:.85rem;margin-bottom:.65rem">
    <div class="av" style="width:44px;height:44px;font-size:.9rem;background:{avatar_bg(a['full_name'])}">{initials(a['full_name'])}</div>
    <div style="flex:1">
      <div style="font-weight:700;font-size:.9rem">{a['full_name']} {'<span class="badge b-urg" style="font-size:.6rem">NEW</span>' if a['status']=='pending' else ''}</div>
      <div style="color:var(--gy);font-size:.77rem">{a['university']}</div>
      <div style="color:var(--or);font-size:.77rem">{'★'*int(a['avg_rating'])}{'☆'*(5-int(a['avg_rating']))} · {a['total_gigs']} gigs done</div>
    </div>
    {status_badge(a['status'])}
  </div>
  <div style="color:var(--gy);font-size:.77rem;margin-bottom:.5rem">Applied for: <strong style="color:var(--dk)">{a['jt']}</strong> · {time_ago(a['applied_at'])}</div>
  {f'<p style="font-size:.8rem;color:var(--gy);font-style:italic;margin-bottom:.5rem">"{a["cover_note"]}"</p>' if a.get('cover_note') else ''}
  <div style="margin-bottom:.7rem">{''.join(f"<span class='stag'>{s.strip()}</span>" for s in (a['skills'] or '').split(',') if s.strip())[:3]}</div>
  <div style="display:flex;gap:.5rem;flex-wrap:wrap">
    <a href="/talent/{a['sid']}" class="btn bo bsm">View Talent Card</a>
    <a href="/business/hire/{a['id']}" class="btn bs bsm">✓ Hire</a>
    <a href="/business/reject/{a['id']}" class="btn bd2 bsm">Pass</a>
  </div>
</div>""" for a in apps)

    body = f"""
{navbar(profile_url="/business/profile", ini=initials(b['business_name']), color=avatar_bg(b['business_name']))}
<div class="sc fade">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.85rem">
    <div class="st" style="margin-bottom:0">Applicants</div>
    <span style="font-size:.79rem;color:var(--gy)">{len(apps)} total</span>
  </div>
  {cards or '<div class="empty"><div class="ei">📭</div><p>No applicants yet.<br>Post a gig to attract students!</p><a href="/business/post" class="btn bp" style="margin-top:1rem">Post a Gig →</a></div>'}
</div>
{bnav("applicants")}"""
    return page(body, "Applicants")

@app.route("/talent/<int:sid>")
@business_required
def talent_card(sid):
    db = get_db()
    s  = db.execute("SELECT s.*,u.email FROM students s JOIN users u ON u.id=s.user_id WHERE s.id=?", (sid,)).fetchone()
    db.close()
    if not s: return redirect(url_for("business_applicants"))
    b     = get_business()
    skills= [x.strip() for x in (s["skills"] or "").split(",") if x.strip()]
    comp  = min(100, sum([20,10*(bool(s["skills"])),10*(bool(s["bio"])),20*(bool(s["wallet_method"])),
                          10*(bool(s["id_card_path"])),10,10*(bool(s["date_of_birth"]))]))
    stars = "★"*int(s["avg_rating"]) + "☆"*(5-int(s["avg_rating"]))
    body = f"""
{navbar(back="/business/applicants", profile_url="/business/profile", ini=initials(b['business_name']), color=avatar_bg(b['business_name']))}
<div style="padding:1.2rem;background:var(--lt);min-height:calc(100vh - 58px)">
  <div class="card fade">
    <div style="text-align:center;padding:.8rem 0 1rem">
      <div class="av" style="width:68px;height:68px;font-size:1.4rem;background:{avatar_bg(s['full_name'])};margin:0 auto .7rem">{initials(s['full_name'])}</div>
      <h2 style="font-family:var(--fh);font-size:1.25rem;font-weight:800">{s['full_name']}</h2>
      <div style="color:var(--gy);font-size:.83rem">{s['university']}</div>
      <div class="tb" style="margin:.45rem auto 0;width:fit-content">⭐ Talent Card</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin-bottom:1.2rem;text-align:center">
      <div class="sc2"><div class="sn">{s['total_gigs']}</div><div class="sl">Gigs</div></div>
      <div class="sc2"><div class="sn">{s['avg_rating']:.1f}</div><div class="sl">Rating</div></div>
      <div class="sc2"><div class="sn">{comp}%</div><div class="sl">Profile</div></div>
    </div>
    <div style="margin-bottom:1rem">
      <div style="font-size:.72rem;font-weight:700;color:var(--gy);letter-spacing:.04em;margin-bottom:.35rem">RATING</div>
      <div style="color:var(--or);font-size:1.1rem;letter-spacing:.1em">{stars}</div>
      <div class="rb mt-1"><div class="rf" style="width:{s['avg_rating']/5*100:.0f}%"></div></div>
    </div>
    <div style="margin-bottom:1rem">
      <div style="font-size:.72rem;font-weight:700;color:var(--gy);letter-spacing:.04em;margin-bottom:.35rem">PROFILE COMPLETION</div>
      <div class="rb"><div class="rf" style="width:{comp}%"></div></div>
    </div>
    {('<div style="margin-bottom:1rem"><div style="font-size:.72rem;font-weight:700;color:var(--gy);letter-spacing:.04em;margin-bottom:.4rem">SKILLS</div><div>' + ''.join(f'<span class="stag">{sk}</span>' for sk in skills) + '</div></div>') if skills else ''}
    {(f'<div style="margin-bottom:1rem"><div style="font-size:.72rem;font-weight:700;color:var(--gy);letter-spacing:.04em;margin-bottom:.35rem">BIO</div><p style="font-size:.84rem;color:var(--gy);line-height:1.6">{s["bio"]}</p></div>') if s["bio"] else ''}
    <div style="background:var(--lt);border-radius:10px;padding:.9rem;font-size:.82rem;color:var(--gy)">
      💳 Payment: {'EasyPaisa ✓' if s['wallet_method']=='easypaisa' else 'JazzCash ✓' if s['wallet_method']=='jazzcash' else 'Not linked yet'}
    </div>
  </div>
</div>
{bnav("applicants")}"""
    return page(body, f"{s['full_name']} — Talent Card")

@app.route("/business/hire/<int:aid>")
@business_required
def business_hire(aid):
    db  = get_db()
    app_row = db.execute("SELECT * FROM applications WHERE id=?", (aid,)).fetchone()
    if app_row:
        db.execute("UPDATE applications SET status='hired' WHERE id=?", (aid,))
        db.execute("UPDATE businesses SET total_hired=total_hired+1 WHERE user_id=?", (session["user_id"],))
        # Record booking time on the job for cancellation window tracking
        booked_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        db.execute("UPDATE jobs SET status='filled', booked_student_id=?, booked_at=? WHERE id=?",
                   (app_row["student_id"], booked_at, app_row["job_id"]))
        db.commit()
    db.close()
    flash("🎉 Student hired! Salary will be processed via EasyPaisa/JazzCash.", "success")
    return redirect(url_for("business_applicants"))

@app.route("/business/reject/<int:aid>")
@business_required
def business_reject(aid):
    db = get_db()
    db.execute("UPDATE applications SET status='rejected' WHERE id=?", (aid,))
    db.commit(); db.close()
    flash("Application updated.", "info")
    return redirect(url_for("business_applicants"))

@app.route("/business/profile", methods=["GET","POST"])
@business_required
@subscription_required
def business_profile():
    b = get_business()
    u = get_user()
    db = get_db()
    if request.method == "POST":
        db.execute("UPDATE businesses SET description=?,website=? WHERE user_id=?",
                   (request.form.get("description",""), request.form.get("website",""), session["user_id"]))
        db.commit(); db.close()
        flash("Profile saved! ✅", "success")
        return redirect(url_for("business_profile"))
    db.close()
    plan_badge = {"trial":f'<span class="badge b-amber">⏱ Trial ({trial_days_left(u)}d left)</span>',
                  "active":'<span class="badge b-green">✅ Pro</span>',
                  "pro":'<span class="badge b-green">✅ Pro</span>'}.get(u["plan"],'<span class="badge b-gray">Free</span>')
    body = f"""
{navbar(profile_url="/business/profile", ini=initials(b['business_name']), color=avatar_bg(b['business_name']))}
{trial_banner(u)}
<div class="sc fade">
  <div class="st">Business Profile</div>
  <div class="card">
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">
      {'<img src="/uploads/logos/' + b["logo_path"] + '" style="width:56px;height:56px;border-radius:12px;object-fit:cover;border:1px solid var(--bd)">' if b["logo_path"] else f'<div style="width:56px;height:56px;background:var(--or);border-radius:12px;display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:1.2rem;font-weight:800;color:#fff">{initials(b["business_name"])}</div>'}
      <div>
        <div style="font-weight:700;font-size:1.05rem">{b['business_name']}</div>
        <div style="color:var(--gy);font-size:.81rem">{b['industry'] or ''}</div>
        <div style="display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.35rem">
          <span class="badge b-green">✓ Verified</span>
          {plan_badge}
        </div>
      </div>
    </div>
    <div style="font-size:.82rem;line-height:2.2;margin-bottom:1rem">
      <div><span style="color:var(--gy)">City:</span> <strong>{b['city'] or '—'}</strong></div>
      <div><span style="color:var(--gy)">Posted:</span> <strong>{b['total_posted']} gigs</strong></div>
      <div><span style="color:var(--gy)">Hired:</span> <strong>{b['total_hired']} students</strong></div>
    </div>
    <hr>
    <form method="POST">
      <div class="fg"><label class="fl">Description</label>
        <textarea class="fi" name="description" rows="3" placeholder="Tell students about your company…">{b['description'] or ''}</textarea></div>
      <div class="fg"><label class="fl">Website</label>
        <input class="fi" name="website" value="{b['website'] or ''}" placeholder="https://yourcompany.pk"></div>
      <button type="submit" class="btn bp bbl">Save Profile</button>
    </form>
    <hr>
    <a href="/subscribe" class="btn bbl" style="background:var(--dk);color:#fff">🚀 Upgrade Plan</a>
    <a href="/logout" class="btn bbl" style="color:var(--rd);border:1.5px solid var(--rd);background:var(--rdl)">Sign Out</a>
  </div>
</div>
{bnav("profile")}"""
    return page(body, "Business Profile")

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/admin")
@admin_required
def admin_dashboard():
    db  = get_db()
    stats = {
        "students":  db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "businesses":db.execute("SELECT COUNT(*) FROM businesses").fetchone()[0],
        "jobs":      db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "open_jobs": db.execute("SELECT COUNT(*) FROM jobs WHERE status='open'").fetchone()[0],
        "apps":      db.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
        "hired":     db.execute("SELECT COUNT(*) FROM applications WHERE status='hired'").fetchone()[0],
        "revenue_total":       db.execute("SELECT COALESCE(SUM(amount),0) FROM payments").fetchone()[0],
        "revenue_student_sub": db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_type='student_premium'").fetchone()[0],
        "revenue_biz_sub":     db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_type='business_subscription'").fetchone()[0],
        "revenue_cancel":      db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_type='cancellation'").fetchone()[0],
        "total_cancellations": db.execute("SELECT COUNT(*) FROM cancellations").fetchone()[0],
        "trial_students": db.execute("SELECT COUNT(*) FROM users WHERE role='student' AND plan='trial'").fetchone()[0],
        "trial_biz":      db.execute("SELECT COUNT(*) FROM users WHERE role='business' AND plan='trial'").fetchone()[0],
        "premium_students": db.execute("SELECT COUNT(*) FROM users WHERE role='student' AND plan='premium'").fetchone()[0],
        "pro_biz":          db.execute("SELECT COUNT(*) FROM users WHERE role='business' AND plan IN ('pro','enterprise')").fetchone()[0],
    }
    students   = db.execute("SELECT s.*,u.email,u.plan,u.trial_start,u.created_at FROM students s JOIN users u ON u.id=s.user_id ORDER BY u.created_at DESC LIMIT 20").fetchall()
    businesses = db.execute("SELECT b.*,u.email,u.plan,u.trial_start,u.created_at FROM businesses b JOIN users u ON u.id=b.user_id ORDER BY u.created_at DESC LIMIT 20").fetchall()
    jobs       = db.execute("SELECT j.*,b.business_name FROM jobs j JOIN businesses b ON b.id=j.business_id ORDER BY j.created_at DESC LIMIT 20").fetchall()
    payments   = db.execute("SELECT p.*,u.email FROM payments p JOIN users u ON u.id=p.user_id ORDER BY p.created_at DESC LIMIT 20").fetchall()
    cancels    = db.execute("SELECT c.*,u.email,j.title FROM cancellations c JOIN users u ON u.id=c.cancelled_by JOIN jobs j ON j.id=c.job_id ORDER BY c.created_at DESC LIMIT 10").fetchall()
    db.close()

    def plan_badge(plan):
        return {
            "trial":      '<span class="badge b-amber">Trial</span>',
            "active":     '<span class="badge b-green">Active</span>',
            "premium":    '<span class="badge b-green">Premium ⭐</span>',
            "pro":        '<span class="badge b-green">Pro 🔥</span>',
            "enterprise": '<span class="badge b-blue">Enterprise</span>',
            "admin":      '<span class="badge b-blue">Admin</span>',
            "free":       '<span class="badge b-gray">Free</span>',
        }.get(plan, '<span class="badge b-gray">Free</span>')

    students_rows  = "".join(f"<tr><td>{s['full_name']}</td><td style='color:var(--gy)'>{s['email']}</td><td>{s['university']}</td><td>{plan_badge(s['plan'])}</td><td style='color:var(--gy)'>{s['created_at'][:10]}</td></tr>" for s in students)
    biz_rows       = "".join(f"<tr><td>{b['business_name']}</td><td style='color:var(--gy)'>{b['email']}</td><td>{b['city'] or '—'}</td><td>{plan_badge(b['plan'])}</td><td style='color:var(--gy)'>{b['created_at'][:10]}</td></tr>" for b in businesses)
    jobs_rows      = "".join(f"<tr><td>{j['title']}</td><td style='color:var(--gy)'>{j['business_name']}</td><td>PKR {int(j['salary']):,}</td><td>{status_badge(j['status'])}</td><td style='color:var(--gy)'>{j['created_at'][:10]}</td></tr>" for j in jobs)
    payments_rows  = "".join(f"<tr><td>{p['email']}</td><td style='color:var(--gn);font-weight:700'>PKR {int(p['amount']):,}</td><td>{p['plan']}</td><td><span class='badge b-blue' style='font-size:.65rem'>{(p['payment_type'] or 'sub').replace('_',' ')}</span></td><td>{p['method'] or '—'}</td><td style='color:var(--gy)'>{p['created_at'][:10]}</td></tr>" for p in payments)
    cancel_rows    = "".join(f"<tr><td>{c['email']}</td><td style='color:var(--gy)'>{c['title']}</td><td>{c['cancelled_role']}</td><td style='color:var(--rd);font-weight:700'>PKR {int(c['fee_charged']):,}</td><td style='color:var(--gy)'>{c['created_at'][:10]}</td></tr>" for c in cancels)

    body = f"""
<div class="nb" style="background:var(--dk)">
  <div style="font-family:var(--fh);font-size:1.3rem;font-weight:800;color:#fff">Gig<span style="color:var(--or)">Bridge</span> <span style="font-size:.75rem;color:#666;font-weight:400">Admin</span></div>
  <a href="/logout" class="btn bsm" style="background:rgba(255,255,255,.1);color:#fff;border:none">Sign Out</a>
</div>
<div style="padding:1.2rem;background:var(--lt);min-height:calc(100vh - 58px)">
  <div class="st">📊 Platform Overview</div>
  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:.8rem;margin-bottom:1.5rem">
    {''.join(f'<div class="sc2"><div class="sn" style="font-size:1.4rem">{v}</div><div class="sl">{k}</div></div>' for k,v in [("Students",stats['students']),("Businesses",stats['businesses']),("Total Gigs",stats['jobs']),("Open Gigs",stats['open_jobs']),("Applications",stats['apps']),("Hired",stats['hired'])])}
  </div>

  <!-- Revenue breakdown -->
  <div class="st">💰 Revenue Streams</div>
  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:.8rem;margin-bottom:1.8rem">
    <div class="card" style="border:2px solid var(--gn);background:var(--gnl);grid-column:1/-1">
      <div style="font-size:.73rem;font-weight:700;color:var(--gn);letter-spacing:.04em;margin-bottom:.3rem">TOTAL REVENUE</div>
      <div style="font-family:var(--fh);font-size:1.8rem;font-weight:800;color:var(--gn)">PKR {int(stats['revenue_total']):,}</div>
    </div>
    <div class="card" style="border:1.5px solid var(--or);background:var(--orl)">
      <div style="font-size:.7rem;font-weight:700;color:var(--or);margin-bottom:.2rem">STUDENT PREMIUM</div>
      <div style="font-family:var(--fh);font-size:1.3rem;font-weight:800">PKR {int(stats['revenue_student_sub']):,}</div>
      <div style="font-size:.74rem;color:var(--gy)">{stats['premium_students']} active premium students</div>
    </div>
    <div class="card" style="border:1.5px solid var(--bl);background:#EFF6FF">
      <div style="font-size:.7rem;font-weight:700;color:var(--bl);margin-bottom:.2rem">BUSINESS SUBSCRIPTIONS</div>
      <div style="font-family:var(--fh);font-size:1.3rem;font-weight:800">PKR {int(stats['revenue_biz_sub']):,}</div>
      <div style="font-size:.74rem;color:var(--gy)">{stats['pro_biz']} pro/enterprise businesses</div>
    </div>
    <div class="card" style="border:1.5px solid var(--rd);background:var(--rdl)">
      <div style="font-size:.7rem;font-weight:700;color:var(--rd);margin-bottom:.2rem">CANCELLATION FEES</div>
      <div style="font-family:var(--fh);font-size:1.3rem;font-weight:800">PKR {int(stats['revenue_cancel']):,}</div>
      <div style="font-size:.74rem;color:var(--gy)">{stats['total_cancellations']} cancellations total</div>
    </div>
    <div class="card" style="border:1.5px solid var(--am);background:var(--aml)">
      <div style="font-size:.7rem;font-weight:700;color:var(--am);margin-bottom:.2rem">ON FREE TRIAL</div>
      <div style="font-family:var(--fh);font-size:1.3rem;font-weight:800">{stats['trial_students'] + stats['trial_biz']}</div>
      <div style="font-size:.74rem;color:var(--am)">{stats['trial_students']} students · {stats['trial_biz']} businesses</div>
    </div>
  </div>

  <!-- Students -->
  <div class="st">🎓 Students (latest 20)</div>
  <div class="card" style="padding:.5rem;overflow-x:auto;margin-bottom:1.5rem">
    <table class="adm-table">
      <thead><tr><th>Name</th><th>Email</th><th>University</th><th>Plan</th><th>Joined</th></tr></thead>
      <tbody>{students_rows}</tbody>
    </table>
  </div>

  <!-- Businesses -->
  <div class="st">🏢 Businesses (latest 20)</div>
  <div class="card" style="padding:.5rem;overflow-x:auto;margin-bottom:1.5rem">
    <table class="adm-table">
      <thead><tr><th>Name</th><th>Email</th><th>City</th><th>Plan</th><th>Joined</th></tr></thead>
      <tbody>{biz_rows}</tbody>
    </table>
  </div>

  <!-- Jobs -->
  <div class="st">💼 Gigs Posted (latest 20)</div>
  <div class="card" style="padding:.5rem;overflow-x:auto;margin-bottom:1.5rem">
    <table class="adm-table">
      <thead><tr><th>Title</th><th>Business</th><th>Salary</th><th>Status</th><th>Posted</th></tr></thead>
      <tbody>{jobs_rows}</tbody>
    </table>
  </div>

  <!-- Payments -->
  <div class="st">💳 All Payments</div>
  <div class="card" style="padding:.5rem;overflow-x:auto;margin-bottom:1.5rem">
    {'<table class="adm-table"><thead><tr><th>Email</th><th>Amount</th><th>Plan</th><th>Type</th><th>Method</th><th>Date</th></tr></thead><tbody>' + payments_rows + '</tbody></table>' if payments else '<div class="empty" style="padding:1.5rem"><div class="ei">💳</div><p>No payments yet</p></div>'}
  </div>

  <!-- Cancellations -->
  <div class="st">❌ Cancellations (latest 10)</div>
  <div class="card" style="padding:.5rem;overflow-x:auto;margin-bottom:1.5rem">
    {'<table class="adm-table"><thead><tr><th>User</th><th>Gig</th><th>Role</th><th>Fee</th><th>Date</th></tr></thead><tbody>' + cancel_rows + '</tbody></table>' if cancels else '<div class="empty" style="padding:1.5rem"><div class="ei">✅</div><p>No cancellations yet</p></div>'}
  </div>
</div>"""
    return page(body, "Admin Dashboard")

# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    print("\n" + "="*55)
    print("  GigBridge v2 is running!")
    print("  App:   http://localhost:5000")
    print("  Admin: http://localhost:5000/admin")
    print("-"*55)
    print("  Admin:    admin@gigbridge.pk / admin123")
    print("  Student:  sara@iba.edu.pk   / password123")
    print("  Business: hr@brewbox.pk     / password123")
    print("="*55 + "\n")
    app.run(host="0.0.0.0", debug=True, port=5000)