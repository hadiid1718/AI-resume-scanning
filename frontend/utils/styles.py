PAGE_CSS = """
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stTextInput input {
        background: #334155 !important;
        border-color: #475569 !important;
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background: #6366f1 !important;
        color: white !important;
        border: none !important;
    }
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    }
    .page-header {
        margin-bottom: 1.5rem;
    }
    .page-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .page-header p {
        color: #64748b;
        margin: 0;
    }
    .card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
    }
</style>
"""


def inject_global_styles() -> None:
    import streamlit as st

    st.markdown(PAGE_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="page-header">
            <h1>{title}</h1>
            {"<p>" + subtitle + "</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )
