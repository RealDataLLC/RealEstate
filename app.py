import plotly.express as px
from jupyter_dash import JupyterDash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd

# zillow rent data
rent_df = pd.read_csv(
    "https://files.zillowstatic.com/research/public_csvs/zori/Metro_ZORI_AllHomesPlusMultifamily_SSA.csv?t=1644973146")
rent_df.drop(columns=["RegionID", "SizeRank"], inplace=True)

# restacking frame
reframed_rent_df = pd.DataFrame(rent_df.set_index("RegionName").stack()).reset_index()
reframed_rent_df.columns = ["RegionName", "Date", "ZRent"]
reframed_rent_df.RegionName = reframed_rent_df.RegionName.str.replace(",", "")

# housing from ZRent
housing_df = pd.read_csv(
    "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv?t=1645574925")
housing_df.drop(columns=["RegionID", "SizeRank", "RegionType", "StateName"], inplace=True)

# restacking frame
reframed_housing_df = pd.DataFrame(housing_df.set_index("RegionName").stack()).reset_index()
reframed_housing_df.columns = ["RegionName", "Date", "ZEstimate"]
reframed_housing_df.RegionName = reframed_housing_df.RegionName.str.replace(",", "")
reframed_housing_df.Date = reframed_housing_df.Date.str[:-3]

# combining rent and housing
reframe_df = pd.merge(reframed_rent_df, reframed_housing_df, how="left", left_on=["RegionName", "Date"],
                      right_on=["RegionName", "Date"])
reindexed_reframed_df = reframe_df.set_index(["RegionName", "Date"])

# rent buy ratio
reindexed_reframed_df["rent_buy_ratio"] = reindexed_reframed_df["ZRent"] / reindexed_reframed_df["ZEstimate"]

# adding percentage change
reindexed_reframed_df["rent_pct_change"] = reindexed_reframed_df["ZRent"].pct_change()
reindexed_reframed_df["home_value_pct_change"] = reindexed_reframed_df["ZEstimate"].pct_change()
reindexed_reframed_df["rent_buy_pct_change"] = reindexed_reframed_df["rent_buy_ratio"].pct_change()

# removing wrong months
reindexed_reframed_df.reset_index(inplace=True)
reindexed_reframed_df = reindexed_reframed_df[reindexed_reframed_df.Date != "2014-01"]

true_housing_df = pd.read_csv(
    "https://files.zillowstatic.com/research/public_csvs/mlp/Metro_mlp_uc_sfrcondo_sm_month.csv?t=1646178611")
true_housing_df.drop(columns=["RegionID", "SizeRank", "RegionType", "StateName"], inplace=True)
reframed_true_housing_df = pd.DataFrame(true_housing_df.set_index("RegionName").stack()).reset_index()

reframed_true_housing_df.columns = ["RegionName", "Date", "ZEstimate"]
reframed_true_housing_df.RegionName = reframed_true_housing_df.RegionName.str.replace(",", "")
reframed_true_housing_df.Date = reframed_true_housing_df.Date.str[:-3]


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


app = JupyterDash(__name__,
                  external_stylesheets=[dbc.themes.BOOTSTRAP],
                  meta_tags=[
                      {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                  ], )
del app.config._read_only["requests_pathname_prefix"]
server = app.server

template = "simple_white"
style = {'width': '49%', 'display': 'inline-block', "text-align": "center", }

app.layout = html.Div([
    html.Div(children=[

        html.Br(),
        html.Label('Pick Cities to compare'),
        dcc.Dropdown(options=reindexed_reframed_df.RegionName.unique(),
                     value=["United States", "Jacksonville FL"],
                     multi=True,
                     id="cities_to_graph"),

    ]),

    graph_layout('Zrent', 'Graph of ZRents'),
    graph_layout('Zrent_pct_change', 'Graph of ZRents Change'),
    graph_layout('ZEst', 'Graph of ZEstimates'),
    graph_layout('ZEst_pct_change', 'Graph of ZEstimates Change'),
    graph_layout('Zrent_buy', 'Graph of ZRent/ZBuy'),
    graph_layout('Zrent_buy_pct_change', 'Graph of ZRent/ZBuy Change'),
    # dash_table.DataTable(df.to_dict('records'),[{"name": i, "id": i} for i in df.columns], id='tbl'),

])


@app.callback(
    Output('Zrent', 'figure'),
    Output('Zrent_pct_change', 'figure'),
    Output('ZEst', 'figure'),
    Output('ZEst_pct_change', 'figure'),
    Output('Zrent_buy', 'figure'),
    Output('Zrent_buy_pct_change', 'figure'),

    Input('cities_to_graph', 'value'))
def update_figure(selected_cities):
    print("selected_cities", selected_cities)
    if not selected_cities:
        selected_cities = ["United States"]

    filtered_df = reindexed_reframed_df[reindexed_reframed_df.RegionName.isin(selected_cities)]

    fig1 = create_sub_plot(filtered_df, "ZRent")
    fig2 = create_sub_plot(filtered_df, "rent_pct_change")
    fig3 = create_sub_plot(filtered_df, "ZEstimate")
    fig4 = create_sub_plot(filtered_df, "home_value_pct_change")

    fig5 = create_sub_plot(filtered_df, "rent_buy_ratio")
    fig6 = create_sub_plot(filtered_df, "rent_buy_pct_change")

    return fig1, fig2, fig3, fig4, fig5, fig6


if __name__ == '__main__':
    app.run_server(debug=False)