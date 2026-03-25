import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import bank_cat as bc
import asyncio
import os


if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'res' not in st.session_state:
    st.session_state.res = pd.DataFrame()

st.write("Upload Bank Transactions \n")
files = st.file_uploader(label='Transactions', accept_multiple_files=True)
col_left, col_right = st.columns([4, 1])
with col_right:
    if st.button("Process PDFs", type="primary", use_container_width=True):
        if files:
            try:
                st.session_state.df = bc.process_and_merge_pdfs(files)
                st.session_state.res = asyncio.run(bc.final_classification_function(st.session_state.df))
            except Exception as e:
                print(e)

if not st.session_state.res.empty: #If my df is there
    # Tags
    res = st.session_state.res
    all_tags = res['Tag'].unique().tolist()
    date_tags = sorted(res['date'].unique().tolist())

    selected_tags_date = st.select_slider("Date Range",
                                                  options=date_tags,
                                                  value=(date_tags[0], date_tags[-1]),
                                        )
    # Current Balance
    curr_bal = res.iloc[-1]['balance']

    col1,col2 = st.columns([1,3], border = True)

    with col1:
        st.markdown(f"<h3 style='color: white; '>Balance</h3>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color: white; '>$ {curr_bal}</h2>", unsafe_allow_html=True)
    #Daily Flow
    daily_flow = res[res['date'].between(selected_tags_date[0], selected_tags_date[1])].groupby('date')['balance'].last().reset_index()
    with col2: 
        st.write("Flow")
        st.area_chart(daily_flow, x='date', y='balance', width='stretch')
    
    
    
    # Filtered Res for Inflow and Outflow
    selected_tags = st.multiselect(
        "Select Tags to Display:",
        options=all_tags,
        default=all_tags  # Default to showing everything
    )
    filtered_res = res[
        (res['Tag'].isin(selected_tags)) & 
        (res['date'].between(selected_tags_date[0], selected_tags_date[1]))
    ]
    #filtered_res = filtered_res.groupby('Tag', as_index=False)['amount'].sum()
    filtered_res = filtered_res.groupby('Tag', as_index=False).agg(
        amount=('amount', 'sum'),
        transaction_count=('amount', 'count')
    )


    ## Inflow and Outflows
    outflow = filtered_res[filtered_res['amount'] < 0]
    outflow['amount'] = outflow['amount'].abs()
    inflow = filtered_res[filtered_res['amount'] > 0]

    col3, col4 = st.columns(2, border = True)
    with col3:
        st.write("Outflow")
        # Create the pie chart using Plotly Express
        fig = px.pie(
            outflow, 
            values='amount', 
            names='Tag', 
            color_discrete_sequence=px.colors.sequential.RdBu,
            custom_data=['transaction_count'],
            hole=0.6,
        )
        fig.update_traces(
            textposition='inside',
            textinfo='label+value',
            hovertemplate="<b>%{label}</b><br>Total: $ %{value}<br>Transactions: %{customdata[0]}<extra></extra>",
            texttemplate='%{label}<br>$ %{value:.2f}'
        )
        fig.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.3,
            xanchor='center',
            x=0.5,
        ),
        showlegend=True,
        )
        # Display the Plotly chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.write("Inflow")
        fig2 = px.pie(
            inflow, 
            values='amount', 
            names='Tag', 
            color_discrete_sequence=px.colors.sequential.Aggrnyl,
            custom_data=['transaction_count'],
            hole=0.6,
        )
        fig2.update_traces(
            textposition='inside',
            textinfo='label+value',
            hovertemplate="<b>%{label}</b><br>Total: $ %{value}<br>Transactions: %{customdata[0]}<extra></extra>",
            texttemplate='%{label}<br>$ %{value:.2f}'
        )
        fig2.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.3,
            xanchor='center',
            x=0.5,
        ),
        showlegend=True,
        )
        # Displ
        # Display the Plotly chart in Streamlit
        st.plotly_chart(fig2, use_container_width=True)

