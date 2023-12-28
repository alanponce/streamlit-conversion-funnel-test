import streamlit as st
import pandas as pd
import numpy as np


import datetime
from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots


import plotly.express as px
import plotly.graph_objects as go

#Set title, icon, and layout
st.set_page_config(
     page_title="FinHabits",
     page_icon="guitar",
     layout="wide")

# CSS
with open("static/styles.css", "r") as f:
    css = f.read()

# Apply the styles using st.markdown
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


#function to load data
@st.cache_data()
def load_data():
    #read the data
    path_to_csv = "data/merge_data_v2.csv"
    df = pd.read_csv(path_to_csv)
    # df[ 'EventDateTime_soft' ] = pd.to_datetime(df[ 'EventDateTime_soft'], format="%Y-%m-%dT%H:%M:%S%z")
    # df[ 'EventDateTime_soft' ] = df["EventDateTime_soft"].dt.date
    # df[ 'EventDateTime_soft' ] = pd.to_datetime(df[ 'EventDateTime_soft'], format="%Y-%m-%d")

    df['EventDateTime_soft'] = pd.to_datetime(df['EventDateTime_soft'], format='ISO8601')
    df[ 'EventDateTime_soft' ] = df["EventDateTime_soft"].dt.date
    df[ 'EventDateTime_soft' ] = pd.to_datetime(df[ 'EventDateTime_soft'], format="%Y-%m-%d")

    df['UserId'] = df['UserId'].astype(str)

    # Create age bins
    #18/25
    #26/35
    #36/45
    #46/55
    #56/66
    #67+
    bins = [18, 26, 36, 46, 56, 67, 100]
    labels = [ '18-25', '26-35', '36-45', '46-55', '56-66', '67+']
    df['AgeBin'] = pd.cut(df['age'], bins=bins, labels=labels, right=False)

    df['income'] = pd.to_numeric(df['income'], errors='coerce').astype('Int64')


    return df

def create_conversionRate(df, event, type_period):
    if type_period == "W":
        type_period= type_period + "-" + (df['EventDateTime_soft'].min() - pd.Timedelta(days=1)) .strftime('%A')[:3]

    result = df.groupby([df['EventDateTime_soft'].dt.to_period(type_period) ]).agg(
        total_rows=pd.NamedAgg(column='EventDateTime_soft', aggfunc='size'),
        count_values_positives=pd.NamedAgg(column='FundingIn2weeks_' + event, aggfunc=lambda x: sum(x == 1))
    ).reset_index()

    result["ConversionRate"] = ( result["count_values_positives"] / result["total_rows"] ) * 100

    result['ConversionRate'] = result['ConversionRate'].round(2)

    if  type_period == "M":
        result['EventDateTime_soft'] = result['EventDateTime_soft'].dt.to_timestamp().dt.strftime('%Y-%m')
    else:
        result['EventDateTime_soft'] = pd.to_datetime(result['EventDateTime_soft'].dt.to_timestamp())

    result["EventType"] =  [df["EventType_"  + event].dropna().unique()[0]] * len(result.index)

    return result

def extra_data(df, type_period, variable_to_represent):
    if type_period == "W":
        type_period= type_period + "-" + (df['EventDateTime_soft'].min() - pd.Timedelta(days=1)) .strftime('%A')[:3]

    pan = df.groupby([df['EventDateTime_soft'].dt.to_period(type_period),variable_to_represent ]).agg(
        count=(variable_to_represent, 'size')
    ).reset_index()
    if  type_period == "M":
        pan['EventDateTime_soft'] = pan['EventDateTime_soft'].dt.to_timestamp().dt.strftime('%Y-%m')
    else:
        pan['EventDateTime_soft'] = pd.to_datetime(pan['EventDateTime_soft'].dt.to_timestamp())

    return pan


@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')


df = load_data()
df_filter = df.copy()

#default vaues for date
today = datetime.datetime.now()
min_date = min(df["EventDateTime_soft"])
max_date = max(df["EventDateTime_soft"])


#default values for age
min_age = df["age"].dropna().min()
max_age = df["age"].dropna().max()

#default values for income
min_income = df["income"].dropna().min()
max_income = df["income"].dropna().max()

#list of platform
platform_list = ["iOS", "Android"]

#list of age bins
age_list = [ '18-25', '26-35', '36-45', '46-55', '56-66', '67+']

#list of income
income_list = df["income"].dropna().unique()


finhabits_colors_lines = ['#FF1780', '#1BE7FF', '#35C3BF', '#805700', '#FF80B9']
#colors
finhabits_colors = ['#FFF04B', '#FFAD00','#805700', '#358400', '#9BE564', '#35C3BF', '#1BE7FF',
                        '#D99AC5','#9680AF', '#1D003F','#AA004D', '#FF1780', '#FF80B9']


#limpiar el form
def clear_form():
    st.session_state["filter_age"] = False
    st.session_state["filter_income"] = False
    st.session_state["filter_platform"] = False

