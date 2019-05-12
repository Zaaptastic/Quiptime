import boto3
import os

sns = boto3.client("sns", 
	region_name = "us-east-1", 
	aws_access_key_id = os.environ.get("AWS_ACCESS_KEY"),
	aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY"))

def publish_message_to_sns(message):
	response = sns.publish(
		TopicArn='arn:aws:sns:us-east-1:295716045588:QuiptimeTopic', 
		Message=message)
	
	return response
