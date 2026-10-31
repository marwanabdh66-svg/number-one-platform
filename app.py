import streamlit as st
import sqlite3
import hashlib
import secrets
import html
import csv
import io
from datetime import datetime
from template_catalog import TEMPLATE_CATALOG, render_preview_data_uri

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


def rows_to_csv(rows):
    """تحويل نتائج قاعدة البيانات إلى ملف CSV مناسب لبرنامج الجداول."""
    if not rows:
        return "".encode("utf-8-sig")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()

    # منع تفسير القيم التي أدخلها المستخدم كمعادلات عند فتح CSV في برامج الجداول.
    safe_rows = []
    for row in rows:
        safe_row = {}
        for key, value in dict(row).items():
            cell = "" if value is None else str(value)
            if cell.lstrip().startswith(("=", "+", "-", "@")):
                cell = "'" + cell
            safe_row[key] = cell
        safe_rows.append(safe_row)

    writer.writerows(safe_rows)
    return output.getvalue().encode("utf-8-sig")


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
            created TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'جديد'
        )
    """)

    # ترقية قواعد البيانات القديمة دون حذف الطلبات السابقة.
    order_columns = {
        row["name"] for row in cur.execute("PRAGMA table_info(orders)").fetchall()
    }
    if "status" not in order_columns:
        cur.execute(
            "ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'جديد'"
        )

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

/* إلغاء القائمة الجانبية بالكامل */
section[data-testid="stSidebar"],
[data-testid="stSidebar"],
button[kind="header"] {
    display: none !important;
}
[data-testid="stAppViewContainer"] > .main {
    margin-left: 0 !important;
}
.block-container {
    max-width: 1440px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}
.top-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 22px;
    margin: 0 0 18px;
    border: 1px solid rgba(215,180,93,.45);
    border-radius: 20px;
    background: linear-gradient(110deg, rgba(28,45,75,.96), rgba(10,17,32,.96));
    box-shadow: 0 12px 35px rgba(0,0,0,.18);
}
.brand-mark { font-size: 35px; }
.brand-name { color: #f0cc70; font-size: 25px; font-weight: 800; letter-spacing: 1px; }
.brand-caption { color: #b9c6dc; font-size: 12px; }
.brand-status { margin-right: auto; color: #8ee0b0; font-size: 12px; }
.welcome-strip {
    padding: 10px 15px;
    margin-bottom: 12px;
    border-radius: 12px;
    color: #e7edf8;
    background: rgba(31,49,77,.7);
    border: 1px solid #344663;
}
div[role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    padding: 10px;
    border: 1px solid #344663;
    border-radius: 16px;
    background: rgba(12,21,38,.92);
    margin-bottom: 22px;
}
div[role="radiogroup"] label {
    background: #192943;
    border: 1px solid #344663;
    border-radius: 11px;
    padding: 7px 12px;
}
div[role="radiogroup"] label p { color: #eaf0fb; font-size: 13px; }


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

/* واجهة سطح المكتب الاحترافية */
@media (min-width: 1100px) {
    .block-container {
        max-width: 1680px;
        padding: 2.1rem 3.2rem 4rem;
    }
    .top-brand {
        min-height: 112px;
        padding: 24px 34px;
        border-radius: 24px;
        margin-bottom: 24px;
    }
    .brand-mark { font-size: 48px; }
    .brand-name { font-size: 32px; letter-spacing: 2px; }
    .brand-caption { font-size: 14px; }
    .brand-status { font-size: 14px; }
    .welcome-strip {
        padding: 15px 22px;
        margin-bottom: 18px;
        font-size: 15px;
    }
    div[role="radiogroup"] {
        display: grid !important;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 10px;
        padding: 14px;
        margin-bottom: 30px;
        border-radius: 20px;
    }
    div[role="radiogroup"] label {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 52px;
        padding: 10px 14px;
        border-radius: 13px;
        transition: all .2s ease;
        text-align: center;
    }
    div[role="radiogroup"] label:hover {
        border-color: #d7b45d;
        background: #243958;
        transform: translateY(-2px);
    }
    div[role="radiogroup"] label p {
        font-size: 14px;
        font-weight: 700;
        margin: 0;
    }
    .hero {
        padding: 52px 36px;
        border-radius: 28px;
        margin-bottom: 34px;
    }
    .hero h1 { font-size: 52px; }
    .hero p { font-size: 19px; }
    .card {
        padding: 28px;
        border-radius: 22px;
        min-height: 150px;
        box-shadow: 0 14px 34px rgba(0,0,0,.16);
        transition: transform .2s ease, border-color .2s ease;
    }
    .card:hover {
        transform: translateY(-4px);
        border-color: rgba(240,204,112,.75);
    }
    h1 { font-size: 2.25rem !important; }
    h2 { font-size: 1.8rem !important; }
    h3 { font-size: 1.3rem !important; }
    p, li, label, .stMarkdown { line-height: 1.85; }
    div.stButton > button, .stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        min-height: 50px;
        border-radius: 13px;
        font-size: 15px;
    }
    .stTextInput input, .stTextArea textarea,
    div[data-baseweb="select"] > div {
        min-height: 48px;
        border-radius: 12px;
    }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #192a45, #101a2d);
        border: 1px solid #344663;
        border-radius: 18px;
        padding: 20px 22px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #344663;
        border-radius: 14px;
        overflow: hidden;
    }
}
/* توازن العرض على الأجهزة المتوسطة والهواتف */
@media (max-width: 1099px) {
    .block-container {
        padding-left: 1.2rem;
        padding-right: 1.2rem;
    }
    div[role="radiogroup"] {
        display: flex;
        overflow-x: auto;
        flex-wrap: nowrap;
        white-space: nowrap;
        scrollbar-width: thin;
    }
    div[role="radiogroup"] label { flex: 0 0 auto; }
}
@media (max-width: 640px) {
    .top-brand { padding: 14px; gap: 9px; }
    .brand-mark { font-size: 27px; }
    .brand-name { font-size: 20px; }
    .brand-caption { font-size: 10px; }
    .brand-status { display: none; }
    .hero h1 { font-size: 29px; }
    .card { padding: 16px; }
}

</style>
""", unsafe_allow_html=True)


