import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
import app_utils  # noqa: E402  (must be imported BEFORE joblib.load)

st.set_page_config(page_title="At-Risk Student Early Warning", page_icon="🎓", layout="wide")

# ---------- styling ----------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
      :root {
        --ink:#14213d; --muted:#5b6784; --bg:#eef2fb; --card:#ffffff; --line:#dde4f3;
        --indigo:#3d4fe0; --indigo-soft:#e6e9ff;
        --risk:#e4572e; --risk-soft:#fde9e2;
        --avg:#f2a541; --avg-soft:#fdf0da;
        --good:#2a9d8f; --good-soft:#dff3f0;
      }
      html, body, [class*="css"], .stApp { font-family:'Plus Jakarta Sans', 'Segoe UI', sans-serif; color:var(--ink); }
      .stApp { background: var(--bg); }
      .block-container { padding-top: 1.6rem; max-width: 1180px; }
      header[data-testid="stHeader"] { background: transparent; }

      /* hero */
      .hero { background: linear-gradient(120deg, #1b2a6b 0%, #3d4fe0 55%, #6c7bff 100%);
              border-radius: 22px; padding: 2rem 2.2rem; color:#fff; margin-bottom: 1.4rem;
              box-shadow: 0 14px 34px rgba(61,79,224,.25); position: relative; overflow: hidden; }
      .hero::after { content:""; position:absolute; right:-60px; top:-60px; width:240px; height:240px;
                     border-radius:50%; background: rgba(255,255,255,.10); }
      .hero::before { content:""; position:absolute; right:110px; bottom:-90px; width:180px; height:180px;
                      border-radius:50%; background: rgba(255,255,255,.07); }
      .hero h1 { margin:0; font-size:2rem; font-weight:800; letter-spacing:-.5px; color:#fff; padding:0; }
      .hero p { margin:.5rem 0 0 0; opacity:.9; font-size:1rem; max-width: 640px; }
      .chip { display:inline-block; background:rgba(255,255,255,.18); border-radius:999px;
              padding:.25rem .8rem; margin:.9rem .4rem 0 0; font-size:.82rem; font-weight:600; }

      /* metric cards */
      div[data-testid="stMetric"] { background: var(--card); border:1px solid var(--line); border-radius:18px;
              padding:1.1rem 1.3rem; box-shadow: 0 4px 14px rgba(20,33,61,.05); }
      div[data-testid="stMetric"] label p { color: var(--muted); font-weight:600; }
      div[data-testid="stMetricValue"] { font-weight:800; color: var(--ink); }

      /* tabs as pills */
      .stTabs [data-baseweb="tab-list"] { gap:.5rem; background: transparent; border-bottom:none; }
      .stTabs [data-baseweb="tab"] { background: var(--card); border:1px solid var(--line); border-radius:999px;
              padding:.5rem 1.2rem; font-weight:700; color: var(--muted); height:auto; }
      .stTabs [aria-selected="true"] { background: var(--indigo); color:#fff !important; border-color: var(--indigo); }
      .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }

      /* form + panels */
      div[data-testid="stForm"] { background: var(--card); border:1px solid var(--line); border-radius:20px;
              padding:1.4rem 1.6rem; box-shadow: 0 4px 14px rgba(20,33,61,.05); }
      h2, h3 { color: var(--ink); font-weight:800; letter-spacing:-.3px; }
      .stButton button, .stDownloadButton button, div[data-testid="stFormSubmitButton"] button {
              border-radius: 12px; font-weight:700; padding:.55rem 1.4rem; border:1px solid var(--line); }
      div[data-testid="stFormSubmitButton"] button, .stButton button[kind="primary"] {
              background: var(--indigo); color:#fff; border-color: var(--indigo); }
      div[data-testid="stFormSubmitButton"] button:hover { background:#2f3fc4; color:#fff; border-color:#2f3fc4; }
      div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:16px; overflow:hidden; }

      /* result */
      .result { border-radius:20px; padding:1.4rem 1.6rem; margin:1rem 0 1.2rem 0; border:1px solid transparent; }
      .result .label { font-size:.85rem; font-weight:700; opacity:.8; }
      .result h2 { margin:.1rem 0 .6rem 0; font-size:2rem; }
      .result .pill { display:inline-block; border-radius:999px; padding:.25rem .85rem; margin-right:.5rem;
                      font-size:.85rem; font-weight:700; background: rgba(255,255,255,.7); }
      .result.risk { background: var(--risk-soft); border-color:#f6c4b4; color:#8f2a0f; }
      .result.avg  { background: var(--avg-soft);  border-color:#f3d9a8; color:#8a5a0a; }
      .result.high { background: var(--good-soft); border-color:#b5e3dc; color:#176a5f; }

      /* ---------- background ---------- */
      .stApp {
        background-color: #eaf0ff;
        background-image:
          radial-gradient(900px 500px at 8% -5%, rgba(108,123,255,.35), transparent 60%),
          radial-gradient(700px 480px at 100% 10%, rgba(42,157,143,.22), transparent 60%),
          radial-gradient(800px 520px at 60% 110%, rgba(228,87,46,.14), transparent 60%),
          radial-gradient(rgba(61,79,224,.10) 1.2px, transparent 1.2px);
        background-size: auto, auto, auto, 26px 26px;
        background-attachment: fixed;
      }

      /* ---------- buttons: move on hover, press on click ---------- */
      .stButton button, .stDownloadButton button, div[data-testid="stFormSubmitButton"] button,
      button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-pillsActive"] {
        transition: transform .15s ease, box-shadow .15s ease, background .15s ease, color .15s ease;
        cursor: pointer;
      }
      .stButton button:hover, .stDownloadButton button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-3px); box-shadow: 0 10px 22px rgba(61,79,224,.30);
      }
      .stButton button:active, .stDownloadButton button:active, div[data-testid="stFormSubmitButton"] button:active {
        transform: translateY(1px) scale(.95); box-shadow: 0 2px 6px rgba(61,79,224,.25);
      }
      div[data-testid="stFormSubmitButton"] button { font-size:1.05rem; padding:.7rem 2rem; }

      /* ---------- number pills (replace the old slider) ---------- */
      button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-pillsActive"] {
        min-width: 46px; height: 46px; border-radius: 14px; font-weight:800; font-size:1.05rem;
        border:1.5px solid var(--line); background:#f6f8ff; color: var(--ink);
      }
      button[data-testid="stBaseButton-pills"]:hover {
        transform: translateY(-4px) scale(1.06); background: var(--indigo-soft); border-color: var(--indigo);
        box-shadow: 0 8px 16px rgba(61,79,224,.22);
      }
      button[data-testid="stBaseButton-pills"]:active, button[data-testid="stBaseButton-pillsActive"]:active {
        transform: scale(.9);
      }
      button[data-testid="stBaseButton-pillsActive"] {
        background: linear-gradient(135deg, #3d4fe0, #6c7bff); color:#fff; border-color: transparent;
        box-shadow: 0 8px 18px rgba(61,79,224,.35); transform: translateY(-2px);
      }

      /* number input */
      div[data-testid="stNumberInput"] input { font-size:1.4rem; font-weight:800; color: var(--ink); }
      div[data-testid="stNumberInput"] > div > div { border-radius:14px; border:1.5px solid var(--line); background:#f6f8ff; }
      div[data-testid="stNumberInput"] button { transition: transform .12s ease; }
      div[data-testid="stNumberInput"] button:active { transform: scale(.85); }

      /* field cards inside the form */
      div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:18px; border-color: var(--line); background:#fff; }
      .field-title { font-weight:800; font-size:1.02rem; margin-bottom:.35rem; display:flex; align-items:center; gap:.55rem; }
      .field-title .ico { width:34px; height:34px; border-radius:11px; display:inline-flex; align-items:center;
                          justify-content:center; background: var(--indigo-soft); font-size:1.1rem; }
      .field-hint { color: var(--muted); font-size:.82rem; margin:.1rem 0 .5rem 0; }

      /* cards and tabs lift a little on hover */
      div[data-testid="stMetric"] { transition: transform .18s ease, box-shadow .18s ease; }
      div[data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 14px 28px rgba(20,33,61,.12); }
      .stTabs [data-baseweb="tab"] { transition: transform .15s ease, background .15s ease; }
      .stTabs [data-baseweb="tab"]:hover { transform: translateY(-2px); background: var(--indigo-soft); }
      .stTabs [aria-selected="true"]:hover { background: var(--indigo); }

      @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- load model + data (cached) ----------
@st.cache_resource
def load_model():
    return joblib.load(BASE / "final_model.joblib")


@st.cache_data
def load_meta():
    return json.loads((BASE / "model_meta.json").read_text())


@st.cache_data
def load_csv(name):
    return pd.read_csv(BASE / name)


try:
    model = load_model()
    meta = load_meta()
    at_risk = load_csv("at_risk_students_final.csv")
    watch = load_csv("watch_list_students.csv")
    everyone = load_csv("all_students_scored.csv")
except Exception as e:  # clear message instead of a stack trace
    st.error(f"Could not load project files: {e}")
    st.info(
        "Keep app.py in the same folder as final_model.joblib, app_utils.py, "
        "model_meta.json and the CSV files, and install requirements.txt."
    )
    st.stop()

# ---------- header ----------
st.markdown(
    f"""
    <div class="hero">
      <h1>🎓 Early warning for at-risk students</h1>
      <p>Spot students who may struggle before the exam, so advisors can offer support in time.</p>
      <span class="chip">Model: {meta['model_name']}</span>
      <span class="chip">At Risk below {meta['thresholds']['at_risk_below']}</span>
      <span class="chip">High Performance from {meta['thresholds']['high_performance_from']}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)
m1.metric("Students analysed", f"{len(everyone):,}")
m2.metric("Flagged at-risk", f"{len(at_risk):,}", f"{len(at_risk) / len(everyone):.1%} of students", delta_color="off")
m3.metric("Watch-list (borderline)", f"{len(watch):,}")

tab_check, tab_risk, tab_watch = st.tabs(["Check a student", "At-risk list", "Watch-list"])

# ---------- tab 1: single student ----------
with tab_check:
    st.subheader("Enter a student's profile")
    rng = meta["input_ranges"]

    def lo_hi(col):
        lo, hi = rng[col]
        return int(lo), int(hi)

    def pick(label, icon, col, default, hint):
        lo, hi = lo_hi(col)
        default = min(max(default, lo), hi)
        with st.container(border=True):
            st.markdown(
                f'<div class="field-title"><span class="ico">{icon}</span>{label}</div>'
                f'<div class="field-hint">{hint} ({lo} to {hi})</div>',
                unsafe_allow_html=True,
            )
            if hi - lo <= 11 and hasattr(st, "pills"):
                v = st.pills(label, list(range(lo, hi + 1)), default=default,
                             selection_mode="single", label_visibility="collapsed", key=f"pill_{col}")
                return default if v is None else v
            return st.number_input(label, min_value=lo, max_value=hi, value=default, step=1,
                                   label_visibility="collapsed", key=f"num_{col}")

    with st.form("student_form"):
        c1, c2 = st.columns(2)
        with c1:
            hours = pick("Hours studied", "📚", "Hours Studied", 5, "Study hours per day")
            papers = pick("Practice papers", "📝", "Sample Question Papers Practiced", 5, "Sample papers solved")
        with c2:
            prev = pick("Previous scores", "🏅", "Previous Scores", 70, "Score in the last exam")
            sleep = pick("Sleep hours", "🌙", "Sleep Hours", 7, "Average sleep per night")
        with st.container(border=True):
            st.markdown(
                '<div class="field-title"><span class="ico">⚽</span>Extracurricular activities</div>'
                '<div class="field-hint">Does the student take part in clubs or sports?</div>',
                unsafe_allow_html=True,
            )
            opts = meta["extracurricular_options"]
            if hasattr(st, "pills"):
                extra = st.pills("Extracurricular", opts, default=opts[0], selection_mode="single",
                                 label_visibility="collapsed", key="pill_extra") or opts[0]
            else:
                extra = st.radio("Extracurricular", opts, horizontal=True, label_visibility="collapsed")
        go = st.form_submit_button("Check student", type="primary")

    if go:
        res = app_utils.predict_student(
            model,
            {
                "Hours Studied": hours,
                "Previous Scores": prev,
                "Sleep Hours": sleep,
                "Sample Question Papers Practiced": papers,
                "Extracurricular Activities": extra,
            },
        )
        css = {"At Risk": "risk", "Average": "avg", "High Performance": "high"}[res["category"]]
        st.markdown(
            f"""<div class="result {css}">
                  <div class="label">Predicted category</div>
                  <h2>{res['category']}</h2>
                  <span class="pill">Risk chance: {res['risk_probability']:.0%}</span>
                  <span class="pill">Priority: {res['priority']}</span>
                </div>""",
            unsafe_allow_html=True,
        )

        left, right = st.columns([1, 1])
        with left:
            st.markdown("**Category probabilities**")
            st.bar_chart(pd.Series(res["probabilities"]), horizontal=True)
        with right:
            if res["category"] == "At Risk" or res["priority"] == "Watch":
                st.markdown("**Recommended support**")
                for item in res["recommended_support"].split("; "):
                    st.write(f"- {item}")
                st.markdown("**Key risk factors**")
                st.write(res["key_risk_factors"])
            else:
                st.success("No support needed right now. Keep monitoring as new scores come in.")
        st.caption("This is decision support only. A person should review each case before acting.")


# ---------- shared table view ----------
def show_table(df, key, with_priority_filter=True):
    f1, f2, f3 = st.columns([1, 1, 1])
    with f1:
        if with_priority_filter and "Priority" in df.columns:
            options = [p for p in ["High", "Medium", "Watch"] if p in set(df["Priority"])]
            chosen = st.multiselect("Priority", options, default=options, key=f"{key}_prio")
        else:
            chosen = None
    with f2:
        min_risk = st.slider("Minimum risk probability", 0.0, 1.0, 0.0, 0.05, key=f"{key}_risk")
    with f3:
        q = st.text_input("Find student ID", placeholder="e.g. S00042", key=f"{key}_q")

    view = df[df["Risk_Probability"] >= min_risk]
    if chosen is not None:
        view = view[view["Priority"].isin(chosen)]
    if q.strip():
        view = view[view["Student_ID"].str.contains(q.strip(), case=False, na=False)]

    st.write(f"Showing {len(view):,} of {len(df):,} students")
    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk_Probability": st.column_config.ProgressColumn(
                "Risk probability", min_value=0.0, max_value=1.0, format="%.2f"
            )
        },
    )
    st.download_button(
        "Download this view as CSV",
        view.to_csv(index=False).encode("utf-8"),
        file_name=f"{key}_students.csv",
        mime="text/csv",
        key=f"{key}_dl",
    )
    return view


with tab_risk:
    st.subheader("Students flagged as at-risk")
    view = show_table(at_risk, "at_risk")
    if len(view):
        st.markdown("**Priority breakdown**")
        st.bar_chart(view["Priority"].value_counts())

with tab_watch:
    st.subheader("Borderline students to keep an eye on")
    st.caption("Predicted Average, but with a notable chance of being at risk. This is the early part of early identification.")
    show_table(watch, "watch", with_priority_filter=False)