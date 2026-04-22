import hashlib
import os
import sys
import warnings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)

import streamlit as st

import backend.config as support_config
from backend.graph import build_graph
from backend.pipeline import build_pdf_retriever, build_support_retriever, get_customer_record


CUSTOMER_RECORDS = getattr(support_config, "CUSTOMER_RECORDS", {})
ISSUE_TYPES = getattr(support_config, "ISSUE_TYPES", ["General Inquiry"])
MODES = ["Customer Support", "PDF Assistant"]


@st.cache_resource
def get_support_graph():
    retriever = build_support_retriever()
    return build_graph(retriever, source_type="customer")


def init_session_state():
    if "customer_chat_history" not in st.session_state:
        st.session_state.customer_chat_history = []
    if "pdf_chat_history" not in st.session_state:
        st.session_state.pdf_chat_history = []
    if CUSTOMER_RECORDS and "active_customer_id" not in st.session_state:
        st.session_state.active_customer_id = next(iter(CUSTOMER_RECORDS))
    if "pdf_graph" not in st.session_state:
        st.session_state.pdf_graph = None
    if "pdf_file_hash" not in st.session_state:
        st.session_state.pdf_file_hash = None
    if "pdf_meta" not in st.session_state:
        st.session_state.pdf_meta = None


def load_pdf_graph(uploaded_file):
    pdf_bytes = uploaded_file.getvalue()
    pdf_file_hash = hashlib.sha256(pdf_bytes).hexdigest()

    if st.session_state.pdf_file_hash == pdf_file_hash:
        return None

    try:
        with st.spinner("Indexing PDF with embeddings..."):
            retriever, metadata = build_pdf_retriever(pdf_bytes, uploaded_file.name)
            st.session_state.pdf_graph = build_graph(retriever, source_type="pdf")
            st.session_state.pdf_file_hash = pdf_file_hash
            st.session_state.pdf_meta = metadata
            st.session_state.pdf_chat_history = []
    except Exception as exc:
        st.session_state.pdf_graph = None
        st.session_state.pdf_file_hash = None
        st.session_state.pdf_meta = None
        return str(exc)

    return None


