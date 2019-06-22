import json
import boto3
import time, datetime

dynamodb = boto3.client('dynamodb')

def now_milliseconds():
   return int(time.time() * 1000)
   
def date_time_milliseconds(date_time_obj):
   return int(time.mktime(date_time_obj.timetuple()) * 1000)


def lambda_handler(event, context):
    try:
        mstimeone = now_milliseconds()
        mstimetwo = date_time_milliseconds(datetime.datetime.utcnow())
        dynamodb.put_item(
            TableName= 'Chat-Messages',
            Item= {
                'ConversationId': {'S': event['id']},
                'Timestamp': {
                    'N': "" + str(mstimetwo)
                },
                'Message': {'S': event['message']},
                'Sender': {'S': event['cognitoUsername']}
            }
        )

    except Exception as e:
        exception_type = e.__class__.__name__
        exception_message = str(e)

        api_exception_obj = {
            "statusCode": 400,
            "isError": True,
            "type": exception_type,
            "message": exception_message
        }
        api_exception_json = json.dumps(api_exception_obj)
        return api_exception_json
