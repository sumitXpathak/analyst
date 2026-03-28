import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. DATA LOADING & CORE LOGIC
# ==========================================
@st.cache_data
def load_and_process_data():
    # Load the data (Make sure your CSV file is in the same folder as this script)
    # Update the filename below if yours is named differently
    df = pd.read_csv('/content/APL_Logistics (1).csv', encoding='latin1')

    # Drop rows with missing values to ensure clean math
    df = df.dropna(subset=['Days for shipping (real)', 'Days for shipment (scheduled)'])

    # Calculate Delay Gap
    df['Delay Gap'] = df['Days for shipping (real)'] - df['Days for shipment (scheduled)']

    # Classify Delivery Status
    def classify_delivery(gap):
        if gap < 0:
            return 'Early'
        elif gap == 0:
            return 'On-Time'
        else:
            return 'Delayed'

    df['Delivery Classification'] = df['Delay Gap'].apply(classify_delivery)
    return df

df = load_and_process_data()

# ==========================================
# 2. DASHBOARD UI & LAYOUT
# ==========================================
st.set_page_config(page_title="APL Logistics Dashboard", layout="wide")
st.title("📦 Delivery Performance & Delay Risk Dashboard")
st.markdown("Diagnostic intelligence for global supply chain operations.")

# --- SIDEBAR: USER CONTROLS ---
st.sidebar.header("Diagnostic Filters")
selected_mode = st.sidebar.multiselect("Shipping Mode", df['Shipping Mode'].unique(), default=df['Shipping Mode'].unique())
selected_region = st.sidebar.multiselect("Order Region", df['Order Region'].unique(), default=df['Order Region'].unique())
selected_segment = st.sidebar.multiselect("Customer Segment", df['Customer Segment'].unique(), default=df['Customer Segment'].unique())

# Apply the filters to the dataframe
filtered_df = df[
    (df['Shipping Mode'].isin(selected_mode)) &
    (df['Order Region'].isin(selected_region)) &
    (df['Customer Segment'].isin(selected_segment))
]

# ==========================================
# 3. KPI SCORECARDS
# ==========================================
st.subheader("High-Level Logistics KPIs")
col1, col2, col3, col4 = st.columns(4)

total_orders = len(filtered_df)
delayed_df = filtered_df[filtered_df['Delivery Classification'] == 'Delayed']
delayed_count = len(delayed_df)
on_time_rate = ((total_orders - delayed_count) / total_orders) * 100 if total_orders > 0 else 0
avg_delay = delayed_df['Delay Gap'].mean() if not delayed_df.empty else 0
high_risk_count = filtered_df['Late_delivery_risk'].sum()

with col1:
    st.metric(label="Total Shipments Processed", value=f"{total_orders:,}")
with col2:
    st.metric(label="On-Time/Early Rate", value=f"{on_time_rate:.1f}%")
with col3:
    st.metric(label="Average Delay (Days)", value=f"{avg_delay:.2f}")
with col4:
    st.metric(label="Total SLA Violations (Late)", value=f"{delayed_count:,}")

st.divider()

# ==========================================
# 4. VISUALIZATIONS
# ==========================================
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### Delivery Status Distribution")
    status_counts = filtered_df['Delivery Classification'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_pie = px.pie(status_counts, values='Count', names='Status',
                     color='Status', color_discrete_map={'On-Time':'#2ca02c', 'Delayed':'#d62728', 'Early':'#1f77b4'},
                     hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.markdown("#### Shipping Mode Bottlenecks")
    mode_analysis = delayed_df.groupby('Shipping Mode').agg(Avg_Delay=('Delay Gap', 'mean')).reset_index()
    fig_bar = px.bar(mode_analysis, x='Shipping Mode', y='Avg_Delay', text_auto='.2f',
                     color='Shipping Mode', title="Average Days Late by Shipping Mode")
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- REGIONAL RISK ANALYSIS ---
st.markdown("#### Regional Delay Risk Index")
region_risk = filtered_df.groupby('Order Region').agg(
    Total_Orders=('Type', 'count'), # Using 'Type' as a proxy for Order ID based on your df.info
    Delayed_Orders=('Late_delivery_risk', 'sum')
).reset_index()
region_risk['SLA Failure Rate (%)'] = (region_risk['Delayed_Orders'] / region_risk['Total_Orders']) * 100

fig_region = px.bar(region_risk.sort_values(by='SLA Failure Rate (%)', ascending=False),
                    x='Order Region', y='SLA Failure Rate (%)',
                    color='SLA Failure Rate (%)', color_continuous_scale='Reds',
                    title="Percentage of Shipments Failing SLA by Region")
st.plotly_chart(fig_region, use_container_width=True)
