import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq
import httpx
import json, time
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Spice Garden — Owner Dashboard",
                   page_icon="📊", layout="wide")

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background:#FAFAFA; }
  .brand-bar { background:linear-gradient(135deg,#C0392B,#922B21);
               padding:18px 28px; border-radius:12px; color:white; margin-bottom:24px; }
  .brand-bar h2 { margin:0; font-size:24px; font-weight:700; }
  .brand-bar p  { margin:4px 0 0; font-size:13px; opacity:0.85; }
  .section { font-size:17px; font-weight:600; margin:28px 0 10px; color:#1a1a1a;
             border-left:3px solid #C0392B; padding-left:10px; }
  .agent-card { border-radius:10px; padding:14px 18px; margin-bottom:10px;
                border:1px solid #eee; background:white; }
  .agent-title { font-size:13px; font-weight:600; margin-bottom:6px; }
  .agent-idle    { border-left:3px solid #ddd; }
  .agent-running { border-left:3px solid #f0ad4e; background:#FFFBF0; }
  .agent-done    { border-left:3px solid #5cb85c; background:#F4FBF4; }
  .agent-error   { border-left:3px solid #d9534f; background:#FDF4F4; }
  .insight-card { border-radius:10px; padding:14px 18px; margin-bottom:10px;
                  background:white; border:1px solid #eee; font-size:13px; line-height:1.8; }
  .summary-box { background:#EAF3DE; border-radius:12px; padding:20px 24px;
                 font-size:14px; color:#1a3a1a; line-height:1.9; }
  .crisis-box  { background:#FCEBEB; border-radius:12px; padding:16px 20px;
                 font-size:13px; color:#5a1a1a; line-height:1.8; margin-bottom:10px; }
  .quote-card  { border-radius:8px; padding:10px 14px; margin-bottom:8px;
                 font-size:12px; line-height:1.6; }
  .badge { display:inline-block; font-size:11px; font-weight:600; padding:2px 8px;
           border-radius:20px; margin-right:4px; }
  .badge-pos { background:#EAF3DE; color:#27500A; }
  .badge-neg { background:#FCEBEB; color:#791F1F; }
  .badge-neu { background:#F1EFE8; color:#555; }
  .trend-up   { color:#27500A; font-weight:600; }
  .trend-down { color:#791F1F; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN GATE
# ─────────────────────────────────────────────────────────────────────────────

LOGIN_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,400&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0d0604 0%, #1e0a06 35%, #2d1208 60%, #0d0604 100%) !important;
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent !important; }

.login-wrap {
    max-width: 420px;
    margin: 80px auto 0;
    padding: 0 20px;
}
.login-brand {
    text-align: center;
    margin-bottom: 36px;
}
.login-icon { font-size: 50px; filter: drop-shadow(0 4px 16px rgba(255,120,40,0.5)); }
.login-brand h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 40px;
    font-style: italic;
    font-weight: 600;
    color: #f5c87a;
    margin: 8px 0 4px;
    letter-spacing: 1px;
}
.login-brand .sub {
    font-family: 'Jost', sans-serif;
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(255,200,130,0.5);
    font-weight: 300;
}
.login-card {
    background: rgba(20, 8, 2, 0.65);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,160,60,0.2);
    border-radius: 20px;
    padding: 36px 36px 32px;
    box-shadow: 0 30px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,200,100,0.08);
}
.login-card-title {
    font-family: 'Jost', sans-serif;
    font-size: 11px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: rgba(255,180,80,0.55);
    text-align: center;
    margin-bottom: 28px;
    font-weight: 500;
}
div[data-testid="stTextInput"] label {
    font-family: 'Jost', sans-serif !important;
    font-weight: 500 !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: rgba(255,200,130,0.65) !important;
}
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,160,60,0.22) !important;
    border-radius: 10px !important;
    color: #000000 !important;
    font-family: 'Jost', sans-serif !important;
    font-size: 14px !important;
    font-weight: 300 !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(255,160,60,0.5) !important;
    box-shadow: 0 0 0 2px rgba(255,130,30,0.1) !important;
}
.stButton > button {
    width: 100%;
    border-radius: 10px;
    background: linear-gradient(135deg, #b83c10, #e06a0a);
    color: #fff8ec;
    font-family: 'Jost', sans-serif;
    font-weight: 500;
    font-size: 12px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    border: none;
    padding: 13px;
    margin-top: 6px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(180,60,10,0.35);
}
.stButton > button:hover {
    box-shadow: 0 6px 28px rgba(220,100,20,0.5);
    transform: translateY(-1px);
}
.login-footer {
    text-align: center;
    margin-top: 22px;
    font-family: 'Jost', sans-serif;
    font-size: 11px;
    letter-spacing: 1.5px;
    color: rgba(200,150,80,0.35);
    text-transform: uppercase;
}
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    background: rgba(200,50,30,0.15) !important;
    border: 1px solid rgba(200,50,30,0.3) !important;
    color: #ffb09a !important;
}
/* Hide sidebar filters & session */
[data-testid="stSidebarContent"] .stExpander,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] .stMarkdown h2 {
    display: none !important;
}
</style>
"""

def show_login():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown('''
<div class="login-wrap">
  <div class="login-brand">
    <div class="login-icon">🍽️</div>
    <h1>Spice Garden</h1>
    <div class="sub">Intelligence Dashboard</div>
  </div>
  <div class="login-card">
    <div class="login-card-title">Owner Access Only</div>
''', unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="Enter your username", key="login_user")
    password = st.text_input("Password", placeholder="Enter your password", type="password", key="login_pass")

    if st.button("Sign In →", key="login_btn"):
        valid_user = st.secrets.get("DASHBOARD_USER", "123")
        valid_pass = st.secrets.get("DASHBOARD_PASS", "123")
        if username == valid_user and password == valid_pass:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect credentials. Please try again.")

    st.markdown('''
  </div>
  <div class="login-footer">Spice Garden · Secured Owner Portal · Bengaluru</div>
</div>
''', unsafe_allow_html=True)

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not st.session_state.get("authenticated", False):
    show_login()
    st.stop()

st.markdown("""
<div class="brand-bar">
  <h2>🍽️ Spice Garden — Owner Intelligence Dashboard</h2>
  <p>Real-time review analysis across all branches</p>
</div>
""", unsafe_allow_html=True)

BRANCHES = [
    "Spice Garden — Koramangala",
    "Spice Garden — Indiranagar",
    "Spice Garden — Whitefield",
    "Spice Garden — JP Nagar",
    "Spice Garden — HSR Layout",
]
COLOR = {"positive":"#5cb85c","neutral":"#f0ad4e","negative":"#d9534f"}
BG    = {"positive":"#EAF3DE","neutral":"#FFF8E6","negative":"#FCEBEB"}
TC    = {"positive":"#27500A","neutral":"#5a3e00","negative":"#5a1a1a"}

# ── Clients ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_groq():
    http_client = httpx.Client(verify=False)
    return Groq(api_key=st.secrets["GROQ_API_KEY"], http_client=http_client)

def get_sheet():
    scopes = ["https://spreadsheets.google.com/feeds",
              "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_key(st.secrets["SHEET_ID"]).sheet1

@st.cache_data(ttl=15)
def load_reviews():
    sheet = get_sheet()
    rows  = sheet.get_all_values()
    if len(rows) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(rows[1:], columns=["timestamp","branch","name","stars","review","status"])
    df["stars"] = pd.to_numeric(df["stars"], errors="coerce").fillna(3).astype(int)
    df = df[df["review"].str.strip() != ""]
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

# ─────────────────────────────────────────────────────────────────────────────
# MULTI-AGENT SYSTEM
# Each agent has one job. They run in sequence and pass context forward.
# ─────────────────────────────────────────────────────────────────────────────

def call_agent(system_prompt: str, user_msg: str, max_tokens=1200) -> dict:
    """Core LLM call — all agents use this. Returns parsed JSON."""
    groq = get_groq()
    resp = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content": system_prompt},
            {"role":"user",  "content": user_msg}
        ],
        max_tokens=max_tokens,
        temperature=0.1,
    )
    raw = resp.choices[0].message.content.strip()
    raw = raw.replace("```json","").replace("```","").strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])


# ── Agent 1: Preprocessor ─────────────────────────────────────────────────────
PREPROCESS_SYS = """You are a Review Preprocessor Agent. Your only job is to clean
and categorise raw restaurant reviews. Detect the language, fix obvious typos in meaning,
flag spam/fake reviews, and extract structured metadata.
Respond ONLY with valid JSON — no markdown, no explanation."""

def agent_preprocessor(df: pd.DataFrame) -> dict:
    reviews_raw = [
        {"id": i+1, "stars": int(row.stars),
         "branch": row.branch.replace("Spice Garden — ",""),
         "text": row.review}
        for i, row in df.iterrows()
    ]
    result = call_agent(
        PREPROCESS_SYS,
        f"""Clean and categorise these reviews. Return:
{{
  "total": <int>,
  "usable": <int — not spam>,
  "spam_count": <int>,
  "languages_detected": ["English", ...],
  "reviews": [
    {{"id":<int>,"branch":"<str>","stars":<int>,"clean_text":"<cleaned review>","is_spam":<bool>,"meal_type":"dine_in or takeaway or delivery or unknown"}}
  ]
}}
Reviews: {json.dumps(reviews_raw)}"""
    )
    return result


# ── Agent 2: Feature Extractor ────────────────────────────────────────────────
FEATURE_SYS = """You are a Feature Extraction Agent specialised in restaurant reviews.
Your only job is to identify which product/service features customers talk about.
You must detect implicit mentions too — e.g. 'waited 40 minutes' implies 'Service Speed'.
Respond ONLY with valid JSON — no markdown, no explanation."""

def agent_feature_extractor(cleaned_reviews: list) -> dict:
    texts = [f"Review {r['id']} ({r['stars']}★, {r['branch']}): {r['clean_text']}"
             for r in cleaned_reviews if not r.get("is_spam")]
    result = call_agent(
        FEATURE_SYS,
        f"""Extract features from these restaurant reviews. Return:
{{
  "features": [
    {{
      "name": "<feature name>",
      "mentions": <int>,
      "review_ids": [<ids that mention this>],
      "sample_phrases": ["<phrase1>","<phrase2>"]
    }}
  ]
}}
Possible features: Food Quality, Taste & Flavour, Portion Size, Service Speed,
Staff Behaviour, Cleanliness, Ambience, Price/Value, Packaging, Order Accuracy,
Waiting Time, Drinks/Beverages. Only include features actually mentioned.
Reviews: {chr(10).join(texts)}"""
    )
    return result


# ── Agent 3: Sentiment Scorer ─────────────────────────────────────────────────
SENTIMENT_SYS = """You are a Sentiment Scoring Agent. Your only job is to score
the sentiment for each feature, per branch, using evidence from the reviews.
Be precise — distinguish 'food is good overall but taste is bland' as positive
for Food Quality but negative for Taste. Use context, not just keywords.
Respond ONLY with valid JSON — no markdown, no explanation."""

def agent_sentiment_scorer(cleaned_reviews: list, features: dict) -> dict:
    texts = [f"Review {r['id']} ({r['stars']}★, {r['branch']}): {r['clean_text']}"
             for r in cleaned_reviews if not r.get("is_spam")]
    feat_names = [f["name"] for f in features["features"]]
    branches   = list(set(r["branch"] for r in cleaned_reviews))
    result = call_agent(
        SENTIMENT_SYS,
        f"""Score sentiment for each feature overall and per branch. Return:
{{
  "overall_score": <0-100>,
  "overall_sentiment": "positive|neutral|negative",
  "scored_features": [
    {{
      "name": "<feature>",
      "score": <0-100>,
      "sentiment": "positive|neutral|negative",
      "mentions": <int>,
      "confidence": "high|medium|low",
      "best_quote": "<exact short quote from reviews>",
      "branch_scores": {{"<branch>": <0-100>}}
    }}
  ],
  "branch_overall": {{"<branch>": {{"score":<0-100>,"sentiment":"..."}}}}
}}
Features to score: {feat_names}
Branches: {branches}
Reviews: {chr(10).join(texts)}""",
        max_tokens=1500
    )
    return result


# ── Agent 4: Insight Generator ────────────────────────────────────────────────
INSIGHT_SYS = """You are a Business Insight Agent for a restaurant chain owner.
Your only job is to turn sentiment scores into actionable business intelligence.
Think like a restaurant consultant — identify root causes, spot trends, prioritise fixes.
Respond ONLY with valid JSON — no markdown, no explanation."""

def agent_insight_generator(sentiment_data: dict, df: pd.DataFrame) -> dict:
    avg_stars = float(df["stars"].mean())
    review_count = len(df)
    result = call_agent(
        INSIGHT_SYS,
        f"""Generate business insights from this sentiment analysis for Spice Garden restaurant chain.
Current avg rating: {avg_stars:.1f}/5 from {review_count} reviews.
Sentiment data: {json.dumps(sentiment_data)}

Return:
{{
  "executive_summary": "<3 sentence summary for the owner>",
  "top_3_strengths": ["<strength 1>","<strength 2>","<strength 3>"],
  "top_3_problems": ["<problem 1>","<problem 2>","<problem 3>"],
  "crisis_alerts": ["<any feature scoring below 35 — urgent action needed>"],
  "weekly_actions": [
    {{"priority":"high|medium|low","action":"<specific thing to do>","expected_impact":"<what improves>"}}
  ],
  "best_branch": "<branch name>",
  "worst_branch": "<branch name>",
  "best_branch_reason": "<why it scores highest>",
  "worst_branch_reason": "<what the worst branch should fix>",
  "predicted_rating_if_fixed": "<e.g. 4.2 stars if delivery time is fixed>"
}}"""
    )
    return result


# ── Agent 5: Report Writer ────────────────────────────────────────────────────
REPORT_SYS = """You are a Report Writing Agent. Your only job is to write a
clear, concise weekly report for a restaurant owner — no jargon, plain English,
like advice from a trusted business advisor. Be specific with numbers and branch names.
Use short paragraphs. Every claim must be backed by a score or customer evidence.
Respond ONLY with valid JSON — no markdown, no explanation."""

def agent_report_writer(insights: dict, sentiment: dict) -> dict:
    result = call_agent(
        REPORT_SYS,
        f"""Write a weekly intelligence report for Spice Garden owner based on:
Insights: {json.dumps(insights)}
Scores: {json.dumps(sentiment.get('scored_features',[]))}

Return:
{{
  "headline": "<one punchy headline summarising this week — include a key number>",
  "one_liner": "<single memorable sentence the owner should act on today>",
  "what_is_working": "<2-3 sentences: specific features and branches that are strong, with scores>",
  "what_needs_fixing": "<2-3 sentences: specific features and branches that are weak, with scores and customer evidence>",
  "this_week_focus": "<1-2 sentences: the single most important thing to fix this week and why>",
  "customer_voice": "<2-3 sentences paraphrasing what customers are saying — use their language, quote flavour without copying verbatim>",
  "competitor_risk": "<2 sentences: what might happen if problems are not fixed — be specific about which competitor type benefits>",
  "owner_note": "<1 warm, direct sentence encouraging the owner — acknowledge what they are doing right>"
}}""",
        max_tokens=1200
    )
    return result



# ── Run full pipeline ─────────────────────────────────────────────────────────
def run_full_pipeline(df: pd.DataFrame, agent_status: dict, placeholders: dict):
    """Runs all 5 agents in sequence, updating UI live."""

    def update(agent_key, state, msg=""):
        agent_status[agent_key] = (state, msg)
        render_pipeline(agent_status, placeholders["pipeline"])

    # Agent 1
    update("preprocess", "running")
    pre = agent_preprocessor(df)
    update("preprocess", "done", f"{pre.get('usable', len(df))} usable reviews, {pre.get('spam_count',0)} spam detected")

    clean_reviews = pre.get("reviews", [
        {"id":i+1,"branch":row.branch.replace("Spice Garden — ",""),
         "stars":int(row.stars),"clean_text":row.review,"is_spam":False}
        for i, row in df.iterrows()
    ])

    # Agent 2
    update("features", "running")
    feat_data = agent_feature_extractor(clean_reviews)
    n_feat = len(feat_data.get("features", []))
    update("features", "done", f"{n_feat} features detected")

    # Agent 3
    update("sentiment", "running")
    sent_data = agent_sentiment_scorer(clean_reviews, feat_data)
    score = sent_data.get("overall_score", 0)
    update("sentiment", "done", f"Overall score: {score}/100")

    # Agent 4
    update("insights", "running")
    insight_data = agent_insight_generator(sent_data, df)
    n_actions = len(insight_data.get("weekly_actions", []))
    update("insights", "done", f"{n_actions} action items generated")

    # Agent 5
    update("report", "running")
    report_data = agent_report_writer(insight_data, sent_data)
    update("report", "done", f'"{report_data.get("headline","Report ready")}"')

    return pre, feat_data, sent_data, insight_data, report_data


def render_pipeline(status: dict, placeholder):
    icons = {"idle":"⬜","running":"🟡","done":"🟢","error":"🔴"}
    labels = {
        "preprocess": "Agent 1 — Preprocessor",
        "features":   "Agent 2 — Feature Extractor",
        "sentiment":  "Agent 3 — Sentiment Scorer",
        "insights":   "Agent 4 — Insight Generator",
        "report":     "Agent 5 — Report Writer",
    }
    html = '<div style="display:flex;flex-direction:column;gap:6px;">'
    for key, label in labels.items():
        state, msg = status.get(key, ("idle",""))
        css = f"agent-{state}"
        spin = ' <span style="color:#f0ad4e;">⟳ working...</span>' if state=="running" else ""
        detail = f'<span style="font-size:11px;color:#777;"> — {msg}</span>' if msg else ""
        html += (f'<div class="agent-card {css}">'
                 f'<span class="agent-title">{icons[state]} {label}{spin}</span>'
                 f'{detail}</div>')
    html += "</div>"
    placeholder.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.sidebar.markdown("---")
    if st.sidebar.button("Sign Out →"):
        st.session_state.authenticated = False
        st.rerun()

    df_all = load_reviews()

    if df_all.empty:
        st.info("No reviews yet.\nShare the customer app link!")
        st.stop()

    branch_choice = st.selectbox("Branch", ["All Branches"] + BRANCHES)
    df = df_all.copy()
    if branch_choice != "All Branches":
        df = df[df["branch"] == branch_choice]

    if df.empty:
        st.warning("No reviews for this branch yet.")
        st.stop()

    st.markdown("---")
    st.metric("Total reviews", len(df))
    st.metric("Avg rating",    f"{df['stars'].mean():.1f} ★")
    st.metric("5★ reviews",    len(df[df["stars"]==5]))
    st.metric("1★ reviews",    len(df[df["stars"]==1]))
    st.markdown("---")
    run_btn = st.button("🤖 Run Multi-Agent Analysis", type="primary", use_container_width=True)
    if st.button("🔄 Refresh reviews", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("🗑️ Clear analysis", use_container_width=True):
        for k in ["ai_full","ai_branch"]:
            st.session_state.pop(k, None)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# REVIEWS TABLE + CHARTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section">📋 Latest Reviews</div>', unsafe_allow_html=True)
show_df = df[["timestamp","branch","name","stars","review"]].copy()
show_df["timestamp"] = show_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
show_df = show_df.sort_values("timestamp", ascending=False).head(30)
show_df.columns = ["Time","Branch","Customer","Stars","Review"]
st.dataframe(show_df, use_container_width=True, hide_index=True,
    column_config={
        "Stars":  st.column_config.NumberColumn("Stars ★", format="%d ★"),
        "Review": st.column_config.TextColumn("Review", width="large"),
        "Branch": st.column_config.TextColumn("Branch", width="medium"),
    })

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="section">⭐ Rating Distribution</div>', unsafe_allow_html=True)
    sc = df["stars"].value_counts().reindex([1,2,3,4,5], fill_value=0)
    fig_s = go.Figure(go.Bar(
        x=[f"{s}★" for s in sc.index], y=sc.values,
        marker_color=["#d9534f","#e88a2e","#f0ad4e","#5bc0de","#5cb85c"],
        text=sc.values, textposition="outside",
    ))
    fig_s.update_layout(height=260, margin=dict(t=10,b=10,l=10,r=10),
                        plot_bgcolor="white", yaxis=dict(gridcolor="#eee"))
    st.plotly_chart(fig_s, use_container_width=True)

with col2:
    if branch_choice == "All Branches" and len(df["branch"].unique()) > 1:
        st.markdown('<div class="section">🏪 Branch Comparison</div>', unsafe_allow_html=True)
        ba = df.groupby("branch")["stars"].agg(["mean","count"]).reset_index()
        ba.columns = ["Branch","Avg","Count"]
        ba["Branch"] = ba["Branch"].str.replace("Spice Garden — ","")
        ba = ba.sort_values("Avg", ascending=True)
        fig_b = go.Figure(go.Bar(
            x=ba["Avg"], y=ba["Branch"], orientation="h",
            marker_color=["#5cb85c" if s>=4 else "#f0ad4e" if s>=3 else "#d9534f" for s in ba["Avg"]],
            text=[f"{s:.1f}★ ({c})" for s,c in zip(ba["Avg"],ba["Count"])],
            textposition="outside",
        ))
        fig_b.update_layout(height=260, xaxis=dict(range=[0,5.8]),
                            margin=dict(t=10,b=10,l=10,r=80), plot_bgcolor="white")
        st.plotly_chart(fig_b, use_container_width=True)
    else:
        st.markdown('<div class="section">📅 Reviews Over Time</div>', unsafe_allow_html=True)
        df_time = df.dropna(subset=["timestamp"]).copy()
        if not df_time.empty:
            df_time["date"] = df_time["timestamp"].dt.date
            daily = df_time.groupby("date").agg(count=("stars","count"), avg=("stars","mean")).reset_index()
            fig_t = go.Figure()
            fig_t.add_trace(go.Bar(x=daily["date"], y=daily["count"],
                                   name="Reviews", marker_color="#C0392B", opacity=0.7))
            fig_t.add_trace(go.Scatter(x=daily["date"], y=daily["avg"],
                                       name="Avg ★", yaxis="y2", line=dict(color="#f0ad4e",width=2)))
            fig_t.update_layout(height=260, plot_bgcolor="white",
                                margin=dict(t=10,b=10,l=10,r=10),
                                yaxis=dict(title="Review Count"),
                                yaxis2=dict(title="Avg Stars", overlaying="y",
                                            side="right", range=[0,5]))
            st.plotly_chart(fig_t, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# MULTI-AGENT ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")

# Agent pipeline runs silently — no headers or status cards shown
init_status = {k:("idle","") for k in ["preprocess","features","sentiment","insights","report"]}
pipeline_ph  = st.empty()

if run_btn:
    st.session_state.pop("ai_full", None)   # clear old results
    status = {k:("idle","") for k in ["preprocess","features","sentiment","insights","report"]}
    placeholders = {"pipeline": pipeline_ph}
    try:
        pre, feat, sent, ins, rep = run_full_pipeline(df, status, placeholders)
        pipeline_ph.empty()
        st.session_state["ai_full"]   = (pre, feat, sent, ins, rep)
        st.session_state["ai_branch"] = branch_choice
    except json.JSONDecodeError as e:
        pipeline_ph.empty()
        st.error(f"An agent returned invalid JSON — click Run again. Detail: {e}")
    except Exception as e:
        pipeline_ph.empty()
        st.error(f"Pipeline error: {e}")

if "ai_full" in st.session_state:
    pre, feat, sent, ins, rep = st.session_state["ai_full"]
    scored = sent.get("scored_features", [])
    st.caption(f"Analysis for: **{st.session_state.get('ai_branch','All')}** · {pre.get('usable', len(df))} reviews processed")

    # ── Headline + one-liner ─────────────────────────────────────────────────
    st.markdown(
        f'<div class="insight-card" style="background:#FFF8E6;border-left:3px solid #f0ad4e;">'
        f'<div style="font-size:18px;font-weight:700;color:#5a3e00;">'
        f'📰 {rep.get("headline","Weekly Report")}</div>'
        f'<div style="margin-top:6px;font-size:14px;color:#7a5800;">'
        f'💡 {rep.get("one_liner","")}</div></div>',
        unsafe_allow_html=True
    )

    # ── Crisis alerts ────────────────────────────────────────────────────────
    alerts = ins.get("crisis_alerts", [])
    if alerts:
        st.markdown('<div class="section">🚨 Crisis Alerts — Needs Immediate Attention</div>',
                    unsafe_allow_html=True)
        for a in alerts:
            st.markdown(f'<div class="crisis-box">⚠️ {a}</div>', unsafe_allow_html=True)

    # ── Top metrics ──────────────────────────────────────────────────────────
    st.markdown('<div class="section">📊 Key Metrics</div>', unsafe_allow_html=True)
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("AI Score",         f"{sent.get('overall_score',0)}/100")
    m2.metric("Sentiment",        sent.get("overall_sentiment","").capitalize())
    m3.metric("Features Analysed",len(scored))
    m4.metric("Best Branch",      ins.get("best_branch","—")[:20])
    m5.metric("Predicted Rating", ins.get("predicted_rating_if_fixed","—"))

    # ── Feature sentiment chart ──────────────────────────────────────────────
    if scored:
        st.markdown('<div class="section">🎯 Feature Sentiment Scores</div>',
                    unsafe_allow_html=True)
        col_a, col_b = st.columns([3,2])

        with col_a:
            df_feat = pd.DataFrame(scored).sort_values("score", ascending=True)
            fig_feat = go.Figure(go.Bar(
                x=df_feat["score"], y=df_feat["name"], orientation="h",
                marker_color=[COLOR.get(s,"#888") for s in df_feat["sentiment"]],
                text=[f'{s}/100  ·  {m}× mentioned  ·  {c.upper()}'
                      for s,m,c in zip(df_feat["score"],
                                       df_feat["mentions"],
                                       df_feat["confidence"])],
                textposition="outside",
            ))
            fig_feat.add_vline(x=66, line_dash="dash", line_color="#aaa", opacity=0.5,
                               annotation_text="Good threshold")
            fig_feat.add_vline(x=33, line_dash="dash", line_color="#aaa", opacity=0.5,
                               annotation_text="Poor threshold")
            fig_feat.update_layout(
                height=420, xaxis=dict(range=[0,130], title="Score"),
                margin=dict(t=20,b=20,l=10,r=10), plot_bgcolor="white",
                yaxis=dict(tickfont=dict(size=12))
            )
            st.plotly_chart(fig_feat, use_container_width=True)

        with col_b:
            # Donut
            pos = sum(1 for f in scored if f["sentiment"]=="positive")
            neu = sum(1 for f in scored if f["sentiment"]=="neutral")
            neg = sum(1 for f in scored if f["sentiment"]=="negative")
            fig_pie = go.Figure(go.Pie(
                labels=["Positive","Neutral","Negative"],
                values=[pos,neu,neg], hole=0.62,
                marker_colors=["#5cb85c","#f0ad4e","#d9534f"],
            ))
            fig_pie.update_layout(
                height=260, margin=dict(t=10,b=10,l=10,r=10),
                annotations=[dict(
                    text=f"<b>{sent.get('overall_score',0)}</b><br><span style='font-size:11px'>/100</span>",
                    x=0.5,y=0.5,font_size=20,showarrow=False
                )]
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            # Evidence quotes
            st.markdown("**🗣️ Customer Evidence**")
            for f in sorted(scored, key=lambda x: x["score"])[:6]:
                if f.get("best_quote"):
                    st.markdown(
                        f'<div class="quote-card" style="background:{BG.get(f["sentiment"],"#f5f5f5")};'
                        f'color:{TC.get(f["sentiment"],"#333")};">'
                        f'<strong>{f["name"]}</strong> '
                        f'<span class="badge badge-{f["sentiment"][:3]}" '
                        f'style="background:{BG.get(f["sentiment"])};color:{TC.get(f["sentiment"])};">'
                        f'{f["score"]}/100</span><br>'
                        f'<em>"{f["best_quote"]}"</em></div>',
                        unsafe_allow_html=True
                    )

    # ── Branch deep dive ─────────────────────────────────────────────────────
    branch_overall = sent.get("branch_overall", {})
    if branch_overall and len(branch_overall) > 1:
        st.markdown('<div class="section">🏪 Branch Intelligence</div>',
                    unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown(
                f'<div class="insight-card" style="border-left:3px solid #5cb85c;">'
                f'<strong>🥇 Best Branch: {ins.get("best_branch","—")}</strong><br>'
                f'{ins.get("best_branch_reason","")}</div>',
                unsafe_allow_html=True
            )
        with bc2:
            st.markdown(
                f'<div class="insight-card" style="border-left:3px solid #d9534f;">'
                f'<strong>⚠️ Needs Work: {ins.get("worst_branch","—")}</strong><br>'
                f'{ins.get("worst_branch_reason","")}</div>',
                unsafe_allow_html=True
            )

        # Heatmap: branches x features
        if scored:
            st.markdown("**Feature scores by branch:**")
            branches_list = list(branch_overall.keys())
            feat_names    = [f["name"] for f in scored]
            heat_data = []
            for fn in feat_names:
                row_scores = []
                f_obj = next((f for f in scored if f["name"]==fn), {})
                for br in branches_list:
                    row_scores.append(f_obj.get("branch_scores",{}).get(br, 50))
                heat_data.append(row_scores)

            fig_heat = go.Figure(go.Heatmap(
                z=heat_data, x=branches_list, y=feat_names,
                colorscale=[[0,"#d9534f"],[0.5,"#f0ad4e"],[1,"#5cb85c"]],
                zmin=0, zmax=100,
                text=heat_data,
                texttemplate="%{text}",
                textfont=dict(size=11),
            ))
            fig_heat.update_layout(height=350, margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig_heat, use_container_width=True)

    # ── Strengths & Problems ─────────────────────────────────────────────────
    st.markdown('<div class="section">💡 Strengths & Problems</div>', unsafe_allow_html=True)
    sp1, sp2 = st.columns(2)
    with sp1:
        st.markdown("**✅ Top Strengths**")
        for i, s in enumerate(ins.get("top_3_strengths",[]), 1):
            st.markdown(
                f'<div class="insight-card" style="border-left:3px solid #5cb85c;">'
                f'<strong>{i}.</strong> {s}</div>',
                unsafe_allow_html=True
            )
    with sp2:
        st.markdown("**❌ Top Problems**")
        for i, p in enumerate(ins.get("top_3_problems",[]), 1):
            st.markdown(
                f'<div class="insight-card" style="border-left:3px solid #d9534f;">'
                f'<strong>{i}.</strong> {p}</div>',
                unsafe_allow_html=True
            )

    # ── Weekly action plan ───────────────────────────────────────────────────
    st.markdown('<div class="section">📋 This Week\'s Action Plan</div>', unsafe_allow_html=True)
    priority_color = {"high":"#d9534f","medium":"#f0ad4e","low":"#5cb85c"}
    for action in ins.get("weekly_actions",[]):
        p = action.get("priority","medium")
        st.markdown(
            f'<div class="insight-card" style="border-left:3px solid {priority_color.get(p,"#888")};">'
            f'<span class="badge" style="background:{priority_color.get(p)};color:white;">'
            f'{p.upper()}</span> '
            f'<strong>{action.get("action","")}</strong><br>'
            f'<span style="font-size:12px;color:#666;">Expected impact: {action.get("expected_impact","")}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Full report ──────────────────────────────────────────────────────────
    st.markdown('<div class="section">📝 Full Intelligence Report</div>', unsafe_allow_html=True)

    def report_block(icon, label, text, bg="#EAF3DE", color="#1a3a1a"):
        return (f'<div style="margin-bottom:14px;">'
                f'<div style="font-size:12px;font-weight:700;color:#888;text-transform:uppercase;'
                f'letter-spacing:0.05em;margin-bottom:4px;">{icon} {label}</div>'
                f'<div style="background:{bg};border-radius:10px;padding:14px 18px;'
                f'font-size:13px;color:{color};line-height:1.8;">{text}</div></div>')

    st.markdown(
        '<div style="padding:4px 0;">',
        unsafe_allow_html=True
    )
    if rep.get("what_is_working"):
        st.markdown(report_block("✅","What's Working",
            rep["what_is_working"], "#EAF3DE","#1a3a1a"), unsafe_allow_html=True)
    if rep.get("what_needs_fixing"):
        st.markdown(report_block("🔧","What Needs Fixing",
            rep["what_needs_fixing"], "#FCEBEB","#5a1a1a"), unsafe_allow_html=True)
    if rep.get("this_week_focus"):
        st.markdown(report_block("🎯","This Week's Focus",
            rep["this_week_focus"], "#FFF8E6","#5a3e00"), unsafe_allow_html=True)
    if rep.get("customer_voice"):
        st.markdown(report_block("🗣️","What Customers Are Saying",
            rep["customer_voice"], "#F1EFE8","#333"), unsafe_allow_html=True)
    if rep.get("competitor_risk"):
        st.markdown(report_block("⚡","Competitor Risk if Unresolved",
            rep["competitor_risk"], "#FDF0FF","#3a1a5a"), unsafe_allow_html=True)
    if rep.get("owner_note"):
        st.markdown(report_block("👋","A Note for the Owner",
            rep["owner_note"], "#E8F4FD","#1a3050"), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
time.sleep(1)
st.rerun()
