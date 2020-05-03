import streamlit as st
import pandas as pd
import numpy as np
from fbprophet import Prophet
import plotly.express as px
import altair as alt
import time
import datetime
import pandas_datareader.data as web


def forecast(data,uncertainty=0.95,changepoint_prior_scale=0.05,future=180):
    data['floor'] = 0
    model = Prophet(interval_width=uncertainty,changepoint_prior_scale=changepoint_prior_scale,changepoint_range=0.8,n_changepoints=20)
    data = data[data['ds'].dt.dayofweek < 5] # removes weekends on raw data
    model.fit(data)
    # changepoints = model.changepoints
    # params = model.params
    future_data = model.make_future_dataframe(periods=future)
    future_data = future_data[future_data['ds'].dt.dayofweek < 5]
    forecast = model.predict(future_data)
    # forecast['dayofweek'] = forecast['ds'].dt.dayofweek
    # print(forecast['dayofweek'].value_counts())
    fig2 = model.plot_components(forecast)
    forecast['fact'] = data['y'].reset_index(drop = True)
    return forecast,fig2,model

def detect_anomalies(forecast):
    forecasted = forecast[['ds','trend', 'yhat', 'yhat_lower', 'yhat_upper', 'fact']].copy()
    #forecast['fact'] = df['y']
    forecasted['anomaly'] = 0
    forecasted.loc[forecasted['fact'] > forecasted['yhat_upper'], 'anomaly'] = 1
    forecasted.loc[forecasted['fact'] < forecasted['yhat_lower'], 'anomaly'] = -1

    #anomaly importances
    forecasted['importance'] = 0
    forecasted.loc[forecasted['anomaly'] ==1, 'importance'] = \
        (forecasted['fact'] - forecasted['yhat_upper'])/forecast['fact']
    forecasted.loc[forecasted['anomaly'] ==-1, 'importance'] = \
        (forecasted['yhat_lower'] - forecasted['fact'])/forecast['fact']
    return forecasted

def plot_anoms(forecasted,title='Anomaly Detection',ytitle='Price'):
    interval = alt.Chart(forecasted[~forecasted['fact'].isnull()]).mark_area(interpolate="basis", color = '#ccffd9',opacity=0.8).encode(
    x=alt.X('ds:T',  title ='Date'),
    y='yhat_upper',
    y2='yhat_lower',
    tooltip=['ds', 'fact','yhat','yhat_lower', 'yhat_upper']
    ).interactive().properties(
        title=title
    )
    interval_predictions = alt.Chart(forecasted[forecasted['fact'].isnull()]).mark_area(interpolate="basis", color = '#DFEAF4').encode(
    x=alt.X('ds:T',  title ='Date'),
    y='yhat_upper',
    y2='yhat_lower',
    tooltip=['ds', 'fact','yhat','yhat_lower', 'yhat_upper']
    ).interactive().properties(
        title=title
    )

    yhat = alt.Chart(forecasted[~forecasted['fact'].isnull()]).mark_line(interpolate="basis", color = '#7fc9b5').encode(
    x=alt.X('ds:T',  title ='Date'),
    #y='yhat_upper',
    y='yhat',
    tooltip=['ds', 'fact','yhat', 'yhat_lower', 'yhat_upper']
    ).interactive().properties(
        title=title
    )
    fact = alt.Chart(forecasted).mark_line(color='Black').encode(
        x='ds:T',
        y=alt.Y('fact', title=ytitle),
        tooltip=['ds', 'fact','yhat', 'yhat_lower', 'yhat_upper']
    ).interactive()
    yhat_future = alt.Chart(forecasted[forecasted['fact'].isnull()]).mark_line(interpolate="basis", color = '#6497B1').encode(
        x='ds:T',
        y=alt.Y('yhat', title=ytitle),
        tooltip=['ds', 'fact','yhat', 'yhat_lower', 'yhat_upper']
    ).interactive()

    anomalies = alt.Chart(forecasted[forecasted.anomaly!=0]).mark_circle(size=30, color = 'Red').encode(
        x='ds:T',
        y=alt.Y('fact', title=ytitle),
        tooltip=['ds', 'fact','yhat', 'yhat_lower', 'yhat_upper']
        # ,size = alt.Size( 'importance',legend=None)
    ).interactive()

    return alt.layer(interval,interval_predictions, yhat,fact,yhat_future, anomalies)\
              .properties(width=900, height=400)\
              .configure_title(fontSize=20)\
              .configure_legend(gradientLength=400,gradientThickness=30,orient='left',labelFontSize=14)

