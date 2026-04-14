import json
import os
from datetime import datetime

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY      = os.getenv("LANGCHAIN_API_KEY", "")
PROJECT_NAME = os.getenv("LANGCHAIN_PROJECT", "exo_langchain")
PROJECT_ID   = os.getenv("LANGCHAIN_PROJECT_ID", "")
ENDPOINT     = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com").rstrip("/")
ORG_ID       = os.getenv("LANGCHAIN_ORG_ID", "")

HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Monitoring · LangSmith", page_icon="📡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"]              { font-family: 'Syne', sans-serif; }
.stApp                                  { background: #0d0f14; color: #e8e6df; }
.stApp p, .stApp label,
.stApp .stMarkdown p                    { color: #c8c6bf !important; }
[data-testid="stCaptionContainer"] p,
.stApp .stCaption, small                { color: #a8a69f !important; }
.stApp .stTextInput label,
.stApp .stSelectbox label,
.stApp .stSlider label                  { color: #c8c6bf !important; }
.stApp .streamlit-expanderHeader        { color: #c8c6bf !important; }
.stApp input::placeholder               { color: #6e6c66 !important; }

[data-testid="stSidebar"]              { background: #111318; border-right: 1px solid #1e2130; }
[data-testid="stSidebar"] *            { color: #c8c6bf; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small        { color: #a8a69f !important; }

.stButton > button {
    font-family: 'Syne', sans-serif; font-weight: 600;
    background: #1a2e22; color: #7fffb2;
    border: 1px solid #2a4f38; border-radius: 8px;
    padding: 0.4rem 1.2rem; transition: all 0.15s ease;
}
.stButton > button:hover { background: #7fffb2; color: #0d0f14; border-color: #7fffb2; }

.metric-card {
    background: #131720; border: 1px solid #1e2535;
    border-radius: 12px; padding: 1.1rem 1.4rem; text-align: center;
}
.metric-value  { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 600; color: #7fffb2; line-height: 1.1; }
.metric-label  { font-size: 0.72rem; color: #a8a69f; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }
.metric-sub    { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #b0b8c4; margin-top: 2px; }

.badge { display:inline-block; font-family:'JetBrains Mono',monospace; font-size:0.65rem;
         padding:2px 8px; border-radius:20px; font-weight:600; letter-spacing:0.05em; }
.badge-ok  { background:#1a2e22; color:#7fffb2; border:1px solid #2a4f38; }
.badge-err { background:#2e1a1a; color:#ff6b6b; border:1px solid #4f2a2a; }
.badge-unk { background:#1a2330; color:#74b9ff; border:1px solid #2a3f5f; }

.section-title { font-family:'Syne',sans-serif; font-weight:800; font-size:1.15rem;
                 color:#e8e6df; letter-spacing:-0.02em; margin-bottom:0.75rem; }
.page-header   { font-family:'Syne',sans-serif; font-weight:800; font-size:2rem;
                 color:#e8e6df; letter-spacing:-0.03em; margin-bottom:0.25rem; }

.io-block {
    background:#0a0c10; border:1px solid #1e2535; border-radius:8px;
    padding:0.75rem 1rem; font-family:'JetBrains Mono',monospace;
    font-size:0.75rem; color:#b0b8c4;
    white-space:pre-wrap; word-break:break-all; max-height:260px; overflow-y:auto;
}
.divider { height:1px; background:linear-gradient(90deg,#7fffb222,#7fffb200); margin:1.25rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def fetch_runs(project_id: str, limit: int, run_type: str) -> tuple[list, str | None]:
    """POST /api/v1/runs/query avec session:[project_id] — endpoint confirmé fonctionnel."""
    try:
        r = requests.post(
            f"{ENDPOINT}/api/v1/runs/query",
            headers=HEADERS,
            json={"session": [project_id], "limit": limit, "run_type": run_type},
            timeout=20,
        )
        if r.status_code == 200:
            data = r.json()
            runs = data if isinstance(data, list) else data.get("runs", data.get("items", []))
            return runs, None
        return [], f"HTTP {r.status_code} — {r.text[:200]}"
    except Exception as e:
        return [], str(e)

def fmt_duration(ms: float | None) -> str:
    if ms is None:
        return "—"
    return f"{ms:.0f} ms" if ms < 1000 else f"{ms / 1000:.2f} s"

def fmt_dt(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m %H:%M:%S")
    except Exception:
        return iso[:19]

def duration_ms(run: dict) -> float | None:
    try:
        s = datetime.fromisoformat(run["start_time"].replace("Z", "+00:00"))
        e = datetime.fromisoformat(run["end_time"].replace("Z", "+00:00"))
        return (e - s).total_seconds() * 1000
    except Exception:
        return None

def status_badge(status: str) -> str:
    if status == "success":
        return '<span class="badge badge-ok">✓ OK</span>'
    if status == "error":
        return '<span class="badge badge-err">✗ ERR</span>'
    return f'<span class="badge badge-unk">{status or "?"}</span>'

def pretty_json(obj) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0 1.25rem">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.2rem;color:#e8e6df">📡 Monitoring</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#9896af;margin-top:4px">LangSmith · REST API</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.page_link("app.py", label="⚗️ Assistant principal")
    st.markdown("---")

    # Projet fixé depuis .env (GET /projects retourne 404)
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;background:#1a2e22;
         border:1px solid #2a4f38;border-radius:6px;padding:6px 10px;color:#7fffb2;margin-bottom:4px">
        {PROJECT_NAME}
    </div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:#9896af;margin-bottom:1rem">
        ID : {PROJECT_ID[:20] + "…" if len(PROJECT_ID) > 20 else PROJECT_ID}
    </div>
    """, unsafe_allow_html=True)

    run_type = st.selectbox("Type de run", ["chain", "llm", "tool", "retriever"], index=0)
    limit    = st.slider("Nombre de traces", min_value=5, max_value=100, value=20, step=5)

    st.markdown("---")
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.rerun()

# ── Guards ────────────────────────────────────────────────────────────────────
if not API_KEY:
    st.error("LANGCHAIN_API_KEY manquante dans le fichier .env")
    st.stop()
if not PROJECT_ID:
    st.error("LANGCHAIN_PROJECT_ID manquant dans le fichier .env")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="page-header">📡 Monitoring <span style="color:#7fffb2">{PROJECT_NAME}</span></div>',
            unsafe_allow_html=True)
st.caption(f"Source : {ENDPOINT} · type={run_type} · limit={limit}")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Fetch ─────────────────────────────────────────────────────────────────────
with st.spinner("Chargement des traces…"):
    runs, fetch_err = fetch_runs(PROJECT_ID, limit, run_type)

if fetch_err:
    st.error(f"Erreur API LangSmith : {fetch_err}")
    st.stop()

if not runs:
    st.info("Aucune trace trouvée pour ce projet / ce type de run.")
    st.stop()

# ── Métriques ─────────────────────────────────────────────────────────────────
total      = len(runs)
n_ok       = sum(1 for r in runs if r.get("status") == "success")
n_err      = sum(1 for r in runs if r.get("status") == "error")
rate       = n_ok / total * 100 if total else 0

durations  = [d for r in runs if (d := duration_ms(r)) is not None]
avg_dur    = sum(durations) / len(durations) if durations else None
max_dur    = max(durations) if durations else None

prompt_tok = sum(r.get("prompt_tokens") or 0 for r in runs)
compl_tok  = sum(r.get("completion_tokens") or 0 for r in runs)

run_names: dict[str, int] = {}
for r in runs:
    n = r.get("name", "unknown")
    run_names[n] = run_names.get(n, 0) + 1
top_chain = max(run_names, key=run_names.get) if run_names else "—"

# ── Metrics row ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Vue d\'ensemble</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{total}</div>
        <div class="metric-label">Traces</div>
        <div class="metric-sub">{run_type}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    rate_color = "#7fffb2" if rate >= 80 else "#ffd166" if rate >= 50 else "#ff6b6b"
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="color:{rate_color}">{rate:.0f}%</div>
        <div class="metric-label">Succès</div>
        <div class="metric-sub">{n_ok} ok · {n_err} err</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{fmt_duration(avg_dur)}</div>
        <div class="metric-label">Durée moyenne</div>
        <div class="metric-sub">max {fmt_duration(max_dur)}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{prompt_tok + compl_tok:,}</div>
        <div class="metric-label">Tokens</div>
        <div class="metric-sub">↑{prompt_tok:,} ↓{compl_tok:,}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value" style="font-size:1rem;padding-top:0.5rem">{top_chain[:14]}</div>
        <div class="metric-label">Chaîne principale</div>
        <div class="metric-sub">{run_names.get(top_chain, 0)}× / {total}</div>
    </div>""", unsafe_allow_html=True)

# ── Graphique latences ────────────────────────────────────────────────────────
if durations:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Latences (ms)</div>', unsafe_allow_html=True)
    st.bar_chart({"ms": durations}, color="#7fffb2", height=180)

# ── Distribution des chaînes ──────────────────────────────────────────────────
if len(run_names) > 1:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distribution des chaînes</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(run_names), 4))
    for i, (name, count) in enumerate(sorted(run_names.items(), key=lambda x: -x[1])):
        pct = count / total * 100
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div class="metric-card" style="text-align:left">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#e8e6df;
                     font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                     title="{name}">{name}</div>
                <div style="display:flex;align-items:center;gap:8px;margin-top:10px">
                    <div style="flex:1;background:#1e2535;border-radius:4px;height:5px">
                        <div style="width:{pct:.0f}%;background:#7fffb2;height:5px;border-radius:4px"></div>
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#7fffb2">{count}×</div>
                </div>
            </div>""", unsafe_allow_html=True)

# ── Liste des traces ──────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Traces récentes</div>', unsafe_allow_html=True)

fc1, fc2 = st.columns(2)
with fc1:
    f_status = st.selectbox("Statut", ["Tous", "success", "error"], key="f_status")
with fc2:
    f_name = st.text_input("Nom de chaîne", placeholder="RunnableLambda…", key="f_name")

filtered = [
    r for r in runs
    if (f_status == "Tous" or r.get("status") == f_status)
    and (not f_name or f_name.lower() in r.get("name", "").lower())
]

if not filtered:
    st.markdown('<div style="color:#a8a69f;padding:1rem 0;font-size:0.85rem">Aucune trace correspondante.</div>',
                unsafe_allow_html=True)

for run in filtered:
    rid     = run.get("id", "")
    rname   = run.get("name", "—")
    rstatus = run.get("status", "")
    rstart  = run.get("start_time", "")
    dur     = duration_ms(run)
    ptok    = run.get("prompt_tokens") or 0
    ctok    = run.get("completion_tokens") or 0
    rerr    = run.get("error") or ""

    with st.expander(f"{rname}  ·  {fmt_dt(rstart)}  ·  {fmt_duration(dur)}", expanded=False):

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(status_badge(rstatus), unsafe_allow_html=True)
        m2.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.72rem;color:#a8a69f">{fmt_dt(rstart)}</span>',
                    unsafe_allow_html=True)
        m3.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.72rem;color:#b0b8c4">⏱ {fmt_duration(dur)}</span>',
                    unsafe_allow_html=True)
        m4.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.72rem;color:#b0b8c4">🔤 ↑{ptok} ↓{ctok}</span>',
                    unsafe_allow_html=True)

        if rerr:
            st.markdown(f'<div style="background:#2e1a1a;border-radius:6px;padding:0.5rem 0.75rem;'
                        f'color:#ff6b6b;font-size:0.78rem;font-family:\'JetBrains Mono\',monospace;'
                        f'margin-top:8px">{rerr[:300]}</div>', unsafe_allow_html=True)

        inputs  = run.get("inputs")
        outputs = run.get("outputs")

        io1, io2 = st.columns(2)
        with io1:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;'
                        'color:#9896af;letter-spacing:0.08em;margin-bottom:4px">INPUT</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="io-block">{pretty_json(inputs)[:800] if inputs else "—"}</div>',
                        unsafe_allow_html=True)

        with io2:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;'
                        'color:#9896af;letter-spacing:0.08em;margin-bottom:4px">OUTPUT</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="io-block">{pretty_json(outputs)[:800] if outputs else "—"}</div>',
                        unsafe_allow_html=True)

        if rid:
            ls_url = f"https://smith.langchain.com/o/{ORG_ID}/projects/p/{PROJECT_ID}/runs/{rid}"
            st.markdown(f'<a href="{ls_url}" target="_blank" style="font-family:\'JetBrains Mono\','
                        f'monospace;font-size:0.7rem;color:#74b9ff">↗ Voir dans LangSmith</a>',
                        unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#9896af;text-align:center">
    {PROJECT_NAME} · {PROJECT_ID[:20]}… · {ENDPOINT}
</div>""", unsafe_allow_html=True)