# =====================================
# رأس الموقع
# =====================================

# =====================================
# القائمة الرئيسية
# =====================================

username = st.session_state.get("username")

pages = [
    "🏠 الرئيسية",
    "🎨 قوالب الإعلانات",
    "🤖 صانع الإعلان",
    "🎬 طلب تصميم",
    "💎 الاشتراكات",
    "💳 طلب الدفع",
    "👤 حسابي",
    "📞 التواصل",
    "🛡️ الإدارة"
]

if not username:
    pages.extend(["🔐 تسجيل الدخول", "📝 إنشاء حساب"])
else:
    pages = [p for p in pages if p not in ("🔐 تسجيل الدخول", "📝 إنشاء حساب")]

# شريط تنقل علوي بدل القائمة الجانبية
st.markdown("""
<div class="top-brand">
  <div class="brand-mark">👑</div>
  <div>
    <div class="brand-name">NUMBER ONE</div>
    <div class="brand-caption">منصتك الإبداعية للتصميم والتجارة الرقمية</div>
  </div>
  <div class="brand-status">● المنصة متاحة</div>
</div>
""", unsafe_allow_html=True)

if username:
    st.markdown(
        f'<div class="welcome-strip">مرحبًا، <b>{html.escape(str(username))}</b> · يسعدنا وجودك في NUMBER ONE</div>',
        unsafe_allow_html=True
    )

if st.session_state.pop("template_navigation_pending", False):
    st.session_state["main_navigation"] = "🤖 صانع الإعلان"

page = st.radio(
    "التنقل الرئيسي",
    pages,
    horizontal=True,
    label_visibility="collapsed",
    key="main_navigation"
)

nav_left, nav_right = st.columns([5, 1])
with nav_right:
    if username and st.button("تسجيل الخروج", key="top_logout"):
        st.session_state.pop("username", None)
        st.session_state["admin_ok"] = False
        st.rerun()


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

    st.info("🎬 توليد الصور والفيديوهات مباشرة داخل المنصة: قريبًا.") 
    st.caption("يمكنك حاليًا إنشاء وصف إعلاني وتجهيزه لاستخدامه في أدوات التصميم.")


