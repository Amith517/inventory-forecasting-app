from modules.alerts import send_daily_essential_forecast

print("Running scheduler task...")
send_daily_essential_forecast()
print("Task completed.")