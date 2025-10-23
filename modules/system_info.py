import psutil, datetime

def get_system_info():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery else "N/A"
    now = datetime.datetime.now().strftime("%I:%M:%S %p")
    return {"CPU": f"{cpu}%", "RAM": f"{ram}%", "Battery": f"{battery_percent}%", "Time": now}
