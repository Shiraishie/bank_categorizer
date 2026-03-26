import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import bank_cat as bc
import asyncio
import os

st.set_page_config(layout="centered", page_title="Finance Dashboard", page_icon="💳")

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

h1, h2, h3, h4 { font-family: 'Syne', sans-serif; font-weight: 700; letter-spacing: -0.02em; }

/* Upload zone */
section[data-testid="stFileUploadDropzone"] {
    border: 1.5px dashed #30363d;
    border-radius: 14px;
    background: #161b22;
    transition: border-color 0.2s;
}
section[data-testid="stFileUploadDropzone"]:hover {
    border-color: #39d353;
}

/* Metric card */
div[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    color: #39d353;
}
div[data-testid="stMetricLabel"] {
    font-family: 'Syne', sans-serif;
    color: #8b949e;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Bordered columns */
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div[data-testid="stVerticalBlock"] {
    border-radius: 14px;
}

/* Slider */
div[data-testid="stSlider"] > div { accent-color: #39d353; }

/* Multiselect tags */
span[data-baseweb="tag"] {
    background-color: #1f2937 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
}

/* Button */
div[data-testid="stButton"] button {
    background: #39d353;
    color: #0d1117;
    border: none;
    border-radius: 10px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    letter-spacing: 0.03em;
    transition: opacity 0.15s;
}
div[data-testid="stButton"] button:hover { opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark theme defaults ─────────────────────────────────────────────────
CHART_BG   = "#0d1117"
CARD_BG    = "#161b22"
BORDER_CLR = "#30363d"
GREEN      = "#39d353"
RED        = "#f85149"
TEXT_CLR   = "#e6edf3"
MUTED_CLR  = "#8b949e"

PLOTLY_BASE = dict(
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="DM Mono, monospace", color=TEXT_CLR),
    margin=dict(t=20, b=20, l=10, r=10),
)

OUTFLOW_COLORS = ["#f85149","#ff7b72","#ffa198","#ffb3ae","#c9404e","#e0434d","#b52d3a","#d6606d"]
INFLOW_COLORS  = ["#39d353","#26a641","#006d32","#0e4429","#56d364","#3fb950","#2ea043","#1a7f37"]

# ── Session state ──────────────────────────────────────────────────────────────
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'res' not in st.session_state:
    st.session_state.res = pd.DataFrame()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='margin-bottom:0'>💳 Finance Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{MUTED_CLR}; font-family: DM Mono, monospace; margin-top:4px'>Upload your bank statements to get started.</p>", unsafe_allow_html=True)
st.divider()

# ── Upload & process ───────────────────────────────────────────────────────────
files = st.file_uploader(label='Bank Statements (PDF)', accept_multiple_files=True)
col_left, col_right = st.columns([4, 1])
with col_right:
    if st.button("Process PDFs", type="primary", use_container_width=True):
        if files:
            with st.spinner("Crunching numbers..."):
                try:
                    st.session_state.df = bc.process_and_merge_pdfs(files)
                    st.session_state.res = asyncio.run(bc.final_classification_function(st.session_state.df))
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

# ── Dashboard ──────────────────────────────────────────────────────────────────
if not st.session_state.res.empty:
    res = st.session_state.res
    all_tags   = res['Tag'].unique().tolist()
    date_tags  = sorted(res['date'].unique().tolist())

    # Date range slider
    selected_tags_date = st.select_slider(
        "Date Range",
        options=date_tags,
        value=(date_tags[0], date_tags[-1]),
    )

    # Derived values
    curr_bal  = res.iloc[-1]['balance']
    mask      = res['date'].between(selected_tags_date[0], selected_tags_date[1])
    period    = res[mask]
    total_in  = period[period['amount'] > 0]['amount'].sum()
    total_out = period[period['amount'] < 0]['amount'].abs().sum()

    # ── Top metric cards ───────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Current Balance", f"${curr_bal:,.2f}")
    with m2:
        st.metric("Total Inflow", f"${total_in:,.2f}", delta=f"+${total_in:,.2f}")
    with m3:
        st.metric("Total Outflow", f"${total_out:,.2f}", delta=f"-${total_out:,.2f}", delta_color="inverse")

    st.divider()

    # ── Balance flow chart ─────────────────────────────────────────────────────
    daily_flow = period.groupby('date')['balance'].last().reset_index()

    fig_flow = go.Figure()
    fig_flow.add_trace(go.Scatter(
        x=daily_flow['date'],
        y=daily_flow['balance'],
        fill='tozeroy',
        fillcolor='rgba(57,211,83,0.12)',
        line=dict(color=GREEN, width=2),
        hovertemplate="<b>%{x}</b><br>Balance: $%{y:,.2f}<extra></extra>",
    ))
    fig_flow.update_layout(
        **PLOTLY_BASE,
        height=220,
        xaxis=dict(showgrid=False, color=MUTED_CLR, tickfont=dict(family="DM Mono")),
        yaxis=dict(showgrid=True, gridcolor=BORDER_CLR, color=MUTED_CLR, tickfont=dict(family="DM Mono"), tickprefix="$"),
        title=dict(text="Balance Over Time", font=dict(family="Syne", size=14, color=TEXT_CLR), x=0),
    )
    st.plotly_chart(fig_flow, use_container_width=True)

    st.divider()

    # ── Tag filter ─────────────────────────────────────────────────────────────
    selected_tags = st.multiselect(
        "Filter by Category:",
        options=all_tags,
        default=all_tags,
    )

    filtered_res = res[
        (res['Tag'].isin(selected_tags)) &
        (res['date'].between(selected_tags_date[0], selected_tags_date[1]))
    ]
    filtered_res = filtered_res.groupby('Tag', as_index=False).agg(
        amount=('amount', 'sum'),
        transaction_count=('amount', 'count')
    )

    outflow = filtered_res[filtered_res['amount'] < 0].copy()
    outflow['amount'] = outflow['amount'].abs()
    inflow  = filtered_res[filtered_res['amount'] > 0].copy()

    # ── Pie charts ─────────────────────────────────────────────────────────────
    col3, col4 = st.columns(2)

    def make_pie(df, colors, label):
        fig = px.pie(
            df,
            values='amount',
            names='Tag',
            color_discrete_sequence=colors,
            custom_data=['transaction_count'],
            hole=0.62,
        )
        fig.update_traces(
            textposition='inside',
            textinfo='label+percent',
            hovertemplate="<b>%{label}</b><br>Total: $%{value:,.2f}<br>Transactions: %{customdata[0]}<extra></extra>",
            texttemplate='%{label}<br>%{percent}',
            textfont=dict(family="DM Mono", size=11),
        )
        fig.update_layout(
            **PLOTLY_BASE,
            height=360,
            showlegend=False,
            annotations=[dict(
                text=label,
                x=0.5, y=0.5,
                font=dict(family="Syne", size=16, color=TEXT_CLR),
                showarrow=False,
            )],
        )
        return fig

    with col3:
        st.markdown(f"<h4 style='color:{RED}'>↓ Outflow</h4>", unsafe_allow_html=True)
        st.plotly_chart(make_pie(outflow, OUTFLOW_COLORS, "Out"), use_container_width=True)

    with col4:
        st.markdown(f"<h4 style='color:{GREEN}'>↑ Inflow</h4>", unsafe_allow_html=True)
        st.plotly_chart(make_pie(inflow, INFLOW_COLORS, "In"), use_container_width=True)

    st.divider()

    # ── Raw transactions table ─────────────────────────────────────────────────
    with st.expander("📋 Raw Transactions"):
        display = res[res['date'].between(selected_tags_date[0], selected_tags_date[1])].copy()
        st.dataframe(
            display.style
                .applymap(lambda v: f"color: {GREEN}" if isinstance(v, (int,float)) and v > 0 else (f"color: {RED}" if isinstance(v, (int,float)) and v < 0 else ""), subset=['amount'])
                .format({'amount': '${:,.2f}', 'balance': '${:,.2f}'}),
            use_container_width=True,
            hide_index=True,
        )