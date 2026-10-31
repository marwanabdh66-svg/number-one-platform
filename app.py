import streamlit as st
import sqlite3
import hashlib
import secrets
from datetime import datetime

# =====================================
# NUMBER ONE - AI AD STUDIO
# =====================================

st.set_page_config(
    page_title="NUMBER ONE | استوديو الإعلانات",
    page_icon="👑",
    layout="wide"
)

DB = "number_one.db"


# =====================================
# قاعدة البيانات
# =====================================

def connect_db():
    con = sqlite3.connect(DB, timeout=20)
    con.row_factory = sqlite3.Row
    return con


def setup_db():
    con = connect_db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            plan TEXT DEFAULT 'Free',
            created TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            method TEXT NOT NULL,
            amount TEXT NOT NULL,
            reference TEXT NOT NULL,
            status TEXT DEFAULT 'قيد المراجعة',
            created TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            category TEXT NOT NULL,
            details TEXT NOT NULL,
            contact TEXT NOT NULL,
            created TEXT NOT NULL
        )
    """)

    con.commit()
    con.close()


setup_db()


# =====================================
# كلمات المرور
# =====================================

def password_hash(password):
    salt = st.secrets.get(
        "NUMBER_ONE_PASSWORD_SALT",
        "change-this-salt-before-production"
    )

    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        200000
    ).hex()


def register_user(username, password):
    con = connect_db()

    try:
        con.execute("""
            INSERT INTO users
            (username, password, plan, created)
            VALUES (?, ?, 'Free', ?)
        """, (
            username.strip(),
            password_hash(password),
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))

        con.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        con.close()


def login_user(username, password):
    con = connect_db()

    user = con.execute(
        "SELECT username, password, plan FROM users WHERE username=?",
        (username.strip(),)
    ).fetchone()

    con.close()

    if user and secrets.compare_digest(
        user[1],
        password_hash(password)
    ):
        return {"username": user[0], "plan": user[2]}

    return None


# =====================================
# التصميم والألوان
# =====================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: Cairo, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top right, #1b3157, transparent 38%),
        linear-gradient(135deg, #070b16, #111a2e);
    color: #f5f7ff;
}

section[data-testid="stSidebar"] {
    background: #0a1120;
    border-left: 1px solid #344563;
}

.hero {
    background: linear-gradient(135deg, #192a49, #0b1221);
    border: 1px solid #d7b45d;
    border-radius: 22px;
    padding: 28px 16px;
    text-align: center;
    margin-bottom: 25px;
}

.hero h1 {
    color: #f0cc70;
    font-size: 40px;
    font-weight: 800;
}

.hero p {
    color: #d7dfef;
    font-size: 16px;
}

.card {
    background: linear-gradient(145deg, #19243a, #0d1526);
    border: 1px solid #344663;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
}

.gold {
    color: #f0cc70;
}

div.stButton > button {
    background: linear-gradient(135deg, #f0cc70, #b78a35);
    color: #111827;
    font-weight: 800;
    border: none;
    border-radius: 10px;
    min-height: 42px;
    width: 100%;
}

div.stButton > button:hover {
    background: #ffe6a0;
    color: #111827;
}

.stTextInput input, .stTextArea textarea {
    background: #111c30;
    color: white;
    border: 1px solid #344663;
}

hr {
    border-color: #344663;
}
</style>
""", unsafe_allow_html=True)


# =====================================
# رأس الموقع
# =====================================

st.markdown("""
<div class="hero">
    <h1>👑 NUMBER ONE</h1>
    <p>استوديو الإعلانات والقوالب الإبداعية</p>
    <p>اصنع فكرتك الإعلانية بأسلوب احترافي</p>
</div>
""", unsafe_allow_html=True)


# =====================================
# القائمة الرئيسية
# =====================================

pages = [
    "🏠 الرئيسية",
    "🎨 قوالب الإعلانات",
    "🤖 صانع الإعلان",
    "🎬 طلب تصميم",
    "💎 الاشتراكات",
    "💳 طلب الدفع",
    "👤 حسابي",
    "🔐 تسجيل الدخول",
    "📝 إنشاء حساب",
    "📞 التواصل",
    "🛡️ الإدارة"
]

