import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import bank_cat as bc
import asyncio
import os


if not os.path.exists('final.csv'):
    bc.process_and_merge()

if os.path.exists('final.csv'):
    df = pd.read_csv('final.csv')
    res = asyncio.run(bc.final_classification_function(df))
    res = pd.read_csv('check.csv')
    st.sidebar.header("Filters")
    all_tags = res['Tag'].unique().tolist()
    date_tags = sorted(res['date'].unique().tolist())
    print(date_tags[0])
    selected_tags = st.sidebar.multiselect(
        "Select Tags to Display:",
        options=all_tags,
        default=all_tags  # Default to showing everything
    )

    selected_tags_date = st.sidebar.select_slider("Date Range",
                                                  options=date_tags,
                                                  value=(date_tags[0], date_tags[-1])
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
    outflow = filtered_res[filtered_res['amount'] < 0]
    outflow['amount'] = outflow['amount'].abs()
    inflow = filtered_res[filtered_res['amount'] > 0]
    
    daily_flow = res[res['date'].between(selected_tags_date[0], selected_tags_date[1])].groupby('date')['balance'].last().reset_index()

    st.write("Balance")
    st.area_chart(daily_flow, x='date', y='balance')
    
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
        hovertemplate="<b>%{label}</b><br>Total: $ %{value}<br>Transactions: %{customdata[0]}<extra></extra>"
    )
    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
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
        hovertemplate="<b>%{label}</b><br>Total: $ %{value}<br>Transactions: %{customdata[0]}<extra></extra>"
    )
    # Displ
    # Display the Plotly chart in Streamlit
    st.plotly_chart(fig2, use_container_width=True)

