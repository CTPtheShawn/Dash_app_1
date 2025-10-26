from dash import Dash, dcc, html, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# ---------- Styles (Bootstrap via CDN) ----------
EXTERNAL_CSS = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css"]

# ---------- App ----------
app = Dash(__name__, external_stylesheets=EXTERNAL_CSS)
server = app.server  # for deployment if needed

# ---------- Stable dataset from plotly ----------
df = px.data.gapminder()  # columns: country, continent, year, lifeExp, pop, gdpPercap, iso_alpha, iso_num

# Pretty names for the table only (不影响内部计算)
TABLE_COL_RENAME = {
    "country": "Country",
    "continent": "Continent",
    "year": "Year",
    "lifeExp": "Life Expectancy",
    "pop": "Population",
    "gdpPercap": "GDP per Capita",
    "iso_alpha": "ISO Alpha Country Code",
    "iso_num": "ISO Numeric Code",
}
table_df = df.rename(columns=TABLE_COL_RENAME)

continents = sorted(df["continent"].unique().tolist())
years = sorted(df["year"].unique().tolist())

continent_options = [{"label": c, "value": c} for c in continents]
year_options = [{"label": str(y), "value": int(y)} for y in years]
VAR_MAP = {"Population": "pop", "GDP per Capita": "gdpPercap", "Life Expectancy": "lifeExp"}
var_options = [{"label": k, "value": k} for k in VAR_MAP.keys()]

# ---------- Theme helpers ----------
def theme_settings(theme):
    if theme == "dark":
        return dict(template="plotly_dark", page_bg="#111827", card_bg="#1f2937", text="#e5e7eb")
    return dict(template="plotly_white", page_bg="#e5ecf6", card_bg="#ffffff", text="#111827")

def empty_figure(msg="No data available for current filters."):
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=16))
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)",
                      xaxis_visible=False, yaxis_visible=False,
                      margin=dict(t=40, l=20, r=20, b=20), height=420)
    return fig

def make_bar(filtered, x_col, y_col, title, template, orient="v", top_n=15):
    if filtered.empty:
        return empty_figure()
    data = filtered.sort_values(by=y_col, ascending=False).head(int(top_n))
    if orient == "h":
        fig = px.bar(data, x=y_col, y=x_col, color=x_col, text_auto=True, orientation="h", title=title)
    else:
        fig = px.bar(data, x=x_col, y=y_col, color=x_col, text_auto=True, title=title)
    fig.update_layout(template=template, paper_bgcolor="rgba(0,0,0,0)", height=600, legend_title="")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig

def create_table(template):
    headers = [TABLE_COL_RENAME.get(c, c) for c in df.columns]
    vals = [table_df[h].values for h in headers]
    fig = go.Figure(data=[go.Table(header=dict(values=headers, align="left"),
                                   cells=dict(values=vals, align="left"))])
    fig.update_layout(template=template, paper_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=0, l=0, r=0, b=0), height=700)
    return fig

def create_population_chart(continent="Asia", year=1952, template="plotly_white", orient="v", top_n=15):
    filtered = df[(df["continent"] == continent) & (df["year"] == int(year))]
    return make_bar(filtered, x_col="country", y_col="pop",
                    title=f"Population for {continent} in {year}",
                    template=template, orient=orient, top_n=top_n)

def create_gdp_chart(continent="Asia", year=1952, template="plotly_white", orient="v", top_n=15):
    filtered = df[(df["continent"] == continent) & (df["year"] == int(year))]
    return make_bar(filtered, x_col="country", y_col="gdpPercap",
                    title=f"GDP per Capita for {continent} in {year}",
                    template=template, orient=orient, top_n=top_n)

def create_life_exp_chart(continent="Asia", year=1952, template="plotly_white", orient="v", top_n=15):
    filtered = df[(df["continent"] == continent) & (df["year"] == int(year))]
    return make_bar(filtered, x_col="country", y_col="lifeExp",
                    title=f"Life Expectancy for {continent} in {year}",
                    template=template, orient=orient, top_n=top_n)

def create_choropleth_map(variable_display, year, template):
    var_col = VAR_MAP.get(variable_display, "lifeExp")
    filtered = df[df["year"] == int(year)]
    if filtered.empty:
        return empty_figure()
    fig = px.choropleth(filtered, color=var_col, locations="iso_alpha", locationmode="ISO-3",
                        color_continuous_scale="RdYlBu",
                        hover_data=["country", var_col],
                        title=f"{variable_display} Choropleth Map [{year}]")
    fig.update_layout(template=template, dragmode=False, paper_bgcolor="rgba(0,0,0,0)",
                      height=600, margin={"l": 0, "r": 0})
    return fig

