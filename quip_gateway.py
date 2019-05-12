import time
import quip
import os

client = quip.QuipClient(
	access_token=os.environ.get("QUIP_API_KEY", "InvalidKey"),
    base_url="https://platform.quip.com")

print(dir(client))

def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))

def get_thread(suffix):
	resp = client.get_thread(suffix)
	print(resp)
	return resp["thread"]["id"]