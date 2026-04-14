import streamlit as st
import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "exam_langchain")
LANGSMITH_ENDPOINT = os.getenv(
    "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
).rstrip("/")
ORG_ID = os.getenv("LANGCHAIN_ORG_ID","")
PROJECT_ID = os.getenv("LANGCHAIN_PROJECT_ID","")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitoring · LangSmith",
    page_icon="📡",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.stApp { background: #0d0f14; color: #e8e6df; }

/* Streamlit native text overrides */
.stApp p, .stApp label, .stApp .stMarkdown p { color: #c8c6bf !important; }
[data-testid="stCaptionContainer"] p, .stApp .stCaption, small { color: #a8a69f !important; }
.stApp .stTextInput label, .stApp .stSelectbox label, .stApp .stSlider label { color: #c8c6bf !important; }
.stApp .streamlit-expanderHeader { color: #c8c6bf !important; }
.stApp input::placeholder { color: #6e6c66 !important; }

[data-testid="stSidebar"] {
    background: #111318;
    border-right: 1px solid #1e2130;
}
[data-testid="stSidebar"] * { color: #c8c6bf; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small { color: #a8a69f !important; }

.metric-card {
    background: #131720;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    text-align: center;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    color: #7fffb2;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.72rem;
    color: #a8a69f;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}
.metric-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #b0b8c4;
    margin-top: 2px;
}

.run-card {
    background: #111318;
    border: 1px solid #1e2535;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.5rem;
    font-size: 0.82rem;
}
.run-card:hover { border-color: #2a3548; }

.run-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #e8e6df;
    font-weight: 600;
}
.run-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #9896af;
    margin-top: 2px;
}

.badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.badge-success { background:#1a2e22; color:#7fffb2; border:1px solid #2a4f38; }
.badge-error   { background:#2e1a1a; color:#ff6b6b; border:1px solid #4f2a2a; }
.badge-running { background:#1a2330; color:#74b9ff; border:1px solid #2a3f5f; }

.section-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.15rem;
    color: #e8e6df;
    letter-spacing: -0.02em;
    margin-bottom: 0.75rem;
}
.page-header {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    color: #e8e6df;
    letter-spacing: -0.03em;
    margin-bottom: 0.25rem;
}

.stButton > button {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    background: #1a2e22;
    color: #7fffb2;
    border: 1px solid #2a4f38;
    border-radius: 8px;
    padding: 0.4rem 1.2rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #7fffb2;
    color: #0d0f14;
    border-color: #7fffb2;
}

.stSelectbox > div { background: #0a0c10; border: 1px solid #1e2535; border-radius: 8px; }
.stSlider { color: #7fffb2; }

.io-block {
    background: #0a0c10;
    border: 1px solid #1e2535;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #b0b8c4;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 220px;
    overflow-y: auto;
}
.divider {
    height: 1px;
    background: linear-gradient(90deg, #7fffb222, #7fffb200);
    margin: 1.25rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── LangSmith API helpers ─────────────────────────────────────────────────────
LS_HEADERS = {
    "x-api-key": LANGSMITH_API_KEY,
    "Content-Type": "application/json",
}

def ls_request(method: str, path: str, params: dict = None, json_data: dict = None):
    """Effectue une requête propre à l'API LangSmith sans slash final pour éviter les 404."""
    # On s'assure que le path est propre (pas de slash au début ou à la fin)
    path = path.strip("/")
    url = f"{LANGSMITH_ENDPOINT}/api/v1/{path}"
    
    try:
        r = requests.request(
            method,
            url,
            headers=LS_HEADERS,
            params=params,
            json=json_data,
            timeout=15
        )
        # Si 405, on tente une redirection manuelle ou un changement de méthode
        if r.status_code == 405:
            return None, f"Erreur 405 : La méthode {method} n'est pas autorisée sur {url}."
            
        if r.status_code == 200:
            return r.json(), None
            
        return None, f"HTTP {r.status_code} sur {url} — {r.text}"
    except Exception as e:
        return None, str(e)        
    
def get_traces():
    url = f"{LANGSMITH_ENDPOINT}/api/v1/runs/query"
    
    # Correction : l'API attend 'session' pour filtrer par projet
    payload = {
        "session": [PROJECT_ID], # L'ID de projet
        "limit": 10,
        "run_type": "chain"
    }
    
    try:
        r = requests.post(url, headers=LS_HEADERS, json=payload, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            # La réponse de /query/ contient souvent les runs dans une clé "runs" ou est une liste
            if isinstance(data, dict):
                return data.get("runs", data.get("items", [])), None
            return data, None
            
        return None, f"Erreur {r.status_code} : {r.text}"
    except Exception as e:
        return None, str(e)
    
        
    
def format_duration(ms: float | None) -> str:
    if ms is None:
        return "—"
    if ms < 1000:
        return f"{ms:.0f} ms"
    return f"{ms/1000:.2f} s"

def format_dt(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m %H:%M:%S")
    except Exception:
        return iso[:19]

def run_status_badge(status: str) -> str:
    if status == "success":
        return '<span class="badge badge-success">✓ OK</span>'
    elif status == "error":
        return '<span class="badge badge-error">✗ ERR</span>'
    else:
        return f'<span class="badge badge-running">{status}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:0.5rem 0 1rem">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.2rem;color:#e8e6df">
            📡 Monitoring
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#9896af;margin-top:4px">
            LangSmith · REST API
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.page_link("app.py", label="⚗️ Assistant principal")

    st.markdown("---")

    # Project selector
    projects_data, projects_err = ls_request("GET", "projects")
    if projects_err:
        st.error(f"Erreur lors de la récupération des projets : {projects_err}")
        projects_data = []
    else:
        # L'API LangSmith renvoie souvent {"items": [...]}
        projects_data = projects_json.get("items", []) if isinstance(projects_json, dict) else projects_json
    
    project_names = []
    if projects_data and isinstance(projects_data, list):
        project_names = [p.get("name", "") for p in projects_data if p.get("name")]
    elif projects_data and "projects" in projects_data:
        project_names = [p.get("name", "") for p in projects_data["projects"] if p.get("name")]

    if project_names:
        selected_project = st.selectbox(
            "Projet",
            options=project_names,
            index=project_names.index(LANGSMITH_PROJECT) if LANGSMITH_PROJECT in project_names else 0,
        )
    else:
        selected_project = LANGSMITH_PROJECT
        st.markdown(f"""
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;background:#1a2e22;
             border:1px solid #2a4f38;border-radius:6px;padding:6px 10px;color:#7fffb2">
            {selected_project}
        </div>
        """, unsafe_allow_html=True)

    # On récupère l'ID du projet (car l'API préfère l'ID au nom)
    selected_project_id = next(
        (p["id"] for p in projects_data if p["name"] == selected_project), 
        None
    )

    st.markdown("---")
    limit = st.slider("Nombre de traces", min_value=5, max_value=100, value=20, step=5)

    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────
if not LANGSMITH_API_KEY:
    st.markdown("""
    <div style="background:#2e1a1a;border:1px solid #4f2a2a;border-radius:12px;padding:1.5rem;margin-top:2rem;text-align:center">
        <div style="font-size:2rem">🔑</div>
        <div style="font-weight:700;font-size:1.1rem;color:#ff6b6b;margin-top:8px">LANGSMITH_API_KEY manquante</div>
        <div style="color:#8892a4;font-size:0.85rem;margin-top:6px">
            Ajoute <code>LANGSMITH_API_KEY</code> dans ton fichier <code>.env</code>.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown(f'<div class="page-header">📡 Monitoring <span style="color:#7fffb2">{selected_project}</span></div>', unsafe_allow_html=True)
st.caption(f"Données temps réel via l'API REST LangSmith · {LANGSMITH_ENDPOINT}")

# ── Fetch runs ────────────────────────────────────────────────────────────────
with st.spinner("Chargement des traces…"):
    if selected_project_id:
        # On prépare le corps de la requête (Body)
        query_body = {
            "project_id": selected_project_id,
            "limit": limit,
            "run_type": "chain"
        }
        
        runs_json, runs_err = ls_request("POST", "runs/query", json_data=query_body)
        
        if runs_err:
            st.error(f"Erreur API LangSmith : {runs_err}")
            runs_data = []
        else:
            if isinstance(runs_json, dict):
                runs_data = runs_json.get("items", [])
            else:
                runs_data = runs_json
    else:
        runs_data = get_traces()
    
   
st.info( runs_data)  
   
runs: list[dict] = []
if isinstance(runs_data, list):
    runs = runs_data
elif isinstance(runs_data, dict):
    runs = runs_data.get("runs", runs_data.get("results", []))

# ── Compute metrics ───────────────────────────────────────────────────────────
total = len(runs)
success = sum(1 for r in runs if r.get("status") == "success")
errors  = sum(1 for r in runs if r.get("status") == "error")
success_rate = (success / total * 100) if total else 0

latencies = [r.get("latency_p50") or r.get("total_tokens") for r in runs if r.get("latency_p50")]
durations_ms = []
for r in runs:
    start = r.get("start_time")
    end = r.get("end_time")
    if start and end:
        try:
            s = datetime.fromisoformat(start.replace("Z", "+00:00"))
            e = datetime.fromisoformat(end.replace("Z", "+00:00"))
            durations_ms.append((e - s).total_seconds() * 1000)
        except Exception:
            pass

avg_duration = sum(durations_ms) / len(durations_ms) if durations_ms else None

total_tokens = sum(
    (r.get("prompt_tokens") or 0) + (r.get("completion_tokens") or 0)
    for r in runs
)

# Tokens breakdown
prompt_tokens_total = sum(r.get("prompt_tokens") or 0 for r in runs)
completion_tokens_total = sum(r.get("completion_tokens") or 0 for r in runs)

# ── Metrics row ───────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Vue d\'ensemble</div>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total}</div>
        <div class="metric-label">Traces</div>
        <div class="metric-sub">sur {limit} demandées</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    color = "#7fffb2" if success_rate >= 80 else "#ffd166" if success_rate >= 50 else "#ff6b6b"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{color}">{success_rate:.0f}%</div>
        <div class="metric-label">Taux de succès</div>
        <div class="metric-sub">{success} ok · {errors} err</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{format_duration(avg_duration)}</div>
        <div class="metric-label">Durée moyenne</div>
        <div class="metric-sub">{len(durations_ms)} runs mesurés</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_tokens:,}</div>
        <div class="metric-label">Tokens totaux</div>
        <div class="metric-sub">↑{prompt_tokens_total:,} ↓{completion_tokens_total:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    # Run type distribution
    run_names = {}
    for r in runs:
        name = r.get("name", "unknown")
        run_names[name] = run_names.get(name, 0) + 1
    top_chain = max(run_names, key=run_names.get) if run_names else "—"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="font-size:1rem;padding-top:0.4rem">{top_chain[:16]}</div>
        <div class="metric-label">Chaîne la + appelée</div>
        <div class="metric-sub">{run_names.get(top_chain, 0)}× sur {total}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Duration chart ────────────────────────────────────────────────────────────
if durations_ms:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Latences (ms) — 20 dernières traces</div>', unsafe_allow_html=True)

    import streamlit as _st
    chart_data = {"Durée (ms)": durations_ms[:20]}
    st.bar_chart(chart_data, color="#7fffb2", height=180)

# ── Chain distribution ────────────────────────────────────────────────────────
if run_names:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distribution des chaînes</div>', unsafe_allow_html=True)

    cols = st.columns(min(len(run_names), 4))
    for i, (name, count) in enumerate(sorted(run_names.items(), key=lambda x: -x[1])):
        pct = count / total * 100 if total else 0
        with cols[i % len(cols)]:
            st.markdown(f"""
            <div class="metric-card" style="text-align:left">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#e8e6df;
                     font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{name}</div>
                <div style="display:flex;align-items:center;gap:8px;margin-top:8px">
                    <div style="flex:1;background:#1e2535;border-radius:4px;height:5px">
                        <div style="width:{pct:.0f}%;background:#7fffb2;height:5px;border-radius:4px"></div>
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#7fffb2">{count}×</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Run list ──────────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Traces récentes</div>', unsafe_allow_html=True)

# Filters
col_f1, col_f2 = st.columns([2, 2])
with col_f1:
    filter_status = st.selectbox("Statut", ["Tous", "success", "error"], key="filter_status")
with col_f2:
    filter_name = st.text_input("Filtrer par nom de chaîne", placeholder="RunnableSequence…", key="filter_name")

filtered_runs = [
    r for r in runs
    if (filter_status == "Tous" or r.get("status") == filter_status)
    and (not filter_name or filter_name.lower() in (r.get("name", "")).lower())
]

if not filtered_runs:
    st.markdown('<div style="color:#a8a69f;font-size:0.85rem;padding:1rem 0">Aucune trace correspondant aux filtres.</div>', unsafe_allow_html=True)

for run in filtered_runs:
    run_id = run.get("id", "")
    run_name = run.get("name", "—")
    run_status = run.get("status", "unknown")
    start = run.get("start_time", "")
    end = run.get("end_time")

    duration_str = "—"
    if start and end:
        try:
            s = datetime.fromisoformat(start.replace("Z", "+00:00"))
            e = datetime.fromisoformat(end.replace("Z", "+00:00"))
            duration_str = format_duration((e - s).total_seconds() * 1000)
        except Exception:
            pass

    ptok = run.get("prompt_tokens") or 0
    ctok = run.get("completion_tokens") or 0
    error_msg = run.get("error", "")

    with st.expander(f"{run_name}  ·  {format_dt(start)}  ·  {duration_str}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(run_status_badge(run_status), unsafe_allow_html=True)
        c2.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.72rem;color:#a8a69f">{format_dt(start)}</span>', unsafe_allow_html=True)
        c3.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.72rem;color:#b0b8c4">⏱ {duration_str}</span>', unsafe_allow_html=True)
        c4.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.72rem;color:#b0b8c4">🔤 ↑{ptok} ↓{ctok}</span>', unsafe_allow_html=True)

        if error_msg:
            st.markdown(f'<div style="background:#2e1a1a;border-radius:6px;padding:0.5rem 0.75rem;color:#ff6b6b;font-size:0.78rem;font-family:\'JetBrains Mono\',monospace;margin-top:8px">{error_msg[:300]}</div>', unsafe_allow_html=True)

        # Input / Output
        inputs = run.get("inputs")
        outputs = run.get("outputs")

        col_io1, col_io2 = st.columns(2)
        with col_io1:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;color:#9896af;letter-spacing:0.08em;margin-bottom:4px">INPUT</div>', unsafe_allow_html=True)
            if inputs:
                import json
                inp_str = json.dumps(inputs, ensure_ascii=False, indent=2)[:600]
                st.markdown(f'<div class="io-block">{inp_str}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="io-block">—</div>', unsafe_allow_html=True)

        with col_io2:
            st.markdown('<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.65rem;color:#9896af;letter-spacing:0.08em;margin-bottom:4px">OUTPUT</div>', unsafe_allow_html=True)
            if outputs:
                import json
                out_str = json.dumps(outputs, ensure_ascii=False, indent=2)[:600]
                st.markdown(f'<div class="io-block">{out_str}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="io-block">—</div>', unsafe_allow_html=True)

        # Deep link to LangSmith UI
        ls_ui = f"https://smith.langchain.com/o/runs/{run_id}"
        st.markdown(f'<a href="{ls_ui}" target="_blank" style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;color:#74b9ff">↗ Voir dans LangSmith</a>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(f"""
<div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#9896af;text-align:center">
    projet · {selected_project} · endpoint · {LANGSMITH_ENDPOINT}
</div>
""", unsafe_allow_html=True)