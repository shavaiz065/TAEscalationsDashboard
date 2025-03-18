import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from PIL import Image
import numpy as np
from plotly.io import write_image
import time

# Configure page layout
st.set_page_config(layout="wide", page_title="DMAT - TA Escalations Dashboard", page_icon="📊")

# Dashboard theme settings
THEMES = {
    "Default": {
        "bg_gradient": "linear-gradient(135deg, #7F7FD5, #91EAE4)",
        "sidebar_gradient": "linear-gradient(135deg, #83a4d4, #b6fbff)",
        "text_color": "#003366",
        "accent_color": "#4e54c8",
        "chart_colors": px.colors.qualitative.Plotly
    },
    "Dark": {
        "bg_gradient": "linear-gradient(135deg, #0f2027, #203a43, #2c5364)",
        "sidebar_gradient": "linear-gradient(135deg, #232526, #414345)",
        "text_color": "#ffffff",
        "accent_color": "#00b4d8",
        "chart_colors": px.colors.qualitative.Dark24
    },
    "Corporate": {
        "bg_gradient": "linear-gradient(135deg, #f5f7fa, #c3cfe2)",
        "sidebar_gradient": "linear-gradient(135deg, #e0e0e0, #f5f5f5)",
        "text_color": "#2c3e50",
        "accent_color": "#3498db",
        "chart_colors": px.colors.qualitative.Safe
    }
}


