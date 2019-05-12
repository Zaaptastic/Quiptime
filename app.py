from flask import Flask
from flask import request
from flask import render_template
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil import parser
from dateutil import tz
from bs4 import BeautifulSoup
from pytz import timezone

import time
import atexit
import quip_gateway
import quip
import datetime
import os
import aws_gateway

app = Flask(__name__)
est_timezone = tz.gettz('US/Eastern')
tzinfos = {"EST": tz.gettz('US/Eastern')}

@app.route('/')
def ping():
    return 'Server is running '

@app.route('/get_thread')
def get_thread():
	suffix = request.args.get('suffix')
	threadId = quip_gateway.get_thread(suffix)
	return render_template('get_thread.html', threadId=threadId)

def fetch_item_updates(thread_id):
	current_time = datetime.datetime.now(est_timezone)
	print(current_time)

	# First, fetch all Reminders from the Document
	html = quip_gateway.get_document_html(thread_id)
	page = BeautifulSoup(html, features="html.parser")
	reminders = page.findAll('li')

	for reminder in reminders:
		process_reminder(reminder, thread_id, current_time)

def process_reminder(reminder, thread_id, current_time):
	# Determine if it is 'checked', if so, ignore it.
	reminder_id = reminder['id']
	reminder_class = reminder['class']
	if ('checked' in reminder_class):
		print("Skipping ReminderId{" + reminder_id + "}")
		return

	# Locate the text in the Reminder describing the time in which it should be triggered.
	text = reminder.text
	time = parser.parse(text.split('@')[1] + " EST", tzinfos = tzinfos)
	print(time)
	if (time > current_time):
		print("Not yet time to trigger: {reminder_id=" + reminder_id + ", time=" + time.strftime("%Y-%m-%d %H:%M:%S") + "}")
	else:
		print("Time (or past time) to trigger: {reminder_id=" + reminder_id + ", time=" + time.strftime("%Y-%m-%d %H:%M:%S") + "}")
		
		sns_response = aws_gateway.publish_message_to_sns(text)

		# If the SNS message was unsuccessful, we want to retry, so we can't check off the checkbox
		if (sns_response['ResponseMetadata']['HTTPStatusCode'] == 200):
			# TODO: Find a way to cap retries
			quip_gateway.toggle_checkmark(thread_id, reminder_id, reminder)
			quip_gateway.new_message(thread_id, text)

# Set up the scheduler 
scheduler = BackgroundScheduler(timezone="EST") # TODO: Don't do this for the timezone
scheduler.add_job(func=fetch_item_updates, 
	args=["fFeAAABnQCd"], # TODO: Put this somewhere else
	trigger="interval", 
	seconds=int(os.environ.get("QUIPTIME_HEARTBEAT_INTERVAL", "60")))
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
