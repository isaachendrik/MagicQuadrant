import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.graph_objects as go
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
import base64

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=["/static/styles.css"])
server = app.server

# List of companies with their respective quadrants and dual-use capabilities
companies = {
    "Visionaries/Innovators": {},
    "Leaders": {},
    "Niche Players": {},
    "Challengers": {}
}

# Placeholder for logos
logo_urls = {}
logos = {}

# Function to fetch and resize logos
def fetch_logo(company_name, url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        logo.thumbnail((150, 150), Image.LANCZOS)  # Resize logos to 150x150 while maintaining aspect ratio
        buffered = BytesIO()
        logo.save(buffered, format="PNG")
        encoded_logo = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{encoded_logo}"
    except Exception as e:
        print(f"Error fetching logo for {company_name}: {e}")
        return None

def update_chart(dual_use_filter=None):
    fig = go.Figure()

    # Positioning for logos in each quadrant
    positions = {
        "Leaders": (75, 75),
        "Challengers": (75, 25),
        "Visionaries/Innovators": (25, 75),
        "Niche Players": (25, 25)
    }

    # Filter companies based on the selected filter
    if dual_use_filter:
        filtered_companies = {quadrant: {company: details for company, details in company_dict.items() if details["dual_use"]} for quadrant, company_dict in companies.items()}
    else:
        filtered_companies = companies

    # Add logos to the chart
    for quadrant, company_dict in filtered_companies.items():
        x, y = positions[quadrant]
        for i, (company, details) in enumerate(company_dict.items()):
            logo = logos.get(company)
            if logo:
                fig.add_layout_image(
                    dict(
                        source=logo,
                        x=x + (i % 3) * 10,  # Adjusted spacing to prevent overlap
                        y=y - (i // 3) * 10,
                        xref="x",
                        yref="y",
                        sizex=10,
                        sizey=10,
                        xanchor="center",
                        yanchor="middle"
                    )
                )

    # Customize layout
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        images=[],
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        width=900,
        height=900,
        dragmode=False  # Disable drag mode to prevent zoom by dragging
    )

    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(range=[0, 100])

    # Add quadrant labels
    fig.add_annotation(x=25, y=100, text="<b>Visionaries/Innovators</b>", showarrow=False, font=dict(size=18, family='Poppins', color='black'))
    fig.add_annotation(x=75, y=100, text="<b>Leaders</b>", showarrow=False, font=dict(size=18, family='Poppins', color='black'))
    fig.add_annotation(x=25, y=0, text="<b>Niche Players</b>", showarrow=False, font=dict(size=18, family='Poppins', color='black'))
    fig.add_annotation(x=75, y=0, text="<b>Challengers</b>", showarrow=False, font=dict(size=18, family='Poppins', color='black'))

    # Draw lines to divide quadrants
    fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=100, line=dict(color="Black", width=2))
    fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line=dict(color="Black", width=2))

    return fig

