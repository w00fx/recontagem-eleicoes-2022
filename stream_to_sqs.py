import json
import os
import boto3
import libs.json_util as dynamo_json


SQS_URL = os.environ['SQS_URL']
sqs_client = boto3.client('sqs')

def enviar_sqs(msgs):
    sqs_client.send_message_batch(
        QueueUrl=SQS_URL,
        Entries=msgs
    )


def lambda_handler(event, context):
    mgs_to_sqs = []
    for record in event.get('Records'):
        if record.get('eventName') == 'INSERT':
            sqs_data = {}
            
            sqs_data['creation_data'] = record.get('dynamodb').get('ApproximateCreationDateTime')
            image = dynamo_json.loads(record.get('dynamodb').get('NewImage'), as_dict=True)
            
            sqs_data['estado'] = image.get('estado')
            sqs_data['file_name'] = image.get('file_name')
            sqs_data['bucket'] = image.get('bucket')
            
            mgs_to_sqs.append(
                {
                    'Id': sqs_data.get('file_name').split('.')[0],
                    'MessageBody': json.dumps(sqs_data)
                }
            )
        else:
            print('Nao e um evento de INSERT.')

    if mgs_to_sqs:
        enviar_sqs(mgs_to_sqs)
        print('Mensagens enviadas ao SQS.')
