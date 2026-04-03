from modules.database import get_connection
from modules.alerts import send_email, record_alert
from modules.preprocessing import get_daily_sales_series
from modules.forecasting import generate_forecast_for_product
from modules.config import SMTP_USER
from datetime import datetime, timedelta


def get_all_products():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.product_id, p.name,p.price, p.min_stock, p.early_warning_stock,
           p.is_essential,
           IFNULL(i.current_stock,0) as current_stock
    FROM products p
    LEFT JOIN inventory i ON p.product_id=i.product_id
    """)

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_min_stock(product_id, min_stock, early_warning):
    try:
        min_stock = int(min_stock)
        early_warning = int(early_warning)
    except:
        return False, "Values must be numeric"

    if early_warning <= min_stock:
        return False, "Early warning must be greater than min stock"

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE products
    SET min_stock=?, early_warning_stock=?
    WHERE product_id=?
    """, (min_stock, early_warning, product_id))

    conn.commit()
    conn.close()

    return True, "OK"


def update_stock(product_id, qty):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT current_stock FROM inventory WHERE product_id=?", (product_id,))
    row = cur.fetchone()

    current = row["current_stock"] if row else 0
    new_stock = current + qty

    if new_stock < 0:
        return "NEGATIVE_STOCK_ERROR"

    if new_stock > 9999:
        return "MAX_STOCK_LIMIT"

    cur.execute("""
    INSERT INTO inventory(product_id,current_stock,last_updated)
    VALUES(?,?,datetime('now'))
    ON CONFLICT(product_id)
    DO UPDATE SET current_stock=?, last_updated=datetime('now')
    """, (product_id, new_stock, new_stock))

    conn.commit()
    conn.close()

    check_and_handle_alert(product_id)
    check_slow_moving(product_id)

    return new_stock


# -------------------------------------------------------
# 🔥 FIXED FUNCTION
# -------------------------------------------------------
def adjust_stock_by_sale(product_id, qty):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT current_stock FROM inventory WHERE product_id=?", (product_id,))
    row = cur.fetchone()

    current = row["current_stock"] if row else 0
    new_stock = current - qty

    if new_stock < 0:
        return "NEGATIVE_STOCK_ERROR"

    cur.execute("""
    UPDATE inventory
    SET current_stock=?, last_updated=datetime('now')
    WHERE product_id=?
    """, (new_stock, product_id))

    # record sale
    cur.execute("""
    INSERT INTO sales(product_id, sale_qty, sale_date)
    VALUES(?, ?, datetime('now'))
    """, (product_id, qty))

    conn.commit()
    conn.close()

    # ✅ EXISTING LOGIC
    generate_forecast_for_product(product_id)
    check_and_handle_alert(product_id)

    # 🔥🔥 IMPORTANT ADDITION
    check_slow_moving(product_id)

    return new_stock


# -------------------------------------------------------
# ✅ SLOW MOVING LOGIC
# -------------------------------------------------------
def check_slow_moving(product_id):
    series = get_daily_sales_series(product_id)

    if len(series) < 7:
        return

    avg = series[-7:].mean()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.name, IFNULL(i.current_stock,0) as stock
    FROM products p
    LEFT JOIN inventory i ON p.product_id=i.product_id
    WHERE p.product_id=?
    """, (product_id,))

    row = cur.fetchone()
    conn.close()

    if avg < 2 and row["stock"] > 20:
        discount = min(50, int((row["stock"]/(avg+1))*5))
        msg = f"{row['name']} slow moving. Suggested discount: {discount}%"

        record_alert(product_id, "slow_moving", msg)
        send_email(SMTP_USER, "Slow Moving Alert", msg)


# -------------------------------------------------------
# ✅ ALERT LOGIC
# -------------------------------------------------------
def check_and_handle_alert(product_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.name, p.min_stock,
           IFNULL(i.current_stock,0) as current_stock
    FROM products p
    LEFT JOIN inventory i ON p.product_id=i.product_id
    WHERE p.product_id=?
    """, (product_id,))

    row = cur.fetchone()

    if not row:
        conn.close()
        return

    name = row["name"]
    current = row["current_stock"]
    min_stock = row["min_stock"]

    # 🔍 get last alert time
    cur.execute("""
    SELECT sent_at FROM alerts
    WHERE product_id=? AND alert_type='low_stock'
    ORDER BY sent_at DESC LIMIT 1
    """, (product_id,))

    last_alert = cur.fetchone()

    allow_send = True

    if last_alert:
        last_time = datetime.fromisoformat(last_alert["sent_at"])
        if datetime.now() - last_time < timedelta(hours=24):
            allow_send = False

    if min_stock is not None and current <= min_stock:

        if allow_send:

            fc = generate_forecast_for_product(product_id, 1)
            next_day = round(fc.iloc[0], 2) if fc is not None else 0

            msg = f"""
🚨 Critical Stock Alert

Product: {name}
Current Stock: {current}
Min Stock: {min_stock}

Next Day Forecast: {next_day}

Action Required: Restock immediately.
"""

            send_email(SMTP_USER, "Critical Stock Alert", msg)
            record_alert(product_id, "low_stock", msg)

    conn.close()