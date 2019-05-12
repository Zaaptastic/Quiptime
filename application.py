from flask import Flask
from flask import request
from flask import render_template
from apscheduler.schedulers.background import BackgroundScheduler

import time
import atexit
import quip_gateway
import quip

app = Flask(__name__)

@app.route('/')
def ping():
    return 'Server is running'

@app.route('/get_thread')
def get_thread():
	suffix = request.args.get('suffix')
	threadId = quip_gateway.get_thread(suffix)
	return render_template('get_thread.html', threadId=threadId)

scheduler = BackgroundScheduler(timezone="EST") # TODO: Don't do this for the timezone
scheduler.add_job(func=quip_gateway.print_date_time, trigger="interval", seconds=3)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())