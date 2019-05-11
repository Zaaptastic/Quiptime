from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

import time
import atexit
import quip_gateway

app = Flask(__name__)

@app.route('/')
def ping():
    return 'Server is running'

scheduler = BackgroundScheduler(timezone="EST") # TODO: Don't do this for the timezone
scheduler.add_job(func=quip_gateway.print_date_time, trigger="interval", seconds=3)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())