st.sidebar.markdown(
    "<h2 style='color:#f0cc70;text-align:center'>👑 NUMBER ONE</h2>",
    unsafe_allow_html=True
)

page = st.sidebar.radio("القائمة", pages)

username = st.session_state.get("username")

if username:
    st.sidebar.success("المستخدم: " + username)

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.pop("username", None)
        st.rerun()
else:
    st.sidebar.info("تصفح الموقع مجانًا")


# =====================================
# الرئيسية
# =====================================

if page == "🏠 الرئيسية":

    st.subheader("مرحبًا بك في NUMBER ONE")

    st.write(
        "منصة تساعدك على إعداد أفكار الإعلانات "
        "وكتابة أوصاف جاهزة لأدوات التصميم."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="card">
            <h3 class="gold">🎨 القوالب</h3>
            <p>أفكار إعلانية لمجالات متنوعة.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
            <h3 class="gold">🤖 صانع الإعلان</h3>
            <p>أنشئ وصفًا إعلانيًا يناسب مشروعك.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="card">
            <h3 class="gold">💎 Pro</h3>
            <p>نظام اشتراكات قابل للتطوير.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### كيف تستخدم الموقع؟")

    st.write("1. اختر مجال الإعلان.")
    st.write("2. أدخل اسم مشروعك.")
    st.write("3. أنشئ وصف الإعلان.")
    st.write("4. نزّل الوصف واستخدمه في أداة التصميم.")

    st.info(
        "توليد الصور والفيديوهات فعليًا يحتاج إلى ربط "
        "خدمة ذكاء اصطناعي خارجية."
    )


# =====================================
# قوالب الإعلانات
# =====================================

elif page == "🎨 قوالب الإعلانات":

    st.subheader("🎨 مكتبة القوالب والأفكار")

    templates = {
        "🍔 المطاعم": [
            "إعلان برغر سينمائي",
            "عرض وجبة عائلية",
            "إعلان قهوة فاخر",
            "إعلان افتتاح مطعم"
        ],
        "🏠 العقارات": [
            "إعلان شقة للبيع",
            "إعلان فيلا فاخرة",
            "إعلان أرض استثمارية",
            "إعلان مشروع سكني"
        ],
        "🛍️ المتاجر": [
            "إعلان تخفيضات",
            "إعلان منتج جديد",
            "إعلان متجر إلكتروني",
            "إعلان ملابس"
        ],
        "💈 الخدمات": [
            "إعلان صالون",
            "إعلان مركز تجميل",
            "إعلان صيانة",
            "إعلان مركز تعليمي"
        ],
        "💻 التقنية": [
            "إعلان تطبيق",
            "إعلان متجر إلكترونيات",
            "إعلان خدمة رقمية",
            "إعلان دورة تدريبية"
        ]
    }

    category = st.selectbox("اختر المجال", list(templates.keys()))

    template = st.selectbox(
        "اختر القالب",
        templates[category]
    )

    st.markdown(f"""
    <div class="card">
        <h3 class="gold">{template}</h3>
        <p>طوّر هذه الفكرة لتناسب مشروعك وعملاءك.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("استخدام القالب"):
        st.session_state["template"] = template
        st.success("تم الاختيار. انتقل إلى صانع الإعلان.")


# =====================================
# صانع الإعلان
# =====================================

elif page == "🤖 صانع الإعلان":

    st.subheader("🤖 صانع وصف الإعلان")

    business = st.text_input(
        "اسم المشروع",
        placeholder="مثال: مطعم النخبة"
    )

    category = st.selectbox(
        "نوع الإعلان",
        ["مطاعم", "عقارات", "متاجر", "خدمات", "تقنية", "تعليم", "عام"]
    )

    audience = st.selectbox(
        "الجمهور المستهدف",
        ["الجميع", "الشباب", "العائلات", "أصحاب الأعمال", "العملاء المحليون"]
    )

    style = st.selectbox(
        "أسلوب التصميم",
        [
            "فاخر وهادئ",
            "عصري وجريء",
            "سينمائي",
            "بسيط وأنيق",
            "ملون وجذاب",
            "تقني ومستقبلي"
        ]
    )

    details = st.text_area(
        "تفاصيل المنتج أو العرض",
        value=st.session_state.get("template", ""),
        placeholder="اكتب السعر والخصومات ومميزات المنتج..."
    )

    if st.button("✨ إنشاء وصف الإعلان"):

        if not business.strip() or not details.strip():
            st.warning("أدخل اسم المشروع وتفاصيل الإعلان.")
        else:
            prompt = f"""
NUMBER ONE — ADVERTISEMENT BRIEF

Business: {business}
Category: {category}
Audience: {audience}
Style: {style}

Details:
{details}

Create a professional advertising concept for social media.
Use an attractive composition, readable typography,
appropriate colors, beautiful lighting and a clear call to action.
Make the business name prominent.
Avoid spelling mistakes and unnecessary visual clutter.
"""

            st.session_state["prompt"] = prompt

    if st.session_state.get("prompt"):

        st.markdown("### وصف الإعلان الناتج")

        st.text_area(
            "يمكنك نسخ الوصف",
            value=st.session_state["prompt"],
            height=250
        )

        st.download_button(
            "📥 تنزيل الوصف",
            data=st.session_state["prompt"],
            file_name="number_one_ad.txt",
            mime="text/plain"
        )


# =====================================
# طلب تصميم
# =====================================

elif page == "🎬 طلب تصميم":

    st.subheader("🎬 طلب تصميم إعلان")

    if not username:
        st.warning("سجّل الدخول أولًا.")
    else:
        category = st.selectbox(
            "نوع التصميم",
            ["إعلان صورة", "فيديو موشن جرافيك", "مطعم", "عقارات", "متجر", "أخرى"]
        )

        details = st.text_area("اشرح التصميم المطلوب")
        contact = st.text_input("رقم واتساب أو وسيلة التواصل")

        if st.button("إرسال طلب التصميم"):

            if not details.strip() or not contact.strip():
                st.error("أكمل تفاصيل الطلب ووسيلة التواصل.")
            else:
                con = connect_db()

                con.execute("""
                    INSERT INTO orders
                    (username, category, details, contact, created)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    username,
                    category,
                    details,
                    contact,
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ))

                con.commit()
                con.close()

                st.success("تم حفظ طلبك في الموقع.")
                st.info("الطلب لم يُرسل إلى مصمم أو واتساب تلقائيًا.")


