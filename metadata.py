import boto3
import os
from botocore.exceptions import ClientError

PROCESSAMENTO_RDVS = os.environ['PROCESSAMENTO_RDVS']

dynamo_table = boto3.resource('dynamodb').Table(PROCESSAMENTO_RDVS)

def inserir_dynamo(data, file_name):
    try:
        res = dynamo_table.put_item(
                Item=data,
                ConditionExpression='attribute_not_exists(file_name)'
            )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f'Arquivo {file_name} ja existe no DynamoDB.')

def parse_nome_arquivo(data):

    identificacao = data.get('file_name').split('-')[1]

    data['municipio'] = int(identificacao[0:5])
    data['zona'] = f"{int(identificacao[5:9]):04n}"
    data['secao'] = f"{int(identificacao[9:13]):04n}"

    return data


def lambda_handler(event, context):
    print(event)
    for record in event.get('Records'):
        data = {}

        s3_data = record.get('s3')
        
        bucket = s3_data.get('bucket').get('name')
        file_key = s3_data.get('object').get('key')
        estado, file_name = file_key.split('/')

        data['s3_file_path'] = f's3://{bucket}/{file_key}'
        data['bucket'] = bucket
        data['file_name'] = file_name
        data['foiProcessado'] = False
        data['estado'] = estado
        data = parse_nome_arquivo(data)

        inserir_dynamo(data, file_name)
