import streamlit as st
import pandas as pd
import numpy as np


import datetime
from dateutil.relativedelta import relativedelta


import plotly.express as px

#Set title, icon, and layout
st.set_page_config(
     page_title="FinHabits",
     page_icon="guitar",
     layout="wide")


#function to load data
@st.cache_data()
def load_data():
    #read the data
    path_to_csv = "data/merge_data.csv"
    df = pd.read_csv(path_to_csv)
    df[ 'EventDateTime_soft' ] = pd.to_datetime(df[ 'EventDateTime_soft'], format="%Y-%m-%dT%H:%M:%S%z")
    df[ 'EventDateTime_soft' ] = df["EventDateTime_soft"].dt.date
    df[ 'EventDateTime_soft' ] = pd.to_datetime(df[ 'EventDateTime_soft'], format="%Y-%m-%d")

    df['UserId'] = df['UserId'].astype(str)

    return df

def create_conversionRate(df, event):

    result = df.groupby([df['EventDateTime_soft'].dt.to_period("M") ]).agg(
        total_rows=pd.NamedAgg(column='EventDateTime_soft', aggfunc='size'),
        count_values_positives=pd.NamedAgg(column='FundingIn2weeks_' + event, aggfunc=lambda x: sum(x == 1))
    ).reset_index()

    result["ConversionRate"] = ( result["count_values_positives"] / result["total_rows"] ) * 100

    result['ConversionRate'] = result['ConversionRate'].round(2)  

    result["ConversionRate"] = result["ConversionRate"].astype(str) 

    result["ConversionRate"]  = result["ConversionRate"]  + "%"

    result['EventDateTime_soft'] = result['EventDateTime_soft'].dt.to_timestamp().dt.strftime('%Y-%m')

    result["EventType"] =  [df["EventType_"  + event].dropna().unique()[0]] * len(result.index)

    #result 
    
    return result

@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')


df = load_data()
df_filter = df.copy()

#default vaues for date
today = datetime.datetime.now()
min_date = min(df["EventDateTime_soft"])

#default values for age
min_age = df["User.M.Age.N"].dropna().min()
max_age = df["User.M.Age.N"].dropna().max()

#default values for income
min_income = df["User.M.Income.N"].dropna().min()
max_income = df["User.M.Income.N"].dropna().max()

#list of platform
platform_list = ["iOS", "Android"]


#limpiar el form 
def clear_form():
    st.session_state["age"] = (min_age, max_age)
    st.session_state["income"] = (min_income, max_income)
    st.session_state["platform"] = "iOS"

with st.sidebar:
    filters_text = []


    filter_age = st.checkbox("Filter by age")

    if filter_age:
        #filter by select range age 
        age = st.slider( 'Select a range of values for age', min_age,max_age ,  (min_age,max_age),  key = "age" ) 

        df_filter = df_filter[df_filter['User.M.Age.N'].between( age[0], age[1])]

        filters_text.append("Age: " + str(age[0]) + " to "+ str(age[1])  )

        
    #filter by select income age 
    filter_income = st.checkbox("Filter by income")

    if filter_income:
        income = st.slider( 'Select a range of values for income',   min_income, max_income,  (min_income, max_income), key = "income") 
        
        df_filter = df_filter[df_filter['User.M.Income.N'].between( income[0], income[1])]

        filters_text.append("Income: " + str(income[0]) + " to "+ str(income[1])  )

    #filter by select platform 
    filter_platform = st.checkbox("Filter by platform")

    if filter_platform:
        platform = st.selectbox( "Platform", platform_list, key = "platform")
        df_filter = df_filter[df_filter['Platform'] == platform]

        filters_text.append("Platform: " + platform  )

    #reset inputs
    clear = st.button(label="Clear", on_click=clear_form)

tab1, tab2 = st.tabs(["Conversion Rate", "Funnel"])


