import json
import boto3
import botocore
import os

INSTANCE_ID = os.environ['INSTANCE_ID'] # The Amazon connect INSTANCE_ID (environment variable)
BUCKET_NAME = os.environ['BUCKET_NAME '] # The S3 BUCKET_NAME (environment variable)
prefix = os.environ['prefix'] # S3 object prefix

# Clients for Amazon Connect and S3

connect_client = boto3.client('connect')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    qcList = getQuickConnectsList()
    datastring = createDatastring(qcList)
    result = write_to_s3(datastring)

    return {
        'body': str(result)
    }

def getQuickConnectsList():

    qcList = [] # A list with all quick-connects details

    # A list of all quick-connects for the  given Aamzon Connect Instance
    response = connect_client.list_quick_connects(InstanceId = INSTANCE_ID, QuickConnectTypes = ['PHONE_NUMBER'], MaxResults = 1000)
    quickconnectslist = response['QuickConnectSummaryList']
    while "NextToken" in response:
        response = connect_client.list_quick_connects(InstanceId = INSTANCE_ID, QuickConnectTypes = ['PHONE_NUMBER'], MaxResults = 1000, NextToken = response['NextToken'])
        quickconnectslist.extend(response['QuickConnectSummaryList'])

    # Get the details for each quick-connect found and add them to qcList
    for index in range(len(quickconnectslist)):
        try: 
            qcdetails = connect_client.describe_quick_connect(InstanceId = INSTANCE_ID, QuickConnectId = quickconnectslist[index]['Id'])
            qcList.append(qcdetails)
        except botocore.exceptions.ClientError as err:
            response = err.response
            print(str(response))
            continue

    return qcList

# Append quick connect details to a datastring to be writtern in S3
def createDatastring(qcList):
    datastring = '' # The string that will be written to the S3 bucket: contains detailas for all quick-cocnnects found

    # Append quick connect details to a datastring to be written in S3
    for item in qcList:
        print(item)
        try:
            quickConnectId = item['QuickConnect']['QuickConnectId']
        except:
            quickConnectId = ''
        try:
            description = item['QuickConnect']['Description']
        except:
            description = ''
        try:
            qcType = item['QuickConnect']['QuickConnectConfig']['QuickConnectType']
        except:
            qcType = ''
        try:
            phonenumber = item['QuickConnect']['QuickConnectConfig']['PhoneNumber']
            datastring += (
                '{"QuickConnectId":"' + quickConnectId + '",'
                '"Description":' + description + '",'
                '"Type":' + qcTypeFormatter(qcType) + '",'
                '"Phone Number":' + phonenumber + '"{\n'
                )        
        except:
            phonenumber = ''

    print(datastring)
    return datastring


# Write datastring to S3 bucket
def write_to_s3(datastring):
    try:
        s3_client.put_object(Bucket = BUCKET_NAME, Key = prefix + '/' + 'quick-connects.json', Body = datastring)
        result = 'The QuickConnect data was written to: ' + BUCKET_NAME + '/' + prefix
    except botocore.exceptions.ClientError as error:
        print(error)
        result = str(error)

    return result
    
# A function to format quick-connect Type
def qcTypeFormatter(qctype):
    switcher = {
        'PHONE_NUMBER': 'External',
        'USER' : 'Agent',
        'QUEUE': 'Queue'
    }

    return switcher.get(qctype, '')