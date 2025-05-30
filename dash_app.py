from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px


def init_dash_app(server):
    dash_app = Dash(__name__, server=server, url_base_pathname='/dashboard/')
    dash_app.title = 'Payment Analytics'

    # Load data
    def load_data():
        try:
            # Load the CSV file
            df = pd.read_csv("data/Payment_details.csv")

            # Verify column names
            required_columns = [
                'Facility Name', 'Payment Entered', 'Payment Received',
                'Credit Source(w Payer)', 'Payment Total Paid (Sum)'
            ]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Missing required columns in CSV file: {missing_columns}")

            # Convert date columns
            df['Payment Received'] = pd.to_datetime(df['Payment Received'], errors='coerce')
            df['Year-Month'] = df['Payment Received'].dt.to_period('M').astype(str)

            # Clean payment amounts (remove dollar signs and commas)
            df['Payment Total Paid (Sum)'] = (
                df['Payment Total Paid (Sum)'].astype(str)
                .str.replace('[\$,]', '', regex=True)
                .pipe(pd.to_numeric, errors='coerce')
            )

            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()  # Return an empty DataFrame if there's an error

    df = load_data()

    # If data loading failed, show an error message
    if df.empty:
        dash_app.layout = html.Div([
            html.H1("Payment Analytics Dashboard", style={'textAlign': 'center'}),
            html.Div("Error: Unable to load data. Please check the CSV file.", style={'color': 'red'})
        ])
        return dash_app

    # Dash layout for successful data loading
    dash_app.layout = html.Div([
        html.H1("Payment Analytics Dashboard", style={'textAlign': 'center'}),

        # Filters
        html.Div([
            dcc.Dropdown(
                id='facility-filter',
                options=[{'label': fac, 'value': fac} for fac in df['Facility Name'].unique()],
                multi=True,
                placeholder="Select Facility(s)"
            ),
            dcc.Dropdown(
                id='payer-filter',
                options=[{'label': payer, 'value': payer} for payer in df['Credit Source(w Payer)'].unique()],
                multi=True,
                placeholder="Select Payer(s)"
            ),
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=df['Payment Received'].min(),
                max_date_allowed=df['Payment Received'].max(),
                start_date=df['Payment Received'].min(),
                end_date=df['Payment Received'].max()
            )
        ], style={'padding': '20px'}),

        # Graphs
        dcc.Graph(id='monthly-trend'),
        dcc.Graph(id='payer-distribution'),
        dcc.Graph(id='payment-distribution'),
        dcc.Graph(id='payer-contribution'),
        dcc.Graph(id='top-facilities'),
        dcc.Graph(id='top-payers'),
        dcc.Graph(id='monthly-growth-rate'),
        dcc.Graph(id='facility-payer-trend')
    ])

    # Callbacks
    @dash_app.callback(
        [Output('monthly-trend', 'figure'),
         Output('payer-distribution', 'figure'),
         Output('payment-distribution', 'figure'),
         Output('payer-contribution', 'figure'),
         Output('top-facilities', 'figure'),
         Output('top-payers', 'figure'),
         Output('monthly-growth-rate', 'figure'),
         Output('facility-payer-trend', 'figure')],
        [Input('facility-filter', 'value'),
         Input('payer-filter', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date')]
    )
    def update_graphs(selected_facilities, selected_payers, start_date, end_date):
        filtered_df = df[
            (df['Payment Received'] >= start_date) &
            (df['Payment Received'] <= end_date)
            ]

        if selected_facilities:
            filtered_df = filtered_df[filtered_df['Facility Name'].isin(selected_facilities)]
        if selected_payers:
            filtered_df = filtered_df[filtered_df['Credit Source(w Payer)'].isin(selected_payers)]

        # 1. Monthly Payment Trend by Facility
        monthly_fig = px.line(
            filtered_df.groupby(['Year-Month', 'Facility Name'], as_index=False)['Payment Total Paid (Sum)'].sum(),
            x='Year-Month',
            y='Payment Total Paid (Sum)',
            color='Facility Name',
            title='Monthly Payment Trend by Facility'
        )

        # 2. Top 10 Payers by Total Payments
        payer_fig = px.bar(
            filtered_df.groupby('Credit Source(w Payer)', as_index=False)['Payment Total Paid (Sum)'].sum().nlargest(10,
                                                                                                                     'Payment Total Paid (Sum)'),
            x='Credit Source(w Payer)',
            y='Payment Total Paid (Sum)',
            title='Top 10 Payers by Total Payments'
        )

        # 3. Payment Distribution Across Facilities (Box Plot)
        payment_dist_fig = px.box(
            filtered_df,
            x='Facility Name',
            y='Payment Total Paid (Sum)',
            title='Payment Distribution Across Facilities'
        )

        # 4. Payer Contribution Distribution (Pie Chart)
        payer_contrib_fig = px.pie(
            filtered_df.groupby('Credit Source(w Payer)', as_index=False)['Payment Total Paid (Sum)'].sum(),
            names='Credit Source(w Payer)',
            values='Payment Total Paid (Sum)',
            title='Payer Contribution Distribution'
        )

        # 5. Top 5 Facilities by Total Payments
        top_facilities_fig = px.bar(
            filtered_df.groupby('Facility Name', as_index=False)['Payment Total Paid (Sum)'].sum().nlargest(5,
                                                                                                            'Payment Total Paid (Sum)'),
            x='Facility Name',
            y='Payment Total Paid (Sum)',
            title='Top 5 Facilities by Total Payments'
        )

        # 6. Top 5 Payers by Total Payments
        top_payers_fig = px.bar(
            filtered_df.groupby('Credit Source(w Payer)', as_index=False)['Payment Total Paid (Sum)'].sum().nlargest(5,
                                                                                                                     'Payment Total Paid (Sum)'),
            x='Credit Source(w Payer)',
            y='Payment Total Paid (Sum)',
            title='Top 5 Payers by Total Payments'
        )

        # 7. Monthly Growth Rate of Payments
        monthly_growth = filtered_df.groupby('Year-Month', as_index=False)['Payment Total Paid (Sum)'].sum()
        monthly_growth['Growth Rate'] = monthly_growth['Payment Total Paid (Sum)'].pct_change() * 100
        monthly_growth_fig = px.line(
            monthly_growth,
            x='Year-Month',
            y='Growth Rate',
            title='Monthly Growth Rate of Payments (%)',
            markers=True
        )

        # 8. Payment Trends by Facility and Payer (Stacked Bar Chart)
        facility_payer_fig = px.bar(
            filtered_df.groupby(['Facility Name', 'Credit Source(w Payer)'], as_index=False)[
                'Payment Total Paid (Sum)'].sum(),
            x='Facility Name',
            y='Payment Total Paid (Sum)',
            color='Credit Source(w Payer)',
            title='Payment Trends by Facility and Payer',
            barmode='stack'
        )

        return (
            monthly_fig, payer_fig, payment_dist_fig, payer_contrib_fig,
            top_facilities_fig, top_payers_fig, monthly_growth_fig, facility_payer_fig
        )

    return dash_app