with st.sidebar:
    filters_text = []

    filter_age = st.checkbox("Filter by age", key="filter_age")

    if filter_age:
        #filter by select age bin
        age = st.selectbox( "AgeBin", age_list, key = "age")
        df_filter = df_filter[df_filter["AgeBin"] == age]
        filters_text.append("AgeBin: " + age  )

    #filter by select income age
    filter_income = st.checkbox("Filter by income", key="filter_income")

    if filter_income:
        income = st.selectbox( "Income", income_list, key = "income")
        df_filter = df_filter[df_filter["income"] == income]
        filters_text.append("Income: " + str(income)  )

    #filter by select platform
    filter_platform = st.checkbox("Filter by platform", key="filter_platform")

    if filter_platform:
        platform = st.selectbox( "devicePlatform", platform_list, key = "devicePlatform")
        df_filter = df_filter[df_filter["devicePlatform"] == platform]

        filters_text.append("Platform: " + platform  )


    #filter by selected date
    min_date = min(df_filter["EventDateTime_soft"])

    date_filter = st.date_input(
        "Select the range of dates",
        (min_date, max_date )
        #,
        #format="YYYY-MM-DD",
    )

    if len(date_filter) == 2:
            df_filter = df_filter[(df_filter['EventDateTime_soft'] >= datetime.datetime.combine(date_filter[0],  datetime.time.min)  ) & (df_filter['EventDateTime_soft'] <=  datetime.datetime.combine(date_filter[1],   datetime.time.min )   )]

    #reset inputs
    clear = st.button(label="Clear", on_click=clear_form)


st.image("static/LOGO_FINHABITS_v2.png")
tab1, tab2 = st.tabs(["Conversion Rate", "Funnel"])


with tab1:

    all_events = ["hot", "mobile", "emma", "identity", "address", "disclosures", "agreements",
                  "financial", "portafolioS", "portafolioC", "identityV",
                  'accountC', 'accountR', 'bankC', 'bankA',
                  "accountIF"]

    select_events = st.multiselect(
        'Events to compare',
        all_events,
        ['hot', 'mobile'], max_selections=5,
        key = "selectEvent")

    # select_events = st.multiselect(
    #     'Events to compare',
    #     all_events,
    #     ['hot', 'mobile'], max_selections=5)

    if len(select_events) == 0:
        st.write('You need to select something!')
    else:
        concat_df = pd.DataFrame(columns=['EventDateTime_soft', 'EventType', 'total_rows', 'count_values_positives' , 'ConversionRate'])

        period = st.selectbox(
            'Choose the period',
            ("Month", "Week", "Day"))

        represent_variable = st.selectbox(
            'Choose an variable',
            ("None","devicePlatform", "maritalStatus", "language", "income", "AgeBin"))


        for value in select_events:
            #st.write('You selected:', value)
            concat_df = pd.concat([concat_df, create_conversionRate(df_filter, value, period[0] )], ignore_index=True)


        st.write("Active Filters")
        if len(filters_text) != 0:
            for f in filters_text:
                st.write(f)
        else:
            st.write("No filter active")

        # Create subplots with one trace for the bar chart and another trace for the line plot
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        if represent_variable != "None":
            data_bar = extra_data(df_filter, period[0], represent_variable)

            variables_to_show = data_bar[represent_variable].unique()
            # Bar chart for the second DataFrame
            for (varible_actual, color) in zip(variables_to_show, finhabits_colors):
                bar = data_bar[data_bar[represent_variable] == varible_actual]
                fig.add_trace(go.Bar(x=bar['EventDateTime_soft'],
                                      y=bar['count'],
                                      marker=dict(color=color),
                                      name=str(varible_actual) ), secondary_y=False)



        # Line plot for the first DataFrame
        for (conver, color) in zip(concat_df['EventType'].unique(), finhabits_colors_lines):
            conver_data = concat_df[concat_df['EventType'] == conver]
            fig.add_trace(go.Scatter(x=conver_data['EventDateTime_soft'],
                                      y=conver_data['ConversionRate'],
                                      marker=dict(color=color),
                                      mode='lines+markers',
                                      name=conver), secondary_y=True)

        # Update layout to show the secondary y-axis
        fig.update_layout(
            yaxis2=dict(
                title='Conversion Rate',
                overlaying='y',
                side='right',
                ticksuffix='%'
            )
        )


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
            key="data12"
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
        suffixes_2023 = [
        'soft', 'hot', 'mobile', 'emma', 'identity', 'address', 'disclosures', 'agreements',
        'financial', 'portafolioS', 'portafolioC', 'identityV',
        'accountC', 'accountR', 'bankC', 'bankA',
                  "accountIF"]

        concat_df = pd.DataFrame(columns=['EventDateTime_soft', 'EventType', 'total_rows', 'count_values_positives' , 'ConversionRate'])

        for value in suffixes_2023:
            concat_df = pd.concat([concat_df, create_conversionRate(df_filter, value,"M")], ignore_index=True)

        fig_funnel = px.funnel(concat_df, x='count_values_positives', y='EventType', title='Conversion Funnel',
                    labels={'count_values_positives': 'Count of Positive Values', 'EventType': 'Event Type'},
                    text = "ConversionRate",
                    orientation='h')



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

        st.write("Graph data")
        concat_df
        concat_df_download = convert_df(concat_df)

        st.download_button(
            label="Download data as CSV",
            data=concat_df_download,
            file_name='large_df.csv',
            mime='text/csv',
            key="graph_data_funnel"
        )

        st.write("Data")
        df_filter

        df_filter_download = convert_df(df_filter)

        st.download_button(
            label="Download data as CSV",
            data=df_filter_download,
            file_name='large_df.csv',
            mime='text/csv',

        )