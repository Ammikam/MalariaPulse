"""Human-reviewed MalariaPulse dashboard.

Agents prepare recommendations; a reviewer must approve them before action.
Run from the project root: streamlit run app/review_app.py
"""
import asyncio
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from malariapulse import store  # noqa: E402
from malariapulse.pipeline import run_pipeline  # noqa: E402

st.set_page_config(page_title="MalariaPulse | Review dashboard", layout="wide")

# ---------------------------------------------------------------------------
# Design system
# One light theme, one accent (teal). Red / amber / green are reserved for
# risk information only. Selectors target Streamlit's stable data-testid /
# baseweb attributes rather than generated class names.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
        --bg: #F8FAFC;
        --surface: #FFFFFF;
        --text: #172B4D;
        --muted: #64748B;
        --accent: #0F766E;
        --accent-hover: #115E59;
        --accent-soft: #F0FDFA;
        --border: #E2E8F0;
        --risk-high: #B42318;
        --risk-moderate: #B54708;
        --risk-low: #067647;
        --radius: 10px;
        --radius-sm: 8px;
    }

    /* ---------- Base ---------- */
    .stApp { background: var(--bg); color: var(--text); }
    [data-testid="stHeader"] { background: rgba(248,250,252,.92); }
    .block-container { padding-top: 4.75rem; padding-bottom: 3rem; max-width: 1360px; }
    .stApp, .stApp p, .stApp li, .stApp label, .stApp span { color: var(--text); }
    h1, h2, h3, h4 { color: var(--accent) !important; letter-spacing: -0.02em; }
    h1 { font-size: 1.85rem !important; font-weight: 650 !important; padding-top: 0 !important; }
    h2 { font-size: 1.15rem !important; font-weight: 650 !important; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
    a, a:visited { color: var(--accent) !important; text-decoration: none; font-weight: 500; }
    a:hover { color: var(--accent-hover) !important; text-decoration: underline; }
    hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.25rem; }
    [data-testid="stSidebar"] hr { margin: 1.25rem 0 !important; }
    .side-meta { display: flex; justify-content: space-between; gap: .75rem; font-size: .84rem;
                 padding: .45rem 0; border-bottom: 1px solid var(--border); }
    .side-meta:last-child { border-bottom: none; }
    .side-meta .k { color: var(--muted); }
    .side-meta .v { color: var(--text); font-weight: 500; text-align: right; }

    /* ---------- Typography helpers ---------- */
    .eyebrow { color: var(--accent); font-size: .74rem; font-weight: 650; letter-spacing: .08em;
               text-transform: uppercase; margin-bottom: .4rem; }
    .subhead { color: var(--muted); font-size: .98rem; line-height: 1.6; max-width: 820px; margin-bottom: 1rem; }
    .section-title { color: var(--accent); font-size: .95rem; font-weight: 650; margin: 0 0 .75rem 0; }
    .field-label { color: var(--muted); font-size: .78rem; font-weight: 600; letter-spacing: .02em;
                   margin: 1rem 0 .4rem 0; }
    .notice { display: flex; gap: .6rem; align-items: flex-start; background: var(--surface);
              border: 1px solid var(--border); border-left: 3px solid var(--accent);
              color: var(--muted); border-radius: var(--radius-sm); padding: .65rem .9rem;
              font-size: .86rem; line-height: 1.5; margin: 0 0 1.5rem 0; }
    .notice strong { color: var(--text); font-weight: 600; }

    /* ---------- Metrics ---------- */
    div[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--border);
        padding: 1.1rem 1.25rem; border-radius: var(--radius); }
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * { color: var(--muted) !important;
        font-size: .84rem; font-weight: 500; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * { color: var(--text) !important;
        font-weight: 650; font-size: 1.9rem; }

    /* ---------- Tabs ---------- */
    div[data-testid="stTabs"] [role="tablist"] { gap: .25rem; border-bottom: 1px solid var(--border); }
    div[data-testid="stTabs"] button[role="tab"] { color: var(--muted); font-weight: 550; padding: .6rem 1rem; }
    div[data-testid="stTabs"] button[role="tab"] p { color: inherit !important; }
    div[data-testid="stTabs"] button[role="tab"]:hover { color: var(--accent); background: transparent; }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: var(--accent); }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--accent); height: 2px; }
    div[data-testid="stTabs"] [data-baseweb="tab-border"] { background-color: var(--border); }

    /* ---------- Expanders (proposal cards) ---------- */
    div[data-testid="stExpander"] { background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius); box-shadow: none; margin-bottom: 1rem; }
    div[data-testid="stExpander"] details { border: none; }
    div[data-testid="stExpander"] details,
    div[data-testid="stExpander"] summary { background: var(--surface) !important; }
    div[data-testid="stExpander"] summary { font-weight: 600; padding: .9rem 1.1rem; }
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary *,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary svg { color: var(--accent) !important; fill: var(--accent) !important;
        -webkit-text-fill-color: var(--accent); }
    div[data-testid="stExpander"] summary:hover,
    div[data-testid="stExpander"] summary:hover * { color: var(--accent-hover) !important;
        -webkit-text-fill-color: var(--accent-hover); }
    div[data-testid="stExpander"] summary:hover { background: var(--accent-soft) !important; }
    /* nested expander (audit trail) is quieter */
    div[data-testid="stExpander"] div[data-testid="stExpander"] { margin: 1rem 0 0 0; }
    div[data-testid="stExpander"] div[data-testid="stExpander"] summary { font-weight: 500; font-size: .9rem; }

    /* ---------- Risk badges (restrained) ---------- */
    .badge { display: inline-block; padding: .12rem .6rem; border-radius: 999px; font-size: .78rem;
             font-weight: 600; border: 1px solid currentColor; background: var(--surface); line-height: 1.5; }
    .badge-high { color: var(--risk-high) !important; }
    .badge-moderate { color: var(--risk-moderate) !important; }
    .badge-low { color: var(--risk-low) !important; }
    .badge-unknown { color: var(--muted) !important; }
    .risk-head { display: flex; align-items: baseline; gap: .75rem; margin-bottom: .25rem; }
    .risk-score { font-size: 1.9rem; font-weight: 650; color: var(--text); line-height: 1.1; }
    .risk-score small { font-size: .8rem; font-weight: 500; color: var(--muted); margin-left: .35rem; }
    .stat-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; margin: .5rem 0 .75rem 0; }
    .stat { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm);
            padding: .6rem .75rem; }
    .stat .k { color: var(--muted); font-size: .72rem; font-weight: 600; line-height: 1.3; }
    .stat .v { color: var(--text); font-size: 1.15rem; font-weight: 650; margin-top: .15rem; }

    /* ---------- Buttons ---------- */
    div.stButton > button, div[data-testid="stBaseButton-secondary"], div[data-testid="stBaseButton-primary"] {
        border-radius: var(--radius-sm); font-weight: 600; min-height: 2.6rem; padding: .45rem 1.1rem;
        transition: background-color .15s ease, border-color .15s ease, color .15s ease; box-shadow: none; }
    /* primary */
    div.stButton > button[kind="primary"] { background: var(--accent); border: 1px solid var(--accent); }
    div.stButton > button[kind="primary"], div.stButton > button[kind="primary"] * { color: #FFFFFF !important; }
    div.stButton > button[kind="primary"]:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
    div.stButton > button[kind="primary"]:focus-visible { box-shadow: 0 0 0 3px rgba(15,118,110,.25); }
    /* secondary (neutral, understated) */
    div.stButton > button[kind="secondary"] { background: var(--surface) !important; border: 1px solid var(--accent); }
    div.stButton > button[kind="secondary"], div.stButton > button[kind="secondary"] * { color: var(--accent) !important;
        -webkit-text-fill-color: var(--accent); }
    div.stButton > button[kind="secondary"]:hover { background: var(--accent-soft) !important; border-color: var(--accent-hover); }
    div.stButton > button[kind="secondary"]:hover * { color: var(--accent-hover) !important;
        -webkit-text-fill-color: var(--accent-hover); }
    div.stButton > button[kind="primary"] * { -webkit-text-fill-color: #FFFFFF; }
    div.stButton > button[kind="secondary"]:focus-visible { box-shadow: 0 0 0 3px rgba(100,116,139,.25); }

    /* ---------- Inputs ---------- */
    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
    [data-baseweb="select"] > div { background: var(--surface) !important; border-color: var(--border) !important;
        border-radius: var(--radius-sm) !important; }
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] * {
        color: var(--text) !important; -webkit-text-fill-color: var(--text); }
    [data-baseweb="input"] input::placeholder { color: #94A3B8 !important; -webkit-text-fill-color: #94A3B8; }
    [data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within,
    [data-baseweb="select"] > div:focus-within { border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(15,118,110,.15) !important; }
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color: var(--text) !important;
        font-size: .86rem; font-weight: 550; }
    [data-baseweb="popover"] ul, [data-baseweb="menu"] { background: var(--surface) !important; }
    [data-baseweb="popover"] li { color: var(--text) !important; }

    /* ---------- Tables (HTML, so they always match the theme) ---------- */
    .tbl-wrap { overflow-x: auto; background: var(--surface); border: 1px solid var(--border);
                border-radius: var(--radius-sm); margin-bottom: .5rem; }
    table.tbl { width: 100%; border-collapse: collapse; font-size: .88rem; background: var(--surface); }
    table.tbl th { background: var(--accent-soft); color: var(--accent); font-weight: 650; text-align: left;
                   padding: .6rem .85rem; border-bottom: 1px solid var(--border); white-space: nowrap; }
    table.tbl td { background: var(--surface); color: var(--text); padding: .55rem .85rem;
                   border-bottom: 1px solid var(--border); vertical-align: top; white-space: nowrap; }
    table.tbl td.wrap { white-space: normal; min-width: 14rem; word-break: break-word; }
    table.tbl tr:last-child td { border-bottom: none; }
    table.tbl tbody tr:hover td { background: var(--accent-soft); }
    table.tbl th.num, table.tbl td.num { text-align: right; }

    /* ---------- Tables / alerts ---------- */
    [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
    [data-testid="stAlert"] { border-radius: var(--radius-sm); border: 1px solid var(--border); }

    /* ---------- Responsive ---------- */
    @media (max-width: 900px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 4.5rem; }
        .stat-grid { grid-template-columns: 1fr; }
        h1 { font-size: 1.5rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def risk_badge(level: str) -> str:
    """Return a restrained pill badge for a risk level (risk colours only live here)."""
    css = level if level in ("high", "moderate", "low") else "unknown"
    return f"<span class='badge badge-{css}'>{escape(level.title())} risk</span>"


def stat(label: str, value) -> str:
    return f"<div class='stat'><div class='k'>{escape(label)}</div><div class='v'>{escape(str(value))}</div></div>"


def render_table(rows) -> None:
    """Render a list of dicts as a clean white/green HTML table (display only; data is unchanged)."""
    rows = [r if isinstance(r, dict) else {"value": r} for r in (rows or [])]
    if not rows:
        return
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)

    def is_num(v) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    head = "".join(
        f"<th class='{'num' if all(is_num(r.get(c)) or r.get(c) is None for r in rows) else ''}'>{escape(str(c))}</th>"
        for c in cols
    )
    body = ""
    for r in rows:
        cells = ""
        for c in cols:
            v = r.get(c)
            text = "—" if v is None or v == "" else escape(str(v))
            cls = "num" if is_num(v) else ("wrap" if len(text) > 40 else "")
            cells += f"<td class='{cls}'>{text}</td>"
        body += f"<tr>{cells}</tr>"
    st.markdown(
        f"<div class='tbl-wrap'><table class='tbl'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown("<div class='eyebrow'>MalariaPulse</div>", unsafe_allow_html=True)
    st.markdown("## Review controls")
    st.caption("Run the agents and record a review decision.")
    reviewer = st.text_input("Reviewer name", value="", placeholder="Enter your name")
    mode = st.selectbox(
        "Processing mode",
        ["rules", "llm"],
        help="Rules mode uses the local baseline. LLM mode requires GEMINI_API_KEY in your environment.",
    )
    run_clicked = st.button("Run assessment", type="primary", use_container_width=True)
    st.divider()
    st.caption("Prototype environment")
    st.markdown(
        "<div class='side-meta'><span class='k'>Data</span><span class='v'>Synthetic demonstration data</span></div>"
        "<div class='side-meta'><span class='k'>Approval</span><span class='v'>Required before action</span></div>"
        "<div class='side-meta'><span class='k'>Delivery</span><span class='v'>Nothing is sent automatically</span></div>",
        unsafe_allow_html=True,
    )

if run_clicked:
    with st.spinner("Running assessment and collecting agent recommendations…"):
        try:
            result = asyncio.run(run_pipeline(mode))
            st.success(
                f"Assessment complete: {len(result['proposals'])} proposal(s) created from "
                f"{len(result['tool_calls'])} tool call(s)."
            )
        except Exception as exc:  # keep the review UI available if a run fails
            st.error(f"Assessment failed: {exc}")

all_rows = store.list_proposals()
pending = [r for r in all_rows if r["status"] == "pending"]
done = [r for r in all_rows if r["status"] != "pending"]

st.markdown("<div class='eyebrow'>Public health operations · Prototype</div>", unsafe_allow_html=True)
st.title("Surveillance review dashboard")
st.markdown(
    "<div class='subhead'>Review malaria risk assessments, proposed supply responses and draft community advisories. "
    "Recommendations remain pending until an authorised reviewer records a decision.</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='notice'><span><strong>Prototype notice.</strong> All displayed data is synthetic. "
    "Risk scores and recommendations are for demonstration only and are not validated for operational "
    "public-health decisions.</span></div>",
    unsafe_allow_html=True,
)

m1, m2, m3 = st.columns(3)
m1.metric("Awaiting review", len(pending))
m2.metric("Reviewed proposals", len(done))
m3.metric("High-risk proposals pending", sum(1 for r in pending if r.get("risk_level") == "high"))

st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
tab_pending, tab_done = st.tabs([f"Pending review ({len(pending)})", f"Decision history ({len(done)})"])

with tab_pending:
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    if not pending:
        st.info("There are no pending proposals. Use Run assessment in the sidebar to generate a new set.")
    for row in pending:
        p = row["payload"]
        risk = p.get("risk", {})
        level = str(risk.get("risk_level", "unknown")).lower()
        with st.expander(f"{p.get('zone', row.get('zone', 'Unknown zone'))}  |  {level.upper()} risk  |  Score {risk.get('risk_score', '—')}", expanded=True):
            left, right = st.columns([1, 1.15], gap="large")
            with left:
                st.markdown("<div class='section-title'>Risk assessment</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='risk-head'><span class='risk-score'>{escape(str(risk.get('risk_score', '—')))}"
                    f"<small>risk score</small></span>{risk_badge(level)}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("<div class='field-label'>Factors considered</div>", unsafe_allow_html=True)
                drivers = risk.get("drivers", [])
                if drivers:
                    for driver in drivers:
                        st.markdown(f"- {driver}")
                else:
                    st.caption("No contributing factors were returned.")
                st.markdown("<div class='field-label'>Case projections</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='stat-grid'>"
                    + stat("Recent weekly cases", risk.get("recent_weekly_cases", "—"))
                    + stat("Baseline", risk.get("baseline_weekly_cases", "—"))
                    + stat("Projected, next 2 weeks", risk.get("projected_cases_next_2_weeks", "—"))
                    + "</div>",
                    unsafe_allow_html=True,
                )
                st.caption(f"Assessment method: {risk.get('model', 'Not specified')}")
            with right:
                st.markdown("<div class='section-title'>Proposed supply response</div>", unsafe_allow_html=True)
                plan = p.get("supply_plan") or {}
                transfers = plan.get("transfers", [])
                restocks = plan.get("restock_requests", [])
                if transfers:
                    st.markdown("<div class='field-label' style='margin-top:0'>Suggested transfers</div>", unsafe_allow_html=True)
                    render_table(transfers)
                if restocks:
                    st.markdown("<div class='field-label'>Restock requests</div>", unsafe_allow_html=True)
                    render_table(restocks)
                if not transfers and not restocks:
                    st.caption("No supply actions were proposed.")
                if plan.get("notes"):
                    st.caption(plan["notes"])

            st.divider()
            st.markdown("<div class='section-title'>Community advisory drafts</div>", unsafe_allow_html=True)
            advisories = p.get("advisories", [])
            selected_text = ""
            if advisories:
                options = [f"{a.get('audience', 'Audience')} · {a.get('language', 'Language')}" for a in advisories]
                chosen = st.selectbox("Select a draft", options, key=f"pick_{row['id']}")
                selected_advisory = advisories[options.index(chosen)]
                selected_text = st.text_area(
                    "Review and edit the message before approval",
                    value=selected_advisory.get("text", ""),
                    height=120,
                    key=f"text_{row['id']}",
                )
                st.markdown(f"[Prepare message in WhatsApp](https://wa.me/?text={quote(selected_text)})")
                st.caption("This opens a prepared message. It is not sent automatically.")
            else:
                st.caption("No advisory drafts were returned.")

            st.divider()
            st.markdown("<div class='section-title'>Reviewer decision</div>", unsafe_allow_html=True)
            note = st.text_input("Reviewer note (optional)", key=f"note_{row['id']}")
            approve_col, reject_col, _ = st.columns([1, 1, 3])
            if approve_col.button("Approve proposal", key=f"approve_{row['id']}", type="primary", use_container_width=True):
                if not reviewer.strip():
                    st.warning("Enter your name in the sidebar before recording a decision.")
                else:
                    store.record_decision(row["id"], "approved", reviewer.strip(), note, selected_text)
                    st.rerun()
            if reject_col.button("Reject proposal", key=f"reject_{row['id']}", use_container_width=True):
                if not reviewer.strip():
                    st.warning("Enter your name in the sidebar before recording a decision.")
                else:
                    store.record_decision(row["id"], "rejected", reviewer.strip(), note)
                    st.rerun()

            with st.expander("Technical audit trail"):
                calls = p.get("agent_calls", [])
                if calls:
                    render_table(calls)
                else:
                    st.caption("No tool-call details were recorded for this proposal.")

with tab_done:
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    if not done:
        st.info("No review decisions have been recorded yet.")
    else:
        render_table(
            [
                {
                    "Proposal ID": r.get("id"),
                    "Zone": r.get("zone"),
                    "Risk level": r.get("risk_level"),
                    "Decision": str(r.get("status", "")).title(),
                    "Reviewer": r.get("reviewer"),
                    "Reviewed at": r.get("reviewed_at"),
                    "Reviewer note": r.get("reviewer_note"),
                }
                for r in done
            ]
        )