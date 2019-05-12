import time
import quip

client = quip.QuipClient(
	access_token="R0NMQU1BWDBMcm0=|1589142576|pmuLMXmBBL+biWIwMNxApoqtXSAamR1GGg9MD6QNCAo=",
    base_url="https://platform.quip.com")

print(dir(client))

def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))