import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

# User database for login functionality
users_db = {
    "admin": {"email": "john@example.com", "password": "admin123"},
    "Admin": {"email": "jane@example.com", "password": "Admin123"}
}

# Function to check login credentials
def check_login(username_or_email, password):
    for user, info in users_db.items():
        if (username_or_email == user or username_or_email == info["email"]) and info["password"] == password:
            return True
    return False

# Snowflake connection function
def get_snowflake_connection():
    conn = snowflake.connector.connect(
        user='ALTRIAAPP',  # Replace with your Snowflake username
        password='Altria123',  # Replace with your Snowflake password
        account='SYB94152',  # Replace with your Snowflake account
        warehouse='COMPUTE_WH',  # Replace with your Snowflake warehouse
        database='CEAT_DB',  # Replace with your Snowflake database
        schema='CEAT_SCHEMA'  # Replace with your Snowflake schema
    )
    return conn

# Streamlit app configuration
st.set_page_config(page_title="Dealer Performance Monitoring App", layout="wide")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login page
if not st.session_state.logged_in:
    st.markdown("""
    <style>
        .header-title {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            flex-direction: column;
        }
        .header-title img {
            width: 100px;  
            height: auto;
            margin-bottom: 10px;  
        }
        .header-title h1 {
            margin: 0;
            font-size: 24px;
            color: #333;
            text-align: center;
        }
        .input-container {
            width: 90%;  
            margin: 0 auto;  
        }
        .stTextInput, .stPasswordInput {
            width: 90%;  
        }
    </style>
    <div class="header-title">
        <img src="https://brandeps.com/logo-download/C/CEAT-logo-vector-01.svg" alt="CEAT Logo">
        <h1>Dealer Performance Monitoring App</h1>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Sign In")
    
    username_or_email = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign In"):
        if check_login(username_or_email, password):
            st.session_state.logged_in = True
            st.session_state.username = username_or_email
            st.success("Login successful! You can now query the data.")
        else:
            st.error("Invalid username, email, or password.")
else:
    # Dashboard Page
    st.markdown("""
    <style>
        .header-title {
            display: flex;
            align-items: center;
        }
        .header-title img {
            width: 200px;  
            height: auto;
            margin-right: 20px;  
        }
        .header-title h1 {
            margin: 0;
            font-size: 40px;
            color: #333;
            padding-top: 10px;
        }
        .pillar-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;  
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
            height: 150px;  
        }
    </style>
    <div class="header-title">
        <img src="https://brandeps.com/logo-download/C/CEAT-logo-vector-01.svg" alt="CEAT Logo">
        <h1>Dealer Performance Monitoring App</h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    @st.cache_data
    def load_data():
        conn = get_snowflake_connection()
        query = "SELECT * FROM CEAT_DB.CEAT_SCHEMA.CEAT_TABLE"
        data = pd.read_sql(query, conn)
        data['DATE'] = pd.to_datetime(data['DATE'])
        conn.close()  # Close the connection after use
        return data

    df = load_data()

    st.sidebar.title("Filters")
    dealers = ["All Dealers"] + list(df['DEALER'].unique())
    selected_dealers = st.sidebar.multiselect("Select Dealers", dealers, default="All Dealers")

    products = ["All Products"] + list(df['PRODUCT'].unique())
    selected_products = st.sidebar.multiselect("Select Products", products, default="All Products")

    min_date = df['DATE'].min().date()
    max_date = df['DATE'].max().date()
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    filtered_df = df[
        (df['DEALER'].isin(selected_dealers) if "All Dealers" not in selected_dealers else True) &
        (df['PRODUCT'].isin(selected_products) if "All Products" not in selected_products else True) &
        (df['DATE'] >= pd.Timestamp(start_date)) & (df['DATE'] <= pd.Timestamp(end_date))
    ]

    st.markdown("<div class='column-frame'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)

    with col1:
        total_sales_value = filtered_df['TOTAL_SALES'].sum()
        target_value = filtered_df['TARGET'].sum()

        achievement_percentage = (total_sales_value / target_value * 100) if target_value > 0 else 0
        target_color = '#ff4d4d' if target_value > total_sales_value else '#2aa13a'

        st.markdown(f"""
        <div class="pillar-card">
            Total Sales Value<br>
            <span style="font-size: 30px;">Rs.{total_sales_value:,.0f}</span><br>
            <span style="font-size: 14px; color: {target_color};">
                Target: Rs.{target_value:,.0f} | 
                Achievement: <span style="color: {'#2aa13a' if achievement_percentage >= 100 else '#ff4d4d'};">
                {achievement_percentage:.2f}%
                </span>
            </span><br>
        </div>
        """, unsafe_allow_html=True)

        product_sales = filtered_df.groupby('PRODUCT')['TOTAL_SALES'].sum().reset_index()
        fig_pie_sales = px.pie(
            product_sales,
            names='PRODUCT',
            values='TOTAL_SALES',
            title='Product Wise Sales Actual Values',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        st.plotly_chart(fig_pie_sales, use_container_width=True)

        dealer_sales = filtered_df.groupby('DEALER')['TOTAL_SALES'].sum().reset_index()
        fig_bar = px.bar(
            dealer_sales,
            x='TOTAL_SALES',
            y='DEALER',
            title='Dealer Wise Sales',
            text='TOTAL_SALES',
            orientation='h',
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
        st.plotly_chart(fig_bar, use_container_width=True)

        dealer_product_sales = filtered_df.groupby(['DEALER', 'PRODUCT'])['TOTAL_SALES'].sum().reset_index()

        fig_grouped_stacked_bar = px.bar(
            dealer_product_sales,
            x='DEALER',
            y='TOTAL_SALES',
            color='PRODUCT',
            title='Dealer Wise Sales Breakdown',
            text='TOTAL_SALES',
            barmode='group',
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig_grouped_stacked_bar.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
        st.plotly_chart(fig_grouped_stacked_bar, use_container_width=True)

    st.markdown("<div style='width: 2px; background-color: #1c1a1a; height: 100%; margin: 0 auto; display: inline-block;'></div>", unsafe_allow_html=True)

    with col2:
        total_quantity = filtered_df['TOTAL_QUANTITY'].sum()
        st.markdown(f"""
        <div class="pillar-card">
            Total Sales Quantity<br>
            <span style="font-size: 30px;">{total_quantity:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        product_quantity = filtered_df.groupby('PRODUCT')['TOTAL_QUANTITY'].sum().reset_index()
        fig_pie_quantity = px.pie(
            product_quantity,
            names='PRODUCT',
            values='TOTAL_QUANTITY',
            title='Product Wise Sales Quantity',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        st.plotly_chart(fig_pie_quantity, use_container_width=True)

        product_quantity_sales = filtered_df.groupby('PRODUCT')['TOTAL_QUANTITY'].sum().reset_index()
        fig_bar_quantity = px.bar(
            product_quantity_sales,
            x='TOTAL_QUANTITY',
            y='PRODUCT',
            title='Product Wise Sales Quantity',
            text='TOTAL_QUANTITY',
            orientation='h',
            color_discrete_sequence=['#d4bab0']
        )
        fig_bar_quantity.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
        st.plotly_chart(fig_bar_quantity, use_container_width=True)

        product_dealer_quantity = filtered_df.groupby(['PRODUCT', 'DEALER'])['TOTAL_QUANTITY'].sum().reset_index()
        fig_grouped_quantity = px.bar(
            product_dealer_quantity,
            x='PRODUCT',
            y='TOTAL_QUANTITY',
            color='DEALER',
            title='Product Wise Sales Quantity Breakdown',
            text='TOTAL_QUANTITY',
            barmode='group',
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig_grouped_quantity.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
        st.plotly_chart(fig_grouped_quantity, use_container_width=True)

    st.markdown("<div style='width: 2px; background-color: #1c1a1a; height: 100%; margin: 0 auto; display: inline-block;'></div>", unsafe_allow_html=True)

    with col3:
        total_sales_return_quantity = filtered_df['SALES_RETURN'].sum()
        st.markdown(f"""
        <div class="pillar-card">
            Total Sales Return Quantity<br>
            <span style="font-size: 30px;">{total_sales_return_quantity:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        dealer_return_quantity = filtered_df.groupby(['DEALER', 'PRODUCT'])['SALES_RETURN'].sum().reset_index()
        fig_return_quantity = px.bar(
            dealer_return_quantity,
            x='SALES_RETURN',
            y='DEALER',
            color='PRODUCT',
            title='Dealer Wise Sales Return Quantity',
            orientation='h',
            text='SALES_RETURN',
            barmode='stack',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_return_quantity.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
        st.plotly_chart(fig_return_quantity, use_container_width=True)

        total_warranty_return_quantity = filtered_df['WARRANTY_RETURN'].sum()
        st.markdown(f"""
        <div class="pillar-card" style="height: 110px;">
            Total Warranty Return Quantity<br>
            <span style="font-size: 30px;">{total_warranty_return_quantity:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)

        product_warranty_return_quantity = filtered_df.groupby('PRODUCT')['WARRANTY_RETURN'].sum().reset_index()
        fig_warranty_return_quantity = px.bar(
            product_warranty_return_quantity,
            x='WARRANTY_RETURN',
            y='PRODUCT',
            title='Product Wise Warranty Return Quantity',
            text='WARRANTY_RETURN',
            orientation='h',
            color_discrete_sequence=px.colors.diverging.RdYlBu
        )
        fig_warranty_return_quantity.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
        st.plotly_chart(fig_warranty_return_quantity, use_container_width=True)

    target_achievement_df = filtered_df.groupby('DEALER').agg(
        Total_Sales=('TOTAL_SALES', 'sum'), 
        Target=('TARGET', 'sum')
    ).reset_index()

    melted_df = target_achievement_df.melt(
        id_vars=['DEALER'], 
        value_vars=['Target', 'Total_Sales'], 
        var_name='Metric', 
        value_name='Value'
    )

    fig_target_achievement = px.bar(
        melted_df,
        y='DEALER',
        x='Value',
        color='Metric',
        title='Dealer Target vs Achievement',
        text='Value',
        orientation='h',
        labels={'Value': 'Amount', 'DEALER': 'Dealer'},
        color_discrete_sequence=['#D3D3D3', '#4CAF50']
    )

    fig_target_achievement.update_layout(
        barmode='group',
        xaxis_title='Amount',
        yaxis_title='Dealer',
        title_x=0,
        margin=dict(l=40, r=40, t=40, b=40),
        legend_title_text='Metric',
        title_font=dict(size=16),
    )

    fig_target_achievement.update_traces(texttemplate='%{text:,.0f}', textposition='auto')
    st.plotly_chart(fig_target_achievement, use_container_width=True)

    st.markdown("---")
    st.subheader("First 5 Rows of Data")
    st.dataframe(df.head(5))

    st.markdown("---")
    st.markdown("© 2025 Dealer Performance Monitoring App. Powered by Snowflake and Streamlit.")
