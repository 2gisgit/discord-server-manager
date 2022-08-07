import schedule
import json
import time

def refresh():
    with open("data.json", "w") as f:
        json.dump({"1": "000"}, f)
schedule.every(1).hours.do(refresh)

while True:
    schedule.run_pending()
    time.sleep(1)
