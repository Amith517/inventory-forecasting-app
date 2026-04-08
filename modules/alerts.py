import smtplib
from email.mime.text import MIMEText
from modules.database import get_connection
from modules.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL, ENABLE_SMTP

# 🔴 CHANGE THIS
DEALER_EMAIL = "namithreddy_it221240@mgit.ac.in"


# ---------------------------------------------------------
# ✅ SEND EMAIL (SAFE)
# ---------------------------------------------------------
def send_email(to_email, subject, body):
    try:
        recipients = [to_email, DEALER_EMAIL]

        if not ENABLE_SMTP:
            print("EMAIL DISABLED")
            print(subject)
            print(body)
            return True

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)

        for email in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL
            msg['To'] = email

            server.sendmail(FROM_EMAIL, email, msg.as_string())

        server.quit()

        print("✅ EMAIL SENT:", subject)
        return True

    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        return False


# ---------------------------------------------------------
# ✅ RECORD ALERT
# ---------------------------------------------------------
def record_alert(product_id, alert_type, message):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO alerts (product_id, alert_type, message)
        VALUES (?, ?, ?)
    """, (product_id, alert_type, message))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# ✅ ESSENTIAL EMAIL
# ---------------------------------------------------------
def send_daily_essential_forecast():
    from modules.forecasting import generate_forecast_for_product
    from modules.database import get_connection

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.product_id, p.name, p.min_stock,
           IFNULL(i.current_stock,0) as current_stock
    FROM essential_products e
    JOIN products p ON e.product_id = p.product_id
    LEFT JOIN inventory i ON p.product_id = i.product_id
    """)

    rows = cur.fetchall()

    if not rows:
        conn.close()
        return

    # 🔥 BUILD ONE COMBINED MESSAGE
    message = "📊 Essential Products Report\n\n"

    for r in rows:
        pid = r["product_id"]
        name = r["name"]
        stock = r["current_stock"]
        min_stock = r["min_stock"]

        message += f"\n{name}\n"
        message += f"Stock: {stock}\n"
        message += f"Min Stock: {min_stock}\n"

        # only forecast if needed
        if min_stock is not None and stock <= min_stock:
            fc = generate_forecast_for_product(pid, 1)
            next_day = round(fc.iloc[0], 2) if fc is not None else 0
            message += f"⚠️ Tomorrow Demand: {next_day}\n"

        message += "------------------------\n"

    conn.close()

    # 🔥 SEND ONLY ONE EMAIL
    send_email(SMTP_USER, "Essential Products Daily Report", message)
# ---------------------------------------------------------
# ✅ NON-ESSENTIAL EMAIL (FIXED)
# ---------------------------------------------------------
def send_non_essential_forecast():
    from modules.forecasting import generate_forecast_for_product
    from datetime import datetime, timedelta

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.product_id, p.name, p.early_warning_stock,
           IFNULL(i.current_stock,0) as current_stock
    FROM products p
    LEFT JOIN inventory i ON p.product_id = i.product_id
    WHERE p.is_essential = 0
    """)

    rows = cur.fetchall()

    if not rows:
        print("No non-essential products")
        conn.close()
        return

    for r in rows:
        pid = r["product_id"]
        name = r["name"]
        stock = r["current_stock"]
        early = r["early_warning_stock"]

        print(f"Checking {name}")

        # ❌ skip if no threshold
        if early is None or stock > early:
            continue

        # 🔴 CHECK LAST EMAIL TIME
        cur.execute("""
        SELECT sent_at FROM alerts
        WHERE product_id=? AND alert_type='non_essential'
        ORDER BY sent_at DESC LIMIT 1
        """, (pid,))

        last = cur.fetchone()

        if last:
            last_time = datetime.fromisoformat(last["sent_at"])
            if datetime.now() - last_time < timedelta(hours=24):
                print(f"⏳ Skipped (24hr cooldown): {name}")
                continue

        print(f"🚨 Sending email for {name}")

        fc = generate_forecast_for_product(pid, 7)
        total = round(fc.sum(), 2) if fc is not None else 0

        message = f"""
⚠️ Early Warning Alert

Product: {name}
Current Stock: {stock}
Early Warning Level: {early}

Next 7 Days Demand: {total}
"""

        send_email(SMTP_USER, f"Early Warning - {name}", message)
        record_alert(pid, "non_essential", message)

    conn.close()