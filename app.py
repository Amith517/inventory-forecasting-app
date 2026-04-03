import streamlit as st
import pandas as pd
import os

from modules.scheduler_service import start_scheduler
from modules.database import get_connection
from modules.inventory_manager import (
    get_all_products,
    set_min_stock,
    update_stock,
    adjust_stock_by_sale
)
import load_products_from_csv

# ---------------- START SCHEDULER (ONLY ONCE) ----------------
start_scheduler()

# ---------------- UI SETTINGS ----------------
st.set_page_config(layout="wide", page_title="Inventory Forecasting & Management")
st.title("Inventory Forecasting & Management")

# -----------------------------------------------------
# AUTO IMPORT CSV
# -----------------------------------------------------
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) as cnt FROM products")
    cnt = cur.fetchone()["cnt"]
    conn.close()

    if cnt == 0:
        csv_path = os.path.join("data", "products.csv")
        if os.path.exists(csv_path):
            load_products_from_csv.load_products()

except Exception as e:
    print("Auto import failed:", e)

# -----------------------------------------------------
# MENU
# -----------------------------------------------------
menu = st.sidebar.selectbox(
    "Menu",
    ["Home", "Products", "Update Stock", "Record Sale", "Dashboard"]
)

# -----------------------------------------------------
# HOME
# -----------------------------------------------------
if menu == "Home":
    st.header("Overview")

    from modules.alerts import send_daily_essential_forecast, send_non_essential_forecast

    if st.button("📧 Test Daily Email"):
        send_daily_essential_forecast()

    if st.button("📧 Test Non-Essential Email"):
        send_non_essential_forecast()

    products = get_all_products()
    df = pd.DataFrame(products)

    if not df.empty:
        df = df.reset_index(drop=True)

        # remove unwanted columns
        df = df.drop(columns=["min_stock", "early_warning_stock", "is_essential"], errors="ignore")

        st.dataframe(df)
    else:
        st.info("No products found.")

# -----------------------------------------------------
# PRODUCTS
# -----------------------------------------------------
if menu == "Products":
    st.header("Products")

    products = get_all_products()
    df = pd.DataFrame(products)

    if not df.empty:
        df = df.reset_index(drop=True)

        # ❌ Remove price column
        if "price" in df.columns:
            df = df.drop(columns=["price"])

        # dropdown for is_essential
        df["is_essential"] = df["is_essential"].astype(int)
        df["is_essential"] = df["is_essential"].map({1: "Yes", 0: "No"})

        edited_df = st.data_editor(
            df,
            column_config={
                "is_essential": st.column_config.SelectboxColumn(
                    "Is Essential",
                    options=["Yes", "No"]
                )
            },
            hide_index=True,
            use_container_width=True
        )

        # SAVE BUTTON
        if st.button("Save Changes"):
            conn = get_connection()
            cur = conn.cursor()

            for _, row in edited_df.iterrows():
                pid = int(row["product_id"])
                val = 1 if row["is_essential"] == "Yes" else 0

                cur.execute(
                    "UPDATE products SET is_essential=? WHERE product_id=?",
                    (val, pid)
                )

                if val == 1:
                    cur.execute("INSERT OR IGNORE INTO essential_products(product_id) VALUES(?)", (pid,))
                else:
                    cur.execute("DELETE FROM essential_products WHERE product_id=?", (pid,))

            conn.commit()
            conn.close()

            st.success("Updated successfully!")

    else:
        st.info("No products available.")

    # ---------------- Threshold Section ----------------
    st.subheader("Update Stock Thresholds")

    product_map = {p['name']: p['product_id'] for p in products}

    selected_product = st.selectbox("Select Product", [""] + list(product_map.keys()))

    if selected_product:
        pid = product_map[selected_product]

        col1, col2 = st.columns(2)

        min_stock = col1.number_input("Min Stock", min_value=0, value=0)
        early_warning = col2.number_input("Early Warning Stock", min_value=0, value=0)

        if st.button("Save Thresholds"):
            if early_warning <= min_stock:
                st.error("❌ Early Warning must be GREATER than Min Stock")
            else:
                ok, msg = set_min_stock(pid, int(min_stock), int(early_warning))

                if ok:
                    st.success("✅ Thresholds updated successfully")
                else:
                    st.error(msg)

# -----------------------------------------------------
# UPDATE STOCK
# -----------------------------------------------------
if menu == "Update Stock":
    st.header("Update Stock")

    products = get_all_products()
    product_map = {p['name']: p['product_id'] for p in products}

    selected = st.selectbox("Select product", [""] + list(product_map.keys()))

    if selected:
        pid = product_map[selected]
        qty = st.number_input("Quantity", value=0)

        if st.button("Update"):
            res = update_stock(pid, int(qty))

            if res == "NEGATIVE_STOCK_ERROR":
                st.error("Stock cannot go below zero!")
            elif res == "MAX_STOCK_LIMIT":
                st.error("Stock cannot exceed 9999!")
            else:
                st.success(f"Updated stock: {res}")

# -----------------------------------------------------
# RECORD SALE
# -----------------------------------------------------
if menu == "Record Sale":
    st.header("Record Sale")

    products = get_all_products()
    product_map = {p['name']: p['product_id'] for p in products}

    selected = st.selectbox("Select product", [""] + list(product_map.keys()))
    qty = st.number_input("Quantity sold", min_value=1, value=1)

    if st.button("Record"):
        if selected:
            pid = product_map[selected]
            res = adjust_stock_by_sale(pid, int(qty))

            if res == "NEGATIVE_STOCK_ERROR":
                st.error("Sale would cause negative stock!")
            else:
                st.success(f"New stock: {res}")
        else:
            st.warning("Select a product.")

# -----------------------------------------------------
# DASHBOARD
# -----------------------------------------------------
if menu == "Dashboard":
    st.header("📊 Sales Dashboard")

    import plotly.express as px
    from modules.dashboard import (
        get_sales_data,
        get_daily_sales,
        get_weekly_sales,
        get_monthly_sales,
        get_top_products,
        get_total_revenue,
        get_slow_products
    )

    df = get_sales_data()

    if df.empty:
        st.warning("No sales data available")
    else:
        daily = get_daily_sales(df)
        weekly = get_weekly_sales(df)
        monthly = get_monthly_sales(df)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Today's Sales", int(daily.iloc[-1]) if len(daily) else 0)
        col2.metric("This Week", int(weekly.iloc[-1]) if len(weekly) else 0)
        col3.metric("This Month", int(monthly.iloc[-1]) if len(monthly) else 0)
        col4.metric("Revenue", f"₹ {get_total_revenue():,.2f}")

        view = st.selectbox("Select View", ["Daily", "Weekly", "Monthly"])

        if view == "Daily":
            data = daily.reset_index()
            x = "sale_date"
        elif view == "Weekly":
            data = weekly.reset_index()
            x = "sale_date"
        else:
            data = monthly.reset_index()
            x = "sale_date"

        fig = px.line(data, x=x, y="sale_qty")
        st.plotly_chart(fig, use_container_width=True)

        top_df = get_top_products()
        st.plotly_chart(px.bar(top_df, x="name", y="total_sales"), use_container_width=True)

        st.plotly_chart(px.pie(top_df, names="name", values="total_sales"), use_container_width=True)

        slow_df = get_slow_products()
        st.dataframe(slow_df)

        if not top_df.empty:
            st.success(f"🔥 {top_df.iloc[0]['name']} is your best selling product!")

        if not slow_df.empty:
            st.warning(f"⚠️ {slow_df.iloc[0]['name']} is slow moving.")