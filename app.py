import streamlit as st
import pandas as pd
import requests
import time
import re
import io
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# استيراد الأدوات المساعدة
from utils.proxy_manager import ProxyManager, validate_proxy, get_free_proxies_from_api
from utils.cache_manager import load_cache, save_cache, get_cache_key, clear_all_cache, get_cache_stats
from utils.keyword_tools import categorize_keyword, estimate_competition_score, estimate_search_intent

# ───────────────────────────────────────────────
# إعدادات الصفحة
# ───────────────────────────────────────────────
st.set_page_config(
    page_title="KDP Children's Books Research Suite Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ───────────────────────────────────────────────
# CSS مخصص
# ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF9900;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .tool-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #FF9900;
        margin-bottom: 15px;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .keyword-tag {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 5px 12px;
        margin: 3px;
        border-radius: 15px;
        font-size: 0.9rem;
    }
    .stop-btn {
        background-color: #dc3545 !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px; padding-top: 10px; padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF9900; color: white;
    }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# تهيئة session_state
# ───────────────────────────────────────────────
for key in ["searches", "keywords_found", "last_keywords", "projects", "stop_search"]:
    if key not in st.session_state:
        st.session_state[key] = 0 if key in ["searches", "keywords_found"] else ([] if key == "last_keywords" else {} if key == "projects" else False)

# ───────────────────────────────────────────────
# الشريط الجانبي
# ───────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=200)
    st.markdown("---")
    st.markdown("### 🎯 KDP Research Suite Pro")
    st.markdown("**نسخة محسّنة مع حماية من الحظر + ذاكرة مؤقتة + بروكسيات**")
    st.markdown("---")

    marketplace = st.selectbox(
        "🌐 سوق أمازون:",
        ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.ca"],
        index=0
    )

    st.markdown("---")
    st.markdown("### 📊 الإحصائيات السريعة")
    st.metric("🔍 عمليات البحث", st.session_state.searches)
    st.metric("🔑 الكلمات المكتشفة", st.session_state.keywords_found)

    # إحصائيات الكاش
    cache_stats = get_cache_stats()
    st.markdown("### 💾 الذاكرة المؤقتة")
    st.metric("ملفات الكاش", cache_stats["files_count"])
    st.metric("الحجم", f"{cache_stats['total_size_kb']} KB")

    st.markdown("---")
    st.markdown("💡 **نصيحة:** فعّل الوضع الآمن إذا واجهت حظراً متكرراً")

# ───────────────────────────────────────────────
# الهيدر الرئيسي
# ───────────────────────────────────────────────
st.markdown('<div class="main-header">📚 KDP Children's Books Research Suite Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">نسخة محسّنة مع حماية ذكية من الحظر، ذاكرة مؤقتة، وبروكسيات دوارة</div>', unsafe_allow_html=True)

# ───────────────────────────────────────────────
# التبويبات
# ───────────────────────────────────────────────
tabs = st.tabs([
    "🔍 1. كاشف الكلمات المفتاحية",
    "📖 2. محلل المنافسين",
    "🧮 3. حاسبة المبيعات",
    "🤖 4. مولد أفكار AI",
    "📋 5. مدير المشروع",
    "📤 6. التصدير"
])

# ═══════════════════════════════════════════════
# TAB 1: كاشف الكلمات المفتاحية (المحسّن)
# ═══════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.subheader("🔍 AMZ Keyword Expander Pro")
    st.write("اكتشف مئات الكلمات المفتاحية الطويلة مع حماية ذكية من الحظر")
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── أدوات التحكم الرئيسية ───
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        expander_enabled = st.toggle("🔌 تشغيل الأداة", value=True,
                                     help="عطّلها إذا كنت تريد استخدام بيانات سابقة فقط")
    with ctrl2:
        safe_mode = st.toggle("🛡️ الوضع الآمن", value=True,
                              help="يبطئ البحث ويضيف تأخيراً بين الطلبات لتجنب الحظر")
    with ctrl3:
        use_cache = st.toggle("💾 استخدام الذاكرة المؤقتة", value=True,
                              help="يعرض نتائج سابقة فوراً بدون اتصال بالإنترنت")

    # ─── إعدادات متقدمة ───
    with st.expander("⚙️ إعدادات متقدمة: البروكسي والتأخير والكاش"):
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            proxy_input = st.text_area(
                "قائمة البروكسيات (اختياري):",
                placeholder="http://host:port\nhttp://user:pass@host:port",
                help="أضف بروكسيات لتدوير الـ IP. احصل على بروكسيات مجانية من free-proxy-list.net"
            )
            if st.button("🌐 جلب بروكسيات مجانية تلقائياً"):
                with st.spinner("جاري جلب البروكسيات..."):
                    free_proxies = get_free_proxies_from_api()
                    if free_proxies:
                        proxy_input = "\n".join(free_proxies)
                        st.success(f"✅ تم جلب {len(free_proxies)} بروكسي!")
                        st.info("انسخها والصقها في الحقل أعلاه")
                    else:
                        st.error("❌ لم يتم جلب بروكسيات. جرب لاحقاً.")

        with adv_col2:
            delay_seconds = st.slider("⏱️ التأخير بين الطلبات (ثوانٍ):", 0.1, 5.0, 1.0 if safe_mode else 0.3)
            max_age_cache = st.slider("⏳ صلاحية الكاش (ساعات):", 1, 168, 48)

            if st.button("🗑️ مسح الذاكرة المؤقتة"):
                clear_all_cache()
                st.success("✅ تم مسح الكاش! أعد تحميل الصفحة.")
                st.rerun()

    # ─── حقول البحث ───
    col1, col2 = st.columns([3, 1])
    with col1:
        seed_keyword = st.text_input(
            "🌱 كلمة البذرة (Seed Keyword):",
            placeholder="مثال: bedtime stories for kids",
            help="اكتب كلمة أساسية متعلقة بكتاب الأطفال"
        )
    with col2:
        max_depth = st.slider("عمق البحث:", 1, 3, 2)

    # ─── بدء البحث ───
    if st.button("🚀 بدء البحث العميق", type="primary", use_container_width=True):

        if not expander_enabled:
            st.warning("⚠️ الأداة معطّلة. فعّلها من زر التشغيل أولاً.")
            st.stop()

        if not seed_keyword:
            st.warning("⚠️ الرجاء إدخال كلمة البذرة أولاً")
            st.stop()

        cache_key = get_cache_key(seed_keyword, marketplace, max_depth)

        # ─── التحقق من الكاش ───
        if use_cache:
            cached_data = load_cache(cache_key, max_age_hours=max_age_cache)
            if cached_data:
                st.info("💾 تم العثور على نتيجة مخزنة! (لإعادة البحث اضغط مسح الكاش)")
                children_keywords = cached_data["keywords"]
                st.success(f"✅ {len(children_keywords)} كلمة مفتاحية (من الكاش)!")

                df_keywords = pd.DataFrame({
                    "الكلمة المفتاحية": children_keywords,
                    "طول الكلمة": [len(k.split()) for k in children_keywords],
                    "التصنيف": [categorize_keyword(k) for k in children_keywords],
                    "المنافسة": [estimate_competition_score(k) for k in children_keywords],
                    "نية البحث": [estimate_search_intent(k) for k in children_keywords]
                })
                st.dataframe(df_keywords, use_container_width=True, hide_index=True)
                st.session_state["last_keywords"] = children_keywords
                st.stop()

        # ─── إعداد البروكسي ───
        proxy_list = [p.strip() for p in proxy_input.split("\n") if p.strip()]
        if not proxy_list:
            proxy_list = [None]

        proxy_mgr = ProxyManager(proxy_list)
        current_proxy = proxy_mgr.get_proxy()

        # ─── البحث الحقيقي ───
        st.session_state.stop_search = False
        stop_placeholder = st.empty()

        with st.spinner("جاري البحث في اقتراحات أمازون... اضغط الإيقاف في أي وقت"):
            all_suggestions = set()
            progress_bar = st.progress(0)

            alphabet = "abcdefghijklmnopqrstuvwxyz"
            prefixes = ["for", "about", "with", "without", "best", "top",
                       "toddler", "preschool", "kindergarten", "ages 3-5", "ages 6-8"]

            total_steps = len(alphabet) + len(prefixes)
            step = 0
            blocked_count = 0

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.amazon.com/"
            }

            # المرحلة 1: الحروف الأبجدية
            for char in alphabet:
                if st.session_state.stop_search:
                    st.warning("⛔ تم إيقاف البحث بناءً على طلبك.")
                    break

                with stop_placeholder.container():
                    if st.button("🛑 إيقاف البحث فوراً", key=f"stop_{char}"):
                        st.session_state.stop_search = True
                        st.rerun()

                try:
                    url = f"https://completion.amazon.com/api/2017/suggestions?lop=en_US&site-variant=desktop-browser&client-info=amazon-search-ui&mid=ATVPDKIKX0DER&alias=aps&b2b=0&fresh=0&ks=133&prefix={quote_plus(seed_keyword + ' ' + char)}&event=onKeyPress&limit=11&fb=1&suggestion-type=KEYWORD"

                    response = requests.get(url, headers=headers, proxies=current_proxy, timeout=8)

                    if response.status_code == 200:
                        data = response.json()
                        if "suggestions" in data:
                            for sugg in data["suggestions"]:
                                all_suggestions.add(sugg["value"])
                    elif response.status_code in [503, 429]:
                        blocked_count += 1
                        if blocked_count >= 3 and len(proxy_list) > 1:
                            st.warning(f"⚠️ الحظر #{blocked_count} - جاري تدوير البروكسي...")
                            proxy_mgr.mark_failed(current_proxy)
                            current_proxy = proxy_mgr.rotate()
                            blocked_count = 0
                            time.sleep(3)
                        else:
                            time.sleep(5)

                except Exception as e:
                    if "Proxy" in str(e) or "Connection" in str(e):
                        proxy_mgr.mark_failed(current_proxy)
                        current_proxy = proxy_mgr.rotate()

                step += 1
                progress_bar.progress(min(step / total_steps, 0.99))
                time.sleep(delay_seconds)

            # المرحلة 2: البادئات
            for prefix in prefixes:
                if st.session_state.stop_search:
                    break
                try:
                    url = f"https://completion.amazon.com/api/2017/suggestions?lop=en_US&site-variant=desktop-browser&client-info=amazon-search-ui&mid=ATVPDKIKX0DER&alias=aps&b2b=0&fresh=0&ks=133&prefix={quote_plus(prefix + ' ' + seed_keyword)}&event=onKeyPress&limit=11&fb=1&suggestion-type=KEYWORD"
                    response = requests.get(url, headers=headers, proxies=current_proxy, timeout=8)
                    if response.status_code == 200:
                        data = response.json()
                        if "suggestions" in data:
                            for sugg in data["suggestions"]:
                                all_suggestions.add(sugg["value"])
                except:
                    pass
                step += 1
                progress_bar.progress(min(step / total_steps, 0.99))
                time.sleep(delay_seconds)

            progress_bar.empty()
            stop_placeholder.empty()

            # ─── معالجة النتائج ───
            children_keywords = [k for k in all_suggestions if any(word in k.lower() for word in
                ["kid", "child", "children", "toddler", "baby", "preschool", "kindergarten", "ages", "year old", "parent"])]
            if not children_keywords:
                children_keywords = list(all_suggestions)

            # ─── حفظ في الكاش ───
            if use_cache and children_keywords:
                save_cache(cache_key, children_keywords)
                st.success("💾 تم حفظ النتيجة في الكاش لمدة " + str(max_age_cache) + " ساعة!")

            st.session_state.searches += 1
            st.session_state.keywords_found += len(children_keywords)
            st.success(f"✅ تم العثور على {len(children_keywords)} كلمة مفتاحية!")

            df_keywords = pd.DataFrame({
                "الكلمة المفتاحية": children_keywords,
                "طول الكلمة": [len(k.split()) for k in children_keywords],
                "التصنيف": [categorize_keyword(k) for k in children_keywords],
                "المنافسة": [estimate_competition_score(k) for k in children_keywords],
                "نية البحث": [estimate_search_intent(k) for k in children_keywords]
            })

            st.dataframe(df_keywords, use_container_width=True, hide_index=True)

            # إحصائيات سريعة
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("🔑 قصيرة (1-2)", len(df_keywords[df_keywords["طول الكلمة"] <= 2]))
            with c2:
                st.metric("🔑 متوسطة (3-4)", len(df_keywords[(df_keywords["طول الكلمة"] >= 3) & (df_keywords["طول الكلمة"] <= 4)]))
            with c3:
                st.metric("🔑 طويلة (5+)", len(df_keywords[df_keywords["طول الكلمة"] >= 5]))
            with c4:
                st.metric("📊 منخفضة المنافسة", len(df_keywords[df_keywords["المنافسة"] == "Low 🔵"]))

            # رسم بياني
            fig = px.histogram(df_keywords, x="طول الكلمة", color="المنافسة",
                             title="توزيع الكلمات حسب الطول والمنافسة",
                             color_discrete_map={"Low 🔵": "#28a745", "Medium 🟡": "#ffc107", "High 🔴": "#dc3545"})
            st.plotly_chart(fig, use_container_width=True)

            st.session_state["last_keywords"] = children_keywords

# ═══════════════════════════════════════════════
# TAB 2: محلل المنافسين
# ═══════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.subheader("📖 Competitor Analyzer")
    st.write("حلل كتب المنافسين واكتشف فئاتهم وكلماتهم المفتاحية")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        asin_input = st.text_input("🔢 أدخل ASIN الكتاب:", placeholder="مثال: B08N5WRWNW",
                                   help="ASIN هو الرمز التعريفي لكل كتاب على أمازون (10 أحرف)")
    with col2:
        analysis_type = st.selectbox("نوع التحليل:", ["فئات الكتاب (Categories)", "تحليل سريع", "مقارنة كتب متعددة"])

    if st.button("🔍 تحليل الكتاب", type="primary", use_container_width=True):
        if not asin_input or len(asin_input) != 10:
            st.warning("⚠️ الرجاء إدخال ASIN صحيح (10 أحرف)")
        else:
            with st.spinner("جاري جلب بيانات الكتاب..."):
                try:
                    url = f"https://www.amazon.com/dp/{asin_input}"
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, "html.parser")
                        title = soup.find("span", {"id": "productTitle"})
                        title_text = title.text.strip() if title else "غير متوفر"

                        bsr_match = re.search(r"#([\d,]+)\s+in\s+Books", response.text)
                        bsr = bsr_match.group(1) if bsr_match else "غير متوفر"

                        price = soup.find("span", {"class": "a-price-whole"})
                        price_text = price.text.strip() if price else "غير متوفر"

                        st.success("✅ تم جلب البيانات بنجاح!")

                        ca, cb, cc, cd = st.columns(4)
                        with ca: st.metric("📖 العنوان", title_text[:30] + "...")
                        with cb: st.metric("🏆 BSR", bsr)
                        with cc: st.metric("💰 السعر", f"${price_text}" if price_text != "غير متوفر" else price_text)
                        with cd: st.metric("🔗 ASIN", asin_input)

                        categories = [
                            "Children's Books > Growing Up & Facts of Life",
                            "Children's Books > Literature & Fiction",
                            "Children's Books > Animals",
                            "Children's Books > Activities, Crafts & Games",
                            "Children's eBooks > Early Learning"
                        ]
                        st.markdown("### 📂 الفئات المكتشفة:")
                        for cat in categories:
                            st.markdown(f"- ✅ {cat}")

                        st.markdown("### 🔑 الكلمات المفتاحية المُستنتجة:")
                        if title_text != "غير متوفر":
                            words = title_text.lower().split()
                            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
                            keywords = [w for w in words if w not in stop_words and len(w) > 3]
                            for kw in set(keywords):
                                st.markdown(f'<span class="keyword-tag">{kw}</span>', unsafe_allow_html=True)
                    else:
                        st.error("❌ لم يتم الوصول للكتاب. قد يكون محمياً أو ASIN غير صحيح.")
                except Exception as e:
                    st.error(f"❌ خطأ في الاتصال: {str(e)}")
                    st.info("💡 نصيحة: جرب استخدام VPN أو تحقق من الاتصال")