# ---------- Layout (Header + Sidebar + Content) ----------
app.layout = html.Div(id="page-root", children=[
    # Header / Navbar
    html.Div(className="d-flex align-items-center justify-content-between px-3 py-2 shadow-sm",
             children=[
                 html.Div([
                     html.H4("Gapminder Dashboard", className="m-0 fw-bold"),
                     html.Small("Dash + Plotly • Interactive Analytics", className="text-muted")
                 ]),
                 html.Div(className="d-flex align-items-center gap-3", children=[
                     html.Span("Theme:", className="me-2"),
                     dcc.RadioItems(
                         id="theme-toggle",
                         options=[{"label": "Light", "value": "light"},
                                  {"label": "Dark", "value": "dark"}],
                         value="light",
                         inline=True,
                         inputStyle={"marginRight": "4px", "marginLeft": "8px"}
                     ),
                 ])
             ]),

    # Main two-column layout
    html.Div(className="container-fluid mt-3", children=[
        html.Div(className="row", children=[
            # Sidebar controls
            html.Div(className="col-12 col-lg-3 mb-3", id="sidebar-card", children=[
                html.Div(className="p-3 rounded-4 shadow-sm", id="sidebar-inner", children=[
                    html.H6("Controls", className="fw-bold mb-3"),
                    html.Div(className="mb-2 fw-semibold text-uppercase small text-muted", children="Population / GDP / Life"),
                    html.Label("Continent", className="form-label mt-1"),
                    dcc.Dropdown(id="cont_all", options=continent_options, value="Asia", clearable=False),
                    html.Label("Year", className="form-label mt-3"),
                    dcc.Dropdown(id="year_all", options=year_options, value=1952, clearable=False),

                    html.Hr(className="my-3"),
                    html.Div(className="mb-2 fw-semibold text-uppercase small text-muted", children="Bar Appearance"),
                    html.Label("Top N countries", className="form-label mt-1"),
                    dcc.Slider(id="topn", min=5, max=25, step=5, value=15,
                               marks={i: str(i) for i in range(5, 26, 5)}),
                    html.Label("Orientation", className="form-label mt-3"),
                    dcc.RadioItems(
                        id="bar-orient",
                        options=[{"label": "Vertical", "value": "v"},
                                 {"label": "Horizontal", "value": "h"}],
                        value="v",
                        inline=True
                    ),

                    html.Hr(className="my-3"),
                    html.Div(className="mb-2 fw-semibold text-uppercase small text-muted", children="Map"),
                    html.Label("Variable", className="form-label mt-1"),
                    dcc.Dropdown(id="var_map", options=[{"label": k, "value": k} for k in VAR_MAP.keys()],
                                 value="Life Expectancy", clearable=False),
                    html.Label("Year (Map)", className="form-label mt-3"),
                    dcc.Dropdown(id="year_map", options=year_options, value=1952, clearable=False),
                ])
            ]),

            # Content area
            html.Div(className="col-12 col-lg-9", children=[
                # Data table card
                html.Div(className="p-3 rounded-4 shadow-sm mb-3", id="card-table", children=[
                    html.Div(className="d-flex justify-content-between align-items-center mb-2",
                             children=[html.H6("Dataset", className="fw-bold m-0")]),
                    dcc.Graph(id="dataset")
                ]),
                # Row of three charts
                html.Div(className="row", children=[
                    html.Div(className="col-12 col-xl-6 mb-3", children=[
                        html.Div(className="p-3 rounded-4 shadow-sm", id="card-pop", children=[
                            html.H6("Population", className="fw-bold mb-2"),
                            dcc.Graph(id="population")
                        ])
                    ]),
                    html.Div(className="col-12 col-xl-6 mb-3", children=[
                        html.Div(className="p-3 rounded-4 shadow-sm", id="card-gdp", children=[
                            html.H6("GDP per Capita", className="fw-bold mb-2"),
                            dcc.Graph(id="gdp")
                        ])
                    ]),
                    html.Div(className="col-12 mb-3", children=[
                        html.Div(className="p-3 rounded-4 shadow-sm", id="card-life", children=[
                            html.H6("Life Expectancy", className="fw-bold mb-2"),
                            dcc.Graph(id="life_expectancy")
                        ])
                    ]),
                ]),
                # Map card
                html.Div(className="p-3 rounded-4 shadow-sm mb-5", id="card-map", children=[
                    html.H6("Choropleth Map", className="fw-bold mb-2"),
                    dcc.Graph(id="choropleth_map")
                ])
            ])
        ])
    ])
])

# ---------- Reactive callbacks ----------
@callback(
    Output("page-root", "style"),
    Output("sidebar-inner", "style"),
    Output("card-table", "style"),
    Output("card-pop", "style"),
    Output("card-gdp", "style"),
    Output("card-life", "style"),
    Output("card-map", "style"),
    Input("theme-toggle", "value")
)
def paint_theme(theme):
    t = theme_settings(theme)
    page_style = {"backgroundColor": t["page_bg"], "minHeight": "100vh"}
    card_style = {"backgroundColor": t["card_bg"], "color": t["text"]}
    return page_style, card_style, card_style, card_style, card_style, card_style, card_style

@callback(Output("dataset", "figure"), Input("theme-toggle", "value"))
def update_table(theme):
    t = theme_settings(theme)
    return create_table(template=t["template"])

@callback(
    Output("population", "figure"),
    Output("gdp", "figure"),
    Output("life_expectancy", "figure"),
    Input("cont_all", "value"),
    Input("year_all", "value"),
    Input("theme-toggle", "value"),
    Input("topn", "value"),
    Input("bar-orient", "value"),
)
def update_bars(continent, year, theme, topn, orient):
    t = theme_settings(theme)
    fig1 = create_population_chart(continent, year, template=t["template"], orient=orient, top_n=topn)
    fig2 = create_gdp_chart(continent, year, template=t["template"], orient=orient, top_n=topn)
    fig3 = create_life_exp_chart(continent, year, template=t["template"], orient=orient, top_n=topn)
    return fig1, fig2, fig3

@callback(
    Output("choropleth_map", "figure"),
    Input("var_map", "value"),
    Input("year_map", "value"),
    Input("theme-toggle", "value"),
)
def update_map(var_display, year, theme):
    t = theme_settings(theme)
    return create_choropleth_map(var_display, year, template=t["template"])

if __name__ == "__main__":
    app.run(debug=True)
