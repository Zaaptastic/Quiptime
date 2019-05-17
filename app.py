from flask import Flask
from flask import request
from flask import render_template
from flask import redirect, url_for
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
import copy
import aws_gateway

app = Flask(__name__)

# Timezone information. One day this won't be hardcoded to EST.
est_timezone = tz.gettz('US/Eastern')
tzinfos = {"EST": tz.gettz('US/Eastern')}
# Password used to add/remove threads via the web interface. One day this will be real authentication
add_thread_password = os.environ.get("ADD_THREAD_PASSWORD")
# Frequency at which to trigger each cycle of checking reminders
heartbeat_interval = int(os.environ.get("QUIPTIME_HEARTBEAT_INTERVAL", "60"))
# Task schedule for recurring jobs
scheduler = BackgroundScheduler(timezone="EST")
# List of threads that will be actively scanned for reminders
threads_list = aws_gateway.fetch_threads_list()
print("Found list of threads to track: " + str(threads_list))
# List of reminders that will be notified on. Technically a dictionary to keep track of associated thread_ids
reminders_list = {}

@app.route('/')
def ping():
    return 'Server is running '

@app.route('/get_thread_id')
def get_thread_id():
	suffix = request.args.get('suffix')
	threadId = quip_gateway.get_thread(suffix)
	return render_template('get_thread_id.html', threadId=threadId)

@app.route('/get_thread_id', methods=["POST"])
def get_thread_id_add():
	thread_id_to_add = request.form['submit']
	submitted_password = request.form['password']
	
	return add_thread(thread_id_to_add, submitted_password)

@app.route('/get_threads')
def get_threads():
	return render_template('get_threads.html', threads_list=threads_list)

@app.route('/get_threads', methods=["POST"])
def get_threads_edit():
	thread_id_to_delete = request.form['submit']
	submitted_password = request.form['password']

	if thread_id_to_delete == "get_threads_add":
		# Instead of deleting, find a thread_id to add
		thread_id_to_add = request.form['thread_id_to_add']
		return add_thread(thread_id_to_add, submitted_password)
	else:
		return delete_thread(thread_id_to_delete, submitted_password)

@app.route('/clear_cache')
def clear_cache():
	reload_threads_list()
	reload_reminders_list()
	return "Cache fully cleared and repopulated"

def fetch_reminders_list():
	reminders_to_return = {}

	for thread_id in threads_list:
		# First, fetch all Reminders from the Document
		html = quip_gateway.get_document_html(thread_id)
		page = BeautifulSoup(html, features="html.parser")
		reminders = page.findAll('li')

		for reminder in reminders:
			reminders_to_return[reminder] = thread_id

	print("Found reminders: " + str(reminders_to_return))

	return reminders_to_return

@scheduler.scheduled_job('interval', seconds=heartbeat_interval*5)
def reload_reminders_list():
	current_time = datetime.datetime.now(est_timezone)
	print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	print("Reloading reminders_list: " + current_time.strftime("%Y-%m-%d %H:%M:%S"))

	global reminders_list
	reminders_list = fetch_reminders_list()

@scheduler.scheduled_job('interval', seconds=(heartbeat_interval*60))
def reload_threads_list():
	current_time = datetime.datetime.now(est_timezone)
	print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	print("Reloading threads_list: " + current_time.strftime("%Y-%m-%d %H:%M:%S"))

	global threads_list
	threads_list = aws_gateway.fetch_threads_list()

@scheduler.scheduled_job('interval', seconds=heartbeat_interval*1)
def check_all_reminders():
	current_time = datetime.datetime.now(est_timezone)
	print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	print("Checking all reminders: " + current_time.strftime("%Y-%m-%d %H:%M:%S"))

	global reminders_list
	for reminder in reminders_list:
		unchecked_reminder = copy.deepcopy(reminder)
		successful_publish = process_reminder(reminder, reminders_list[reminder], current_time)
		if successful_publish:
			reminders_list.pop(unchecked_reminder)

# This initializes the Scheduler with jobs defined in the functions above.		
reload_reminders_list()	
scheduler.start()
print("Application initialized!")

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

def add_thread(thread_id_to_add, submitted_password):
	threads_list.append(thread_id_to_add)
	aws_gateway.upload_threads_list(threads_list)

	if add_thread_password == submitted_password:
		print("Adding thread_id={" + thread_id_to_add + "} to Tracked Threads")
		return redirect(url_for('get_threads'))
	else:
		print("Authentication Failed while adding thread_id={" + thread_id_to_add + "} to Tracked Threads")
		return render_template('get_thread_id.html', threadId=thread_id_to_add)

def delete_thread(thread_id_to_delete, submitted_password):
	if thread_id_to_delete not in threads_list:
		return render_template('get_threads.html', threads_list=threads_list)		
	elif add_thread_password == request.form['password']:
		print("Deleting thread_id={" + thread_id_to_delete + "} to Tracked Threads")
		threads_list.remove(thread_id_to_delete)
		aws_gateway.upload_threads_list(threads_list)
		return render_template('get_threads.html', threads_list=threads_list)
	else:
		print("Authentication Failed while deleting thread_id={" + thread_id_to_delete + "} to Tracked Threads")
		return render_template('get_threads.html', threads_list=threads_list)

def process_reminder(reminder, thread_id, current_time):
	# Determine if it is 'checked', if so, ignore it.
	reminder_id = reminder['id']
	reminder_class = reminder['class']
	if ('checked' in reminder_class):
		print("Skipping completed (checked) ReminderId{" + reminder_id + "}")
		return

	# Locate the text in the Reminder describing the time in which it should be triggered.
	text = reminder.text
	time = parser.parse(text.split('@')[1] + " EST", tzinfos = tzinfos)
	
	if (time > current_time):
		print("Not yet time to trigger: {reminder_id=" + reminder_id + ", time=" + time.strftime("%Y-%m-%d %H:%M:%S") + "}")
		return False
	else:
		print("Time (or past time) to trigger: {reminder_id=" + reminder_id + ", time=" + time.strftime("%Y-%m-%d %H:%M:%S") + "}")
		
		sns_response = aws_gateway.publish_message_to_sns(text)

		# If the SNS message was unsuccessful, we want to retry, so we can't check off the checkbox
		if (sns_response['ResponseMetadata']['HTTPStatusCode'] == 200):
			# TODO: Find a way to cap retries
			quip_gateway.toggle_checkmark(thread_id, reminder_id, reminder)
			quip_gateway.new_message(thread_id, text)
			return True
		return False
