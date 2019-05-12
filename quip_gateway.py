import quip
import os

client = quip.QuipClient(
	access_token=os.environ.get("QUIP_API_KEY", "InvalidKey"),
    base_url="https://platform.quip.com")

# Fetches all attributes of client, useful for debugging
# print(dir(client))

def get_thread(suffix):
	# TODO: Make this handle URLs as well by parsing out the junk
	resp = client.get_thread(suffix)
	print(resp)
	return resp["thread"]["id"]

def get_document_html(thread_id):
	resp = client.get_thread(thread_id)
	return resp["html"]

def toggle_checkmark(thread_id, section_id, item):
	if ('checked' in item['class']):
		item['class'].remove('checked')
	else:
		item['class'].append('checked')
	replace_document_section(thread_id, section_id, item)

def replace_document_section(thread_id, section_id, item):
	client.edit_document(thread_id = thread_id, 
		content = item, 
		operation = quip.QuipClient.REPLACE_SECTION, 
		format = "html",
		section_id = section_id)

def new_message(thread_id, content):
	client.new_message(thread_id, content)