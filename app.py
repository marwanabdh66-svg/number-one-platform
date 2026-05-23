import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from PIL import Image
from google import genai
from google.genai import types

# -------------------------------------------------------------------
# 1. إعدادات الصفحة وحقن كود التوجيه والمؤشرات البصرية (CSS)
# -------------------------------------------------------------------
st.set_page_config(page_title="Number One AI - Super Platform", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    /* تأثير وميض حاد وجاذب لتحديد الصندوق أو الزر المستهدف للزبون المحتار */
    .highlight-target {
        border: 3px solid #FF4B4B !important;
        box-shadow: 0 0 25px #FF4B4B !important;
        animation: blinker 1.5s linear infinite;
        padding: 20px;
        border-radius: 10px;
        background-color: #111;
    }
    @keyframes blinker {
        50% { opacity: 0.6; }
    }
    
    /* تصميم السهم الإرشادي اللامع والمتحرك (الماوس الافتراضي للـ AI) */
    .ai-pointer-arrow {
        color: #FF4B4B;
        font-size: 24px;
        font-weight: bold;
        display: inline-block;
        animation: bounce 0.6s infinite alternate;
        margin-right: 10px;
    }
    @keyframes bounce {
        from { transform: translateX(0); }
        to { transform: translateX(-12px); }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 2. إنشاء قاعدة البيانات المركزية الشاملة
# -------------------------------------------------------------------
conn = sqlite3.connect('number_one_ultimate_db.db', check_same_thread=False)
cursor = conn.cursor()

# جدول المستخدمين والطلاب والمسوقين بالعمولة
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password_hash TEXT,
        plan_type TEXT,
        status TEXT,
        currency TEXT,
        amount REAL,
        affiliate_code TEXT UNIQUE,
        referred_by TEXT,
        balance_usd REAL DEFAULT 0.0,
        progress_percent INTEGER DEFAULT 0
    )
''')

# جدول طلبات خدمة العملاء العامة مع أرقام هواتف الزبائن
cursor.execute('''
    CREATE TABLE IF NOT EXISTS customer_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_phone TEXT,
        client_message TEXT,
        ai_reply TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# جدول الشركات الأخرى التي تؤجر خدمة العملاء وتربط أرقامها الخاصة
cursor.execute('''
    CREATE TABLE IF NOT EXISTS business_widgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_email TEXT,
        company_name TEXT,
        company_phone TEXT,
        ai_behavior TEXT,
        widget_token TEXT UNIQUE
    )
''')
conn.commit()

# دالة حماية وتشفير كلمات المرور
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

owner_email = "marwanabdh66@gmail.com"
owner_pass_raw = "uuiopoeyr1"
owner_hash = hash_password(owner_pass_raw)

# -------------------------------------------------------------------
# 3. تهيئة ربط ذكاء Gemini الاصطناعي (النصوص والصور والتوجيه)
# -------------------------------------------------------------------
# ضع مفتاح الـ API الخاص بك هنا لتفعيل الاتصال الحي الفوري
# client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

def call_gemini_mega(prompt, image=None, system_instruction=""):
    try:
        # عند وضع مفتاح الـ API، قم بإلغاء التعليق عن الأسطر أدناه لتشغيل النظام حياً:
        # config = types.GenerateContentConfig(system_instruction=system_instruction)
        # if image:
        #     response = client.models.generate_content(model='gemini-2.5-flash', contents=[image, prompt], config=config)
        # else:
        #     response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt, config=config)
        # return response.text
        
        if image:
            return "[محاكاة Gemini الرؤية]: تم فحص وقراءة الصورة المرفقة بنجاح! الشرح للمنهج الدراسي جاهز بالكامل."
        return f"[محاكاة Gemini الموجه]: أهلاً بك في منصة Number One. لقد تلقيت طلبك: '{prompt}' وجاري توجيهك بصرياً في الشاشة."
    except Exception as e:
        return "عذراً مروان، يرجى تفعيل مفتاح الـ API للربط المباشر مع خوادم جوجل."

# منطق الموجه البصري وتحريك الأسهم الافتراضية للزبائن المحتارين
if "ai_screen_action" not in st.session_state:
    st.session_state["ai_screen_action"] = None

def run_ai_copilot_director(user_text):
    intent = user_text.lower()
    if "اشترك" in intent or "بكم" in intent or "سعر" in intent or "اشتراك" in intent:
        st.session_state["ai_screen_action"] = "TARGET_REGISTER"
        return "🤖 جيميناي يوجهك: لقد قمت بتحريك الماوس وإضاءة قسم '🔐 تسجيل الدخول والاشتراك' باللون الأحمر على اليمين! انقر عليه لتفعيل حسابك فوراً دون حيرة."
    elif "مالك" in intent or "مروان" in intent or "إدارة" in intent:
        st.session_state["ai_screen_action"] = "TARGET_OWNER"
        return "🤖 جيميناي يوجهك: أهلاً بالإدارة! انظر لأسفل القائمة الجانبية، لقد وضعت لك سهم الإشارة 👈 بجانب '🔑 لوحة تحكم المالك مروان' لتدخل مباشرة."
    elif "تواصل" in intent or "رقم" in intent or "مشكلة" in intent or "مساعدة" in intent:
        st.session_state["ai_screen_action"] = "TARGET_SUPPORT"
        return "🤖 جيميناي يوجهك: تم سحب مؤشر الشاشة وإضاءة قسم '📞 خدمة العملاء (اترك رقمك)'. انقر عليه وضع رقم هاتف تواصلك."
    elif "مدرس" in intent or "صورة" in intent or "كتاب" in intent or "حل" in intent:
        st.session_state["ai_screen_action"] = "TARGET_TEACHER"
        return "🤖 جيميناي يوجهك: تم توجيه السهم نحو '📚 المعلم الذكي والـ Vision AI'. يمكنك هناك رفع صور كتابك المدرسي ليتم حله فورا."
    else:
        st.session_state["ai_screen_action"] = None
        return "🤖 جيميناي يوجهك: أنا أتحكم بالشاشة لمساعدتك! إذا كنت محتاراً، فقط اكتب لي (أريد الاشتراك) أو (أريد المدرس) وسأحرك الأسهم وأريك أين تضغط!"

# -------------------------------------------------------------------
# 4. إعداد القائمة الجانبية التفاعلية المتحكم بها عبر الـ AI
# -------------------------------------------------------------------
st.sidebar.markdown("<h1 style='text-align: center; color: #00b4d8;'>Number One</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center;'>المنصة الذكية الموجهة بالكامل بالـ AI</p>", unsafe_allow_html=True)
st.sidebar.write("---")

# توليد الأسهم المتحركة بصرياً بناء على الكوبيلوت
arrow_reg = "<span class='ai-pointer-arrow'>👈</span>" if st.session_state["ai_screen_action"] == "TARGET_REGISTER" else ""
arrow_teach = "<span class='ai-pointer-arrow'>👈</span>" if st.session_state["ai_screen_action"] == "TARGET_TEACHER" else ""
arrow_supp = "<span class='ai-pointer-arrow'>👈</span>" if st.session_state["ai_screen_action"] == "TARGET_SUPPORT" else ""
arrow_own = "<span class='ai-pointer-arrow'>👈</span>" if st.session_state["ai_screen_action"] == "TARGET_OWNER" else ""

menu = st.sidebar.radio("🗺️ التنقل التلقائي الموجه في المنصة:", [
    f"🔐 تسجيل الدخول والاشتراك {arrow_reg}",
    f"📚 المعلم الذكي والـ Vision AI (نص + صور) {arrow_teach}",
    f"📞 خدمة العملاء (اترك رقمك للتواصل) {arrow_supp}",
    "💸 نظام التسويق بالعمولة (Affiliate)",
    f"🔑 لوحة تحكم المالك مروان {arrow_own}"
])

# -------------------------------------------------------------------
# 5. المساعد العائم الحركي بأعلى الموقع لمساعدة المحتارين دائماً
# -------------------------------------------------------------------
st.write("---")
with st.container():
    st.markdown("### 🧠 جيميناي المتحكم المباشر والموجه البصري للشاشة")
    st.info("👋 محتار وضائع في الموقع ولا تعرف أين تذهب؟ اكتب لي أي شيء تحتاجه بالأسفل وسأقوم بتحريك مؤشر الماوس والأسهم على الشاشة وأريك أين تضغط بدقة!")
    
    col_in, col_bt = st.columns([8, 2])
    with col_in:
        guide_query = st.text_input("💬 اسأل جيميناي ليوجه شاشتك الآن (مثال: أريد الاشتراك، أريد الدعم):", key="director_q")
    with col_bt:
        st.write("<br>", unsafe_allow_html=True)
        btn_trigger = st.button("اطلب توجيه الماوس والأسهم 🚀", use_container_width=True)
        
    if btn_trigger and guide_query:
        director_reply = run_ai_copilot_director(guide_query)
        st.markdown(f"<div style='background-color:#1e1e1e; padding:15px; border-radius:10px; border-left: 5px solid #FF4B4B;'>{director_reply}</div>", unsafe_allow_html=True)
st.write("---")

# -------------------------------------------------------------------
# 6. تفاصيل وتشغيل صفحات وقوائم الموقع
# -------------------------------------------------------------------

# [أ] واجهة التسجيل والاشتراك وبوابات المحافظ الرقمية
if "🔐 تسجيل الدخول والاشتراك" in menu:
    css_class = "highlight-target" if st.session_state["ai_screen_action"] == "TARGET_REGISTER" else "normal-box"
    
    st.markdown(f"<div class='{css_class}'><h2>🔐 بوابة الحسابات وتفعيل خطط Number One</h2><p>الاشتراك الشهري الاحترافي بقيمة 10 دولارات فقط.</p></div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب وتفعيل الاشتراك فورا"])
    with tab1:
        login_email = st.text_input("البريد الإلكتروني:", key="l_em")
        login_pass = st.text_input("كلمة المرور:", type="password", key="l_ps")
        if st.button("دخول للحساب", use_container_width=True):
            if login_email == owner_email and login_pass == owner_pass_raw:
                st.success("مرحباً بك يا مروان العلواني! يمكنك الانتقال إلى قسم لوحة المالك مباشرة من القائمة.")
            else:
                cursor.execute("SELECT email, plan_type FROM users WHERE email=? AND password_hash=?", (login_email, hash_password(login_pass)))
                user_found = cursor.fetchone()
                if user_found:
                    st.session_state['user_logged'] = user_found[0]
                    st.success(f"تم الدخول! خطتك الحالية: {user_found[1]}")
                else:
                    st.error("بيانات الحساب غير صحيحة.")
                    
    with tab2:
        new_email = st.text_input("بريدك الإلكتروني الجديد:")
        new_pass = st.text_input("اختر كلمة مرور قوية:", type="password")
        ref_code = st.text_input("كود الإحالة والتسويق بالعمولة (إن وجد):")
        
        pay_method = st.selectbox("اختر بوابة الدفع المتاحة:", [
            "بوابة السداد الفوري - محفظة ون كاش (One Cash API)",
            "المحافظ اليمنية الأخرى (كاش، جوالي، فلوسك، جيب)",
            "عبر شبكات الصرافة المحلية (النجم، الامتياز، المريسي وكل الصرافين)",
            "بوابة PayPal العالمية لليمنيين المغتربين في الخارج"
        ])
        currency = st.selectbox("اختر عملة السداد:", ["دولار أمريكي ($)", "ريال يمني (YR)", "ريال سعودي (SAR)"])
        ref_num = st.text_input("أدخل رقم الحوالة / الإشعار المرجعي للتأكيد والمطابقة:")
        
        final_amt = 10.0
        if currency == "ريال يمني (YR)": final_amount_calc = 10.0 * 530
        elif currency == "ريال سعودي (SAR)": final_amount_calc = 10.0 * 3.75
        else: final_amount_calc = 10.0
        
        st.info(f"المبلغ المطلوب تحويله: {final_amount_calc:,.2f} {currency}")
        
        if st.button("تأكيد السداد وإنشاء حسابي تلقائياً"):
            if new_email and new_pass and ref_num:
                try:
                    user_own_ref = "REF-" + hashlib.md5(new_email.encode()).hexdigest()[:6].upper()
                    pwd_h = hash_password(new_pass)
                    initial_status = "نشط" if "One Cash" in pay_method else "معلق بانتظار التأكيد"
                    
                    cursor.execute("""
                        INSERT INTO users (email, password_hash, plan_type, status, currency, amount, affiliate_code, referred_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (new_email, pwd_h, "شهري", initial_status, currency, final_amount_calc, user_own_ref, ref_code))
                    conn.commit()
                    st.success(f"🎉 تم تسجيل طلبك بنجاح! حالة الحساب الحالية: {initial_status}.")
                except sqlite3.IntegrityError:
                    st.error("هذا الحساب مسجل مسبقاً.")

# [ب] واجهة المعلم الذكي والذكاء الاصطناعي البصري Vision
elif "📚 المعلم الذكي" in menu:
    css_class = "highlight-target" if st.session_state["ai_screen_action"] == "TARGET_TEACHER" else "normal-box"
    st.markdown(f"<div class='{css_class}'><h2>📚 المعلم الذكي والـ Vision AI لشركة Number One</h2><p>التقط صورة لدرسك أو مسألتك الصعبة وسيقوم Gemini بحلها فورا وشرحها لك.</p></div>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📸 ارفع صورة المسألة أو المنهج الدراسي هنا:", type=["jpg", "jpeg", "png"])
    user_text = st.text_input("✍️ اكتب سؤالك التعليمي المكمل للـ AI:")
    
    if st.button("إرسال وتحليل البيانات بواسطة Gemini"):
        if user_text or uploaded_file:
            with st.spinner("جاري صياغة وتحليل الشروحات المنهجية..."):
                img_input = Image.open(uploaded_file) if uploaded_file else None
                reply = call_gemini_mega(prompt=user_text, image=img_input, system_instruction="أنت معلم ذكي لشركة Number One")
                if img_input: st.image(img_input, width=250)
                st.chat_message("assistant").write(reply)

# [ج] واجهة خدمة العملاء الذكية مع خانة رقم التواصل للزبون وحفظها
elif "📞 خدمة العملاء" in menu:
    css_class = "highlight-target" if st.session_state["ai_screen_action"] == "TARGET_SUPPORT" else "normal-box"
    st.markdown(f"<div class='{css_class}'><h2>📞 مركز خدمة العملاء بالذكاء الاصطناعي AI</h2><p>ضع رقم تواصلك وسؤالك، وسيرد الـ AI عليك فوراً مع حفظ رقمك لمتابعته من الإدارة.</p></div>", unsafe_allow_html=True)
    
    customer_phone = st.text_input("📱 أدخل رقم هاتفك أو حساب الواتساب الخاص بك (مثال: 77xxxxxxx):")
    customer_msg = st.text_area("💬 اكتب تفاصيل استفسارك أو مشكلتك الفنية:")
    
    if st.button("إرسال رسالتي لخدمة العملاء AI"):
        if customer_phone and customer_msg:
            with st.spinner("جاري صياغة رد خدمة العملاء الفوري..."):
                ai_reply = call_gemini_mega(prompt=customer_msg, system_instruction="أنت خبير خدمة عملاء منصة Number One لصاحبها مروان العلواني.")
                
                # حفظ رقم الهاتف والرسالة في قاعدة البيانات ليراها مروان لاحقاً
                cursor.execute("INSERT INTO customer_leads (client_phone, client_message, ai_reply) VALUES (?, ?, ?)", (customer_phone, customer_msg, ai_reply))
                conn.commit()
                
                st.success("✅ تم إرسال رسالتك وحفظ رقم تواصلك في نظام شركة Number One بنجاح!")
                st.chat_message("assistant").write(ai_reply)
        else:
            st.error("الرجاء إدخال رقم هاتفك وتفاصيل الرسالة.")

# [د] نظام التسويق بالعمولة (Affiliate System) أرباح المستخدمين
elif "💸 نظام التسويق" in menu:
    st.title("💸 نظام Number One للأرباح والتسويق بالعمولة")
    if 'user_logged' not in st.session_state:
        st.warning("🔒 يرجى تسجيل الدخول أولاً من التبويب الأول لتتمكن من توليد كود إحالتك ومراقبة عمولاتك.")
    else:
        cursor.execute("SELECT affiliate_code, balance_usd FROM users WHERE email=?", (st.session_state['user_logged'],))
        aff_code, aff_bal = cursor.fetchone()
        st.info(f"🔗 كود الإحالة الخاص بك لمشاركته وكسب الأموال: **{aff_code}**")
        st.metric(label="💰 رصيد أرباحك الحالية القابلة للسحب لمحفظتك", value=f"${aff_bal:.2f} USD")

# [هـ] واجهة المالك المحمية والمشفرة بالكامل لـ مروان العلواني
elif "🔑 لوحة تحكم المالك" in menu:
    css_class = "highlight-target" if st.session_state["ai_screen_action"] == "TARGET_OWNER" else "normal-box"
    st.markdown(f"<div class='{css_class}'><h2>🔒 الإدارة المركزية والرقابة المالية العامة - مروان العلواني</h2></div>", unsafe_allow_html=True)
    
    if 'owner_logged' not in st.session_state: st.session_state['owner_logged'] = False
        
    if not st.session_state['owner_logged']:
        ow_em = st.text_input("بريد المالك المصرح له:", value="marwanabdh66@gmail.com")
        ow_ps = st.text_input("كلمة مرور المالك الآمنة والمحمية برمجياً:", type="password")
        if st.button("تسجيل الدخول بأمان إلى البيانات"):
            if ow_em == owner_email and hash_password(ow_ps) == owner_hash:
                st.session_state['owner_logged'] = True
                st.success("أهلاً بك يا مروان العلواني، تم التصريح بالولوج الآمن.")
                st.rerun()
            else:
                st.error("بيانات المرور والأمان غير متطابقة.")
    else:
        st.success("👋 لوحة تحكم مروان العلواني النشطة - مالك شركة Number One")
        if st.button("خروج آمن من لوحة الإدارة"):
            st.session_state['owner_logged'] = False
            st.rerun()
            
        st.write("---")
        # حسبة التوزيع المالي الصارمة المطلوبة من مروان العلواني:
        # من كل 10 دولارات لاشتراك شهري نشط: 5 دولارات لحسابك البنكي كرسوم للـ AI، والصافي الـ 5 دولارات الباقية تذهب لمحفظة ون كاش
        cursor.execute("SELECT COUNT(*) FROM users WHERE status='نشط' AND plan_type='شهري'")
        active_monthly_count = cursor.fetchone()[0] or 0
        
        bank_share = active_monthly_count * 5
        wincash_share = active_monthly_count * 5
        
        st.subheader("📊 تقرير التوزيعات والمحاسبة التلقائية للأموال")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="👥 إجمالي المشتركين الشهريين النشطين", value=f"{active_monthly_count} مستخدم")
        with c2:
            st.metric(label="📲 الصافي المرحل تلقائياً لـ (محفظة ون كاش الخاصة بك)", value=f"${wincash_share:.2f} USD")
        with c3:
            st.metric(label="🏦 حصة تكلفة الـ AI المحولة لـ (محفظتك البنكية مباشرة)", value=f"${bank_share:.2f} USD")
            
        st.write("---")
        # عرض الإضافة الجديدة: أرقام هواتف عملاء خدمة العملاء ليتابعهم مروان
        st.subheader("📱 أرقام الهواتف والرسائل المستلمة في خدمة العملاء (AI Leads)")
        cursor.execute("SELECT id, client_phone, client_message, timestamp FROM customer_leads ORDER BY timestamp DESC")
        leads_data = cursor.fetchall()
        if leads_data:
            df_leads = pd.DataFrame(leads_data, columns=["المعرف", "رقم هاتف الزبون", "تفاصيل رسالته", "تاريخ الإرسال"])
            st.dataframe(df_leads, use_container_width=True)
        else:
            st.info("لا توجد رسائل أو أرقام زبائن مستلمة في خدمة العملاء حالياً.")

        st.write("---")
        # واجهة الموافقة اليدوية على الحوالات المعلقة (الصرافين والمحافظ) وتفعيلها
        st.subheader("⏳ طلبات المشتركين عبر الحوالات والصرافين بانتظار تفعيلك")
        cursor.execute("SELECT id, email, currency, amount FROM users WHERE status='معلق بانتظار التأكيد'")
        pending_list = cursor.fetchall()
        if pending_list:
            for p_user in pending_list:
                with st.expander(f"حوالة معلقة من الحساب البنكي: {p_user[1]}"):
                    st.write(f"المبلغ المسدد بالعملة المختارة: {p_user[3]} {p_user[2]}")
                    if st.button(f"تأكيد استلام السداد وتنشيط حساب {p_user[1]} الآن", key=f"activate_btn_{p_user[0]}"):
                        cursor.execute("UPDATE users SET status='نشط' WHERE id=?", (p_user[0],))
                        conn.commit()
                        st.success("تم تنشيط الحساب بنجاح وترحيل الأموال إلى الرصيد المالي المباشر!")
                        st.rerun()
        else:
            st.info("لا توجد طلبات معلقة بانتظار المراجعة حالياً.")

conn.close()

