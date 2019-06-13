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
        path = event['pathParameters']['proxy']
        if path == 'conversations':
            data = dynamodb.query(
                TableName= 'Chat-conversations',
                IndexName= 'Username-ConversationId-index',   
                Select= 'ALL_PROJECTED_ATTRIBUTES',
                KeyConditionExpression= 'Username = :username',
                ExpressionAttributeValues= {':username': {'S': 'Student'}}
                )
            content = handleIdQuery(data, [], 'Student')
            return {
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': 'https://arihant-serverless-chat-app.s3.us-east-2.amazonaws.com'
                },
                'statusCode': 200,
                'body': json.dumps(content)
            }
        elif path.startswith('conversations/'):
            id = path[path.index("/")+1:]
            if event['httpMethod'] == 'GET':
                data = dynamodb.query(
                    TableName= 'Chat-Messages',
                    ProjectionExpression= '#T, Sender, Message',
                    ExpressionAttributeNames= {'#T': 'Timestamp'},
                    KeyConditionExpression= 'ConversationId = :id',
                    ExpressionAttributeValues= {':id': {'S': id}}
                )
                data= loadMessages(data, id, [])
                return {
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': 'https://arihant-serverless-chat-app.s3.us-east-2.amazonaws.com'
                    },
                    'statusCode': 200,
                    'body': json.dumps(data)
                }
            if event['httpMethod'] == 'POST':
                mstimeone = now_milliseconds()
                mstimetwo = date_time_milliseconds(datetime.datetime.utcnow())
                dynamodb.put_item(
                    TableName= 'Chat-Messages',
                    Item= {
                        'ConversationId': {'S': id},
                        'Timestamp': {
                            'N': "" + str(mstimetwo)
                        },
                        'Message': {'S': event['body']},
                        'Sender': {'S': 'Student'}
                    }
                )
            return {
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': 'https://arihant-serverless-chat-app.s3.us-east-2.amazonaws.com'
                    },
                    'statusCode': 200}

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

        
def loadMessages(data, id, messages):
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
        loadMessages(data, id, messages)
    else:
        return (loadConversationDetail(id, messages))
    
def loadConversationDetail(id, messages):
    data = dynamodb.query(
            TableName= 'Chat-conversations',
            Select= 'ALL_ATTRIBUTES',
            KeyConditionExpression= 'ConversationId = :id',
            ExpressionAttributeValues= {':id': {'S': id}}
        )
    participants = []
    for item in data['Items']:
        participants.append(item['Username']['S'])
    return {
            'id': id,
            'participants': participants,
            'last': messages[len(messages)-1]['time'],
            'messages': messages
    }


def handleIdQuery(data, ids, username):
    for item in data['Items']:
        ids.append(item['ConversationId']['S'])
    if 'LastEvaluatedKey' in data:
        data = dynamodb.query(
                TableName= 'Chat-conversations',
                IndexName= 'Username-ConversationId-index',
                Select= 'ALL_PROJECTED_ATTRIBUTES',
                KeyConditionExpression= 'Username = :username',
                ExpressionAttributeValues= {':username': {'S': username}},
                ExclusiveStartKey= data['LastEvaluatedKey']
            )
        handleIdQuery(data, ids, username)
    else:
        return loadDetails(ids)


def loadDetails(ids):
    convos = []
    for id in ids:
        convo = {'id': id}
        convos.append(convo)

    if len(convos) > 0:
        for convo in convos:
            return loadConvoLast(convo, convos)
    else:
        return convos


def loadConvoLast(convo, convos):
    data = dynamodb.query(
        TableName= 'Chat-Messages',
        ProjectionExpression= '#T',
        Limit= 1,
        ScanIndexForward= False,
        KeyConditionExpression= 'ConversationId = :id',
        ExpressionAttributeNames= {'#T': 'Timestamp'},
        ExpressionAttributeValues= {':id': {'S': convo['id']}}
    )
    if len(data['Items'])==1:
        convo['last'] = int(data['Items'][0]['Timestamp']['N'])
    return loadConvoParticipants(convo, convos)


def loadConvoParticipants(convo, convos):
    data = dynamodb.query(
            TableName= 'Chat-conversations',
            Select= 'ALL_ATTRIBUTES',
            KeyConditionExpression= 'ConversationId = :id',
            ExpressionAttributeValues= {':id': {'S': convo['id']}}
        )
    participants = []
    for item in data['Items']:
        participants.append(item['Username']['S'])
    convo['participants'] = participants
    return convos
    if finished(convos):
        return convos


def finished(convos):
    for c in convos:
        if c['participants']:
            return False
    return True
