
import os
import requests
import streamlit as st

# ============================================================
# 1. CONFIGURATION
# ============================================================

API_URL = os.getenv(
    "RAG_API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

st.set_page_config(
    page_title="Production RAG Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "upload_results" not in st.session_state:
    st.session_state.upload_results = []


# ============================================================
# 3. PREMIUM DESIGN SYSTEM
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #080e1b;
    --panel: #101b2d;
    --panel2: #15243b;
    --border: rgba(148,163,184,0.16);
    --text: #edf4ff;
    --muted: #91a3bd;
    --blue: #4385f5;
    --cyan: #42d8ed;
    --green: #35d39a;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stAppViewContainer"] .main {
    background:
        radial-gradient(
            circle at 85% 0%,
            rgba(50,110,210,0.13),
            transparent 32%
        ),
        var(--bg);
}

.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: #0c1525;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #b8c6da;
}

.brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 23px;
    font-weight: 700;
    color: white;
    letter-spacing: -0.8px;
}

.brand-accent {
    color: var(--cyan);
}

.brand-subtitle {
    color: #8196b4;
    font-size: 9px;
    letter-spacing: 2px;
    margin-top: 5px;
}

.sidebar-label {
    color: #8298b8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-top: 25px;
    margin-bottom: 10px;
}

/* HERO */

.hero {
    padding: 36px;
    border-radius: 20px;
    border: 1px solid rgba(91,151,255,0.25);
    background:
        radial-gradient(
            circle at 85% 25%,
            rgba(53,214,237,0.18),
            transparent 28%
        ),
        linear-gradient(
            120deg,
            #142747,
            #10213d 60%,
            #15365b
        );
    margin-bottom: 25px;
    position: relative;
    overflow: hidden;
}

.hero-eyebrow {
    color: #65dff2;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.2px;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    color: white;
    font-size: clamp(29px, 3vw, 43px);
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -1.5px;
    margin: 15px 0 12px 0;
}

.hero-description {
    color: #c2d1e5;
    font-size: 13px;
    line-height: 1.8;
    max-width: 720px;
}

.hero-tag {
    display: inline-block;
    margin-top: 18px;
    border: 1px solid rgba(75,214,237,0.3);
    background: rgba(53,214,237,0.08);
    color: #7be5f4;
    border-radius: 30px;
    padding: 7px 13px;
    font-size: 10px;
    letter-spacing: 1px;
}

/* HEADINGS */

.section-title {
    font-family: 'Space Grotesk', sans-serif;
    color: #edf4ff;
    font-size: 19px;
    font-weight: 700;
    margin-bottom: 4px;
}

.section-caption {
    color: var(--muted);
    font-size: 12px;
    margin-bottom: 17px;
}

/* METRIC CARDS */

.metric-card {
    background: linear-gradient(
        145deg,
        #15243b,
        #101a2b
    );
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 20px;
    min-height: 115px;
}

.metric-label {
    color: #9aacc5;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.1px;
    text-transform: uppercase;
}

.metric-value {
    font-family: 'Space Grotesk', sans-serif;
    color: white;
    font-size: 30px;
    font-weight: 700;
    margin-top: 9px;
}

.metric-note {
    color: #8296b2;
    font-size: 10px;
    margin-top: 4px;
}

/* STATUS */

.online {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 25px;
    color: #55e2ae;
    background: rgba(53,211,154,0.09);
    border: 1px solid rgba(53,211,154,0.22);
    font-size: 10px;
    font-weight: 700;
}

.offline {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 25px;
    color: #ff9aa6;
    background: rgba(255,80,100,0.09);
    border: 1px solid rgba(255,80,100,0.22);
    font-size: 10px;
    font-weight: 700;
}

/* WORKSPACE */

.workspace-card {
    background: linear-gradient(
        135deg,
        #13233b,
        #101b2d
    );
    border: 1px solid rgba(80,143,245,0.22);
    border-radius: 16px;
    padding: 25px;
    margin: 12px 0 16px 0;
}

