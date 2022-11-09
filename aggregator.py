import json
import boto3
import os
import libs.json_util as dynamo_json
from collections import defaultdict, Counter
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

TABELA_ESTADO = os.environ['TABELA_ESTADO']
tabela_aggr = boto3.resource('dynamodb').Table(TABELA_ESTADO)


def criar_update_item(votos):
    update_exp = 'SET '
    exp_attr = {}
    attr_names = {}

    for i, (candidato, qt_votos) in enumerate(votos.items()):
        if update_exp != 'SET ':
            update_exp = update_exp + ', '
        update_exp = update_exp + f'#{i} = #{i} + :{i}'
        exp_attr[f':{i}'] = qt_votos
        attr_names[f'#{i}'] = str(candidato)

    update_exp = update_exp + ', #version = #version + :inc'
    attr_names[f'#version'] = 'version'
    exp_attr[f':inc'] = 1
    print(update_exp)

    return update_exp, exp_attr, attr_names


def aggregar_valores(estado, update_exp, exp_attr, attr_names, teste=False):

    version = tabela_aggr.get_item(
        Key={'estado': estado}
    )['Item']['version']

    try:
        tabela_aggr.update_item(
            Key={'estado': estado},
            UpdateExpression=update_exp,
            ExpressionAttributeNames=attr_names,
            ExpressionAttributeValues=exp_attr,
            ConditionExpression=Attr('version').eq(version)
        )
        print(f'Agregacao feita para o estado {estado}.')
    except ClientError as e:
        print('Versao nao bate. Tentando recursivamente.')
        aggregar_valores(
            estado, update_exp, exp_attr, attr_names, teste=True
        )


def lambda_handler(event, context):
    print(json.dumps(event))

    all_aggr = {}

    for record in event.get('Records'):
        if record.get('eventName') == 'INSERT':
            image = dynamo_json.loads(record.get('dynamodb').get('NewImage'), as_dict=True)
            estado = image.get('estado')
            votos_proc = image.get('votos_processados')
            if estado not in all_aggr:
                votos_proc['rdvs'] = 1
                all_aggr.setdefault(estado, votos_proc)
            else:
                votos_proc['rdvs'] =+ 1
                inc1 = Counter(all_aggr[estado])
                inc2 = Counter(votos_proc)
                all_aggr[estado] = inc1 + inc2

    for estado, resultados in all_aggr.items():
        if type(resultados) is dict:
            pass
        else:
            resultados = dict(resultados)

        update_exp, exp_attr, attr_names = criar_update_item(resultados)

        #Agregar valores para estado
        aggregar_valores(
            estado,
            update_exp,
            exp_attr,
            attr_names
        )

        #agregar valores para pais
        aggregar_valores(
            'br',
            update_exp,
            exp_attr,
            attr_names
        )

    return {
        'statusCode': 200,
    }