# =====================================
# قوالب الإعلانات
# =====================================

elif page == "🎨 قوالب الإعلانات":

    st.subheader("🎨 مكتبة قوالب NUMBER ONE")
    st.caption(
        "تضم المكتبة 400 صيغة بداية موزعة على 10 مجالات و5 مقاسات. "
        "المعاينات رسومات SVG أصلية تُنشأ داخل المنصة، وليست ملفات PSD أو Canva متعددة الطبقات."
    )

    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    with filter_col1:
        search_query = st.text_input(
            "ابحث باسم القالب أو المجال أو المقاس",
            placeholder="مثال: قهوة، عقارات، قصة عمودية...",
            key="template_search"
        )
    with filter_col2:
        category_options = ["كل المجالات"] + sorted(
            {item["category"] for item in TEMPLATE_CATALOG}
        )
        selected_category = st.selectbox(
            "المجال",
            category_options,
            key="template_category_filter"
        )
    with filter_col3:
        format_options = ["كل المقاسات"] + sorted(
            {item["format"] for item in TEMPLATE_CATALOG}
        )
        selected_format = st.selectbox(
            "المقاس",
            format_options,
            key="template_format_filter"
        )

    normalized_query = search_query.strip().casefold()
    filtered_templates = [
        item for item in TEMPLATE_CATALOG
        if (
            selected_category == "كل المجالات"
            or item["category"] == selected_category
        )
        and (
            selected_format == "كل المقاسات"
            or item["format"] == selected_format
        )
        and (
            not normalized_query
            or normalized_query in " ".join(
                [
                    item["title"],
                    item["category"],
                    item["topic"],
                    item["format"],
                    item["style"],
                ]
            ).casefold()
        )
    ]

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("إجمالي الصيغ", f"{len(TEMPLATE_CATALOG):,}")
    metric_b.metric("نتائج البحث", f"{len(filtered_templates):,}")
    metric_c.metric("المجالات", len(category_options) - 1)

    if not filtered_templates:
        st.warning("لم نعثر على قالب يطابق البحث. جرّب كلمة أخرى أو غيّر المجال.")
    else:
        page_size = st.selectbox(
            "عدد القوالب في الصفحة",
            [6, 9, 12],
            index=1,
            key="template_page_size"
        )
        total_pages = max(
            1,
            (len(filtered_templates) + page_size - 1) // page_size
        )
        page_options = list(range(1, total_pages + 1))
        page_number = st.selectbox(
            f"صفحة النتائج (من {total_pages})",
            page_options,
            key=f"template_page_{len(filtered_templates)}_{page_size}"
        )

        first_item = (page_number - 1) * page_size
        visible_templates = filtered_templates[first_item:first_item + page_size]
        st.caption(
            f"عرض {first_item + 1}–{first_item + len(visible_templates)} "
            f"من أصل {len(filtered_templates)} نتيجة."
        )

        preview_columns = st.columns(3)
        for index, item in enumerate(visible_templates):
            with preview_columns[index % 3]:
                preview_uri = render_preview_data_uri(item)
                safe_title = html.escape(item["title"])
                safe_category = html.escape(item["category"])
                safe_format = html.escape(item["format"])
                safe_style = html.escape(item["style"])
                st.markdown(
                    f"""
                    <div class="card" style="padding:10px;min-height:0">
                        <img
                            src="{preview_uri}"
                            alt="{safe_title}"
                            loading="lazy"
                            style="display:block;width:100%;height:auto;border-radius:12px"
                        >
                        <div style="padding:10px 4px 2px">
                            <div style="color:#f0cc70;font-size:12px">{safe_category}</div>
                            <h4 style="margin:5px 0;color:#ffffff">{safe_title}</h4>
                            <div style="color:#c7d2e5;font-size:12px">
                                {safe_format} · {safe_style}
                            </div>
                            <div style="color:#8fa2bf;font-size:11px;margin-top:7px">
                                {item["id"]} · معاينة SVG أصلية
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    "استخدام هذا القالب",
                    key=f"use_template_{item['id']}",
                    use_container_width=True
                ):
                    st.session_state["template"] = item["title"]
                    st.session_state["selected_template_id"] = item["id"]
                    st.session_state["ad_details_input"] = (
                        f"القالب المختار: {item['title']}\n"
                        f"المجال: {item['category']}\n"
                        f"المقاس: {item['format']}\n"
                        f"الأسلوب: {item['style']}\n"
                        f"فكرة التصميم: {item['description']}\n"
                        "أضف اسم مشروعك والسعر والتفاصيل التي تريد ظهورها في الإعلان."
                    )
                    st.session_state["template_selected_notice"] = item["title"]
                    st.session_state["template_navigation_pending"] = True
                    st.rerun()

    st.caption(
        "ملاحظة: هذه معاينات تصميمية أصلية خفيفة؛ لا تمثل بعد ملفات تصميم مفتوحة الطبقات. "
        "سيتم توسيع مكتبة الصور والفيديو في خطوة مستقلة."
    )


# =====================================
# صانع الإعلان
# =====================================

elif page == "🤖 صانع الإعلان":

    st.subheader("🤖 صانع وصف الإعلان")

    selected_notice = st.session_state.pop("template_selected_notice", None)
    if selected_notice:
        st.success(f"تم تحميل القالب «{selected_notice}» في نموذج الإعلان. أكمل بيانات مشروعك.")

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
        placeholder="اكتب السعر والخصومات ومميزات المنتج...",
        key="ad_details_input"
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

    st.info("🖼️ إنشاء الصور والفيديوهات تلقائيًا داخل NUMBER ONE: قريبًا.")

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
                st.info("إرسال الطلب تلقائيًا إلى مصمم أو واتساب ومتابعة التنفيذ المباشر: قريبًا.")


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
            <p>⏳ القوالب الحصرية: قريبًا</p>
            <p>⏳ أدوات الذكاء الاصطناعي المتقدمة: قريبًا</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("تفعيل مزايا Pro المدفوعة وبيع الاشتراكات تلقائيًا: قريبًا. لن يتم تحصيل أي مبلغ تلقائيًا حاليًا.")


# =====================================
# طلب الدفع
# =====================================

elif page == "💳 طلب الدفع":

    st.subheader("💳 طلب اشتراك Pro")

    if not username:
        st.warning("سجّل الدخول أولًا.")
    else:
        st.info("الدفع الإلكتروني المباشر وربط المحافظ والبنوك: قريبًا. طلب الدفع الحالي يُرسل للمراجعة اليدوية فقط.")

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

        orders = con.execute("""
            SELECT category, details, contact, created, status
            FROM orders
            WHERE username=?
            ORDER BY id DESC
        """, (username,)).fetchall()

        con.close()

        if user:
            st.subheader("👤 حسابي")

            safe_username = html.escape(str(user[0]))
            safe_plan = html.escape(str(user[1]))
            safe_created = html.escape(str(user[2]))
            st.markdown(f"""
            <div class="card">
                <h3 class="gold">مرحبًا {safe_username}</h3>
                <p>الخطة الحالية: {safe_plan}</p>
                <p>تاريخ التسجيل: {safe_created}</p>
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

        st.markdown("### طلبات التصميم الخاصة بي")
        if orders:
            st.dataframe(
                [
                    {
                        "نوع الطلب": o["category"],
                        "التفاصيل": o["details"],
                        "وسيلة التواصل": o["contact"],
                        "تاريخ الطلب": o["created"],
                        "حالة الطلب": o["status"]
                    }
                    for o in orders
                ],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("لم ترسل أي طلبات تصميم بعد.")


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

    st.info("إرسال الرسائل مباشرة إلى فريق الدعم وحفظ سجل المحادثات: قريبًا.")

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

            users = con.execute("""
                SELECT id, username, plan, created
                FROM users ORDER BY id DESC
            """).fetchall()
            payments = con.execute("""
                SELECT * FROM payments ORDER BY id DESC
            """).fetchall()
            orders = con.execute("""
                SELECT * FROM orders ORDER BY id DESC
            """).fetchall()

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

            if payments:
                st.dataframe(
                    [dict(p) for p in payments],
                    use_container_width=True
                )
            else:
                st.info("لا توجد طلبات دفع.")

            con.close()

            st.markdown("### إضافة عملية دفع يدويًا")
            st.caption("يمكن للمالك تسجيل عملية دفع استلمها خارج الموقع بعد التأكد منها بنفسه.")
            with st.form("owner_add_payment_form"):
                manual_username = st.selectbox(
                    "اختر حساب المستخدم",
                    [u["username"] for u in users],
                    index=None,
                    placeholder="اختر المستخدم"
                )
                manual_method = st.selectbox(
                    "طريقة استلام الدفع",
                    ["محفظة محلية", "تحويل بنكي", "نقدًا", "طريقة أخرى"]
                )
                manual_amount = st.text_input("المبلغ والعملة")
                manual_reference = st.text_input("رقم العملية أو وصفها")
                manual_status = st.selectbox(
                    "حالة العملية",
                    ["تم التحقق من الدفع", "قيد المراجعة", "مرفوض"]
                )
                add_manual_payment = st.form_submit_button(
                    "إضافة عملية الدفع إلى حساب المستخدم"
                )

            if add_manual_payment:
                if not users:
                    st.error("لا يوجد مستخدمون لإضافة عملية دفع لهم.")
                elif not manual_username or not manual_amount.strip() or not manual_reference.strip():
                    st.error("اختر المستخدم وأدخل المبلغ ومرجع العملية.")
                else:
                    con = connect_db()
                    con.execute("""
                        INSERT INTO payments
                        (username, method, amount, reference, status, created)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        manual_username,
                        manual_method,
                        manual_amount.strip(),
                        manual_reference.strip(),
                        manual_status,
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    if manual_status == "تم التحقق من الدفع":
                        con.execute(
                            "UPDATE users SET plan='Pro' WHERE username=?",
                            (manual_username,)
                        )
                    con.commit()
                    con.close()
                    st.success("تمت إضافة عملية الدفع إلى سجل المستخدم.")
                    st.rerun()

            st.markdown("### تحديث حالة طلب التصميم")
            if orders:
                order_options = {
                    f'طلب #{o["id"]} — {o["username"]} — {o["category"]}': o["id"]
                    for o in orders
                }
                selected_order_label = st.selectbox(
                    "اختر طلب التصميم",
                    list(order_options.keys())
                )
                order_status = st.selectbox(
                    "حالة طلب التصميم",
                    ["جديد", "قيد التنفيذ", "بانتظار مراجعة العميل", "مكتمل", "مرفوض"]
                )
                if st.button("حفظ حالة التصميم"):
                    con = connect_db()
                    con.execute(
                        "UPDATE orders SET status=? WHERE id=?",
                        (order_status, order_options[selected_order_label])
                    )
                    con.commit()
                    con.close()
                    st.success("تم تحديث حالة طلب التصميم.")
                    st.rerun()
            else:
                st.info("لا توجد طلبات لتحديث حالتها.")

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

            # ملخص سريع ونسخ احتياطية قابلة للتنزيل من لوحة المالك
            st.markdown("### ملخص المنصة")
            metric_a, metric_b, metric_c = st.columns(3)
            metric_a.metric("عدد المستخدمين", len(users))
            metric_b.metric("طلبات الدفع", len(payments))
            metric_c.metric("طلبات التصميم", len(orders))

            st.markdown("### تنزيل التقارير")
            export_a, export_b, export_c = st.columns(3)
            with export_a:
                st.download_button(
                    "تنزيل المستخدمين",
                    data=rows_to_csv(users),
                    file_name="number_one_users.csv",
                    mime="text/csv",
                    disabled=not users
                )
            with export_b:
                st.download_button(
                    "تنزيل المدفوعات",
                    data=rows_to_csv(payments),
                    file_name="number_one_payments.csv",
                    mime="text/csv",
                    disabled=not payments
                )
            with export_c:
                st.download_button(
                    "تنزيل طلبات التصميم",
                    data=rows_to_csv(orders),
                    file_name="number_one_orders.csv",
                    mime="text/csv",
                    disabled=not orders
                )

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
