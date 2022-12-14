# Recontagem das Eleiçōes 2022

Para quaisquer dúvidas referente a esse projeto, vejam esse [link](https://medium.com/@raphaelmoura/como-eu-recontei-todos-os-votos-do-primeiro-e-segundo-turno-das-eleições-2022-usando-aws-e-eb4ff7b40c79).

Sigam esses passos para executar esse projeto:

## Criando o projeto

Esse projeto foi criado usando o Serverless-Framework. Instale seguindo as instruçōes nesse [link](https://www.serverless.com/framework/docs/getting-started).

Faça o deploy com a flag `--stage` para indicar se será primeiro ou segundo turno. Exemplo abaixo:

```bash
serverless deploy --stage 2turno 
```

E no final, execute o script Python na pasta `script` para criar todos os objetos na tabela Resultado Estados. Nao esqueca de adicionar o nome da tabela no script. Se esse script não for executado, a agregaçåo não funcionará.

```bash
python3 script/insert_dynamo.py
```

## Arquitetura do projeto
![Alt text](/Recontagem-TSE.png)