def plot_returns(forecasted, title='Day to Day `pct_change`',ytitle='Pct Change (%)'):
        fact_change = alt.Chart(forecasted[forecasted['fact_pct_change'] != 0]).mark_line(color='Black').encode(
            x='ds:T',
            y=alt.Y('fact_pct_change', title=ytitle,axis=alt.Axis(format='%')),
            tooltip=['fact_pct_change']).interactive()
        # yhat_change = alt.Chart(forecasted[forecasted['fact'].isnull()]).mark_line(color='#7fc9b5').encode(
        #     x='ds:T',
        #     y=alt.Y('yhat_pct_change', title=ytitle,axis=alt.Axis(format='%')),
        #     tooltip=['yhat_pct_change']).interactive()
        return alt.layer(fact_change)\
                  .properties(width=900, height=400)\
                  .configure_title(fontSize=20)\
                  .configure_legend(gradientLength=400,gradientThickness=30,orient='left',labelFontSize=14)
def plot_cum_returns(forecasted, title='Cumulative `pct_change`',ytitle='Pct Change (%)'):
        fact_change = alt.Chart(forecasted[~forecasted['fact'].isnull()]).mark_line(color='Black').encode(
            x='ds:T',
            y=alt.Y('fact_cum_change', title=ytitle,axis=alt.Axis(format='%')),
            tooltip=['ds', 'fact','yhat', 'yhat_lower', 'yhat_upper']
        ).interactive()
        return alt.layer(fact_change)\
                  .properties(width=900, height=400)\
                  .configure_title(fontSize=20)\
                  .configure_legend(gradientLength=400,gradientThickness=30,orient='left',labelFontSize=14)


@st.cache(allow_output_mutation=True)
def generating_forecasts(df, stock,interval=0.95,changepoint_prior_scale=0.05,future=180):
    df_forecast,plot_components,model= forecast(df,uncertainty=interval,changepoint_prior_scale=changepoint_prior_scale,future=future)
    df_forecast = detect_anomalies(df_forecast)
    # window = today - pd.to_timedelta(180,unit='d')
    plot = plot_anoms(df_forecast,title=stock,ytitle='Stock Price ($)')
    return df_forecast, plot , plot_components,model

def generating_returns(forecast):
    forecast['fact_pct_change'] = forecast['fact'].pct_change()
    forecast['yhat_pct_change'] = forecast['yhat'].pct_change()
    forecast['fact_cum_change'] = forecast['fact_pct_change'].cumsum()
    returns = plot_returns(forecast)
    cumreturns = plot_cum_returns(forecast)
    return returns, cumreturns
st.write(
        """
        <style type="text/css" media="screen">
        div[role="listbox"] ul {
            height:200px;
        }
        </style>
        """
        ,
        unsafe_allow_html=True,
    )

@st.cache(suppress_st_warning=True)
def stocklist(file):
    stock_index = {}
    with open(file) as f:
        for line in f:
            (val, key) = line.split('\t') #
            stock_index[key.strip()] = val
    list_index = []
    for key, value in stock_index.items() :
        list_index.append(key + ' ({})'.format(value))
    list_index.sort()
    return stock_index,list_index

stock_index,list_index = stocklist("exchange.txt")

today = pd.to_datetime('today').today()
while today.weekday() in [5,6]:
    today = today - pd.to_timedelta(1,unit='d')

