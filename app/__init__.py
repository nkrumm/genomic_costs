import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

from app.components.helpers import row, col, container, panel, stat_summary_box

import numpy as np

external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css', 
    'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

control_panel = [
    panel(title="1. Test volumes", children=[
        # potentially support ranges? Also allow for average size to be modified?
        container([
            row(["Genomes/year: ", 
                 dcc.Input(id='volumes-genome-count', className='border-bottom', min=0, value=0, type='number'),
                 " tests of ",
                 dcc.Input(id='volumes-genome-size', className='border-bottom', min=1, value=120, type='number'),
                 " GB each."]),
            row(["Exomes/year: ", 
                 dcc.Input(id='volumes-exome-count', className='border-bottom', min=0, value=0, type='number'),
                 " tests of ",
                 dcc.Input(id='volumes-exome-size', className='border-bottom', min=1, value=6, type='number'),
                 " GB each."]),
            row(["Targeted Panels/year: ", 
                 dcc.Input(id='volumes-panel-count', className='border-bottom', min=0, value=0, type='number'),
                 " tests of ",
                 dcc.Input(id='volumes-panel-size', className='border-bottom', min=0.1, value=1, type='number'),
                 " GB each."]),
            row(html.Strong(["Total volume per year: ", html.Span(id='volumes-total-count')])),
            row(html.Strong(["Total GB per year: ", html.Span(id='volumes-total-size')]))
        ])
        
    ]),
    panel(title="2. File types", children=["BAM or FASTQ? Compression?"]),
        # Likely just some check/radio boxes
    panel(title="3. Retention time and storage", children=[
        # use a slider to create two storage tiers
        # have info buttons to describe tiers/differences on AWS (and other cloud providers?)
        container([
            row(["Store data in ", 
                 html.Div([dcc.Dropdown(options=[
                    {'label': "Amazon S3", 'value': "S3"},
                    {'label': "Amazon S3 Single AZ", 'value': "S3SAZ"},
                    {'label': "Amazon Glacier", 'value': "glacier"}],
                    value='S3', clearable=False, multi=False, className='border-bottom-input')], style={"display": "inline-block", "width": 200}),
                 " for ", 
                 dcc.Input(id='retention-years-tier1', className='border-bottom', min=0, value=2, type='number'),
                 " years."]),
            row(["Then, store data in ", 
                 html.Div([dcc.Dropdown(options=[
                    {'label': "Amazon S3", 'value': "S3"},
                    {'label': "Amazon S3 Single AZ", 'value': "S3SAZ"},
                    {'label': "Amazon Glacier", 'value': "glacier"}],
                    value='glacier', clearable=False, multi=False, className='border-bottom-input')], style={"display": "inline-block", "width": 200}),
                 " for ",
                 dcc.Input(id='retention-years-tier2', className='border-bottom', min=0, value=3, type='number'),
                 " years."]),
        ])
    ]),
    panel(title="4. Data re-access", children=[
        #"rate/# of cases accessed each year; potentially split by years/storage tiers"
        container([
            row(["# of cases re-accessed per year: ", 
                 dcc.Input(id='reaccess-count', className='border-bottom', min=0, value=0, type='number')])
        ])
    ]),
    panel(title="5. Other", children=[
        container([
            row(["Expected volume growth of ", 
                dcc.Input(id='volume-growth', className='border-bottom', min=0, max=100, value=10, type='number'),
                " percent per year."]),
            row(["other: Inflation, test volume growth, expected storage cost decrease"]),
        ])
    ])
]

output_panel = [
    container([
        row([
            col("col-md-12", [stat_summary_box("Costs per year", dcc.Graph(id='plot', config={'displayModeBar': False}))])
        ]),
        row([
            col("col-md-4", [stat_summary_box("Total lifetime cost: ", "$400")]),
            col("col-md-4", [stat_summary_box("Average cost per sample: ", "$40")])
        ])
    ])
]

app.layout = container([
    html.H2("The cost of genomic data storage in the clinical lab"),
    row([
        col('col-md-4', control_panel),
        col('col-md-8', output_panel)
    ], style={"marginTop": 30})
], fluid=True)


@app.callback(
    Output(component_id='volumes-total-count', component_property='children'),
    [Input(component_id='volumes-genome-count', component_property='value'),
     Input(component_id='volumes-exome-count', component_property='value'),
     Input(component_id='volumes-panel-count', component_property='value')]
)
def update_total_count(genome_count, exome_count, panel_count):
    genome_count = int(genome_count)
    exome_count = int(exome_count)
    panel_count = int(panel_count)
    total_tests = genome_count + exome_count + panel_count
    return total_tests

