GigBridge v2 — Python Web App
==============================

HOW TO RUN:
-----------
1. Make sure Python 3.10+ is installed (python.org)
2. Open terminal / command prompt in this folder
3. Install Flask (one time only):
   pip install flask werkzeug
4. Run:
   python app.py
5. Open browser:  http://localhost:5000
   Admin panel:   http://localhost:5000/admin

TEST ACCOUNTS (password: password123)
--------------------------------------
Admin:    admin@gigbridge.pk  / admin123
Student:  sara@iba.edu.pk    / password123
Business: hr@brewbox.pk      / password123

WHAT'S NEW IN v2:
-----------------
✅ Sign-in bug fixed — login works correctly after registration
✅ 5-day free trial — new users get 5 days free, then subscription paywall
✅ Subscription system — PKR 999/mo (students) / PKR 2,999/mo (business)
✅ EasyPaisa / JazzCash subscription payment flow
✅ Uploaded files displayed — ID cards & logos shown on profile pages
✅ Admin dashboard — see all signups, gigs, revenue, subscriptions
✅ Trial banner — countdown shown on every page
✅ Search gigs by keyword
✅ Business logo shown on profile if uploaded
✅ Student ID card preview shown on profile

ADMIN DASHBOARD SHOWS:
-----------------------
- Total students, businesses, jobs, applications
- Revenue from subscriptions (PKR)
- Users currently on free trial
- Latest 20 students with their plan status
- Latest 20 businesses with their plan status
- Latest 20 gigs posted
- All subscription payments with method & amount