.workspace-eyebrow {
    color: #66d9ed;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.8px;
}

.workspace-heading {
    color: white;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 21px;
    font-weight: 700;
    margin: 10px 0;
}

.workspace-description {
    color: #9eb1ca;
    font-size: 12px;
    line-height: 1.7;
}

/* BUTTONS */

.stButton > button {
    background: linear-gradient(
        110deg,
        #3479eb,
        #3c65cb
    );
    color: white;
    border: 1px solid rgba(119,169,255,0.25);
    border-radius: 10px;
    min-height: 40px;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    color: white;
    border-color: #67d8f2;
    transform: translateY(-1px);
    box-shadow: 0 5px 18px rgba(55,112,220,0.2);
}

/* FILE UPLOADER */

[data-testid="stFileUploader"] {
    background: #111e32;
    border: 1px dashed rgba(87,157,255,0.4);
    border-radius: 13px;
    padding: 10px;
}

[data-testid="stFileUploader"] section {
    background: transparent;
}

[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] small {
    color: #bdcce0 !important;
}

/* CHAT */

[data-testid="stChatMessage"] {
    background: rgba(17,29,48,0.82);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 12px;
}

[data-testid="stChatInput"] {
    background: #111e32;
    border: 1px solid rgba(91,145,255,0.3);
    border-radius: 14px;
}

[data-testid="stChatInput"] textarea {
    color: white !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #8094b0 !important;
}

/* EXPANDERS */

[data-testid="stExpander"] {
    background: #111e32;
    border: 1px solid var(--border);
    border-radius: 12px;
}

[data-testid="stExpander"] summary {
    color: #dce9fb;
}

/* FOOTER */

.footer {
    border-top: 1px solid var(--border);
    padding-top: 18px;
    margin-top: 35px;
    color: #71839d;
    font-size: 10px;
    text-align: center;
    letter-spacing: 1px;
}

hr {
    border-color: var(--border);
}

