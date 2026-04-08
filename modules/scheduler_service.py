import schedule
import time
from threading import Thread

from modules.inventory_manager import get_all_products, check_slow_moving


# ---------------------------------------------------------
# ✅ CHECK ALL PRODUCTS (NEW)
# ---------------------------------------------------------
def check_all_products():
    print("🔄 Running daily slow-moving check...")

    products = get_all_products()

    for p in products:
        pid = p["product_id"]
        check_slow_moving(pid)

    print("✅ Daily check completed")


# ---------------------------------------------------------
# ✅ START SCHEDULER
# ---------------------------------------------------------
def start_scheduler():
    schedule.clear()

    # 🔥 RUN EVERY DAY AT 3:30 PM
    schedule.every().day.at("15:30").do(check_all_products)

    # (Optional testing — uncomment)
    # schedule.every(1).minutes.do(check_all_products)

    def run_loop():
        while True:
            schedule.run_pending()
            time.sleep(1)

    t = Thread(target=run_loop, daemon=True)
    t.start()
    return t