# =====================================
# الاشتراكات
# =====================================

elif page == "💎 الاشتراكات":

    st.subheader("💎 خطط الاشتراك")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div class="card">
            <h2 class="gold">🆓 Free</h2>
            <h3>مجانية</h3>
            <hr>
            <p>✔ تصفح القوالب</p>
            <p>✔ كتابة أوصاف الإعلانات</p>
            <p>✔ تنزيل النصوص</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
            <h2 class="gold">👑 Pro</h2>
            <h3>اشتراك مدفوع</h3>
            <hr>
            <p>✔ مزايا الخطة المجانية</p>
            <p>✔ قابل لإضافة قوالب حصرية</p>
            <p>✔ قابل لربط أدوات الذكاء الاصطناعي</p>
        </div>
        """, unsafe_allow_html=True)

    st.warning(
        "المزايا المدفوعة الإضافية تحتاج إلى تطوير فعلي قبل بيع الاشتراك."
    )


# =====================================
# طلب الدفع
# =====================================

elif page == "💳 طلب الدفع":

    st.subheader("💳 طلب اشتراك Pro")

    if not username:
        st.warning("سجّل الدخول أولًا.")
    else:
        st.info(
            "أضف بيانات محفظتك اليمنية أو حسابك البنكي الحقيقية "
            "إلى الموقع قبل استقبال المدفوعات."
        )

        method = st.selectbox(
            "طريقة الدفع",
            ["محفظة محلية", "تحويل بنكي", "طريقة أخرى"]
        )

        amount = st.text_input("المبلغ والعملة")
        reference = st.text_input("رقم العملية أو مرجع التحويل")

        if st.button("إرسال طلب الدفع"):

            if not amount.strip() or not reference.strip():
                st.error("أدخل المبلغ ورقم العملية.")
            else:
                con = connect_db()

                con.execute("""
                    INSERT INTO payments
                    (username, method, amount, reference, status, created)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    method,
                    amount,
                    reference,
                    "قيد المراجعة",
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ))

                con.commit()
                con.close()

                st.success("تم إرسال طلب الدفع للمراجعة.")
                st.info("سيحتاج المسؤول إلى التحقق من التحويل يدويًا.")


