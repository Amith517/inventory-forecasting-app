import schedule
import time
from threading import Thread


def start_scheduler():
    from modules.alerts import (
        send_daily_essential_forecast,
        send_non_essential_forecast
    )

    # ✅ ESSENTIAL → DAILY AT 9 PM
    schedule.every().day.at("21:00").do(send_daily_essential_forecast)

    # ✅ NON-ESSENTIAL → CHECK EVERY HOUR
    schedule.every(1).hours.do(send_non_essential_forecast)

    def run():
        while True:
            schedule.run_pending()
            time.sleep(1)

    Thread(target=run, daemon=True).start()