@media (max-width: 700px) {
    .hero {
        padding: 23px;
    }

    .hero-title {
        font-size: 29px;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 4. API FUNCTIONS
# ============================================================

def get_health():

    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None


def ask_backend(question):

    response = requests.post(
        f"{API_URL}/ask",
        json={"question": question},
        timeout=(10, 180)
    )

    response.raise_for_status()

    return response.json()


def upload_document(uploaded_file):

    response = requests.post(
        f"{API_URL}/upload",
        files={
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        },
        timeout=(10, 600)
    )

    response.raise_for_status()

    return response.json()


def format_score(value):

    try:
        if value is None:
            return "N/A"

        return f"{float(value):.3f}"

    except (ValueError, TypeError):
        return "N/A"


# ============================================================
# 5. SOURCE INTELLIGENCE
# ============================================================

def display_sources(sources):

    if not sources:
        st.info("No supporting source chunks were returned.")
        return

    with st.expander(
        f"◈ SOURCE INTELLIGENCE · {len(sources)} SOURCES",
        expanded=False
    ):

        for number, source in enumerate(sources, start=1):

            left, right = st.columns([4, 1])

            with left:

                st.markdown(
                    f"**SOURCE {number} · "
                    f"{source.get('document', 'Unknown document')}**"
                )

                st.caption(
                    f"Page: {source.get('page', 'N/A')} | "
                    f"Type: {source.get('content_type', 'N/A')}"
                )

            with right:

                st.metric(
                    "Similarity",
                    format_score(
                        source.get("similarity_score")
                    )
                )

            st.divider()


# ============================================================
# 6. LIVE BACKEND STATUS
# ============================================================

health = get_health()

connected = health is not None

document_count = (
    health.get("total_documents", 0)
    if health else 0
)

vector_count = (
    health.get("total_vectors", 0)
    if health else 0
)


# ============================================================
# 7. SIDEBAR
# ============================================================

with st.sidebar:

    st.html("""
    <div class="brand">
        ◈ Production RAG<span class="brand-accent">.</span>
    </div>

    <div class="brand-subtitle">
        ENTERPRISE DOCUMENT INTELLIGENCE
    </div>
    """)

    st.markdown(
        '<div class="sidebar-label">SYSTEM STATUS</div>',
        unsafe_allow_html=True
    )

    if connected:

        st.html("""
        <div class="online">● SYSTEM ONLINE</div>
        """)

        st.caption("FastAPI backend connected")

    else:

        st.html("""
        <div class="offline">● SYSTEM OFFLINE</div>
        """)

        st.caption("Start the FastAPI backend.")

    st.markdown(
        '<div class="sidebar-label">DOCUMENT INGESTION</div>',
        unsafe_allow_html=True
    )

    uploaded_files = st.file_uploader(
        "Add knowledge documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="PDF files up to 50 MB each."
    )

    if uploaded_files:

        st.caption(
            f"{len(uploaded_files)} PDF file(s) selected"
        )

    upload_clicked = st.button(
        "＋ PROCESS DOCUMENTS",
        use_container_width=True,
        disabled=not uploaded_files or not connected
    )

    if upload_clicked:

        results = []

        progress = st.progress(0)

        for position, uploaded_file in enumerate(uploaded_files):

            try:

                with st.spinner(
                    f"Processing {uploaded_file.name}..."
                ):

                    result = upload_document(uploaded_file)

                results.append({
                    "name": uploaded_file.name,
                    "success": True,
                    "result": result
                })

            except requests.HTTPError as error:

                detail = (
                    error.response.text
                    if error.response is not None
                    else str(error)
                )

                results.append({
                    "name": uploaded_file.name,
                    "success": False,
                    "error": detail
                })

            except requests.RequestException as error:

                results.append({
                    "name": uploaded_file.name,
                    "success": False,
                    "error": str(error)
                })

            progress.progress(
                (position + 1) / len(uploaded_files)
            )

        st.session_state.upload_results = results

        st.rerun()

    if st.session_state.upload_results:

        with st.expander("Previous upload results"):

            for item in st.session_state.upload_results:

                if item["success"]:

                    result = item["result"]

                    st.success(item["name"])

                    st.caption(
                        f"Pages: {result.get('pages', 'N/A')} | "
                        f"Chunks: {result.get('chunks', 'N/A')} | "
                        f"Embeddings: {result.get('embeddings', 'N/A')}"
                    )

                else:

                    st.error(item["name"])

                    st.caption(item["error"][:500])

    st.markdown(
        '<div class="sidebar-label">KNOWLEDGE INDEX</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Documents", document_count)

    with col2:
        st.metric("Vectors", f"{vector_count:,}")

    st.caption("Live values from FastAPI health endpoint.")

    st.divider()

    if st.button(
        "＋ NEW CONVERSATION",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.pending_prompt = None

        st.rerun()

    if st.button(
        "CLEAR CHAT HISTORY",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()

    st.html("""
    <div style="
        margin-top:30px;
        color:#71839d;
        font-size:10px;
        line-height:1.9;
    ">
        POWERED BY<br>
        FASTAPI · FAISS · GROQ<br>
        <span style="color:#42d8ed">
            DOCUMENT INTELLIGENCE ENGINE
        </span>
    </div>
    """)


# ============================================================
# 8. HERO SECTION
# ============================================================

st.html("""
<div class="hero">

    <div class="hero-eyebrow">
        INTELLIGENT KNOWLEDGE SYSTEM · VERSION 1.0
    </div>

    <div class="hero-title">
        Your documents.<br>
        One intelligent workspace.
    </div>

    <div class="hero-description">
        Search, understand and explore your document collections
        using retrieval-augmented generation. Every answer is
        grounded in your indexed documents and accompanied by
        source references.
    </div>

    <div class="hero-tag">
        ◈ PRIVATE DOCUMENT INTELLIGENCE
    </div>

</div>
""")


# ============================================================
# 9. WORKSPACE OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">Workspace overview</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-caption">'
    'Live operational status of your document intelligence system.'
    '</div>',
    unsafe_allow_html=True
)

metric1, metric2, metric3 = st.columns(3)

with metric1:

    st.html(f"""
    <div class="metric-card">
        <div class="metric-label">INDEXED DOCUMENTS</div>
        <div class="metric-value">{document_count}</div>
        <div class="metric-note">Documents available to RAG</div>
    </div>
    """)

with metric2:

    st.html(f"""
    <div class="metric-card">
        <div class="metric-label">KNOWLEDGE VECTORS</div>
        <div class="metric-value">{vector_count:,}</div>
        <div class="metric-note">Indexed vector records</div>
    </div>
    """)

with metric3:

    if connected:
        health_label = "OPERATIONAL"
        health_color = "#35d39a"
    else:
        health_label = "DISCONNECTED"
        health_color = "#ff9aa6"

    st.html(f"""
    <div class="metric-card">
        <div class="metric-label">BACKEND HEALTH</div>
        <div class="metric-value"
             style="font-size:23px;color:{health_color}">
            {health_label}
        </div>
        <div class="metric-note">FastAPI service status</div>
    </div>
    """)


st.markdown("---")


# ============================================================
# 10. AI CHAT WORKSPACE
# ============================================================

st.markdown(
    '<div class="section-title">◈ AI knowledge assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-caption">'
    'Ask questions across your indexed documents.'
    '</div>',
    unsafe_allow_html=True
)


# Welcome screen

if not st.session_state.messages:

    st.html("""
    <div class="workspace-card">

        <div class="workspace-eyebrow">
            START EXPLORING
        </div>

        <div class="workspace-heading">
            What would you like to discover?
        </div>

        <div class="workspace-description">
            Ask a question, compare concepts or find specific
            information from your knowledge base. Answers are
            generated using your indexed documents.
        </div>

    </div>
    """)

    suggestions = [
        "Explain the difference between NameNode and DataNode in Hadoop.",
        "Explain supervised and unsupervised learning.",
        "What is code generation in compiler design?",
        "Summarize the important concepts in my documents."
    ]

    left, right = st.columns(2)

    for index, prompt in enumerate(suggestions):

        with (left if index % 2 == 0 else right):

            if st.button(
                prompt,
                key=f"suggestion_{index}",
                use_container_width=True
            ):

                st.session_state.pending_prompt = prompt

                st.rerun()


# Display conversation history

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant":

            display_sources(
                message.get("sources", [])
            )


# ============================================================
# 11. CHAT INPUT AND ANSWER GENERATION
# ============================================================

question = st.chat_input(
    "Ask anything about your indexed documents..."
)

if st.session_state.pending_prompt:

    question = st.session_state.pending_prompt

    st.session_state.pending_prompt = None


if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.markdown(question)

    with st.chat_message("assistant"):

        if not connected:

            answer = (
                "The backend is currently unavailable. "
                "Please start FastAPI and try again."
            )

            sources = []

            st.error(answer)

        else:

            try:

                with st.spinner(
                    "Searching your knowledge base and generating an answer..."
                ):

                    result = ask_backend(question)

                answer = result.get(
                    "answer",
                    "No answer was returned."
                )

                sources = result.get("sources", [])

                st.markdown(answer)

                display_sources(sources)

            except requests.HTTPError as error:

                answer = f"Backend HTTP error: {error}"

                sources = []

                st.error(answer)

            except requests.Timeout:

                answer = (
                    "The request timed out. Please try again."
                )

                sources = []

                st.error(answer)

            except requests.RequestException as error:

                answer = (
                    f"Unable to connect to the backend: {error}"
                )

                sources = []

                st.error(answer)

            except Exception as error:

                answer = (
                    f"An unexpected error occurred: {error}"
                )

                sources = []

                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })


# ============================================================
# 12. FOOTER
# ============================================================

st.html("""
<div class="footer">
    PRODUCTION RAG ASSISTANT
    &nbsp; | &nbsp;
    ENTERPRISE DOCUMENT INTELLIGENCE
    &nbsp; | &nbsp;
    VERSION 1.0
</div>
""")
