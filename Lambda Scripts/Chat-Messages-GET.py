import json
import boto3

dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    try:
        id = event['id']
        data = dynamodb.query(
            TableName= 'Chat-Messages',
            ProjectionExpression= '#T, Sender, Message',
            ExpressionAttributeNames= {'#T': 'Timestamp'},
            KeyConditionExpression= 'ConversationId = :id',
            ExpressionAttributeValues= {':id': {'S': id}}
        )
        data= loadMessages(data, id, event['cognitoUsername'], [])
        return data
            
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

        
def loadMessages(data, id, username, messages):
    for items in data['Items']:
        messages.append({'sender': items['Sender']['S'],
            'time': int(items['Timestamp']['N']),
            'message': items['Message']['S']
        })
    if 'LastEvaluatedKey' in data:
        return data
        data = dynamodb.query(
                TableName= 'Chat-Messages',
                ProjectionExpression= '#T, Sender, Message',
                KeyConditionExpression= 'ConversationId = :id',
                ExpressionAttributeNames= {'#T': 'Timestamp'},
                ExpressionAttributeValues= {':id': {'S': id}},
                ExclusiveStartKey= data['LastEvaluatedKey']
            )
        loadMessages(data, id, username, messages)
    else:
        return (loadConversationDetail(id, username, messages))
    
def loadConversationDetail(id, username, messages):
    data = dynamodb.query(
            TableName= 'Chat-conversations',
            Select= 'ALL_ATTRIBUTES',
            KeyConditionExpression= 'ConversationId = :id',
            ExpressionAttributeValues= {':id': {'S': id}}
        )
    participants = []
    for item in data['Items']:
        participants.append(item['Username']['S'])
    if not username in participants:
        return {
            'unauthorized': 'unauthorized'
        }
    return {
            'id': id,
            'participants': participants,
            'last': messages[len(messages)-1]['time'],
            'messages': messages
    }

