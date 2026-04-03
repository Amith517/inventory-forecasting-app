import pandas as pd
from modules.database import get_connection


# -----------------------------------------------------
# GET SALES DATA
# -----------------------------------------------------
def get_sales_data():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT sale_date, sale_qty, product_id
        FROM sales
    """, conn)

    conn.close()

    if df.empty:
        return df

    df['sale_date'] = pd.to_datetime(df['sale_date'])
    return df


# -----------------------------------------------------
# DAILY SALES
# -----------------------------------------------------
def get_daily_sales(df):
    return df.groupby(df['sale_date'].dt.date)['sale_qty'].sum()


# -----------------------------------------------------
# WEEKLY SALES
# -----------------------------------------------------
def get_weekly_sales(df):
    return df.resample('W', on='sale_date')['sale_qty'].sum()


# -----------------------------------------------------
# MONTHLY SALES
# -----------------------------------------------------
def get_monthly_sales(df):
    return df.resample('ME', on='sale_date')['sale_qty'].sum()


# -----------------------------------------------------
# 🔥 TOP SELLING PRODUCTS
# -----------------------------------------------------
def get_top_products():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT p.name, SUM(s.sale_qty) as total_sales
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.name
        ORDER BY total_sales DESC
        LIMIT 5
    """, conn)

    conn.close()
    return df


# -----------------------------------------------------
# 💰 TOTAL REVENUE
# -----------------------------------------------------
def get_total_revenue():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT SUM(s.sale_qty * p.price) as revenue
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
    """, conn)

    conn.close()

    if df.empty or df.iloc[0]["revenue"] is None:
        return 0

    return df.iloc[0]["revenue"]

# -----------------------------------------------------
# 📊 DAILY PRODUCT-WISE SALES
# -----------------------------------------------------
def get_daily_product_sales():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT DATE(s.sale_date) as date,
               p.name as product,
               SUM(s.sale_qty) as total_qty
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY date, product
        ORDER BY date DESC
    """, conn)

    conn.close()
    return df


# -----------------------------------------------------
# 📊 WEEKLY PRODUCT-WISE SALES
# -----------------------------------------------------
def get_weekly_product_sales():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT strftime('%Y-%W', s.sale_date) as week,
               p.name as product,
               SUM(s.sale_qty) as total_qty
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY week, product
        ORDER BY week DESC
    """, conn)

    conn.close()
    return df


# -----------------------------------------------------
# 📊 MONTHLY PRODUCT-WISE SALES
# -----------------------------------------------------
def get_monthly_product_sales():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT strftime('%Y-%m', s.sale_date) as month,
               p.name as product,
               SUM(s.sale_qty) as total_qty
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY month, product
        ORDER BY month DESC
    """, conn)

    conn.close()
    return df

def get_slow_products():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT p.name, SUM(s.sale_qty) as total
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.name
        ORDER BY total ASC
        LIMIT 5
    """, conn)

    conn.close()
    return df