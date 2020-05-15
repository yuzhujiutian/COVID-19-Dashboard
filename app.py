# Import libraries
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

#import plotly.graph_objects as go
import plotly.express as px
#from IPython.core.display import display, HTML

import pandas as pd
import numpy as np
from datetime import date, timedelta

### Data Pre-processing ###
# todo create a separate etl file to do the pre-processing and call it

url_1 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/time-series-19-covid-combined.csv'
url_2 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv'
url_3 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/key-countries-pivoted.csv'
url_4 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/worldwide-aggregated.csv'
time_series = pd.read_csv(url_1, index_col=0,parse_dates=[0]).reset_index()
countries = pd.read_csv(url_2, index_col=0,parse_dates=[0]).reset_index()
countries_pv = pd.read_csv(url_3, index_col=0,parse_dates=[0]).reset_index()
ww_agg = pd.read_csv(url_4, index_col=0,parse_dates=[0]).reset_index()

# convert Date object to Datetime
countries['Date'] = pd.to_datetime(countries['Date'])
countries_pv['Date'] = pd.to_datetime(countries_pv['Date'])
time_series['Date'] = pd.to_datetime(time_series['Date'])
ww_agg['Date'] = pd.to_datetime(ww_agg['Date'])

# A df of all countries, incl co-ordinates for map
# A cleaner country df, without province/state but includes lat and long for mapping purposes
countries_df = time_series.copy()
countries_df.rename(columns={"Country/Region": "Country"}, inplace=True)
countries_df.fillna(0, inplace=True)
countries_df.drop(['Province/State'], axis=1, inplace=True)
countries_df['Active'] = countries_df['Confirmed'] - countries_df['Recovered']


countries_df = countries_df.groupby(['Date', 'Country'], as_index=False).agg({'Lat': 'mean',
                                                                       'Long': 'mean',
                                                                       'Confirmed': 'sum',
                                                                       'Deaths': 'sum',
                                                                       'Recovered': 'sum',
                                                                       'Active':'sum'
                                                                     })

# update country centroid which are spread due to provinces/colonies
countries_df.loc[countries_df['Country'] == 'US', 'Lat'] = 39.810489
countries_df.loc[countries_df['Country'] == 'US', 'Long'] = -98.555759

countries_df.loc[countries_df['Country'] == 'France', 'Lat'] = 46.2276
countries_df.loc[countries_df['Country'] == 'France', 'Long'] = 2.2137

countries_df.loc[countries_df['Country'] == 'United Kingdom', 'Lat'] = 55.3781
countries_df.loc[countries_df['Country'] == 'United Kingdom', 'Long'] = -3.4360

countries_df.loc[countries_df['Country'] == 'Denmark', 'Lat'] = 56.2639
countries_df.loc[countries_df['Country'] == 'Denmark', 'Long'] = 9.5018

countries_df.loc[countries_df['Country'] == 'Netherlands', 'Lat'] = 52.1326
countries_df.loc[countries_df['Country'] == 'Netherlands', 'Long'] = 5.2913

countries_df.loc[countries_df['Country'] == 'Canada', 'Lat'] = 59.050000
countries_df.loc[countries_df['Country'] == 'Canada', 'Long'] = -112.833333

countries_df['Active'] = countries_df['Confirmed'] - countries_df['Recovered']

# Description for map
countries_df['Description'] = countries_df['Country'] + '<br>' \
+ 'Confirmed: ' + countries_df['Confirmed'].astype(int).map('{:,.0f}'.format) + '<br>' \
+ 'Deaths: ' + countries_df['Deaths'].astype(int).map('{:,.0f}'.format) + '<br>' \
+ 'Recovered: ' + countries_df['Recovered'].astype(int).map('{:,.0f}'.format) + '<br>' \
+ 'Active: ' + countries_df['Active'].astype(int).map('{:,.0f}'.format)
#countries_df = countries_df.assign(logCumConf = np.where(countries_df['Confirmed'] > 0, np.log(countries_df['Confirmed']) / np.log(2), 0))

# Total daily counts
national_daily_count = countries_df.groupby(['Date','Country'])['Confirmed','Deaths','Recovered','Active'].sum().reset_index()
global_daily_count = countries_df.groupby(['Date'])['Confirmed','Deaths','Recovered','Active'].sum().reset_index()
global_melt = global_daily_count.melt(id_vars=['Date'],
                                      value_vars=['Recovered','Deaths','Active','Confirmed'],
                                      var_name='Type',value_name='Count'
                                      )