# =====================================
# حساب المستخدم
# =====================================

elif page == "👤 حسابي":

    if not username:
        st.warning("سجّل الدخول لعرض حسابك.")
    else:
        con = connect_db()

        user = con.execute(
            "SELECT username, plan, created FROM users WHERE username=?",
            (username,)
        ).fetchone()

        payments = con.execute("""
            SELECT method, amount, status, created
            FROM payments
            WHERE username=?
            ORDER BY id DESC
        """, (username,)).fetchall()

        con.close()

        if user:
            st.subheader("👤 حسابي")

            st.markdown(f"""
            <div class="card">
                <h3 class="gold">مرحبًا {user[0]}</h3>
                <p>الخطة الحالية: {user[1]}</p>
                <p>تاريخ التسجيل: {user[2]}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### طلبات الدفع السابقة")

        if payments:
            st.dataframe(
                [dict(p) for p in payments],
                use_container_width=True
            )
        else:
            st.info("لا توجد طلبات دفع حتى الآن.")


# =====================================
# تسجيل الدخول
# =====================================

elif page == "🔐 تسجيل الدخول":

    st.subheader("🔐 تسجيل الدخول")

    with st.form("login_form"):
        login_name = st.text_input("اسم المستخدم")
        login_password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول")

    if submitted:
        user = login_user(login_name, login_password)

        if user:
            st.session_state["username"] = user["username"]
            st.success("تم تسجيل الدخول.")
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")


# =====================================
# إنشاء حساب
# =====================================

elif page == "📝 إنشاء حساب":

    st.subheader("📝 إنشاء حساب جديد")

    with st.form("register_form"):
        new_name = st.text_input("اسم المستخدم")
        new_password = st.text_input("كلمة المرور", type="password")
        confirm_password = st.text_input("تأكيد كلمة المرور", type="password")

        submitted = st.form_submit_button("إنشاء الحساب")

    if submitted:

        if len(new_name.strip()) < 3:
            st.error("اسم المستخدم يجب أن يكون 3 أحرف على الأقل.")

        elif len(new_password) < 8:
            st.error("كلمة المرور يجب أن تكون 8 أحرف على الأقل.")

        elif new_password != confirm_password:
            st.error("كلمتا المرور غير متطابقتين.")

        elif register_user(new_name, new_password):
            st.success("تم إنشاء الحساب. انتقل إلى تسجيل الدخول.")

        else:
            st.error("اسم المستخدم موجود مسبقًا.")


# =====================================
# التواصل
# =====================================

elif page == "📞 التواصل":

    st.subheader("📞 تواصل معنا")

    name = st.text_input("اسمك")
    contact = st.text_input("رقم التواصل")
    message = st.text_area("رسالتك")

    if st.button("تجهيز الرسالة"):

        if not name.strip() or not message.strip():
            st.warning("أدخل اسمك ورسالتك.")
        else:
            text = (
                f"الاسم: {name}\n"
                f"التواصل: {contact}\n"
                f"الرسالة: {message}"
            )

            st.text_area("رسالتك الجاهزة", value=text, height=150)

            st.download_button(
                "تنزيل الرسالة",
                data=text,
                file_name="number_one_message.txt"
            )


# =====================================
# لوحة الإدارة
# =====================================

elif page == "🛡️ الإدارة":

    st.subheader("🛡️ لوحة الإدارة")

    # يدعم أسماء الأسرار القديمة والجديدة حتى لا تتعطل إعدادات المالك الحالية
    admin_name = st.secrets.get(
        "NUMBER_ONE_OWNER_USERNAME",
        st.secrets.get("ADMIN_USERNAME", "")
    )
    admin_password = st.secrets.get(
        "NUMBER_ONE_OWNER_PASSWORD",
        st.secrets.get("ADMIN_PASSWORD", "")
    )

    if not admin_name or not admin_password:
        st.error(
            "لوحة الإدارة تحتاج إلى إعداد NUMBER_ONE_OWNER_USERNAME "
            "و NUMBER_ONE_OWNER_PASSWORD في أسرار الاستضافة."
        )

    else:

        if not st.session_state.get("admin_ok"):

            with st.form("admin_form"):
                entered_name = st.text_input("اسم المسؤول")
                entered_password = st.text_input(
                    "كلمة مرور المسؤول",
                    type="password"
                )

                submitted = st.form_submit_button("دخول الإدارة")

            if submitted:

                if (
                    secrets.compare_digest(entered_name, admin_name)
                    and secrets.compare_digest(entered_password, admin_password)
                ):
                    st.session_state["admin_ok"] = True
                    st.rerun()
                else:
                    st.error("بيانات المسؤول غير صحيحة.")

        if st.session_state.get("admin_ok"):

            if st.button("خروج المسؤول"):
                st.session_state["admin_ok"] = False
                st.rerun()

            con = connect_db()

            st.markdown("### المستخدمون")

            users = con.execute("""
                SELECT id, username, plan, created
                FROM users ORDER BY id DESC
            """).fetchall()

            if users:
                st.dataframe(
                    [dict(u) for u in users],
                    use_container_width=True
                )
            else:
                st.info("لا يوجد مستخدمون حتى الآن.")

            st.markdown("### طلبات الدفع")

            payments = con.execute("""
                SELECT * FROM payments ORDER BY id DESC
            """).fetchall()

            if payments:
                st.dataframe(
                    [dict(p) for p in payments],
                    use_container_width=True
                )
            else:
                st.info("لا توجد طلبات دفع.")

            con.close()

            st.markdown("### مراجعة الدفع")

            payment_id = st.number_input(
                "رقم طلب الدفع",
                min_value=1,
                step=1
            )

            status = st.selectbox(
                "حالة الطلب",
                ["قيد المراجعة", "تم التحقق من الدفع", "مرفوض"]
            )

            if st.button("حفظ حالة الطلب"):

                con = connect_db()

                payment = con.execute(
                    "SELECT username FROM payments WHERE id=?",
                    (int(payment_id),)
                ).fetchone()

                if payment:

                    con.execute(
                        "UPDATE payments SET status=? WHERE id=?",
                        (status, int(payment_id))
                    )

                    if status == "تم التحقق من الدفع":
                        con.execute(
                            "UPDATE users SET plan='Pro' WHERE username=?",
                            (payment[0],)
                        )

                    con.commit()
                    st.success("تم تحديث الطلب.")
                    st.rerun()

                else:
                    st.error("رقم الطلب غير موجود.")

                con.close()

            st.markdown("### طلبات التصميم")

            con = connect_db()

            orders = con.execute("""
                SELECT * FROM orders ORDER BY id DESC
            """).fetchall()

            con.close()

            if orders:
                st.dataframe(
                    [dict(o) for o in orders],
                    use_container_width=True
                )
            else:
                st.info("لا توجد طلبات تصميم.")


# =====================================
# نهاية الموقع
# =====================================

st.markdown("---")

st.markdown("""
<div style="text-align:center;color:#aab6ce;padding:12px">
    <h3 style="color:#f0cc70">👑 NUMBER ONE</h3>
    <p>من فكرتك تبدأ الحكاية.</p>
</div>
""", unsafe_allow_html=True)
