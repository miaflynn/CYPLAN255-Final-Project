import json
import pandas as pd
import geopandas as gpd
from dash import Dash, dcc, html, Input, Output, State, callback
import dash_leaflet as dl
from dash_extensions.javascript import assign
import plotly.graph_objects as go

app = Dash(__name__)
server = app.server

sf_map = gpd.read_file('data/processed/open_close_neighs.geojson')
sf_map = sf_map.to_crs(epsg=4326)
geojson_data = json.loads(sf_map.to_json())

naics_df = pd.read_parquet('data/processed/naics_year_charts.parquet')

for feature in geojson_data['features']:
    props = feature['properties']
    props['tooltip'] = f"<b>{props['neighborhood']}</b><br>Businesses: {int(props['biz_stock'])}"

DEFAULT_SELECTION = ['Sunset/Parkside', 'Bayview Hunters Point']

style_handle = assign("""
function(feature, context) {
    const { selected, low, high } = context.hideout;
    const isSelected = selected.includes(feature.properties.neighborhood);
    const bizStock = feature.properties.biz_stock;

    const norm = Math.min(Math.max((bizStock - low) / (high - low), 0), 1);
    const r = 255;
    const g = Math.round(165 * (1 - norm));
    const b = 0;

    return {
        fillColor: isSelected ? 'steelblue' : `rgb(${r},${g},${b})`,
        fillOpacity: isSelected ? 0.8 : 0.6,
        color: 'white',
        weight: 1
    };
}
""")

app.layout = html.Div([
    html.H1('SF Business Openings and Closings'),
    html.P('Selected neighborhoods:'),
    html.Div(
        id='selected-display',
        style={'display': 'flex', 'gap': '8px', 'padding': '10px 0', 'flexWrap': 'wrap'}
    ),
    dcc.Store(id='selected-neighborhoods', data=DEFAULT_SELECTION),
    html.Div('Business Density 2016–2025', style={
        'fontSize': '25px', 'color': '#666', 'textAlign': 'right', 'marginBottom': '4px'
    }),
    html.Div('Select up to four neighborhoods to compare', style={
        'fontSize': '15px', 'color': '#666', 'textAlign': 'right', 'marginBottom': '4px'
    }),
    html.Div(
        [
            dl.Map(
                center=[37.7749, -122.4194],
                zoom=12,
                children=[
                    dl.TileLayer(),
                    dl.GeoJSON(
                        id='sf-geojson',
                        data=geojson_data,
                        options=dict(style=style_handle),
                        hideout=dict(
                            selected=DEFAULT_SELECTION,
                            low=float(sf_map['biz_stock'].quantile(0.05)),
                            high=float(sf_map['biz_stock'].quantile(0.95))
                        ),
                        zoomToBounds=True,
                    ),
                    dl.Colorbar(
                        colorscale=['rgb(255,165,0)', 'rgb(255,0,0)'],
                        width=200,
                        height=12,
                        min=float(sf_map['biz_stock'].quantile(0.05)),
                        max=float(sf_map['biz_stock'].quantile(0.95)),
                        position='bottomright',
                    )
                ],
                style={'height': '600px'}
            ),
        ],
        className='map-container'
    ),

    # chart grid
    html.Div([
        html.Div([
            html.Div('Chart 1', className='chart-placeholder'),
            html.Div([
                dcc.RadioItems(
                    id='metric-toggle',
                    options=[
                        {'label': 'Openings', 'value': 'opened'},
                        {'label': 'Closings', 'value': 'closed'},
                    ],
                    value='opened',
                    inline=True,
                    style={'marginBottom': '8px', 'fontSize': '13px'}
                ),
                html.Div(id='sector-charts', style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'})
            ], style={
                'background': '#f5f5f5',
                'border': '2px dashed #ddd',
                'borderRadius': '12px',
                'padding': '16px',
                'flex': 1,
                'minHeight': '300px',
                'maxHeight': '300px',
                'overflow': 'hidden'
            }),
        ], style={'display': 'flex', 'gap': '16px', 'height': '300px'}),
        html.Div([
            html.Div('Chart 3', className='chart-placeholder'),
            html.Div('Chart 4', className='chart-placeholder'),
        ], style={'display': 'flex', 'gap': '16px', 'height': '300px'}),
    ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '16px', 'marginTop': '24px'})

], className='app-wrapper')


@callback(
    Output('sf-geojson', 'hideout'),
    Output('selected-neighborhoods', 'data'),
    Output('selected-display', 'children'),
    Input('sf-geojson', 'n_clicks'),
    State('sf-geojson', 'clickData'),
    State('selected-neighborhoods', 'data')
)
def select_neighborhood(n_clicks, clickData, current_selection):
    if not n_clicks or clickData is None:
        pills = [html.Span(n, className='pill') for n in current_selection]
        return dict(
            selected=current_selection,
            low=float(sf_map['biz_stock'].quantile(0.05)),
            high=float(sf_map['biz_stock'].quantile(0.95))
        ), current_selection, pills

    clicked = clickData['properties']['neighborhood']

    if clicked in current_selection:
        current_selection.remove(clicked)
    elif len(current_selection) < 4:
        current_selection.append(clicked)

    pills = [html.Span(n, className='pill') for n in current_selection]
    label = pills if current_selection else 'No neighborhoods selected'

    return dict(
        selected=current_selection,
        low=float(sf_map['biz_stock'].quantile(0.05)),
        high=float(sf_map['biz_stock'].quantile(0.95))
    ), current_selection, label


@callback(
    Output('sector-charts', 'children'),
    Input('selected-neighborhoods', 'data'),
    Input('metric-toggle', 'value')
)
def update_sector_charts(selected, metric):
    if not selected:
        return []

    
    chart_height = 260 if len(selected) <= 2 else 200

    charts = []
    for neighborhood in selected:
        df = naics_df[naics_df['neighborhood'] == neighborhood]

        fig = go.Figure()
        for sector in df['naics_group'].unique():
            sector_df = df[df['naics_group'] == sector].sort_values('year')
            fig.add_trace(go.Scatter(
                x=sector_df['year'],
                y=sector_df[metric],
                mode='lines',
                name=sector
            ))

        fig.update_layout(
            title=dict(text=neighborhood, font=dict(size=11)),
            height=chart_height,
            margin=dict(l=20, r=10, t=30, b=20),
            legend=dict(font=dict(size=8)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        charts.append(dcc.Graph(
            figure=fig,
            style={'flex': 1, 'minWidth': 0}
        ))

    return charts


if __name__ == '__main__':
    app.run(debug=True)