### PLOTS ###
# todo re-create plots for app callback function

fig_area = px.area(global_melt
              ,x="Date"
              ,y="Count"
              ,color='Type'
              #,height=600
              #,width=900
              ,title='Worldwide Cases by Type'
              ,template='plotly_dark'
             )
fig_area.update_layout(xaxis_rangeslider_visible=True)

# Time Series
fig_timeseries = px.line(x=countries_df['Date'].dt.strftime('%Y-%m-%d'),
        y=countries_df["Confirmed"],
        color=countries_df["Country"],
        hover_name=countries_df["Country"],
        line_shape="spline",
        render_mode="svg",
        template='plotly_dark'
)
fig_timeseries.update_layout(title = "Timeline of Confirmed Cases",
    xaxis_title = "Date",
    yaxis_title = "Confirmed Cases",
    legend_title = "Country")

# World Map
fig_map = px.choropleth(countries_df
                    ,locations="Country"
                    ,locationmode='country names'
                    ,color=np.log(countries_df["Confirmed"])#np.log(covid_ts["Confirmed"]) #logarithmic scale
                    ,hover_name='Description'
                    ,animation_frame=countries_df["Date"].dt.strftime('%Y-%m-%d')
                    ,title='Global Heatmap of Confirmed Cases'
                    ,color_continuous_scale=px.colors.sequential.Reds #Magenta
                    ,template='plotly_dark'
                    ,height=600
                    ,width=1700
                   )
#fig_map.update_geos(fitbounds = "locations")
fig_map.update(layout_coloraxis_showscale=True)

# Bubble Map
formatted_gdf = countries_df.groupby(['Date','Country','Description','Lat','Long'])['Confirmed'].max().reset_index()
formatted_gdf['Date'] = formatted_gdf['Date'].dt.strftime('%m/%d/%Y')
formatted_gdf['size'] = formatted_gdf['Confirmed'].pow(0.2)
fig_bubble = px.scatter_geo(formatted_gdf,
                     locations = "Country",
                     locationmode = "country names",
                     color = "Confirmed",
                     hover_name = "Description",
                     size = "size",
                     animation_frame = "Date",
                     projection = "natural earth",
                     range_color= [0, 2500],
                     color_continuous_scale="portland",
                     template = "plotly_dark",
                     title = "Covid-19 Confirmed Cases over Time",
                     height=800
                            )
fig_bubble.update_layout(margin=dict(t=100,pad=4),autosize=True)

# Mapbox
fig_mapbox = px.scatter_mapbox(
    mapbox_style='carto-darkmatter',
    title='Global Outbreak Map - Hover for Detailed Information',
    lat=formatted_gdf['Lat'],
    lon=formatted_gdf['Long'],
    hover_name=formatted_gdf['Description'],
    size=formatted_gdf['Confirmed'].pow(0.3),
    range_color=[0, 4000],
    opacity=0.6,
    size_max=40,
    zoom=1.2,
    animation_frame=countries_df['Date'].astype(str),
    # center=go.layout.mapbox.Center(lat=14,lon=21),
    template='plotly_dark',
    color=formatted_gdf['Confirmed'],
    color_continuous_scale='portland',
    #color_discrete_sequence=px.colors.qualitative.Light24,
    #height=800
    )
fig_mapbox.update_layout(autosize=True,coloraxis_showscale=False)

default_layout = {
    'autosize': True,
    'xaxis': {'title': None},
    'yaxis': {'title': None},
    'margin': {'l': 40, 'r': 20, 't': 40, 'b': 10},
    'paper_bgcolor': '#303030',
    'plot_bgcolor': '#303030',
    'hovermode': 'x',
}

# optional color scheme
dash_colors = {
    'background': '#111111',
    'text': '#BEBEBE',
    'grid': '#333333',
    'red': '#BF0000',
    'red_bright': '#d7191c',
    'blue': '#466fc2',
    'green': '#5bc246',
    'orange':'5A9E6F'
}

def ticker_color(tick_value):
    if tick_value > 0:
        return dash_colors['red']
    else:
        return dash_colors['green']
# todo update function to include colors for all metric types

