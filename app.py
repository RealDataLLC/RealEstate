import plotly.express as px
from jupyter_dash import JupyterDash
from dash import Input, Output, dcc, html
import pandas as pd

#zillow rent data
df = pd.read_csv("https://files.zillowstatic.com/research/public_csvs/zori/Metro_ZORI_AllHomesPlusMultifamily_SSA.csv?t=1644973146")
df.drop(columns= ["RegionID", "SizeRank"], inplace=True)

reframe_df = pd.DataFrame(df.set_index("RegionName").stack()).reset_index()
reframe_df.columns = ["RegionName", "Date", "ZRent"]
reframe_df.RegionName = reframe_df.RegionName.str.replace(",", "")

reindexed_reframed_df = reframe_df.set_index(["RegionName", "Date"])
# adding percentage change
reindexed_reframed_df["pct_change"] = reindexed_reframed_df["ZRent"].pct_change()
reindexed_reframed_df.reset_index(inplace = True)
reindexed_reframed_df = reindexed_reframed_df[reindexed_reframed_df.Date != "2014-01"]


app = JupyterDash(__name__)
del app.config._read_only["requests_pathname_prefix"]
server = app.server

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
    
                  ),
    
    html.Div(children=[
        
        html.Br(),
        html.Label('Graph of ZRents Change'),
        dcc.Graph(
            id='Zrent_pct_change',
        )]
    
                  ),

    ])
@app.callback(
    Output('Zrent', 'figure'),
    Output('Zrent_pct_change', 'figure'),

    Input('cities_to_graph', 'value'))

def update_figure(selected_cities):
    
    print("selected_cities", selected_cities)
    if not selected_cities:
        selected_cities = ["United States"]
        
    filtered_df = reindexed_reframed_df[reindexed_reframed_df.RegionName.isin(selected_cities)]   
    fig1 = px.scatter(filtered_df, x="Date", y="ZRent", color="RegionName", hover_name="RegionName")
    fig1.update_layout(transition_duration=500)

    
    fig2 = px.scatter(filtered_df, x="Date", y="pct_change", color="RegionName", hover_name="RegionName")
    fig2.update_layout(transition_duration=500)
    
    return fig1, fig2
    
if __name__ == '__main__':
    app.run_server(debug=False)