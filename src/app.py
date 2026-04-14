import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_API = os.getenv("ASSISTANT_API_URL", "http://localhost:8000")
AUTH_API = os.getenv("AUTH_API_URL", "http://localhost:8001")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PyTest Assistant",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}
.stApp {
    background: #0d0f14;
    color: #e8e6df;
}

/* Streamlit native text overrides — captions, helper text, labels */
.stApp p, .stApp label, .stApp .stMarkdown p {
    color: #c8c6bf !important;
}
[data-testid="stCaptionContainer"] p,
.stApp .stCaption,
small {
    color: #a8a69f !important;
}
/* Form labels */
.stApp .stTextInput label,
.stApp .stTextArea label,
.stApp .stSelectbox label,
.stApp .stSlider label {
    color: #c8c6bf !important;
    font-size: 0.85rem !important;
}
/* Expander headers */
.stApp .streamlit-expanderHeader {
    color: #c8c6bf !important;
}
/* Placeholder text */
.stApp input::placeholder,
.stApp textarea::placeholder {
    color: #6e6c66 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111318;
    border-right: 1px solid #1e2130;
}
[data-testid="stSidebar"] * {
    font-family: 'Syne', sans-serif !important;
    color: #c8c6bf;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small {
    color: #a8a69f !important;
}

/* Header accent */
.app-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 2rem;
}
.app-header h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2.2rem;
    color: #e8e6df;
    margin: 0;
    letter-spacing: -0.03em;
}
.app-header .accent {
    color: #7fffb2;
}
.version-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    background: #1a2e22;
    color: #7fffb2;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid #2a4f38;
}