st.title('Stock Predictor :dollar:')
option = st.selectbox('Select a Stock you\'d like to track:',list_index,index=list_index.index('Apple Inc (AAPL)'))
company = option.split('(')[0][:-1]
stock = option.split('(')[1][:-1]
st.write('You selected: ', company, ' :moneybag:')

st.sidebar.header('Model Tuning :chart_with_upwards_trend:')
start = st.sidebar.date_input("How far back do you want to look?",datetime.datetime(2016, 1, 1))
future_range = st.sidebar.number_input("How many days into the future do you want to predict?",180)
UI = st.sidebar.slider('Pick your designated uncertainty interval:',min_value=0.0,max_value=1.0,value=0.95)
genre = st.sidebar.radio("Select your Changepoint Prior Scale value",(0.001, 0.05, 0.1,0.2),index=1)
end = datetime.datetime(2020, 4, 30)




df = web.DataReader(stock, 'yahoo', start, today)
df['Date'] = pd.to_datetime(df.index,infer_datetime_format=True)
df = df[['Date', 'Adj Close']]
df.columns = ['ds','y']

forecast, plot, plot_components, model = generating_forecasts(df,stock='{} Stock Price'.format(company),interval=UI,changepoint_prior_scale=genre,future=future_range)

changepoints = model.changepoints
changepoints=pd.DataFrame(changepoints)
changepoints.columns = ['Changepoints']
st.sidebar.subheader('Model Info')
st.sidebar.markdown('Changepoints detected during Fitting:')
st.sidebar.dataframe(changepoints,width=500)
st.altair_chart(plot,use_container_width=True)


todays_forecast = forecast[forecast['ds'] <= today]
future_forecast = forecast[forecast['ds'] > today]
print(todays_forecast['ds'].dt.dayofweek.value_counts())
print(future_forecast['ds'].dt.dayofweek.value_counts())

yesterday = round(todays_forecast['fact'].iloc[-2],2)
yesterday2 = todays_forecast.iloc[-2]

today = round(todays_forecast['yhat'].iloc[-1],2)
today2 = todays_forecast.iloc[-1]

one_week = round(future_forecast['yhat'].iloc[4],2)
one_week2 = future_forecast.iloc[4]

one_month = round(future_forecast['yhat'].iloc[20],2)
one_month2 = future_forecast.iloc[20]

today_change = str(round((today-yesterday) * 100/yesterday,3)) + '%'
week_change = str(round((one_week-yesterday) * 100/yesterday,3)) + '%'
month_change = str(round((one_month-yesterday) * 100/yesterday,3)) + '%'

st.subheader('Predictions')
st.write('These are the predictions for the market close `{}`, `{}` and `{}` from now.'.format('today','one_week','one_month'))
st.table(pd.DataFrame({
    'Date': [yesterday2['ds'], today2['ds'],one_week2['ds'],one_month2['ds']],
    'Prediction Reference': ['yesterday', 'today','one_week','one_month'],
    'Share Price': [yesterday,today,one_week,one_month],
    'Change in Pct': [0,today_change,week_change, month_change]
}))
st.write('The Time Series we observed for `' + company + '` can be broken down into three areas; Trend, Weekly Seasonality and Yearly Seasonality.')
st.pyplot(plot_components,use_container_width=True)

st.write('Looking at daily `pct_change` could also prove valuable: ')
returns,cumulative = generating_returns(forecast)
st.altair_chart(returns,use_container_width=True)
# st.write('We can slightly adjust this to look at the Cumulative sum of these returns to see the Stock performance over time: ')
# st.altair_chart(cumulative,use_container_width=True)

st.subheader('About')
st.markdown('The data is gathered via the Yahoo API that is being accessed through the `pandas_datareader` package. The Stock symbol information has been transformed from data gathered [here](http://www.eoddata.com/default.aspx). The actual data processing and Forecasting was done through Prophet, a framework developed by Facebook (can be found [here](https://facebook.github.io/prophet/)). The plotting was done using `Altair`.')


# To do list:
# Pct change plot option
# Add NYSE, check FTSE stocks
#
#
#
#
#
#
#
#
#
