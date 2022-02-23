import plotly.express as px
from jupyter_dash import JupyterDash
from dash import Input, Output, dcc, html
import pandas as pd


### zillow rent data
df = pd.read_csv("https://files.zillowstatic.com/research/public_csvs/zori/Metro_ZORI_AllHomesPlusMultifamily_SSA.csv?t=1644973146")
df.drop(columns= ["RegionID", "SizeRank"], inplace=True)

reframe_df = pd.DataFrame(df.set_index("RegionName").stack()).reset_index()
reframe_df.columns = ["RegionName", "Date", "ZRent"]
reframe_df.RegionName = reframe_df.RegionName.str.replace(",", "")


### Zilllow housing
housing_df = pd.read_csv("https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv?t=1645574925")
housing_df.drop(columns= ["RegionID", "SizeRank", "RegionType", "StateName"], inplace=True)

reframed_housing_df = pd.DataFrame(housing_df.set_index("RegionName").stack()).reset_index()
reframed_housing_df.columns = ["RegionName", "Date", "ZEstimate"]
reframed_housing_df.RegionName = reframed_housing_df.RegionName.str.replace(",", "")
reframed_housing_df.Date = reframed_housing_df.Date.str[:-3]

### Combining data frames
reframe_df = pd.merge(reframed_rent_df, reframed_housing_df, how = "left", left_on = ["RegionName", "Date"], right_on = ["RegionName", "Date"])
reindexed_reframed_df = reframe_df.set_index(["RegionName", "Date"])

### adding percentage change
reindexed_reframed_df["rent_pct_change"] = reindexed_reframed_df["ZRent"].pct_change()
reindexed_reframed_df["home_value_pct_change"] = reindexed_reframed_df["ZEstimate"].pct_change()

# removing first month because of overlap issue
reindexed_reframed_df.reset_index(inplace = True)
reindexed_reframed_df = reindexed_reframed_df[reindexed_reframed_df.Date != "2014-01"]

### PLOTTING ###
app = JupyterDash(__name__)
del app.config._read_only["requests_pathname_prefix"]

template = "simple_white"
style = {'width': '49%', 'display': 'inline-block',"text-align" : "center",}

app.layout = html.Div([
    html.Div(children=[
        
        html.Br(),
        html.Label('Pick Cities to compare'),
        dcc.Dropdown(options = reindexed_reframed_df.RegionName.unique(),
                     value = ["United States", "Jacksonville FL"],
                     multi=True, 
                     id="cities_to_graph"),
       
    ]),
    
    html.Div(children=[
        
        html.Br(),
        html.Label('Graph of ZRents'),

        dcc.Graph(
            id='Zrent',
        )]
    
     ,style=style),
    
    html.Div(children=[
        
        html.Br(),
        html.Label('Graph of ZRents Change'),
        dcc.Graph(
            id='Zrent_pct_change',
        )]
    
     ,style=style  ),
    html.Div(children=[
        
        html.Br(),
        html.Label('Graph of ZEstimates'),
        dcc.Graph(
            id='ZEst',
        )]
    
       ,style=style             ),
    html.Div(children=[
        
        html.Br(),
        html.Label('Graph of ZEstimates Change'),
        dcc.Graph(
            id='ZEst_pct_change',
        )]
        ,style=style  
                  ),

    ], style = title_settings)

@app.callback(
    Output('Zrent', 'figure'),
    Output('Zrent_pct_change', 'figure'),
    Output('ZEst', 'figure'),
    Output('ZEst_pct_change', 'figure'),

    Input('cities_to_graph', 'value'))

def update_figure(selected_cities):
    
    print("selected_cities", selected_cities)
    if not selected_cities:
        selected_cities = ["United States"]
        
    filtered_df = reindexed_reframed_df[reindexed_reframed_df.RegionName.isin(selected_cities)]   
    fig1 = px.scatter(filtered_df, x="Date", y="ZRent", color="RegionName", hover_name="RegionName")
    fig1.update_layout(transition_duration=500, template = template)

    
    fig2 = px.scatter(filtered_df, x="Date", y="rent_pct_change", color="RegionName", hover_name="RegionName")
    fig2.update_layout(transition_duration=500, template = template,)
    
    fig3 = px.scatter(filtered_df, x="Date", y="ZEstimate", color="RegionName", hover_name="RegionName")
    fig3.update_layout(transition_duration=500, template = template)
    
    fig4 = px.scatter(filtered_df, x="Date", y="home_value_pct_change", color="RegionName", hover_name="RegionName")
    fig4.update_layout(transition_duration=500, template = template)
    
    return fig1, fig2, fig3, fig4
    
if __name__ == '__main__':
    app.run_server(debug=False)