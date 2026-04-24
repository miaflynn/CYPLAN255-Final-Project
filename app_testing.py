import json
import geopandas as gpd
from dash import Dash, dcc, html, Input, Output, State, callback
import dash_leaflet as dl
from dash_extensions.javascript import assign

app = Dash(__name__)
server = app.server

sf_map = gpd.read_file('data/processed/open_close_neighs.geojson')
sf_map = sf_map.to_crs(epsg=4326)
geojson_data = json.loads(sf_map.to_json())

for feature in geojson_data['features']:
    props = feature['properties']
    props['tooltip'] = f"<b>{props['neighborhood']}</b> <br> Businesses: {int(props['biz_stock'])}"

low  = float(sf_map['biz_stock'].quantile(0.05))
high = float(sf_map['biz_stock'].quantile(0.95))

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
    html.H1('SF Business Dynamics'),
    html.Div(
        id='selected-display',
        style={'display': 'flex', 'gap': '8px', 'padding': '10px 0', 'flexWrap': 'wrap'}
    ),
    dcc.Store(id='selected-neighborhoods', data=DEFAULT_SELECTION),

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
                        hideout=dict(selected=DEFAULT_SELECTION, low=low, high=high),
                        zoomToBounds=True,
                    ),
                    dl.Colorbar(
                        colorscale=['rgb(255,165,0)', 'rgb(255,0,0)'],
                        width=200,
                        height=12,
                        min=low,
                        max=high,
                        position='bottomright',
                    )
                ],
                style={'height': '600px'}
            ),
        ],
        className='map-container'
    ),

    html.Div([
        html.Div([
            html.Div('Chart 1', className='chart-placeholder'),
            html.Div('Chart 2', className='chart-placeholder'),
        ], style={'display': 'flex', 'gap': '16px'}),
        html.Div([
            html.Div('Chart 3', className='chart-placeholder'),
            html.Div('Chart 4', className='chart-placeholder'),
        ], style={'display': 'flex', 'gap': '16px'}),
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
        return dict(selected=current_selection, low=low, high=high), current_selection, pills

    clicked = clickData['properties']['neighborhood']

    if clicked in current_selection:
        current_selection.remove(clicked)
    elif len(current_selection) < 4:
        current_selection.append(clicked)

    pills = [html.Span(n, className='pill') for n in current_selection]
    label = pills if current_selection else 'No neighborhoods selected'

    return dict(selected=current_selection, low=low, high=high), current_selection, label

if __name__ == '__main__':
    app.run(debug=True)