/* Cards */
.result-card {
    background: #131720;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
}
.result-card.success { border-left: 3px solid #7fffb2; }
.result-card.warning { border-left: 3px solid #ffd166; }
.result-card.error   { border-left: 3px solid #ff6b6b; }
.result-card.info    { border-left: 3px solid #74b9ff; }

/* Status badge */
.badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    padding: 2px 10px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.badge-green  { background:#1a2e22; color:#7fffb2; border:1px solid #2a4f38; }
.badge-red    { background:#2e1a1a; color:#ff6b6b; border:1px solid #4f2a2a; }
.badge-yellow { background:#2e2a1a; color:#ffd166; border:1px solid #4f4228; }

/* Code blocks */
.stCodeBlock, code {
    font-family: 'JetBrains Mono', monospace !important;
    background: #0a0c10 !important;
}

/* Buttons */
.stButton > button {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    background: #1a2e22;
    color: #7fffb2;
    border: 1px solid #2a4f38;
    border-radius: 8px;
    padding: 0.4rem 1.2rem;
    transition: all 0.15s ease;
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    background: #7fffb2;
    color: #0d0f14;
    border-color: #7fffb2;
}

/* Text areas */
.stTextArea textarea {
    font-family: 'JetBrains Mono', monospace;
    background: #0a0c10;
    color: #e8e6df;
    border: 1px solid #1e2535;
    border-radius: 8px;
    font-size: 0.85rem;
}

/* Text inputs */
.stTextInput input {
    font-family: 'JetBrains Mono', monospace;
    background: #0a0c10;
    color: #e8e6df;
    border: 1px solid #1e2535;
    border-radius: 8px;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #1e2535;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    color: #5a6070;
    background: transparent;
    border-radius: 8px 8px 0 0;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    color: #7fffb2 !important;
    background: #131720 !important;
    border-bottom: 2px solid #7fffb2 !important;
}

/* Chat messages */
.chat-msg-user {
    background: #1a1e2c;
    border: 1px solid #252b3d;
    border-radius: 12px 12px 4px 12px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    text-align: right;
    font-size: 0.9rem;
}
.chat-msg-assistant {
    background: #131720;
    border: 1px solid #1e2535;
    border-radius: 12px 12px 12px 4px;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
}
.chat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #9896af;
    margin-bottom: 4px;
    letter-spacing: 0.08em;
}

/* History item */
.hist-item {
    background: #111318;
    border: 1px solid #1e2535;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.82rem;
}
.hist-type {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #9896af;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* Divider */
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, #7fffb222, #7fffb200);
    margin: 1.5rem 0;
}

/* Selectbox */
.stSelectbox select {
    background: #0a0c10;
    color: #e8e6df;
    border: 1px solid #1e2535;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
for key, default in {
    "token": None,
    "username": None,
    "chat_messages": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Helpers ───────────────────────────────────────────────────────────────────
def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def api_post(endpoint: str, payload: dict, auth: bool = True):
    headers = auth_headers() if auth else {}
    try:
        r = requests.post(f"{ASSISTANT_API}{endpoint}", json=payload, headers=headers, timeout=60)
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def api_get(endpoint: str):
    try:
        r = requests.get(f"{ASSISTANT_API}{endpoint}", headers=auth_headers(), timeout=30)
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def badge(text, color="green"):
    return f'<span class="badge badge-{color}">{text}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1.5rem">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.3rem;color:#e8e6df;letter-spacing:-0.02em">
            ⚗️ PyTest<span style="color:#7fffb2">AI</span>
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#5a6070;margin-top:4px">
            v1.0 · LangChain + FastAPI
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.token:
        st.markdown("---")
        st.markdown("##### Connexion requise")
        st.caption("Connecte-toi pour accéder à l'assistant.")
    else:
        st.markdown(f"""
        <div style="background:#1a2e22;border:1px solid #2a4f38;border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:1rem">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#5a6070;letter-spacing:0.08em">CONNECTÉ EN TANT QUE</div>
            <div style="color:#7fffb2;font-weight:600;font-size:0.9rem;margin-top:2px">@{st.session_state.username}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔓 Déconnexion", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.chat_messages = []
            st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem;color:#5a6070;line-height:1.8">
        <div style="color:#e8e6df;font-weight:600;margin-bottom:6px">Fonctionnalités</div>
        🔍 Analyse de code<br>
        🧪 Génération de tests<br>
        📖 Explication de tests<br>
        ⚡ Pipeline complet<br>
        💬 Chat libre<br>
        📜 Historique
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.page_link("pages/2_langsmith.py", label="📡 Monitoring LangSmith", icon=None)

# ── Main header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>PyTest<span class="accent">AI</span> Assistant</h1>
    <span class="version-tag">v1.0</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# AUTH SECTION (if not logged in)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.token:
    col_l, col_r = st.columns([1, 1], gap="large")

    with col_l:
        st.markdown("### Connexion")
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", placeholder="alice")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Se connecter →", use_container_width=True)

        if submitted:
            try:
                r = requests.post(
                    f"{AUTH_API}/login",
                    json={"username": username, "password": password},
                    timeout=10,
                )
                if r.status_code == 200:
                    st.session_state.token = r.json()["access_token"]
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.markdown('<div class="result-card error">❌ Identifiants incorrects.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="result-card error">❌ Erreur de connexion : {e}</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown("### Créer un compte")
        with st.form("signup_form"):
            new_user = st.text_input("Nom d'utilisateur", placeholder="bob", key="signup_user")
            new_pass = st.text_input("Mot de passe", type="password", placeholder="••••••••", key="signup_pass")
            new_pass2 = st.text_input("Confirmer", type="password", placeholder="••••••••", key="signup_pass2")
            signup_btn = st.form_submit_button("Créer le compte →", use_container_width=True)

        if signup_btn:
            if new_pass != new_pass2:
                st.markdown('<div class="result-card warning">⚠️ Les mots de passe ne correspondent pas.</div>', unsafe_allow_html=True)
            elif len(new_pass) < 4:
                st.markdown('<div class="result-card warning">⚠️ Mot de passe trop court.</div>', unsafe_allow_html=True)
            else:
                try:
                    r = requests.post(
                        f"{AUTH_API}/signup",
                        json={"username": new_user, "password": new_pass},
                        timeout=10,
                    )
                    if r.status_code == 200:
                        st.markdown('<div class="result-card success">✅ Compte créé ! Tu peux maintenant te connecter.</div>', unsafe_allow_html=True)
                    elif r.status_code == 400:
                        st.markdown('<div class="result-card error">❌ Ce nom d\'utilisateur est déjà pris.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="result-card error">❌ Erreur : {r.json()}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="result-card error">❌ {e}</div>', unsafe_allow_html=True)

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP (logged in)
# ══════════════════════════════════════════════════════════════════════════════

tab_analyze, tab_test, tab_explain, tab_pipeline, tab_chat, tab_history = st.tabs([
    "🔍 Analyser",
    "🧪 Générer test",
    "📖 Expliquer test",
    "⚡ Pipeline",
    "💬 Chat",
    "📜 Historique",
])

# ── TAB 1 : Analyse ───────────────────────────────────────────────────────────
with tab_analyze:
    st.markdown("#### Analyse de code Python")
    st.caption("Soumets un extrait de code pour obtenir une analyse détaillée de sa qualité.")

    code_input = st.text_area(
        "Code Python",
        height=200,
        placeholder="def add(a, b):\n    return a + b",
        key="analyze_code",
    )
    if st.button("Analyser →", key="btn_analyze"):
        if not code_input.strip():
            st.warning("Saisis du code avant d'analyser.")
        else:
            with st.spinner("Analyse en cours…"):
                data, status = api_post("/analyze", {"code": code_input})

            if status == 200:
                is_opt = data.get("is_optimal", False)
                badge_html = badge("OPTIMAL", "green") if is_opt else badge("NON OPTIMAL", "red")
                st.markdown(f'<div class="result-card {"success" if is_opt else "warning"}">'
                            f'<div style="margin-bottom:8px">{badge_html}</div>', unsafe_allow_html=True)

                issues = data.get("issues", [])
                suggestions = data.get("suggestions", [])

                if issues:
                    st.markdown("**Problèmes identifiés**")
                    for issue in issues:
                        st.markdown(f"- 🔴 {issue}")

                if suggestions:
                    st.markdown("**Suggestions d'amélioration**")
                    for s in suggestions:
                        st.markdown(f"- 💡 {s}")

                if not issues and not suggestions:
                    st.markdown("✅ Aucun problème détecté.")

                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-card error">❌ Erreur {status} : {data.get("detail", data)}</div>', unsafe_allow_html=True)

# ── TAB 2 : Génération de tests ───────────────────────────────────────────────
with tab_test:
    st.markdown("#### Génération de test unitaire pytest")
    st.caption("Fournis une fonction Python et obtiens un test unitaire complet.")

    code_for_test = st.text_area(
        "Fonction Python",
        height=200,
        placeholder="def multiply(a, b):\n    \"\"\"Multiplie deux nombres.\"\"\"\n    return a * b",
        key="test_code",
    )
    if st.button("Générer le test →", key="btn_test"):
        if not code_for_test.strip():
            st.warning("Saisis une fonction avant de générer.")
        else:
            with st.spinner("Génération en cours…"):
                data, status = api_post("/generate_test", {"code": code_for_test})

            if status == 200:
                unit_test = data.get("unit_test", "")
                st.markdown('<div class="result-card success">', unsafe_allow_html=True)
                st.markdown("**Test unitaire généré**")
                st.code(unit_test, language="python")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-card error">❌ Erreur {status} : {data.get("detail", data)}</div>', unsafe_allow_html=True)

# ── TAB 3 : Explication ───────────────────────────────────────────────────────
with tab_explain:
    st.markdown("#### Explication pédagogique d'un test")
    st.caption("Colle un test pytest pour obtenir une explication claire et détaillée.")

    test_to_explain = st.text_area(
        "Test pytest",
        height=200,
        placeholder="def test_add():\n    assert add(1, 2) == 3\n    assert add(-1, 1) == 0",
        key="explain_test",
    )
    if st.button("Expliquer →", key="btn_explain"):
        if not test_to_explain.strip():
            st.warning("Saisis un test avant d'expliquer.")
        else:
            with st.spinner("Explication en cours…"):
                data, status = api_post("/explain_test", {"code": test_to_explain})

            if status == 200:
                explanation = data.get("explanation", "")
                st.markdown('<div class="result-card info">', unsafe_allow_html=True)
                st.markdown("**Explication**")
                st.markdown(explanation)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-card error">❌ Erreur {status} : {data.get("detail", data)}</div>', unsafe_allow_html=True)

# ── TAB 4 : Pipeline ─────────────────────────────────────────────────────────
with tab_pipeline:
    st.markdown("#### Pipeline complet")
    st.caption("Analyse → génération → explication en une seule passe. S'arrête si le code n'est pas optimal.")

    pipeline_code = st.text_area(
        "Code Python",
        height=200,
        placeholder="def divide(a, b):\n    \"\"\"Divise a par b.\"\"\"\n    if b == 0:\n        raise ValueError('Division par zéro')\n    return a / b",
        key="pipeline_code",
    )
    if st.button("Lancer le pipeline ⚡", key="btn_pipeline"):
        if not pipeline_code.strip():
            st.warning("Saisis du code avant de lancer le pipeline.")
        else:
            with st.spinner("Pipeline en cours…"):
                data, status = api_post("/full_pipeline", {"code": pipeline_code})

            if status == 200:
                # Stopped early
                if "error" in data:
                    st.markdown(f'<div class="result-card warning">'
                                f'{badge("ARRÊT", "yellow")} <strong>{data["error"]}</strong>'
                                f'</div>', unsafe_allow_html=True)
                    analysis = data.get("analysis", {})
                    if analysis.get("issues"):
                        st.markdown("**Problèmes :**")
                        for i in analysis["issues"]:
                            st.markdown(f"- 🔴 {i}")
                    if analysis.get("suggestions"):
                        st.markdown("**Suggestions :**")
                        for s in analysis["suggestions"]:
                            st.markdown(f"- 💡 {s}")
                else:
                    # Full run
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('<div class="result-card success">', unsafe_allow_html=True)
                        st.markdown(f"**Analyse** {badge('OPTIMAL', 'green')}", unsafe_allow_html=True)
                        analysis = data.get("analysis", {})
                        sug = analysis.get("suggestions", [])
                        st.markdown("✅ Code optimal." if not sug else "\n".join(f"- {s}" for s in sug))
                        st.markdown('</div>', unsafe_allow_html=True)

                    with col2:
                        st.markdown('<div class="result-card info">', unsafe_allow_html=True)
                        st.markdown("**Test généré**")
                        test_data = data.get("test", {})
                        st.code(test_data.get("unit_test", ""), language="python")
                        st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown('<div class="result-card info">', unsafe_allow_html=True)
                    st.markdown("**Explication**")
                    exp_data = data.get("explanation", {})
                    st.markdown(exp_data.get("explanation", ""))
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-card error">❌ Erreur {status} : {data.get("detail", data)}</div>', unsafe_allow_html=True)

# ── TAB 5 : Chat ─────────────────────────────────────────────────────────────
with tab_chat:
    st.markdown("#### Chat libre")
    st.caption("Pose toutes tes questions sur Python, les tests, les bonnes pratiques…")

    # Display chat history
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div>
                <div class="chat-label" style="text-align:right">TOI</div>
                <div class="chat-msg-user">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div>
                <div class="chat-label">ASSISTANT</div>
                <div class="chat-msg-assistant">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Message",
            placeholder="Comment écrire un bon test paramétrique avec pytest ?",
            label_visibility="collapsed",
        )
        col_send, col_clear = st.columns([4, 1])
        with col_send:
            send = st.form_submit_button("Envoyer →", use_container_width=True)
        with col_clear:
            clear = st.form_submit_button("Effacer", use_container_width=True)

    if send and user_input.strip():
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.spinner("…"):
            data, status = api_post("/chat", {"input": user_input})
        if status == 200:
            response = data.get("response", "")
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
        else:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": f"❌ Erreur : {data.get('detail', data)}"
            })
        st.rerun()

    if clear:
        st.session_state.chat_messages = []
        st.rerun()

# ── TAB 6 : Historique ────────────────────────────────────────────────────────
with tab_history:
    st.markdown("#### Historique des requêtes")
    st.caption("Toutes tes interactions avec l'assistant pour cette session.")

    col_refresh, col_spacer = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Rafraîchir", key="btn_history"):
            st.rerun()

    data, status = api_get("/history")

    if status == 200:
        history = data.get("history", [])
        if not history:
            st.markdown('<div class="result-card info">Aucun historique pour cette session.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"**{len(history)} entrée(s)**")
            for i, entry in enumerate(reversed(history), 1):
                entry_type = entry.get("type", entry.get("role", "message"))
                role = entry.get("role", "")

                # Determine color
                color_map = {
                    "analyze": "#74b9ff",
                    "generate_test": "#7fffb2",
                    "explain_test": "#a29bfe",
                    "full_pipeline": "#ffd166",
                    "full_pipeline_analysis": "#ffd166",
                    "user": "#ffeaa7",
                    "assistant": "#dfe6e9",
                    "message": "#dfe6e9",
                }
                color = color_map.get(entry_type, color_map.get(role, "#5a6070"))
                label = entry_type.replace("_", " ").upper() if entry_type else role.upper()

                with st.expander(f"#{len(history) - i + 1} · {label}", expanded=False):
                    # Show content key or full dump
                    if "content" in entry:
                        st.markdown(entry["content"])
                    elif "unit_test" in entry:
                        st.code(entry["unit_test"], language="python")
                    elif "explanation" in entry:
                        st.markdown(entry["explanation"])
                    elif "is_optimal" in entry:
                        opt = entry.get("is_optimal")
                        b = badge("OPTIMAL", "green") if opt else badge("NON OPTIMAL", "red")
                        st.markdown(b, unsafe_allow_html=True)
                        for issue in entry.get("issues", []):
                            st.markdown(f"- 🔴 {issue}")
                    else:
                        st.json(entry)
    else:
        st.markdown(f'<div class="result-card error">❌ Impossible de charger l\'historique : {data.get("detail", data)}</div>', unsafe_allow_html=True)