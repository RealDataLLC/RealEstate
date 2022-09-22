import plotly.express as px
from jupyter_dash import JupyterDash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd


"""
TODO: 
1. move helper functions
2. set time slider
3. add 2020 census data

"""
def restack_frame(df, target_variable):
    # restacking frame for merging
    
    df.drop(columns= ["RegionID", "SizeRank", "RegionType", "StateName"], inplace=True)

    reframed_rent_df = pd.DataFrame(df.set_index("RegionName").stack()).reset_index()
    reframed_rent_df.columns = ["RegionName", "Date", target_variable]
    reframed_rent_df.RegionName = reframed_rent_df.RegionName.str.replace(",", "")
    reframed_rent_df.Date = reframed_rent_df.Date.str[:7]
    
    return reframed_rent_df

def graph_layout(id_name, title):
    return html.Div(children=[

        html.Br(),
        html.Label(title),
        dcc.Graph(
            id=id_name,
        )],
        style=style, draggable=True)


def create_sub_plot(filtered_df, dependent_variable):
    fig = px.line(filtered_df, x="Date", y=dependent_variable, color="RegionName", hover_name="RegionName")
    fig.update_layout(transition_duration=500, template=template)
    return fig

# ZRent from Zillow
rent_df = pd.read_csv("https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_sm_sa_month.csv?t=1663774133")
reframed_rent_df = restack_frame(rent_df, "ZRent")

# housing from Zillow
housing_df = pd.read_csv("https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv?t=1663287638")
reframed_housing_df = restack_frame(housing_df, "ZEstimate")

# inventory from Zillow
inventory_df = pd.read_csv("https://files.zillowstatic.com/research/public_csvs/invt_fs/Metro_invt_fs_uc_sfrcondo_sm_month.csv?t=1663287638")
reframed_inventory_df = restack_frame(inventory_df, "Inventory")

# combining rent and housing
reframe_df = pd.merge(reframed_rent_df, reframed_housing_df, how = "left", left_on = ["RegionName", "Date"], right_on = ["RegionName", "Date"])
reframe_df = pd.merge(reframe_df, reframed_inventory_df, how = "left", left_on = ["RegionName", "Date"], right_on = ["RegionName", "Date"])

reindexed_reframed_df = reframe_df.set_index(["RegionName", "Date"])


# rent buy ratio
reindexed_reframed_df["rent_buy_ratio"] = reindexed_reframed_df["ZRent"]/reindexed_reframed_df["ZEstimate"]

# adding percentage change
reindexed_reframed_df["rent_pct_change"] = reindexed_reframed_df["ZRent"].astype(float).pct_change()
reindexed_reframed_df["home_value_pct_change"] = reindexed_reframed_df["ZEstimate"].pct_change()
reindexed_reframed_df["inventory_pct_change"] = reindexed_reframed_df["Inventory"].pct_change()

reindexed_reframed_df["rent_buy_pct_change"] = reindexed_reframed_df["rent_buy_ratio"].pct_change()

# removing wrong months
reindexed_reframed_df.reset_index(inplace = True)
reindexed_reframed_df = reindexed_reframed_df[reindexed_reframed_df.Date != "2015-03"]


# census data
census_data = pd.read_csv("https://raw.githubusercontent.com/nelsonlin2708968/RealEstate/master/data/fully_interpolated_census_data_msa.csv")

census_data.rename(columns = {"year" : "Date"}, inplace=True)
census_data["population_change"] = census_data["population"].pct_change()
census_data["median_income_change"] = census_data["median_income"].pct_change()





app = JupyterDash(__name__, 
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],)
del app.config._read_only["requests_pathname_prefix"]
server = app.server


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
    
    graph_layout('Zrent', 'Graph of ZRents'), 
    graph_layout('Zrent_pct_change', 'Graph of ZRents Change'), 
    
    graph_layout('ZEst', 'Graph of ZEstimates'), 
    graph_layout('ZEst_pct_change', 'Graph of ZEstimates Change'),
    
    graph_layout('Zrent_buy', 'Graph of ZRent/ZBuy'), 
    graph_layout('Zrent_buy_pct_change', 'Graph of ZRent/ZBuy Change'),
    
    graph_layout('Inventory', 'Graph of Inventory'), 
    graph_layout('inventory_pct_change', 'Inventory Rate of Change'),
    
    graph_layout(id_name = 'median_income', title = 'Incomes (Projected 2020-2022)'), 
    graph_layout(id_name = 'median_income_change', title = 'Income Growth (Projected 2020-2022)'), 

    graph_layout(id_name = 'population', title = 'Population (Projected 2020-2022)'),
    graph_layout(id_name = 'population_change', title = 'Population Growth (Projected 2020-2022)'),
    
    
    ])

@app.callback(
    Output('Zrent', 'figure'),
    Output('Zrent_pct_change', 'figure'),
    Output('ZEst', 'figure'),
    Output('ZEst_pct_change', 'figure'),
    Output('Zrent_buy', 'figure'),
    Output('Zrent_buy_pct_change', 'figure'),
    Output('Inventory', 'figure'),
    Output('inventory_pct_change', 'figure'),
    Output('median_income', 'figure'),
    Output('median_income_change', 'figure'),
    Output('population', 'figure'),
    Output('population_change', 'figure'),

    Input('cities_to_graph', 'value'))

def update_figure(selected_cities):
    
    print("selected_cities", selected_cities)
    if not selected_cities:
        selected_cities = ["United States"]
        
    filtered_df = reindexed_reframed_df[reindexed_reframed_df.RegionName.isin(selected_cities)]  
    census_filtered_df = census_data[census_data.RegionName.isin(selected_cities)]  

    fig1 = create_sub_plot(filtered_df, "ZRent")
    fig2 = create_sub_plot(filtered_df, "rent_pct_change")
    
    fig3 = create_sub_plot(filtered_df, "ZEstimate")
    fig4 = create_sub_plot(filtered_df, "home_value_pct_change")
    
    fig5 = create_sub_plot(filtered_df, "rent_buy_ratio")
    fig6 = create_sub_plot(filtered_df, "rent_buy_pct_change")
    
    fig7 = create_sub_plot(filtered_df[(filtered_df["RegionName"] != "United States") & (filtered_df["Date"] > "2018-01")], "Inventory")
    fig8 = create_sub_plot(filtered_df[filtered_df["Date"] > "2018-01"], "inventory_pct_change")
    
    fig9 = create_sub_plot(census_filtered_df, "median_income")
    fig10 = create_sub_plot(census_filtered_df[census_filtered_df["Date"] != 2015], "median_income_change")
    
    fig11 = create_sub_plot(census_filtered_df[census_filtered_df["RegionName"] != "United States"], "population")
    fig12 = create_sub_plot(census_filtered_df[census_filtered_df["Date"] != 2015], "population_change")
    
    return fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11, fig12
    
if __name__ == '__main__':
    app.run_server(debug=False)