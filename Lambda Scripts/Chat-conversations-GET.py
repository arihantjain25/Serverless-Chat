import json
import boto3

dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    try:
        data = dynamodb.query(
            TableName= 'Chat-conversations',
            IndexName= 'Username-ConversationId-index',   
            Select= 'ALL_PROJECTED_ATTRIBUTES',
            KeyConditionExpression= 'Username = :username',
            ExpressionAttributeValues= {':username': {'S': event['cognitoUsername']}}
            )
        content = handleIdQuery(data, [], event['cognitoUsername'])
        return content
                
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
