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

def publish_message_to_sns(message):
	response = sns.publish(
		TopicArn='arn:aws:sns:us-east-1:295716045588:QuiptimeTopic', 
		Message=message)
	
	return response

def fetch_threads_list():
	threads_file = s3.get_object(Bucket = "quiptime", Key = "thread_id_list.txt")
	threads_list = threads_file['Body'].read().decode('utf-8') 
	
	return threads_list.split("\r\n")
