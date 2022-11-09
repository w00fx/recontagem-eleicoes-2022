import boto3

dynamo_table = boto3.resource('dynamodb').Table('TABELA_RESULTADO_ESTADOS')

lista_estados = "ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to zz br"

for estado in lista_estados.split(' '):
    dynamo_table.put_item(
        Item={
            "12": 0,
            "13": 0,
            "14": 0,
            "15": 0,
            "16": 0,
            "21": 0,
            "22": 0,
            "27": 0,
            "30": 0,
            "44": 0,
            "80": 0,
            "estado": estado,
            "branco": 0,
            "nulo": 0,
            "rdvs": 0,
            "version": 0
        },
    )
    print(f'Estado {estado} inserido.')
print('Finalizado.')