@app.callback(
    Output(component_id='volumes-total-size', component_property='children'),
    [Input(component_id='volumes-genome-count', component_property='value'),
     Input(component_id='volumes-exome-count', component_property='value'),
     Input(component_id='volumes-panel-count', component_property='value'),
     Input(component_id='volumes-genome-size', component_property='value'),
     Input(component_id='volumes-exome-size', component_property='value'),
     Input(component_id='volumes-panel-size', component_property='value')]
)
def update_totals_div(genome_count, exome_count, panel_count, 
    genome_size, exome_size, panel_size):
    genome_count = int(genome_count)
    exome_count = int(exome_count)
    panel_count = int(panel_count)
    genome_size = int(genome_size)
    exome_size = int(exome_size)
    panel_size = int(panel_size)
    total_gb = (genome_count * genome_size) + (exome_count * exome_size) + (panel_count * panel_size)
    return total_gb


def marginal_s3_cost(gb):
    # First 50 TB / Month $0.023 per GB
    # Next 450 TB / Month $0.022 per GB
    # Over 500 TB / Month $0.021 per GB
    if gb <= 50000:
        return gb * 0.023
    elif gb <= 500000:
        return (50000 * 0.023) + ((gb-50000)*0.022)
    else:
        return (50000 * 0.023) + (450000*0.022) + ((gb- 500000) *0.021)


@app.callback(
    Output('plot', 'figure'),
    [Input(component_id='volumes-genome-count', component_property='value'),
     Input(component_id='volumes-exome-count', component_property='value'),
     Input(component_id='volumes-panel-count', component_property='value'),
     Input(component_id='volumes-genome-size', component_property='value'),
     Input(component_id='volumes-exome-size', component_property='value'),
     Input(component_id='volumes-panel-size', component_property='value'),
     Input(component_id='retention-years-tier1', component_property='value'),
     Input(component_id='retention-years-tier2', component_property='value'),
     Input(component_id='volume-growth', component_property='value'),
     Input(component_id='reaccess-count', component_property='value')]
)

def update_plot(genome_count, exome_count, panel_count,
                genome_size, exome_size, panel_size, 
                retention_years_tier1, retention_years_tier2,
                volume_growth, reaccess_count):
    total_gb = (genome_count * genome_size) + (exome_count * exome_size) + (panel_count * panel_size)
    volume_multiplier = (1 + float(volume_growth/100))
    year_range = list(range(0,max(retention_years_tier1, retention_years_tier1+retention_years_tier2, 20)))

    yearly_costs = []
    yearly_total_stored = []
    running_total_s3 = 0
    running_total_glacier = 0

    for y in year_range:
        total_gb = total_gb * volume_multiplier
        s3_cost      = marginal_s3_cost(12 * running_total_s3)
        glacier_cost = 0.004 * 12 * running_total_glacier

        if y < retention_years_tier1:
            running_total_s3 += total_gb
        elif y < retention_years_tier1 + retention_years_tier2:
            running_total_glacier += total_gb
        else:
            running_total_glacier *= volume_multiplier
        
        if (running_total_s3 + running_total_glacier) > 0:
            fraction_in_glacier = running_total_glacier / float(running_total_s3 + running_total_glacier)
            mean = np.mean(genome_count * [genome_size] + exome_count * [exome_size] + panel_count * [panel_size])
            glacier_retrieval_cost = (fraction_in_glacier * reaccess_count * mean * 0.03) + (reaccess_count * 0.01)
        else:
            glacier_retrieval_cost = 0
        yearly_total_stored.append(running_total_s3 + running_total_glacier)

        yearly_costs.append(s3_cost + glacier_cost + glacier_retrieval_cost)

    y_max = max(500, max(yearly_costs) * 1.1)
    y_max2 = max(50, max(yearly_total_stored) * 1.8)
    if y_max2 >= 1000:
        yearly_total_stored = np.array(yearly_total_stored)/1000.
        y_max2 = y_max2 / 1000.
        units = "TB"
    else:
        units = "GB"

    traces = [

        go.Bar(
            x= year_range,
            y = yearly_total_stored,
            name="Total %s Stored" % units,
            yaxis='y2',
            opacity=0.6,
        ),
        go.Scatter(
            x = year_range,
            y = yearly_costs,
            name="Yearly Cost"
        ),
    ]
    

    return {
        'data': traces,
        'layout': go.Layout(
            margin=dict(l=70,r=130,t=10,b=30),
            height=500,
            yaxis = go.layout.YAxis(range=[0,y_max], title="Yearly Cost", tickprefix="$", fixedrange=True),
            yaxis2 = go.layout.YAxis(range=[0,y_max2], showgrid=False, title="Total %s Stored" % units, ticksuffix=units, overlaying='y', side='right', fixedrange=True),
            xaxis = go.layout.XAxis(title="Year", fixedrange=True),
            legend=dict(orientation="h"),
        )
    }