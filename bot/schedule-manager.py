import schedule
import json
import time

def refresh():
    print("working")
    with open("data.json", "w") as f:
        json.dump({"1": "000"}, f)
schedule.every(10).seconds.do(refresh)

while True:
    schedule.run_pending()
    time.sleep(1)
