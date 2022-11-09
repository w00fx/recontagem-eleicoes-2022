import json
import boto3
import os
import sys
from collections import defaultdict
from datetime import datetime
from botocore.exceptions import ClientError

sys.path.insert(0, os.environ['LIBS_PATH'])

import asn1tools

ASN1_PATH = os.environ['ASN1_PATH']
PROCESSAMENTO_TABLE = os.environ['PROCESSAMENTO_TABLE']
RESULTADOS_TABELA = os.environ['RESULTADOS_TABELA']

s3_client = boto3.client('s3')
tabela_proc = boto3.resource('dynamodb').Table(PROCESSAMENTO_TABLE)
tabela_res = boto3.resource('dynamodb').Table(RESULTADOS_TABELA)

conv = asn1tools.compile_files(ASN1_PATH)


def atualizar_status_processamento(estado, file_name):
    table = tabela_proc.update_item(
        Key={
            'estado': estado,
            'file_name': file_name
        },
        UpdateExpression="set foiProcessado = :r, processamento_finalizado = :h",
        ExpressionAttributeValues={
            ':r': True,
            ':h': int(datetime.now().timestamp())
        }
    )
    print(f'Processamento de arquivo {file_name} atualizado')


def inserir_resultado(data):
    try:
        tabela_res.put_item(
            Item=data,
            ConditionExpression="attribute_not_exists(zonasecao)"
        )
        print('RDV inserido na tabela de estado.')
    except ClientError as e:  
        if e.response['Error']['Code']=='ConditionalCheckFailedException':  
            print('Item ja existente na tabela.')
        else:
            print('Erro desconhecido.')


def get_arquivo_s3(bucket, caminho_arquivo):
    s3_object = s3_client.get_object(
        Bucket=bucket,
        Key=caminho_arquivo
    )

    return s3_object.get('Body').read()


def processar_votos(votos):
    votos_totalizados = defaultdict(int)
    total_votos = 0

    for voto in votos.get('votos'):
        tipo_voto = voto.get('tipoVoto')
        if tipo_voto == 'nominal':
            votos_totalizados[voto.get('digitacao')] += 1
            total_votos += 1
        elif tipo_voto == 'branco':
            votos_totalizados['branco'] += 1
            total_votos += 1
        elif tipo_voto == 'nulo':
            votos_totalizados['nulo'] += 1
            total_votos += 1

    return dict(votos_totalizados), total_votos


def lambda_handler(event, context):
    rdvs_list = []
    for record in event.get('Records'):
        final_data = {}
        sqs_data = json.loads(record.get('body'))

        estado = sqs_data.get('estado')
        file_name = sqs_data.get('file_name')
        bucket = sqs_data.get('bucket')

        caminho_s3 = f'{estado}/{file_name}'

        rdv_encoded = get_arquivo_s3(bucket, caminho_s3)
        rdv_decoded = conv.decode("EntidadeResultadoRDV", rdv_encoded)
        print(rdv_decoded)

        rdv_data = rdv_decoded.get("rdv")
        identificacao = rdv_data.get('identificacao')

        zona = f"{identificacao.get('municipioZona').get('zona'):04n}"
        secao = f"{identificacao.get('secao'):04n}"

        final_data['municipio'] = identificacao.get('municipioZona').get('municipio')
        final_data['ZONA#SECAO'] =  f'{zona}#{secao}'
        final_data['estado'] = estado

        todos_votos = rdv_data.get("eleicoes")[1]

        for votos_cargo in todos_votos:
            for votos in votos_cargo.get('votosCargos'):
                if 'presidente' in votos.get('idCargo'):
                    votos_processados, total_votos = processar_votos(votos)

        final_data['votos_processados'] = votos_processados
        final_data['total_votos'] = total_votos

        rdvs_list.append({file_name: final_data})

    for rdv in rdvs_list:
        (file_name, data), = rdv.items()
        estado = data.get('estado')
        atualizar_status_processamento(estado, file_name)
        inserir_resultado(data)

    return {}