with tab1:
        
    all_events = ["hot", "mobile", "emma", "identity", "address", "disclosures", "agreements", "financial", "portafolioS", "portafolioC", "identityV", "accountIF"]

    select_events = st.multiselect(
        'Events to compare',
        all_events,
        ['hot', 'mobile'], max_selections=3)


    if len(select_events) == 0:
        st.write('You need to select something!')
    else:
        concat_df = pd.DataFrame(columns=['EventDateTime_soft', 'EventType', 'total_rows', 'count_values_positives' , 'ConversionRate'])

        for value in select_events:
            #st.write('You selected:', value)
            concat_df = pd.concat([concat_df, create_conversionRate(df_filter, value)], ignore_index=True)


        st.write("Active Filters")
        if len(filters_text) != 0:
            for f in filters_text:
                st.write(f)
        else:
            st.write("No filter active")
        fig = px.line(concat_df,
                        x='EventDateTime_soft', y='ConversionRate', color='EventType', markers=True,
                        text='ConversionRate')

        fig.update_traces(textposition='bottom center')
        #plot in streamlit
        st.plotly_chart(
            fig, 
            theme="streamlit", use_container_width=True, height=800
        )

        st.write("Graph data")
        concat_df
        concat_df_download = convert_df(concat_df)

        st.download_button(
            label="Download data as CSV",
            data=concat_df_download,
            file_name='large_df.csv',
            mime='text/csv',
        )
        st.write("Data")
        df_filter
        df_filter_download = convert_df(df_filter)

        st.download_button(
            label="Download data as CSV",
            data=df_filter_download,
            file_name='large_df.csv',
            mime='text/csv',
            key="filter_data_download"
        )
with tab2:
    #filter by selected date  
    min_date = min(df_filter["EventDateTime_soft"])

    date_filter = st.date_input(
        "Select the range of dates",
        (min_date, datetime.date(min_date.year, min_date.month, 1)  + relativedelta(months=1) - datetime .timedelta(days=1)),
        format="YYYY-MM-DD",
    )

    if len(date_filter) == 2:
        df_filter = df_filter[(df_filter['EventDateTime_soft'] >= datetime.datetime.combine(date_filter[0],  datetime.time.min)  ) & (df_filter['EventDateTime_soft'] <=  datetime.datetime.combine(date_filter[1],   datetime.time.min )   )]


        suffixes_2023 = [
        'soft', 'hot', 'mobile', 'emma', 'identity', 'address', 'disclosures', 'agreements',
        'financial', 'portafolioS', 'portafolioC', 'identityV','accountIF']

        concat_df = pd.DataFrame(columns=['EventDateTime_soft', 'EventType', 'total_rows', 'count_values_positives' , 'ConversionRate'])

        for value in suffixes_2023:
            #st.write('You selected:', value)
            concat_df = pd.concat([concat_df, create_conversionRate(df_filter, value)], ignore_index=True)
        
        fig_funnel = px.funnel(concat_df, x='count_values_positives', y='EventType', title='Conversion Funnel',
                    labels={'count_values_positives': 'Count of Positive Values', 'EventType': 'Event Type'},
                    text = "ConversionRate", 
                    orientation='h')


        # Define the custom colors
        finhabits_colors = ['#feef4b', '#444b4d', '#caa72f', '#38c0b8', '#fa1d7c']

        fig_funnel.update_traces(textposition='inside', texttemplate="%{x:.0f\n}<br>%{text}", 
                        marker=dict(color=finhabits_colors))
        
        st.write("Active Filters")
        if len(filters_text) != 0:
            for f in filters_text:
                st.write(f)
        else:
            st.write("No filter active")
        fig_funnel.update_layout(height=1000)
        st.plotly_chart(
            fig_funnel, 
            theme="streamlit", use_container_width=True 
        )
        st.write("Graph data", key = "text_funnel2")
        concat_df
        concat_df_download = convert_df(concat_df)

        st.download_button(
            label="Download data as CSV",
            data=concat_df_download,
            file_name='large_df.csv',
            mime='text/csv',
            key="graph_data_funnel"
        )
        
        st.write("Data", key = "text_funnel1")
        df_filter

        df_filter_download = convert_df(df_filter)

        st.download_button(
            label="Download data as CSV",
            data=df_filter_download,
            file_name='large_df.csv',
            mime='text/csv',
            key="filter_data_download_funnel"
        )