def generate_company_list():
    company_list = []
    for quadrant, company_dict in companies.items():
        company_list.append(html.Div([
            html.H3(quadrant, style={'font-family': 'Poppins', 'font-weight': 'bold'}),
            html.Ul([html.Li([
                html.Img(src=logos.get(company), style={'height': '30px', 'marginRight': '10px'}),
                html.Span(company, style={'marginRight': '10px', 'font-family': 'Poppins'}),
                html.Button('Delete', id={'type': 'delete-button', 'index': company}, n_clicks=0, style={'backgroundColor': 'red', 'color': 'white', 'border': 'none', 'padding': '5px 10px', 'cursor': 'pointer', 'font-family': 'Poppins'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}) for company in company_dict.keys()])
        ]))
    return company_list

def generate_csv():
    data = []
    for quadrant, company_dict in companies.items():
        for company, details in company_dict.items():
            data.append({
                "Company": company,
                "Quadrant": quadrant,
                "Dual Use": details["dual_use"]
            })
    df = pd.DataFrame(data)
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    return "data:text/csv;base64," + base64.b64encode(csv_buffer.getvalue()).decode()

# Layout of the Dash app
app.layout = html.Div([
    dcc.Input(id='title-input', type='text', value='Magic Quadrant', className='title-input'),
    html.H1(id='title', className="header"),
    dcc.Graph(id='quadrant-chart', figure=update_chart(), config={
        'modeBarButtonsToAdd': ['zoom2d', 'pan2d', 'resetScale2d', 'toImage'],
        'displaylogo': False
    }, className="chart"),
    
    html.H2("Add a Company", className="subheader"),
    html.Div([
        dcc.Input(id='company-name', type='text', placeholder='Company Name', className="input"),
        dcc.Dropdown(
            id='quadrant',
            options=[
                {'label': 'Visionaries/Innovators', 'value': 'Visionaries/Innovators'},
                {'label': 'Leaders', 'value': 'Leaders'},
                {'label': 'Niche Players', 'value': 'Niche Players'},
                {'label': 'Challengers', 'value': 'Challengers'}
            ],
            placeholder='Select Quadrant',
            className="dropdown",
            style={'width': '100%'}  # Ensure the dropdown is full width
        ),
        dcc.Checklist(
            id='dual-use',
            options=[{'label': 'Dual Use', 'value': 'dual_use'}],
            className="checklist"
        ),
        dcc.Input(id='logo-url', type='text', placeholder='Logo URL', className="input"),
        html.Button('Add Company', id='add-company-button', n_clicks=0, className="button")
    ], className="form-container"),

    html.H2("Filter Companies", className="subheader"),
    html.Div([
        dcc.Checklist(
            id='dual-use-filter',
            options=[{'label': 'Show Only Dual Use Companies', 'value': 'dual_use'}],
            className="checklist"
        )
    ], className="form-container"),

    html.H2("Company List", className="subheader"),
    html.Div(generate_company_list(), id='company-list', className="company-list"),

    html.A('Download Company List', id='download-link', download="company_list.csv", href="", target="_blank", className="button download-button"),

    html.Button('Reset Graph', id='reset-graph-button', n_clicks=0, className="button")
], className="container")

@app.callback(
    [Output('title', 'children'),
     Output('quadrant-chart', 'figure'),
     Output('company-list', 'children'),
     Output('download-link', 'href')],
    [Input('title-input', 'value'),
     Input('add-company-button', 'n_clicks'),
     Input('dual-use-filter', 'value'),
     Input('reset-graph-button', 'n_clicks'),
     Input({'type': 'delete-button', 'index': ALL}, 'n_clicks')],
    [State('company-name', 'value'),
     State('quadrant', 'value'),
     State('dual-use', 'value'),
     State('logo-url', 'value')]
)
def update_output(title, n_add_clicks, dual_use_filter, n_reset_clicks, n_delete_clicks, company_name, quadrant, dual_use, logo_url):
    global companies, logo_urls, logos

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id']

    # Handle title input change
    title_output = title

    # Handle company addition
    if 'add-company-button' in triggered_id:
        if company_name and quadrant and logo_url:
            companies[quadrant][company_name] = {"dual_use": bool(dual_use)}
            logo_urls[company_name] = logo_url
            logos[company_name] = fetch_logo(company_name, logo_url)

    # Handle company deletion
    if 'delete-button' in triggered_id:
        try:
            company_to_delete = eval(ctx.triggered[0]['prop_id'].split('.')[0])['index']
            for quadrant, company_dict in companies.items():
                if company_to_delete in company_dict:
                    del companies[quadrant][company_to_delete]
                    del logos[company_to_delete]
                    break
        except Exception as e:
            print(f"Error in delete button handler: {e}")

    # Handle filter application
    dual_use_filter_value = dual_use_filter and 'dual_use' in dual_use_filter

    # Handle graph reset
    if 'reset-graph-button' in triggered_id:
        companies = {
            "Visionaries/Innovators": {},
            "Leaders": {},
            "Niche Players": {},
            "Challengers": {}
        }
        logo_urls = {}
        logos = {}
        dual_use_filter_value = None

    return title_output, update_chart(dual_use_filter_value), generate_company_list(), generate_csv()

if __name__ == '__main__':
    app.run_server(debug=True)
