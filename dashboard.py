import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Indian Startup Funding Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
  .stApp {
      background: linear-gradient(135deg, #fffaf3 0%, #f5e6ca 100%);
      font-family: 'Poppins', sans-serif;
      color: #3b2f2f;
  }
  h1, h2, h3, h4 { color: #4b3621; font-weight: 600; }
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #f3e5ab 0%, #e8d4a2 100%);
      border-right: 1px solid #d2b48c;
  }
  .metric-container {
      background: #ffffffd9; border-radius: 15px;
      box-shadow: 0 4px 15px rgba(90, 64, 35, 0.15);
      padding: 25px; text-align: center;
      transition: all 0.3s ease;
  }
  .metric-container:hover { transform: translateY(-6px); }
  footer { text-align:center; padding:10px; font-size:14px; color:#5a3e1b; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    try:
        data = pd.read_csv("merged.csv.csv", encoding="ISO-8859-1", header=4)
    except Exception as e:
        st.error(f"⚠ Couldn't load 'merged.csv.csv'. {e}")
        return pd.DataFrame()

    try:
        df = data.iloc[:, [13, 14, 15, 17, 19, 20]].copy()
        df.columns = ['Date', 'Startup Name', 'Sector', 'City', 'Investment Type', 'Amount']
    except Exception as e:
        st.error(f"Column mismatch. Please check your CSV format. {e}")
        return pd.DataFrame()

    # Clean amount
    def clean_amount(x):
        if isinstance(x, str):
            x = x.replace(',', '').replace('$', '').strip().lower()
            if any(u in x for u in ['lac', 'lakh', 'cr', 'unknown', 'n/a']):
                return np.nan
        try:
            return float(x) / 1_000_000
        except:
            return np.nan

    df['Amount'] = df['Amount'].apply(clean_amount)
    df.dropna(subset=['Amount'], inplace=True)
    df = df[df['Amount'] > 0]

    # Parse date
    def clean_date(d):
        try:
            return datetime.strptime(str(d).strip(), '%d/%m/%Y')
        except:
            return pd.NaT

    df['Date'] = df['Date'].apply(clean_date)
    df.dropna(subset=['Date'], inplace=True)
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    # Clean text
    for col in ['Sector', 'City', 'Investment Type', 'Startup Name']:
        df[col] = (
            df[col].astype(str).str.strip().str.title()
              .replace({'Nan': 'Other', 'N/A': 'Other'})
        )
    df['City'] = df['City'].replace({
        'Bengaluru': 'Bangalore',
        'New Delhi': 'Delhi',
        'Gurugram': 'Gurgaon',
        'Hydrabad': 'Hyderabad'
    })
    df['Investment Type'] = df['Investment Type'].replace({'Seed/ Angel Funding': 'Seed/Angel Funding'})
    df = df[df['Amount'] < 1000]
    return df

# --- KPI SECTION ---
def display_kpis(df):
    total_funding = df['Amount'].sum()
    total_startups = df['Startup Name'].nunique()
    avg_funding = df['Amount'].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div class='metric-container'><h3>💰 Total Funding</h3><h2>{total_funding:,.2f} M USD</h2></div>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<div class='metric-container'><h3>🚀 Total Startups</h3><h2>{total_startups:,}</h2></div>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"<div class='metric-container'><h3>📈 Avg. Investment</h3><h2>{avg_funding:,.2f} M USD</h2></div>",
            unsafe_allow_html=True
        )

# --- FUNDING TREND (LINE CHART) ---
def plot_funding_trend(df):
    st.subheader("📊 Funding Trend Over Time")

    df['Month_dt'] = pd.to_datetime(df['Month'], errors='coerce')
    time_df = df.groupby('Month_dt', as_index=False)['Amount'].sum()

    fig = px.line(time_df, x='Month_dt', y='Amount', markers=True, template='plotly_white')
    fig.update_traces(
        line=dict(color='#8B4513', width=3, shape='spline'),
        marker=dict(size=8, color='#D2B48C', line=dict(width=1.5, color='#4B3621'))
    )
    fig.update_layout(
        plot_bgcolor="#fffaf3",
        paper_bgcolor="#fffaf3",
        font=dict(color='black', family='Poppins'),
        hovermode="x unified",
        xaxis=dict(
            title=dict(text="Month", font=dict(size=14, color='black', family='Poppins', weight='bold')),
            tickformat="%b\n%Y",
            showline=True,
            linecolor='black',
            mirror=True,
            ticks='outside',
            tickfont=dict(color='black', size=12, family='Poppins'),
            showgrid=True,
            gridcolor="#d2b48c"
        ),
        yaxis=dict(
            title=dict(text="Funding (M USD)", font=dict(size=14, color='black', family='Poppins', weight='bold')),
            showline=True,
            linecolor='black',
            mirror=True,
            ticks='outside',
            tickfont=dict(color='black', size=12, family='Poppins'),
            showgrid=True,
            gridcolor="#d2b48c"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# --- TOP CITIES (BAR CHART) ---
def plot_top_cities(df):
    st.subheader("🏙 Top 10 Cities by Deal Count")
    city_df = df['City'].value_counts().nlargest(10).reset_index()
    city_df.columns = ['City', 'Deal Count']

    fig = px.bar(
        city_df, x='City', y='Deal Count', text='Deal Count',
        template='plotly_white', color='Deal Count',
        color_continuous_scale=['#F4E1B5', '#C19A6B', '#8B4513']
    )
    fig.update_traces(texttemplate="<b>%{text}</b>", textposition='outside', marker_line_color='#4B3621')
    fig.update_layout(
        plot_bgcolor="#fffaf3",
        paper_bgcolor="#fffaf3",
        font=dict(color='black', family='Poppins'),
        coloraxis_showscale=False,
        xaxis=dict(
            title=dict(text="City", font=dict(size=14, color='black', family='Poppins', weight='bold')),
            tickangle=-25,
            tickfont=dict(color='black', size=12),
            showline=True,
            linecolor='black'
        ),
        yaxis=dict(
            title=dict(text="Deal Count", font=dict(size=14, color='black', family='Poppins', weight='bold')),
            tickfont=dict(color='black', size=12),
            showline=True,
            linecolor='black',
            gridcolor="#d2b48c"
        )
    )
    st.plotly_chart(fig, use_container_width=True)

# --- INVESTMENT TYPE (PIE CHART) ---
def plot_investment_pie(df):
    st.subheader("🥧 Funding Distribution by Investment Type")
    pie_df = df.groupby('Investment Type')['Amount'].sum().reset_index().sort_values('Amount', ascending=False)

    fig = px.pie(
        pie_df, names='Investment Type', values='Amount',
        color_discrete_sequence=['#8B4513', '#C19A6B', '#D2B48C', '#F4E1B5', '#E8D4A2']
    )
    fig.update_traces(
        textinfo='percent+label',
        pull=[0.05]*len(pie_df),
        hovertemplate="<b>%{label}</b><br>Funding: %{value:.2f} M USD"
    )
    fig.update_layout(
        paper_bgcolor='#fffaf3',
        font=dict(color='black', family='Poppins'),
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

# --- MAIN APP ---
def main():
    # Clean, minimal title
    st.markdown(
        "<h1 style='text-align: center; color: #3b2f2f; font-family: Poppins;'>Indian Startup Funding Dashboard</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='text-align: center; font-size:18px;color:#3b2f2f;font-family:Poppins;'>Gain insights into India's startup ecosystem with funding trends, top cities, and investment patterns.</div>",
        unsafe_allow_html=True
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        return

    # Sidebar filters
    st.sidebar.header("🎛 Filter Data")
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.sidebar.slider("📅 Year Range", min_value=min_year, max_value=max_year, value=(min_year, max_year))
    all_cities = sorted(df['City'].unique().tolist())
    selected_cities = st.sidebar.multiselect("📍 Select Cities", options=all_cities, default=['Bangalore', 'Mumbai', 'Delhi'])
    min_amt, max_amt = float(df['Amount'].min()), float(df['Amount'].max())
    funding_range = st.sidebar.slider("💸 Funding Amount (M USD)", min_value=min_amt, max_value=max_amt, value=(min_amt, max_amt))

    filtered_df = df[
        (df['Year'] >= year_range[0]) &
        (df['Year'] <= year_range[1]) &
        (df['City'].isin(selected_cities)) &
        (df['Amount'].between(funding_range[0], funding_range[1]))
    ]

    st.markdown(f"<h3 style='color:#3b2f2f;'>Showing results for {filtered_df['Startup Name'].nunique():,} startups.</h3>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("⚠ No data matches your filters.")
        return

    display_kpis(filtered_df)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Charts
    plot_funding_trend(filtered_df)
    st.markdown("<hr>", unsafe_allow_html=True)
    plot_top_cities(filtered_df)
    st.markdown("<hr>", unsafe_allow_html=True)
    plot_investment_pie(filtered_df)

    st.markdown("<hr><footer>© 2025 | Crafted using Streamlit & Plotly</footer>", unsafe_allow_html=True)

if _name_ == "_main_":
    main()