def render_history(history, key_prefix, mode):
    if not history:
        return

    history_col1, history_col2 = st.columns([4, 1])

    with history_col1:
        st.markdown("### Conversation History")

    with history_col2:
        clear_history = st.button(
            "Clear History",
            key=f"{key_prefix}_clear_history",
            use_container_width=True,
        )

    if clear_history:
        st.session_state[f"{key_prefix}_chat_history"] = []
        st.rerun()

    for chat in reversed(history):
        if mode == "customer":
            st.markdown(
                f"""
            <div class="response-box">
                <strong style="color: #0f4c81;">Customer:</strong> {chat['customer_id']}<br>
                <strong style="color: #0f4c81;">Issue Type:</strong> {chat['issue_type']}<br>
                <strong style="color: #0f4c81;">Order:</strong> {chat['order_id']}<br><br>
                <strong style="color: #0f4c81;">Q:</strong> {chat['question']}<br><br>
                <strong style="color: #333333;">A:</strong> <span style="color: #000000;">{chat['response']}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
            <div class="response-box">
                <strong style="color: #0f4c81;">Document:</strong> {chat['file_name']}<br><br>
                <strong style="color: #0f4c81;">Q:</strong> {chat['question']}<br><br>
                <strong style="color: #333333;">A:</strong> <span style="color: #000000;">{chat['response']}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_customer_mode():
    if not CUSTOMER_RECORDS:
        st.markdown(
            """
        <div class="status-warning">
            No customer records were loaded from <code>backend/config.py</code>. Restart Streamlit after saving the file.
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    customer_ids = list(CUSTOMER_RECORDS.keys())

    st.markdown("### Customer")

    lookup_col1, lookup_col2, lookup_col3 = st.columns([2.2, 2, 1.6])

    with lookup_col1:
        selected_customer_id = st.selectbox(
            "Select customer",
            customer_ids,
            format_func=lambda customer_id: f"{customer_id} - {CUSTOMER_RECORDS[customer_id]['name']}",
        )

    selected_customer = get_customer_record(selected_customer_id)
    order_options = ["Account overview"] + [
        order["order_id"] for order in selected_customer.get("orders", [])
    ]

    with lookup_col2:
        selected_order = st.selectbox(
            "Focus order",
            order_options,
            format_func=lambda order_id: order_id
            if order_id == "Account overview"
            else next(
                (
                    f"{order['order_id']} - {order['item']} ({order['status']})"
                    for order in selected_customer["orders"]
                    if order["order_id"] == order_id
                ),
                order_id,
            ),
        )

    with lookup_col3:
        issue_type = st.selectbox("Issue type", ISSUE_TYPES)

    if st.session_state.active_customer_id != selected_customer_id:
        st.session_state.active_customer_id = selected_customer_id
        st.session_state.customer_chat_history = []

    profile_col1, profile_col2, profile_col3, profile_col4 = st.columns(4)
    profile_col1.metric("Plan", selected_customer["plan"])
    profile_col2.metric("Status", selected_customer["account_status"])
    profile_col3.metric("Region", selected_customer["region"])
    profile_col4.metric("Renewal", selected_customer["renewal_date"])

    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
**Customer:** {selected_customer['name']}  
**Email:** {selected_customer['email']}  
**Preferred Channel:** {selected_customer['preferred_channel']}  
**Last Ticket:** {selected_customer['last_ticket']}
"""
    )
    st.markdown(
        f"""
        <div class="customer-notes">
            <strong>Notes:</strong><br>
            {selected_customer['notes']}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Orders**")
    for order in selected_customer.get("orders", []):
        st.markdown(
            f"""
            <div class="order-card">
                <strong>{order['order_id']}</strong> - {order['item']}<br>
                Status: {order['status']}<br>
                Placed: {order['placed_on']}<br>
                {order['delivery_date']}<br>
                Amount: {order['amount']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Reply")
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.caption("The first customer reply can take a little longer while the local embedding model loads.")

    query = st.text_input(
        "Customer question",
        placeholder="Example: Where is my order?",
        key="customer_query",
    )
    ask_button = st.button("Generate Reply", use_container_width=True, key="customer_ask")

    st.markdown("</div>", unsafe_allow_html=True)

    if ask_button and not query.strip():
        st.markdown(
            """
        <div class="status-warning">
            Enter a customer question before generating a reply.
        </div>
        """,
            unsafe_allow_html=True,
        )

    if ask_button and query.strip():
        try:
            with st.spinner("Preparing support context and drafting a reply..."):
                support_graph = get_support_graph()
                result = support_graph.invoke(
                    {
                        "question": query,
                        "customer_id": selected_customer_id,
                        "issue_type": issue_type,
                        "order_id": None if selected_order == "Account overview" else selected_order,
                        "source_type": "customer",
                    }
                )
        except Exception as exc:
            st.markdown(
                f"""
            <div class="status-warning">
                Support retrieval could not be initialized: {exc}
            </div>
            """,
                unsafe_allow_html=True,
            )
            return

        st.session_state.customer_chat_history.append(
            {
                "question": query,
                "response": result["response"],
                "issue_type": issue_type,
                "customer_id": selected_customer_id,
                "order_id": selected_order,
            }
        )

    render_history(st.session_state.customer_chat_history, "customer", "customer")


def render_pdf_mode():
    st.markdown("### Document")
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        help="Upload a PDF and ask questions using embedding-based retrieval.",
        key="pdf_uploader",
    )

    if uploaded_file:
        error = load_pdf_graph(uploaded_file)
        if error:
            st.markdown(
                f"""
            <div class="status-warning">
                PDF indexing failed: {error}
            </div>
            """,
                unsafe_allow_html=True,
            )

    pdf_meta = st.session_state.pdf_meta
    if pdf_meta:
        st.markdown(
            f"""
**File:** {pdf_meta['file_name']}  
**Pages:** {pdf_meta['page_count']}  
**Chunks:** {pdf_meta['chunk_count']}
"""
        )

    query = st.text_input(
        "Document question",
        placeholder="Example: Summarize the refund policy in this PDF.",
        key="pdf_query",
    )
    ask_button = st.button("Ask PDF", use_container_width=True, key="pdf_ask")

    st.markdown("</div>", unsafe_allow_html=True)

    if ask_button and not query.strip():
        st.markdown(
            """
        <div class="status-warning">
            Enter a question before querying the PDF.
        </div>
        """,
            unsafe_allow_html=True,
        )

    if ask_button and query.strip() and not st.session_state.pdf_graph:
        st.markdown(
            """
        <div class="status-warning">
            Upload and index a PDF before asking questions.
        </div>
        """,
            unsafe_allow_html=True,
        )

    if ask_button and query.strip() and st.session_state.pdf_graph:
        with st.spinner("Searching the PDF and drafting an answer..."):
            result = st.session_state.pdf_graph.invoke(
                {
                    "question": query,
                    "source_type": "pdf",
                    "file_name": pdf_meta["file_name"],
                }
            )

        st.session_state.pdf_chat_history.append(
            {
                "question": query,
                "response": result["response"],
                "file_name": pdf_meta["file_name"],
            }
        )

    render_history(st.session_state.pdf_chat_history, "pdf", "pdf")


st.set_page_config(
    page_title="Support RAG Workspace",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0f4c81 0%, #1279be 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(15, 76, 129, 0.24);
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        font-size: 1.05rem;
        opacity: 0.92;
        font-weight: 400;
    }

    .panel-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #dde5ee;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    .response-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #d9e4f5 100%);
        border: 1px solid #d6dfeb;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        color: #000000;
    }

    .status-warning {
        background: linear-gradient(135deg, #ef6c00, #fb8c00);
        color: white;
        padding: 0.85rem 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-weight: 500;
    }

    .sidebar-info {
        background: linear-gradient(135deg, #0f4c81 0%, #1279be 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    .customer-notes {
        background: #f7fafc;
        border-left: 4px solid #1279be;
        padding: 1rem;
        border-radius: 8px;
        color: #243b53;
        margin-top: 1rem;
    }

    .order-card {
        background: #f8fbff;
        border: 1px solid #d8e5f4;
        border-radius: 10px;
        padding: 1rem;
        margin-top: 0.75rem;
        color: #102a43;
    }
</style>
""",
    unsafe_allow_html=True,
)

init_session_state()

with st.sidebar:
    st.markdown(
        """
    <div class="sidebar-info">
        <h3 style="margin-top: 0; color: white;">Support RAG Workspace</h3>
        <p style="margin-bottom: 0; opacity: 0.9;">Customer support and PDF retrieval in one place.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
<div class="main-header">
    <h1 class="main-title">Support RAG Workspace</h1>
    <p class="subtitle">Customer-aware support plus PDF question answering with embeddings and graph routing.</p>
</div>
""",
    unsafe_allow_html=True,
)

mode = st.radio(
    "Mode",
    MODES,
    horizontal=True,
)

if mode == "Customer Support":
    with st.sidebar:
        st.markdown("### Customers")
        for customer_id, customer in CUSTOMER_RECORDS.items():
            st.markdown(f"- `{customer_id}`: {customer['name']}")
    render_customer_mode()
else:
    with st.sidebar:
        st.markdown("### PDF")
        st.markdown("Upload one file and ask grounded questions.")
    render_pdf_mode()

st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <small>Embedding-based retrieval, LangGraph routing, and optional human escalation.</small>
</div>
""",
    unsafe_allow_html=True,
)