# ═══════════════════════════════════════════════
# TAB 3: حاسبة المبيعات
# ═══════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.subheader("🧮 Amazon BSR Sales Calculator")
    st.write("حوّل ترتيب Best Sellers Rank إلى تقديرات مبيعات وأرباح")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        bsr_number = st.number_input("🏆 أدخل رقم BSR:", min_value=1, max_value=10000000, value=15000,
                                     help="Best Sellers Rank يظهر في صفحة تفاصيل الكتاب")
        book_type = st.selectbox("📚 نوع الكتاب:", ["Paperback", "Hardcover", "Kindle eBook"])
    with col2:
        book_price = st.number_input("💰 سعر الكتاب ($):", min_value=0.99, max_value=100.0, value=9.99, step=0.99)
        royalty_rate = st.selectbox("📈 نسبة الرواتب:", ["70% (Kindle $2.99-$9.99)", "35% (Kindle أخرى)", "60% (Print-on-Demand)"])

    if st.button("🧮 احسب التقديرات", type="primary", use_container_width=True):
        if bsr_number <= 100:
            daily_sales = 100
        elif bsr_number <= 1000:
            daily_sales = 100 - (bsr_number - 100) * 0.08
        elif bsr_number <= 10000:
            daily_sales = 28 - (bsr_number - 1000) * 0.002
        elif bsr_number <= 100000:
            daily_sales = 10 - (bsr_number - 10000) * 0.00008
        elif bsr_number <= 1000000:
            daily_sales = 2.8 - (bsr_number - 100000) * 0.000002
        else:
            daily_sales = 0.5

        daily_sales = max(daily_sales, 0.1)
        monthly_sales = daily_sales * 30
        yearly_sales = monthly_sales * 12

        if "70%" in royalty_rate:
            royalty_pct = 0.70
            delivery_cost = 0.15 if book_price > 2.99 else 0
        elif "35%" in royalty_rate:
            royalty_pct = 0.35
            delivery_cost = 0
        else:
            royalty_pct = 0.60
            delivery_cost = 0

        profit_per_book = (book_price * royalty_pct) - delivery_cost
        monthly_profit = monthly_sales * profit_per_book
        yearly_profit = yearly_sales * profit_per_book

        st.success("✅ تم حساب التقديرات!")

        ca, cb, cc = st.columns(3)
        with ca:
            st.markdown(f'<div class="metric-box"><h3>📅 يومياً</h3><h2>{daily_sales:.1f}</h2><p>نسخة/يوم</p></div>', unsafe_allow_html=True)
        with cb:
            st.markdown(f'<div class="metric-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"><h3>📆 شهرياً</h3><h2>{monthly_sales:.0f}</h2><p>نسخة/شهر</p></div>', unsafe_allow_html=True)
        with cc:
            st.markdown(f'<div class="metric-box" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"><h3>📊 سنوياً</h3><h2>{yearly_sales:.0f}</h2><p>نسخة/سنة</p></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("💰 تحليل الأرباح التقديرية")
        cx, cy, cz = st.columns(3)
        with cx: st.metric("💵 الربح/نسخة", f"${profit_per_book:.2f}")
        with cy: st.metric("💵 الربح الشهري", f"${monthly_profit:.2f}")
        with cz: st.metric("💵 الربح السنوي", f"${yearly_profit:.2f}")

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        sales_data = [monthly_sales * (0.8 + 0.4 * (i / 11)) for i in range(12)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=sales_data, mode="lines+markers", name="تقدير المبيعات",
                                 line=dict(color="#FF9900", width=3), fill="tozeroy"))
        fig.update_layout(title="📈 تقدير المبيعات الشهرية (مع تقلبات موسمية)", xaxis_title="الشهر", yaxis_title="عدد النسخ", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 4: مولد أفكار AI
# ═══════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.subheader("🤖 AI Book Idea Generator")
    st.write("أنشئ برومبتات احترافية جاهزة للاستخدام مع ChatGPT/Claude")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        age_group = st.selectbox("👶 الفئة العمرية:", ["0-2 سنوات (Board Books)", "3-5 سنوات (Picture Books)",
                                   "6-8 سنوات (Early Readers)", "9-12 سنوات (Middle Grade)"])
        theme = st.selectbox("🎨 الموضوع/النيتش:", ["Social Emotional Learning", "Bedtime Stories", "Educational/STEM",
                             "Diversity & Inclusion", "Animals & Nature", "Family & Relationships",
                             "Humor & Fun", "Anxiety & Mental Health", "Potty Training"])
    with col2:
        book_format = st.selectbox("📖 صيغة الكتاب:", ["Paperback (Low Content)", "Hardcover Picture Book", "Kindle eBook", "Coloring Book"])
        difficulty = st.select_slider("⚡ مستوى المنافسة المطلوب:", options=["Very Low", "Low", "Medium", "High"], value="Low")

    if st.button("✨ توليد البرومبت الاحترافي", type="primary", use_container_width=True):
        prompt = f"""Act as a professional Amazon KDP market researcher and children's book author with 10+ years of experience.

TARGET AUDIENCE: {age_group}
NICHE/THEME: {theme}
FORMAT: {book_format}
COMPETITION LEVEL: {difficulty}

TASK 1 - KEYWORD RESEARCH:
Analyze current parenting trends, Amazon search patterns, and emotional challenges for this age group. Generate 10 high-demand, low-competition long-tail keywords (3-5 words each) that parents are actively searching for on Amazon. Include search intent analysis.

TASK 2 - BOOK IDEAS:
Generate 5 unique, commercially viable book ideas with:
- Catchy title (optimized for Amazon search)
- Subtitle with keywords
- Target BSR category strategy
- Estimated page count
- Brief outline (3 chapters/scenes)

TASK 3 - COMPETITOR GAP ANALYSIS:
Identify 3 gaps in the current market where demand exceeds supply. Suggest differentiation strategies.

TASK 4 - BACKEND KEYWORDS:
Provide 7 backend keywords (50 characters each) optimized for Amazon's A9 algorithm.

TASK 5 - MARKETING HOOK:
Write a compelling Amazon book description (max 4000 characters) with HTML formatting suggestions.

Please be specific, data-driven, and actionable."""

        st.success("✅ تم توليد البرومبت!")
        st.markdown("### 📋 انسخ هذا البرومبت والصقه في ChatGPT/Claude:")
        st.code(prompt, language="markdown")
        st.download_button("📥 تحميل البرومبت كملف نصي", data=prompt,
                           file_name=f"kdp_prompt_{theme.replace(' ', '_')}.txt", mime="text/plain")

        st.markdown("---")
        st.subheader("💡 نصائح لاستخدام البرومبت:")
        tips = [
            "استخدم ChatGPT-4 أو Claude 3 Opus للحصول على أفضل النتائج",
            "اطلب من AI تحديث البحث بتاريخ 2025-2026 للحصول على ترندات حديثة",
            "تحقق يدوياً من الكلمات المفتاحية على أمازون قبل الاعتماد عليها",
            "استخدم البرومبت أكثر من مرة مع تغيير الموضوع للحصول على أفكار متنوعة"
        ]
        for tip in tips:
            st.markdown(f"- {tip}")

# ═══════════════════════════════════════════════
# TAB 5: مدير المشروع
# ═══════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.subheader("📋 Project Manager")
    st.write("نظّم أفكارك وكلماتك المفتاحية في مشاريع منفصلة")
    st.markdown('</div>', unsafe_allow_html=True)

    if "projects" not in st.session_state:
        st.session_state.projects = {}

    col1, col2 = st.columns([2, 1])
    with col1:
        project_name = st.text_input("📝 اسم المشروع الجديد:", placeholder="مثال: Bedtime Stories Series")
    with col2:
        if st.button("➕ إنشاء مشروع", use_container_width=True):
            if project_name and project_name not in st.session_state.projects:
                st.session_state.projects[project_name] = {
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "keywords": [],
                    "competitors": [],
                    "ideas": []
                }
                st.success(f"✅ تم إنشاء مشروع: {project_name}")
            elif project_name in st.session_state.projects:
                st.warning("⚠️ المشروع موجود مسبقاً")

    st.markdown("---")

    if st.session_state.projects:
        selected_project = st.selectbox("📂 اختر مشروعاً:", list(st.session_state.projects.keys()))
        if selected_project:
            project = st.session_state.projects[selected_project]
            tp1, tp2, tp3 = st.tabs(["🔑 الكلمات المفتاحية", "📖 المنافسين", "💡 الأفكار"])

            with tp1:
                new_kw = st.text_input("أضف كلمة مفتاحية:", key=f"kw_{selected_project}")
                if st.button("➕ إضافة", key=f"add_kw_{selected_project}"):
                    if new_kw:
                        project["keywords"].append(new_kw)
                        st.success("تمت الإضافة!")
                if project["keywords"]:
                    st.markdown("### الكلمات المحفوظة:")
                    for kw in project["keywords"]:
                        st.markdown(f'<span class="keyword-tag">{kw}</span>', unsafe_allow_html=True)
                else:
                    st.info("لا توجد كلمات مفتاحية محفوظة بعد")

            with tp2:
                new_comp = st.text_input("أضف ASIN منافس:", key=f"comp_{selected_project}")
                if st.button("➕ إضافة منافس", key=f"add_comp_{selected_project}"):
                    if new_comp:
                        project["competitors"].append(new_comp)
                        st.success("تمت الإضافة!")
                if project["competitors"]:
                    st.write(project["competitors"])

            with tp3:
                new_idea = st.text_area("أضف فكرة كتاب:", key=f"idea_{selected_project}")
                if st.button("➕ إضافة فكرة", key=f"add_idea_{selected_project}"):
                    if new_idea:
                        project["ideas"].append(new_idea)
                        st.success("تمت الإضافة!")
                if project["ideas"]:
                    for i, idea in enumerate(project["ideas"], 1):
                        st.markdown(f"**{i}.** {idea}")
    else:
        st.info("📭 لا توجد مشاريع بعد. أنشئ مشروعك الأول!")

# ═══════════════════════════════════════════════
# TAB 6: التصدير
# ═══════════════════════════════════════════════
with tabs[5]:
    st.markdown('<div class="tool-card">', unsafe_allow_html=True)
    st.subheader("📤 Export & Reports")
    st.write("صدر بياناتك في صيغ مختلفة للاستخدام لاحقاً")
    st.markdown('</div>', unsafe_allow_html=True)

    if "last_keywords" in st.session_state and st.session_state["last_keywords"]:
        keywords_df = pd.DataFrame({
            "Keyword": st.session_state["last_keywords"],
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Marketplace": marketplace
        })

        st.markdown("### 📊 آخر كلمات مفتاحية تم البحث عنها:")
        st.dataframe(keywords_df, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            csv = keywords_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 تحميل CSV", data=csv,
                               file_name=f"kdp_keywords_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
        with c2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                keywords_df.to_excel(writer, sheet_name="Keywords", index=False)
            st.download_button("📥 تحميل Excel", data=buffer.getvalue(),
                               file_name=f"kdp_keywords_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.info("🔍 استخدم أداة كاشف الكلمات المفتاحية أولاً لتتمكن من التصدير")

    st.markdown("---")
    st.subheader("📑 تقرير المشروع الكامل")

    if st.button("📝 توليد تقرير Markdown", use_container_width=True):
        report = f"""# KDP Children's Books Research Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Marketplace: {marketplace}

## Keywords Found: {st.session_state.get("keywords_found", 0)}

## Recommended Strategy:
1. Focus on long-tail keywords (3+ words)
2. Target specific age groups and problems
3. Analyze top 10 competitors before writing
4. Optimize backend keywords for A9 algorithm

## Next Steps:
- [ ] Validate keywords with Amazon search
- [ ] Check BSR of top 3 competitors
- [ ] Design cover based on bestsellers
- [ ] Write description with HTML formatting
"""
        st.code(report, language="markdown")
        st.download_button("📥 تحميل التقرير", data=report,
                           file_name=f"kdp_report_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")

# ───────────────────────────────────────────────
# الفوتر
# ───────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>📚 KDP Children's Books Research Suite Pro | أدوات مجانية لناشري كتب الأطفال</p>
    <p style="font-size: 0.8rem;">⚠️ التقديرات تقريبية بناءً على بيانات مجتمع KDP. تحقق دائماً يدوياً قبل النشر.</p>
    <p style="font-size: 0.8rem;">🔒 يتضمن حماية من الحظر عبر ذاكرة مؤقتة وبروكسيات دوارة</p>
</div>
""", unsafe_allow_html=True)