# Latest count per country
global_total = global_daily_count[global_daily_count['Date'] == global_daily_count['Date'].max()]
delta = global_daily_count[global_daily_count['Date'] == global_daily_count['Date'].max() - timedelta(days=1)]
update_date = time_series['Date'].max().strftime('%Y-%m-%d')
# todo add daily percent change for number plates

'''BEGIN DASH APP'''
# todo add a page for twitter/social media mentions

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
server = app.server
# https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/


app.layout = html.Div(children=[
    html.H1(children='Covid-19 Interactive Tracker',
            style={'textAlign':'center'}),

    html.Div(children='Data last updated: ' + time_series['Date'].max().strftime('%Y-%m-%d') +
                      ' (Maintained by John Hopkins University)',
             style={'textAlign':'center'}),

    html.Div(dcc.RadioItems(id='view-picker',
                            options=[{'label':i,'value':i} for i in ['Global','Top','Canada']],
                            value='Global',
                            labelStyle={'float':'center','display':'inline-block','padding':'5px'}),
             style={'textAlign':'center','width':'100%','float':'center','display':'inline-block'}
             ),

    html.Div(id='number-plate',
             style={'marginLeft':'1.5%','marginRight':'1.5%','marginBottom':'.5%','marginTop':'.5%'},
             children=[
                 html.Div(id='conf-ind',
                          style={'width':'24.4%','marginRight':'.8%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign':'center',
                                                  'color':dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Confirmed Cases'),
                                    html.H3(style={'textAlign':'center',
                                                   'fontWeight':'bold','color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Confirmed']))),
                                    html.P(style={'textAlign':'center',
                                                  'color': ticker_color(int(global_total['Confirmed']) - int(delta['Confirmed'])),
                                                  'fontSize':20},
                                            children='{0:+,d}'.format(int(global_total['Confirmed']) - int(delta['Confirmed'])))
                                    ],
                          className='four columns'),

                 html.Div(id='death-ind',
                          style={'width':'24.4%','marginRight':'.8%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign':'center',
                                                  'color':dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Deaths'),
                                    html.H3(style={'textAlign':'center',
                                                   'fontWeight':'bold','color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Deaths']))),
                                    html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'], 'fontSize': 20},
                                           children='{0:+,d}'.format(int(global_total['Deaths']) - int(delta['Deaths'])))
                                    ],
                          className='four columns'),

                 html.Div(id='rec-ind',
                          style={'width': '24.4%', 'marginRight': '.8%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Recoveries'),
                                    html.H3(style={'textAlign': 'center',
                                                   'fontWeight': 'bold', 'color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Recovered']))),
                                    html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['green'], 'fontSize': 20},
                                           children='{0:+,d}'.format(int(global_total['Recovered']) - int(delta['Recovered'])))
                                    ],
                          className='four columns'),

                 html.Div(id='active-ind',
                          style={'width': '24.4%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Active Cases'),
                                    html.H3(style={'textAlign': 'center',
                                                   'fontWeight': 'bold', 'color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Active']))),
                                    html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'], 'fontSize': 20},
                                           children='{0:+,d}'.format(int(global_total['Active']) - int(delta['Active'])))
                                    ],
                          className='four columns')

             ],className='row'

# children=[html.P(style={'textAlign':'center','fontWeight':'bold','color':'#d7191c','padding':'1rem'},

        # children = confirmed_number,
        #      style={
        #          'textAlign': 'center',
        #          'color': dash_colors['red'],
        #          'width': '25%',
        #          'float': 'left',
        #          'display': 'inline-block'
        #      }
),

    html.Div(id='global-trending',
             style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'},
             children=[
                 html.Div(dcc.Graph(id='global-melt',figure=fig_area),
                          style={'width':'49.6%','display':'inline-block','marginRight':'.8%'}),
                 html.Div(dcc.Graph(id='time-series',figure=fig_timeseries),
                          style={'width':'49.6%','display':'inline-block'})
             ],className='row'),

    html.Div(id='world-map',
             style={'marginLeft':'1.5%','marginRight':'1.5%','marginBottom':'.5%','marginTop':'.5%'},
             children=[html.Div(dcc.Graph(id='global-outbreak',figure = fig_mapbox,style={'height':800}))
             ])
])


if __name__ == '__main__':
    app.run_server()