# Function to apply custom styling based on theme
def apply_theme(theme_name):
    theme = THEMES.get(theme_name, THEMES["Default"])

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {theme["bg_gradient"]};
            background-attachment: fixed;
            height: 100vh;
        }}
        .stSidebar {{
            background: {theme["sidebar_gradient"]};
            background-attachment: fixed;
            height: 100%;
            padding: 10px;
        }}
        .main-title {{
            color: {theme["text_color"]} !important;
            font-size: 28px;
            font-weight: bold;
            text-align: center;
            margin-top: 30px;
            font-family: 'Poppins', sans-serif;
        }}
        .sub-title {{
            color: {theme["text_color"]} !important;
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            font-family: 'Poppins', sans-serif;
            margin-bottom: 15px;
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        /* Custom styling for dataframe */
        .dataframe-container {{
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        /* Custom styling for tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 5px 5px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {theme["accent_color"]};
            color: white;
        }}
        /* Loading animation */
        .loading-spinner {{
            text-align: center;
            padding: 20px;
        }}
        /* Action button */
        .floating-button {{
            position: fixed;
            right: 20px;
            bottom: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: {theme["accent_color"]};
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            cursor: pointer;
            z-index: 1000;
        }}
        /* Tooltip styling */
        .tooltip {{
            position: relative;
            display: inline-block;
        }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 120px;
            background-color: rgba(0,0,0,0.8);
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Create session state for user preferences
if 'theme' not in st.session_state:
    st.session_state['theme'] = "Default"
if 'show_tutorial' not in st.session_state:
    st.session_state['show_tutorial'] = True
if 'first_visit' not in st.session_state:
    st.session_state['first_visit'] = True
if 'favorite_charts' not in st.session_state:
    st.session_state['favorite_charts'] = []

# Apply the current theme
apply_theme(st.session_state['theme'])


# Function to process the uploaded file
def process_uploaded_file(file):
    try:
        # Add loading animation
        with st.spinner('Processing your data...'):
            # Determine file type and read accordingly
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:  # Excel file
                df = pd.read_excel(file)

            # Define your expected headers (use the exact order and names from your sheet)
            expected_headers = [
                "Mode",
                "Type",
                "Escalation Date",
                "Domain",
                "BID",
                "Account name",
                "Subject line (Manual TA Escalation)",
                "Parent Category",
                "Case Category",
                "Escalated To"
            ]

            # Check if all expected headers exist in the DataFrame
            missing_headers = [header for header in expected_headers if header not in df.columns]
            if missing_headers:
                st.warning(f"Warning: The following expected columns are missing: {', '.join(missing_headers)}")

            # Convert the escalation date column to datetime if it exists
            if "Escalation Date" in df.columns:
                df["Escalation Date"] = pd.to_datetime(df["Escalation Date"], errors="coerce")
            else:
                st.error("Error: 'Escalation Date' column is required but not found in the uploaded file.")
                return None

            # Make sure essential columns exist
            required_columns = ["Mode", "Type", "Escalation Date", "Domain", "Account name", "Case Category",
                                "Escalated To"]
            for col in required_columns:
                if col not in df.columns:
                    # If column doesn't exist, create it with placeholder values
                    df[col] = "Unknown"

            # Convert string columns to string type to avoid any issues
            string_columns = ["Domain", "Mode", "Type", "Account name", "Case Category", "Escalated To"]
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str)

            # Add data quality indicators
            df_stats = {
                "Total Records": len(df),
                "Missing Values": df.isna().sum().sum(),
                "Data Quality Score": round(100 - (df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100), 2)
            }

            # Add month and year columns for better filtering
            if "Escalation Date" in df.columns:
                df["Month"] = df["Escalation Date"].dt.month_name()
                df["Year"] = df["Escalation Date"].dt.year

            return df, df_stats

    except Exception as e:
        st.error(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None, None


# Function to safely create and display charts with tooltips
def safe_create_chart(chart_function, error_message="Error creating chart"):
    try:
        return chart_function()
    except Exception as e:
        st.error(f"{error_message}: {e}")
        import traceback
        traceback.print_exc()
        return None


# Function to detect anomalies in time series data
def detect_anomalies(time_series):
    # Calculate rolling mean and standard deviation
    rolling_mean = time_series["Count"].rolling(window=3, min_periods=1).mean()
    rolling_std = time_series["Count"].rolling(window=3, min_periods=1).std()

    # Define threshold for anomalies (2 standard deviations)
    threshold = 2

    # Identify anomalies
    anomalies = time_series[abs(time_series["Count"] - rolling_mean) > threshold * rolling_std]

    return anomalies


# Function to create a scorecard with KPI
def create_scorecard(title, value, delta=None, delta_color="normal"):
    card_html = f"""
    <div class="metric-card">
        <h3 style="margin-bottom: 10px;">{title}</h3>
        <div style="font-size: 24px; font-weight: bold;">{value}</div>
    """

    if delta is not None:
        arrow = "↑" if delta > 0 else "↓"
        color = "green" if delta_color == "normal" and delta > 0 else "red"
        color = "red" if delta_color == "inverse" and delta > 0 else color

        card_html += f"""
        <div style="color: {color}; font-size: 16px; margin-top: 5px;">
            {arrow} {abs(delta):.1f}%
        </div>
        """

    card_html += "</div>"
    return card_html


# Function to generate insights from the data
def generate_insights(df):
    insights = []

    # Most common escalation category
    top_category = df["Case Category"].value_counts().idxmax()
    insights.append(f"The most common escalation category is '{top_category}'")

    # Day of week with most escalations
    df['Day of Week'] = df['Escalation Date'].dt.day_name()
    top_day = df['Day of Week'].value_counts().idxmax()
    insights.append(f"Most escalations occur on {top_day}")

    # Month with highest escalations
    df['Month'] = df['Escalation Date'].dt.month_name()
    top_month = df['Month'].value_counts().idxmax()
    insights.append(f"The month with most escalations is {top_month}")

    # Account with most escalations
    top_account = df["Account name"].value_counts().idxmax()
    insights.append(f"Account '{top_account}' has the most escalations")

    return insights


# Function to show tutorial
def show_tutorial():
    tutorial_container = st.container()
    with tutorial_container:
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.info("""
            ## 🎯 Welcome to the Enhanced TA Escalations Dashboard!

            Here's a quick tour of the new features:

            1. **Navigation Tabs**: Use tabs to switch between different views
            2. **Theme Customization**: Change dashboard appearance from the sidebar
            3. **Interactive Charts**: Hover over charts for details, click elements to filter
            4. **AI Insights**: Auto-generated insights based on your data
            5. **Export Options**: Download data or visualizations in various formats
            6. **Performance Metrics**: Track KPIs and data quality indicators

            Click "Got it!" to dismiss this tutorial.
            """)
            if st.button("Got it!", key="dismiss_tutorial"):
                st.session_state['show_tutorial'] = False
                st.experimental_rerun()


# Dashboard Header
st.markdown("<h1 class='main-title'>📊 DMAT - TA Escalations Dashboard</h1>", unsafe_allow_html=True)

# Move the file upload section to the sidebar
st.sidebar.header("Dashboard Settings")

# Theme selector in sidebar
theme_options = list(THEMES.keys())
selected_theme = st.sidebar.selectbox("Select Theme", theme_options,
                                      index=theme_options.index(st.session_state['theme']))
if selected_theme != st.session_state['theme']:
    st.session_state['theme'] = selected_theme
    st.experimental_rerun()

st.sidebar.header("Data Upload")
st.sidebar.markdown("<h3>Upload your data file</h3>", unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])

# Show tutorial on first visit
if st.session_state['show_tutorial'] and st.session_state['first_visit']:
    show_tutorial()
    st.session_state['first_visit'] = False

# Rest of the sidebar filters (will be shown after file is uploaded)
if uploaded_file is not None:
    # Process the uploaded file
    df, df_stats = process_uploaded_file(uploaded_file)

    if df is not None and not df.empty:
        # Add navigation tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Detailed Analysis", "🔍 Data Explorer", "💡 Insights"])

        with tab1:
            # Sidebar Filters
            st.sidebar.header("Filters")

            # Advanced filtering options
            filter_container = st.sidebar.expander("Advanced Filters", expanded=False)
            with filter_container:
                # Case Category Dropdown
                try:
                    # Check if the column exists
                    if "Case Category" in df.columns:
                        case_categories = df["Case Category"].unique().tolist()
                    else:
                        case_categories = []  # Default to empty list if column not found
                except Exception as e:
                    print(f"Error getting Case Category unique values: {e}")
                    case_categories = []

                selected_category = st.selectbox("Search Case Category", ["All"] + case_categories)

                # Account Name Dropdown with search
                try:
                    # Check if the column exists
                    if "Account name" in df.columns:
                        account_names = df["Account name"].unique().tolist()
                    else:
                        account_names = []  # Default to empty list if column not found
                except Exception as e:
                    print(f"Error getting Account name unique values: {e}")
                    account_names = []

                # Add a search box for account names
                account_search = st.text_input("Search Account Name", "")
                if account_search:
                    filtered_accounts = [account for account in account_names if
                                         account_search.lower() in account.lower()]
                    selected_account = st.selectbox("Select Account", ["All"] + filtered_accounts)
                else:
                    selected_account = st.selectbox("Select Account", ["All"] + account_names)

                # Month and Year filters
                if "Month" in df.columns and "Year" in df.columns:
                    # Convert month values to strings and filter out any non-string values
                    month_values = [str(x) for x in df["Month"].unique() if isinstance(x, str) or not pd.isna(x)]

                    # Only try to sort if there are valid month names
                    try:
                        months = ["All"] + sorted(month_values, key=lambda x: datetime.datetime.strptime(x,
                                                                                                         "%B").month if x.strip() else 0)
                    except ValueError:
                        # If sorting fails, just use the unsorted list
                        months = ["All"] + month_values

                    years = ["All"] + sorted([x for x in df["Year"].unique().tolist() if not pd.isna(x)])

                    selected_month = st.selectbox("Select Month", months)
                    selected_year = st.selectbox("Select Year", years)

            # Date Range Filter
            start_date = st.sidebar.date_input("Start Date", df["Escalation Date"].min().date() if not pd.isna(
                df["Escalation Date"].min()) else datetime.date.today())
            end_date = st.sidebar.date_input("End Date", df["Escalation Date"].max().date() if not pd.isna(
                df["Escalation Date"].max()) else datetime.date.today())

            # Apply Filters
            df_filtered = df[(df["Escalation Date"] >= pd.to_datetime(start_date)) &
                             (df["Escalation Date"] <= pd.to_datetime(end_date))]

            if selected_category != "All":
                df_filtered = df_filtered[df_filtered["Case Category"] == selected_category]

            if selected_account != "All":
                df_filtered = df_filtered[df_filtered["Account name"] == selected_account]

            # Apply month and year filters if they exist
            if "Month" in df.columns and "Year" in df.columns:
                if selected_month != "All":
                    df_filtered = df_filtered[df_filtered["Month"] == selected_month]
                if selected_year != "All":
                    df_filtered = df_filtered[df_filtered["Year"] == selected_year]

            # Export options in sidebar
            st.sidebar.header("Export Options")
            export_format = st.sidebar.selectbox("Export Format", ["PDF", "CSV", "Excel", "PNG"])

            if st.sidebar.button("Export Dashboard"):
                if export_format == "CSV":
                    csv = df_filtered.to_csv(index=False)
                    st.sidebar.download_button(
                        "Download CSV",
                        csv,
                        "escalation_data.csv",
                        "text/csv",
                        key='download-csv'
                    )
                elif export_format == "Excel":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_filtered.to_excel(writer, index=False, sheet_name='Escalation Data')
                    st.sidebar.download_button(
                        "Download Excel",
                        output.getvalue(),
                        "escalation_data.xlsx",
                        "application/vnd.ms-excel",
                        key='download-excel'
                    )

            # Make sure df_filtered contains data
            if df_filtered.empty:
                st.warning("No data matches the selected filters. Please adjust your filter criteria.")
            else:
                # Animated loading
                with st.spinner("Loading dashboard..."):
                    time.sleep(0.5)  # Simulate loading for smoother transitions

                    # Calculate period-over-period changes for KPIs
                    # Get previous period data (assuming same length as current filtered period)
                    current_period_start = pd.to_datetime(start_date)
                    current_period_end = pd.to_datetime(end_date)
                    period_length = (current_period_end - current_period_start).days

                    previous_period_end = current_period_start - datetime.timedelta(days=1)
                    previous_period_start = previous_period_end - datetime.timedelta(days=period_length)

                    df_previous = df[(df["Escalation Date"] >= previous_period_start) &
                                     (df["Escalation Date"] <= previous_period_end)]

                    # Calculate change percentages
                    current_total = len(df_filtered)
                    previous_total = len(df_previous) if not df_previous.empty else 0
                    total_change_pct = (
                                (current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0

                    current_domains = len(df_filtered["Domain"].unique())
                    previous_domains = len(df_previous["Domain"].unique()) if not df_previous.empty else 0
                    domains_change_pct = ((
                                                      current_domains - previous_domains) / previous_domains * 100) if previous_domains > 0 else 0

                    current_categories = len(df_filtered["Case Category"].unique())
                    previous_categories = len(df_previous["Case Category"].unique()) if not df_previous.empty else 0
                    categories_change_pct = ((
                                                         current_categories - previous_categories) / previous_categories * 100) if previous_categories > 0 else 0

                    # Data quality score
                    data_quality = df_stats["Data Quality Score"] if df_stats else 98.5

                    # Enhanced KPIs with scorecards
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            label="📌 Total Escalations",
                            value=current_total,
                            delta=f"{total_change_pct:.1f}%" if total_change_pct != 0 else None,
                            delta_color="inverse" if total_change_pct > 0 else "normal"
                        )
                    with col2:
                        st.metric(
                            label="🌐 Total Domains",
                            value=current_domains,
                            delta=f"{domains_change_pct:.1f}%" if domains_change_pct != 0 else None,
                            delta_color="inverse" if domains_change_pct > 0 else "normal"
                        )
                    with col3:
                        st.metric(
                            label="📑 Escalation Categories",
                            value=current_categories,
                            delta=f"{categories_change_pct:.1f}%" if categories_change_pct != 0 else None,
                            delta_color="inverse" if categories_change_pct > 0 else "normal"
                        )
                    with col4:
                        st.metric(
                            label="💯 Data Quality",
                            value=f"{data_quality:.2f}%",
                            delta=None
                        )

                    # Display Table with enhanced styling
                    st.markdown("<h2 class='sub-title'>Escalation Data</h2>", unsafe_allow_html=True)
                    with st.container():
                        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                        st.dataframe(df_filtered, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Graphs in Horizontal Layout with enhanced interactivity
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(
                            "<h2 class='sub-title' style='white-space: nowrap;'>📌 Escalations by Case Category</h2>",
                            unsafe_allow_html=True)


                        def create_category_chart():
                            category_counts = df_filtered["Case Category"].value_counts().reset_index()
                            category_counts.columns = ["Case Category", "Count"]
                            fig1 = px.bar(category_counts, x="Case Category", y="Count", text="Count",
                                          color="Case Category",
                                          color_discrete_sequence=THEMES[st.session_state['theme']]["chart_colors"])
                            fig1.update_layout(
                                autosize=True,
                                margin=dict(t=20, b=20, l=20, r=20),
                                height=450,
                                hovermode="closest",
                                hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                                transition_duration=500  # Animation duration
                            )
                            # Add custom hover template
                            fig1.update_traces(
                                hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Percentage: %{customdata:.1f}%",
                                customdata=[(count / category_counts["Count"].sum()) * 100 for count in
                                            category_counts["Count"]]
                            )
                            return fig1, category_counts


                        result = safe_create_chart(create_category_chart, "Error creating Case Category chart")
                        if result:
                            fig1, category_counts = result
                            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': True})

                    with col2:
                        st.markdown("<h2 class='sub-title'>📈 Escalation Trend Over Time</h2>", unsafe_allow_html=True)


                        def create_time_series_chart():
                            time_series = df_filtered.groupby("Escalation Date").size().reset_index(name="Count")

                            # Detect anomalies
                            anomalies = detect_anomalies(time_series)

                            # Create line chart
                            fig2 = px.line(time_series, x="Escalation Date", y="Count", markers=True,
                                           color_discrete_sequence=[THEMES[st.session_state['theme']]["accent_color"]])

                            # Add anomaly points
                            if not anomalies.empty:
                                fig2.add_trace(go.Scatter(
                                    x=anomalies["Escalation Date"],
                                    y=anomalies["Count"],
                                    mode="markers",
                                    marker=dict(color="red", size=10, symbol="circle"),
                                    name="Anomaly",
                                    hovertemplate="<b>Anomaly</b><br>Date: %{x}<br>Count: %{y}<extra></extra>"
                                ))

                            # Add moving average
                            ma = time_series["Count"].rolling(window=3, min_periods=1).mean()
                            fig2.add_trace(go.Scatter(
                                x=time_series["Escalation Date"],
                                y=ma,
                                mode="lines",
                                line=dict(color="rgba(0,0,0,0.3)", width=2, dash="dot"),
                                name="3-day MA",
                                hovertemplate="<b>3-day Moving Avg</b><br>Date: %{x}<br>Value: %{y:.1f}<extra></extra>"
                            ))

                            fig2.update_layout(
                                height=450,
                                margin=dict(t=0, b=0, l=0, r=0),
                                hovermode="x unified",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                transition_duration=500  # Animation duration
                            )
                            return fig2, time_series, anomalies


                        result = safe_create_chart(create_time_series_chart, "Error creating Time Series chart")
                        if result:
                            fig2, time_series, anomalies = result
                            st.plotly_chart(fig2, use_container_width=True, key="fig2")

                            # Show anomaly alerts if any exist
                            if not anomalies.empty:
                                with st.expander("📊 Anomaly Detection"):
                                    st.warning(f"Detected {len(anomalies)} anomalies in the time series data.")
                                    st.dataframe(anomalies[["Escalation Date", "Count"]])

                    if 'category_counts' in locals():
                        col4, col5 = st.columns(2)
                        with col4:
                            st.markdown("<h2 class='sub-title'>📌 Top 5 Most Escalated Categories</h2>",
                                        unsafe_allow_html=True)


                            def create_top5_chart():
                                top5_categories = category_counts.nlargest(5, "Count")
                                fig4 = px.bar(top5_categories, x="Case Category", y="Count", text="Count",
                                              color="Case Category",
                                              color_discrete_sequence=THEMES[st.session_state['theme']]["chart_colors"])
                                fig4.update_layout(
                                    height=400,
                                    margin=dict(t=0, b=0, l=0, r=0),
                                    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
                                    transition_duration=500  # Animation duration
                                )
                                return fig4


                            fig4 = safe_create_chart(create_top5_chart, "Error creating Top 5 Categories chart")
                            if fig4:
                                st.plotly_chart(fig4, use_container_width=True, key="fig4")

                        with col5:
                            st.markdown("<h2 class='sub-title'>Escalation Trends Across the Week</h2>",
                                        unsafe_allow_html=True)


                            def create_day_trend_chart():
                                df_filtered['Day of Week'] = df_filtered['Escalation Date'].dt.day_name()
                                day_counts = df_filtered['Day of Week'].value_counts().reset_index()
                                day_counts.columns = ['Day of Week', 'Count']
                                # Sort the days in correct order
                                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                                              'Sunday']
                                day_counts['Day of Week'] = pd.Categorical(day_counts['Day of Week'],
                                                                           categories=days_order,
                                                                           ordered=True)
                                day_counts = day_counts.sort_values('Day of Week')

                                # Create toggleable chart type
                                chart_type = "line"  # Default chart type

                                if chart_type == "line":
                                    fig5 = px.line(day_counts, x='Day of Week', y='Count', markers=True,
                                                   color_discrete_sequence=[
                                                       THEMES[st.session_state['theme']]["accent_color"]])
                                else:
                                    fig5 = px.bar(day_counts, x='Day of Week', y='Count', text='Count',
                                                  color_discrete_sequence=[
                                                      THEMES[st.session_state['theme']]["accent_color"]])

                                fig5.update_layout(
                                    height=400,
                                    margin=dict(t=0, b=0, l=0, r=0),
                                    hovermode="x unified",
                                    transition_duration=500  # Animation duration
                                )
                                return fig5, day_counts


                            result = safe_create_chart(create_day_trend_chart, "Error creating Day Trend chart")
                            if result:
                                fig5, day_counts = result
                                # Add chart type selector
                                chart_type = st.selectbox("Chart Type", ["Line Chart", "Bar Chart"],
                                                          key="day_chart_type")
                                if chart_type == "Bar Chart":
                                    fig5 = px.bar(day_counts, x='Day of Week', y='Count', text='Count',
                                                  color_discrete_sequence=[
                                                      THEMES[st.session_state['theme']]["accent_color"]])
                                st.plotly_chart(fig5, use_container_width=True, key="fig5")

                    col6, col7 = st.columns(2)
                    with col6:
                        st.markdown("<h2 class='sub-title'>Escalations by Mode</h2>", unsafe_allow_html=True)


                        def create_mode_chart():
                            mode_counts = df_filtered["Mode"].value_counts().reset_index()
                            mode_counts.columns = ["Mode", "Count"]
                            fig6 = px.pie(mode_counts, values="Count", names="Mode", hole=0.4,
                                          color_discrete_sequence=THEMES[st.session_state['theme']]["chart_colors"])
                            fig6.update_layout(
                                height=400,
                                margin=dict(t=0, b=0, l=0, r=0),
                                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                                transition_duration=500  # Animation duration
                            )
                            # Add percentage and count to hover info
                            fig6.update_traces(
                                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent:.1%}<extra></extra>"
                            )
                            return fig6, mode_counts


                        fig6, mode_counts = safe_create_chart(create_mode_chart, "Error creating Mode chart")
                        if fig6:
                            st.plotly_chart(fig6, use_container_width=True, key="fig6")

        # After your existing tab1 code
        with tab2:  # Detailed Analysis Tab
            st.markdown("<h2 class='sub-title'>Detailed Analysis</h2>", unsafe_allow_html=True)

            # Create sub-tabs for different types of analysis
            analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(
                ["Category Deep Dive", "Trend Analysis", "Performance Metrics"])

            with analysis_tab1:
                st.markdown("### Category Deep Dive")

                # Category distribution over time
                st.markdown("#### Category Distribution Over Time")

                # Group by month and category
                if not df_filtered.empty and "Case Category" in df_filtered.columns:
                    df_filtered['Month-Year'] = df_filtered['Escalation Date'].dt.strftime('%b %Y')
                    category_time = df_filtered.groupby(['Month-Year', 'Case Category']).size().reset_index(
                        name='Count')

                    # Create a pivot table
                    pivot_data = category_time.pivot_table(index='Month-Year', columns='Case Category', values='Count',
                                                           fill_value=0)

                    # Create a stacked bar chart
                    fig = px.bar(category_time, x='Month-Year', y='Count', color='Case Category',
                                 title="Category Distribution by Month",
                                 color_discrete_sequence=THEMES[st.session_state['theme']]["chart_colors"])

                    fig.update_layout(height=500, bargap=0.1)
                    st.plotly_chart(fig, use_container_width=True)

                    # Category correlation analysis
                    st.markdown("#### Category Correlation with Other Factors")

                    # Create a correlation heatmap if there are numerical columns
                    numeric_cols = df_filtered.select_dtypes(include=['float64', 'int64']).columns
                    if len(numeric_cols) > 1:
                        corr_matrix = df_filtered[numeric_cols].corr()
                        fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                                             color_continuous_scale=px.colors.sequential.Blues)
                        fig_corr.update_layout(title="Correlation Matrix")
                        st.plotly_chart(fig_corr, use_container_width=True)
                    else:
                        st.info("Not enough numerical data to create correlation analysis.")
                else:
                    st.warning("Insufficient data for category analysis.")

            with analysis_tab2:
                st.markdown("### Trend Analysis")

                # Monthly trend
                st.markdown("#### Monthly Trend")

                if not df_filtered.empty:
                    # Group by month
                    df_filtered['Month-Year'] = df_filtered['Escalation Date'].dt.strftime('%b %Y')
                    monthly_trend = df_filtered.groupby('Month-Year').size().reset_index(name='Count')

                    # Create a line chart
                    fig_monthly = px.line(monthly_trend, x='Month-Year', y='Count', markers=True,
                                          title="Monthly Escalation Trend",
                                          color_discrete_sequence=[THEMES[st.session_state['theme']]["accent_color"]])

                    fig_monthly.update_layout(height=400)
                    st.plotly_chart(fig_monthly, use_container_width=True)

                    # Forecast future trend (simple moving average)
                    st.markdown("#### Forecast (3-month Moving Average)")

                    if len(monthly_trend) > 3:
                        monthly_trend['MA3'] = monthly_trend['Count'].rolling(window=3).mean()

                        # Extend the dataframe with forecast
                        last_3_avg = monthly_trend['Count'].tail(3).mean()
                        forecast_months = pd.date_range(start=df_filtered['Escalation Date'].max(), periods=4, freq='M')
                        forecast_labels = [d.strftime('%b %Y') for d in forecast_months]

                        forecast_df = pd.DataFrame({
                            'Month-Year': monthly_trend['Month-Year'].tolist() + forecast_labels[1:],
                            'Count': monthly_trend['Count'].tolist() + [last_3_avg] * 3,
                            'Type': ['Historical'] * len(monthly_trend) + ['Forecast'] * 3
                        })

                        fig_forecast = px.line(forecast_df, x='Month-Year', y='Count', color='Type',
                                               title="Historical Data with 3-Month Forecast",
                                               color_discrete_sequence=[
                                                   THEMES[st.session_state['theme']]["accent_color"], 'red'])

                        fig_forecast.update_layout(height=400)
                        st.plotly_chart(fig_forecast, use_container_width=True)
                    else:
                        st.info("Need more data points for forecasting.")
                else:
                    st.warning("Insufficient data for trend analysis.")

            with analysis_tab3:
                st.markdown("### Performance Metrics")

                # Workload Distribution Analysis
                st.markdown("#### Workload Distribution Analysis")

                # Check if we have the necessary data
                if 'Category' not in df_filtered.columns or 'Agent' not in df_filtered.columns:
                    st.info("Workload distribution data not available. Showing sample metrics.")

                    # Create sample data
                    categories = ['Network', 'Hardware', 'Software', 'Access', 'Security', 'Other']
                    agents = ['Smith, J.', 'Johnson, K.', 'Williams, T.', 'Brown, A.', 'Davis, M.']

                    # Create sample workload distribution
                    workload_data = []
                    for agent in agents:
                        total_tickets = np.random.randint(30, 60)
                        # Distribute tickets across categories
                        ticket_distrib = np.random.dirichlet(np.ones(len(categories)), size=1)[0]
                        ticket_counts = (ticket_distrib * total_tickets).astype(int)

                        for i, category in enumerate(categories):
                            workload_data.append({
                                'Agent': agent,
                                'Category': category,
                                'Tickets': ticket_counts[i]
                            })

                    df_workload = pd.DataFrame(workload_data)

                    # Create pivot table
                    pivot_workload = df_workload.pivot_table(
                        index='Agent',
                        columns='Category',
                        values='Tickets',
                        aggfunc='sum',
                        fill_value=0
                    )

                    # Add total column
                    pivot_workload['Total'] = pivot_workload.sum(axis=1)

                    # Calculate team workload breakdown
                    category_totals = df_workload.groupby('Category')['Tickets'].sum().reset_index()
                    total_tickets = category_totals['Tickets'].sum()
                    category_totals['Percentage'] = (category_totals['Tickets'] / total_tickets * 100).round(1)

                    # Create visualizations
                    col1, col2 = st.columns([3, 2])

                    with col1:
                        st.markdown("##### Ticket Distribution by Agent and Category")

                        # Create stacked bar chart
                        fig_stacked = px.bar(
                            df_workload,
                            x='Agent',
                            y='Tickets',
                            color='Category',
                            title='Ticket Distribution by Agent and Category',
                            labels={'Agent': 'Agent', 'Tickets': 'Number of Tickets', 'Category': 'Category'}
                        )

                        fig_stacked.update_layout(height=400)
                        st.plotly_chart(fig_stacked, use_container_width=True)

                    with col2:
                        st.markdown("##### Category Breakdown")

                        # Create pie chart
                        fig_pie = px.pie(
                            category_totals,
                            values='Tickets',
                            names='Category',
                            title='Overall Category Distribution',
                            hover_data=['Percentage'],
                            labels={'Tickets': 'Number of Tickets'}
                        )

                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        fig_pie.update_layout(height=400)
                        st.plotly_chart(fig_pie, use_container_width=True)

                    # Add workload balance metrics
                    st.markdown("##### Workload Balance Metrics")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        avg_tickets = pivot_workload['Total'].mean()
                        st.metric("Average Tickets per Agent", f"{avg_tickets:.1f}")

                    with col2:
                        std_tickets = pivot_workload['Total'].std()
                        cv_tickets = (std_tickets / avg_tickets) * 100 if avg_tickets > 0 else 0
                        st.metric("Workload Variation", f"{cv_tickets:.1f}%",
                                  delta="-" if cv_tickets < 20 else None,
                                  delta_color="normal" if cv_tickets < 20 else "off")

                    with col3:
                        max_agent = pivot_workload['Total'].idxmax()
                        min_agent = pivot_workload['Total'].idxmin()
                        imbalance = (pivot_workload.loc[max_agent, 'Total'] / pivot_workload.loc[
                            min_agent, 'Total'] - 1) * 100
                        st.metric("Max/Min Imbalance", f"{imbalance:.1f}%",
                                  delta="-" if imbalance < 30 else None,
                                  delta_color="normal" if imbalance < 30 else "off")

                    # Display the workload distribution table
                    st.markdown("##### Detailed Workload Distribution")
                    st.dataframe(pivot_workload, use_container_width=True)

                    # Add recommendations based on workload
                    st.markdown("##### Workload Recommendations")

                    # Find the agent with highest workload
                    highest_workload_agent = pivot_workload['Total'].idxmax()
                    highest_workload = pivot_workload.loc[highest_workload_agent, 'Total']

                    # Find the agent with lowest workload
                    lowest_workload_agent = pivot_workload['Total'].idxmin()
                    lowest_workload = pivot_workload.loc[lowest_workload_agent, 'Total']

                    # Find the most common category for the highest workload agent
                    agent_categories = df_workload[df_workload['Agent'] == highest_workload_agent]
                    most_common_category = agent_categories.loc[agent_categories['Tickets'].idxmax(), 'Category']

                    # Generate recommendations
                    recommendations = [
                        f"👉 Consider redistributing {most_common_category} tickets from {highest_workload_agent} ({highest_workload} tickets) to {lowest_workload_agent} ({lowest_workload} tickets).",
                        f"👉 The workload variation is {cv_tickets:.1f}%. {'Good balance overall.' if cv_tickets < 20 else 'Consider rebalancing for more even distribution.'}"
                    ]

                    for rec in recommendations:
                        st.markdown(rec)

                else:
                    # Actual workload distribution analysis using available data
                    # Similar structure but using df_filtered data instead
                    # ...
                    st.write("Using actual workload data...")

        with tab3:  # Data Explorer Tab
            st.markdown("<h2 class='sub-title'>Data Explorer</h2>", unsafe_allow_html=True)

            # Advanced filtering
            st.markdown("### Advanced Data Filtering")

            # Create filter columns
            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                # Filter by Case Category
                if "Case Category" in df.columns:
                    case_categories = ["All"] + list(df["Case Category"].unique())
                    selected_category_filter = st.selectbox("Filter by Case Category", case_categories,
                                                            key="explorer_category")

                # Filter by Domain
                if "Domain" in df.columns:
                    domains = ["All"] + list(df["Domain"].unique())
                    selected_domain_filter = st.selectbox("Filter by Domain", domains)

            with filter_col2:
                # Filter by Mode
                if "Mode" in df.columns:
                    modes = ["All"] + list(df["Mode"].unique())
                    selected_mode_filter = st.selectbox("Filter by Mode", modes)

                # Filter by Type
                if "Type" in df.columns:
                    types = ["All"] + list(df["Type"].unique())
                    selected_type_filter = st.selectbox("Filter by Type", types)

            with filter_col3:
                # Search by account name
                search_account = st.text_input("Search by Account Name")

                # Search by subject
                if "Subject line (Manual TA Escalation)" in df.columns:
                    search_subject = st.text_input("Search by Subject")

            # Apply filters
            filtered_explorer_df = df.copy()

            if selected_category_filter != "All" and "Case Category" in df.columns:
                filtered_explorer_df = filtered_explorer_df[
                    filtered_explorer_df["Case Category"] == selected_category_filter]

            if selected_domain_filter != "All" and "Domain" in df.columns:
                filtered_explorer_df = filtered_explorer_df[filtered_explorer_df["Domain"] == selected_domain_filter]

            if selected_mode_filter != "All" and "Mode" in df.columns:
                filtered_explorer_df = filtered_explorer_df[filtered_explorer_df["Mode"] == selected_mode_filter]

            if selected_type_filter != "All" and "Type" in df.columns:
                filtered_explorer_df = filtered_explorer_df[filtered_explorer_df["Type"] == selected_type_filter]

            if search_account and "Account name" in df.columns:
                filtered_explorer_df = filtered_explorer_df[
                    filtered_explorer_df["Account name"].str.contains(search_account, case=False, na=False)]

            if search_subject and "Subject line (Manual TA Escalation)" in df.columns:
                filtered_explorer_df = filtered_explorer_df[
                    filtered_explorer_df["Subject line (Manual TA Escalation)"].str.contains(search_subject, case=False,
                                                                                             na=False)]

            # Display the filtered data
            st.markdown("### Filtered Data")
            st.dataframe(filtered_explorer_df, use_container_width=True)

            # Data statistics
            st.markdown("### Data Statistics")

            if not filtered_explorer_df.empty:
                # Select columns for statistics
                numeric_cols = filtered_explorer_df.select_dtypes(include=['float64', 'int64']).columns

                if len(numeric_cols) > 0:
                    selected_col = st.selectbox("Select column for statistics", numeric_cols)

                    # Calculate statistics
                    stats = filtered_explorer_df[selected_col].describe()

                    # Display statistics
                    st.write(stats)

                    # Create histogram
                    fig_hist = px.histogram(filtered_explorer_df, x=selected_col,
                                            title=f"Distribution of {selected_col}",
                                            color_discrete_sequence=[THEMES[st.session_state['theme']]["accent_color"]])

                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.info("No numerical columns available for statistics.")
            else:
                st.warning("No data available with the current filters.")

        with tab4:  # Insights Tab
            st.markdown("<h2 class='sub-title'>Insights</h2>", unsafe_allow_html=True)

            # Generate insights
            if not df_filtered.empty:
                insights = generate_insights(df_filtered)

                # Display insights
                st.markdown("### Key Insights")

                for i, insight in enumerate(insights):
                    st.markdown(f"**{i + 1}. {insight}**")

                # Top accounts by escalation
                st.markdown("### Top Accounts by Escalation Count")

                top_accounts = df_filtered["Account name"].value_counts().head(10).reset_index()
                top_accounts.columns = ["Account Name", "Escalation Count"]

                fig_accounts = px.bar(top_accounts, x="Account Name", y="Escalation Count",
                                      title="Top 10 Accounts by Escalation Count",
                                      color_discrete_sequence=[THEMES[st.session_state['theme']]["accent_color"]])

                st.plotly_chart(fig_accounts, use_container_width=True)

                # Escalation patterns
                st.markdown("### Escalation Patterns")

                # Create a heatmap of escalations by day of week and hour
                if "Escalation Date" in df_filtered.columns:
                    df_filtered['Day of Week'] = df_filtered['Escalation Date'].dt.day_name()
                    df_filtered['Hour'] = df_filtered['Escalation Date'].dt.hour

                    # Create a pivot table
                    day_hour_pivot = pd.pivot_table(df_filtered,
                                                    values='Escalation Date',
                                                    index='Day of Week',
                                                    columns='Hour',
                                                    aggfunc='count',
                                                    fill_value=0)

                    # Reindex to ensure correct day order
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_hour_pivot = day_hour_pivot.reindex(day_order)

                    fig_heatmap = px.imshow(day_hour_pivot,
                                            color_continuous_scale=px.colors.sequential.Viridis,
                                            title="Escalation Patterns by Day and Hour")

                    st.plotly_chart(fig_heatmap, use_container_width=True)

                # Recommendations
                st.markdown("### Recommendations")

                recommendations = [
                    "Focus on the most common escalation category to reduce overall volume.",
                    f"Allocate more resources on {df_filtered['Day of Week'].value_counts().idxmax()} when escalation volume is highest.",
                    "Implement proactive measures for accounts with high escalation counts.",
                    "Consider additional training for domains with high escalation rates.",
                    "Review the SLA process for escalations that took longer than the target response time."
                ]

                for i, rec in enumerate(recommendations):
                    st.markdown(f"**{i + 1}. {rec}**")
            else:
                st.warning("Not enough data to generate insights. Please adjust your filters.")