from flask import Flask
import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from tzlocal import get_localzone

app = Flask(__name__)

@app.route('/')
def ping():
    return 'Server is running'

def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


print(get_localzone())
scheduler = BackgroundScheduler(timezone="EST")
scheduler.add_job(func=print_date_time, trigger="interval", seconds=3)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())