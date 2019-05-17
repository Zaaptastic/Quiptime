import boto3
import os

sns = boto3.client("sns", 
	region_name = "us-east-1", 
	aws_access_key_id = os.environ.get("AWS_ACCESS_KEY"),
	aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY"))
s3 = boto3.client("s3", 
	region_name = "us-east-1", 
	aws_access_key_id = os.environ.get("AWS_ACCESS_KEY"),
	aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY"))
s3_resource = boto3.resource("s3", 
	region_name = "us-east-1", 
	aws_access_key_id = os.environ.get("AWS_ACCESS_KEY"),
	aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY"))

quiptime_endpoint = os.environ.get("QUIPTIME_ENDPOINT", "devo")
quiptime_bucketname = "quiptime"
threads_list_keyname = "thread_id_list_" + quiptime_endpoint + ".txt"

def publish_message_to_sns(message):
	response = sns.publish(
		TopicArn='arn:aws:sns:us-east-1:295716045588:QuiptimeTopic', 
		Message=message,
		Subject="Reminder")
	
	return response

def fetch_threads_list():
	print("Loading: " + threads_list_keyname)
	threads_file = s3.get_object(Bucket = quiptime_bucketname, Key = threads_list_keyname)
	threads_list = threads_file['Body'].read().decode('utf-8') 
	
	return threads_list.split("\r\n")

def upload_threads_list(threads_list):
	threads_list_as_string = "\r\n".join(threads_list)

	s3_resource.Object(quiptime_bucketname, threads_list_keyname).put(Body=threads_list_as_string)
