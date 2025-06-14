import requests
import boto3
import uuid
from datetime import datetime

def lambda_handler(event, context):
    # Determinar año (puedes parametrizarlo desde `event` si lo deseas)
    year = datetime.utcnow().year
    url = f"https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/{year}"

    # Llamada al endpoint JSON
    response = requests.get(url)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder al endpoint de sismos'
        }

    # La respuesta es directamente una lista de dicts
    sismos = response.json()

    # Volcar a un formato uniforme para DynamoDB
    items = []
    for i, s in enumerate(sismos, start=1):
        items.append({
            'id': str(uuid.uuid4()),
            '#': i,
            'codigo': s.get('codigo'),
            'fecha_local': s.get('fecha_local'),
            'hora_local': s.get('hora_local'),
            'fecha_utc': s.get('fecha_utc'),
            'hora_utc': s.get('hora_utc'),
            'latitud': float(s.get('latitud', 0)),
            'longitud': float(s.get('longitud', 0)),
            'magnitud': float(s.get('magnitud', 0)),
            'profundidad': s.get('profundidad'),
            'referencia': s.get('referencia'),
            'intensidad': s.get('intensidad'),
        })

    # Guardar los datos en DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScraping2')

    # Borrar todos los ítems existentes (opcional)
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan.get('Items', []):
            batch.delete_item(Key={'id': each['id']})

    # Insertar los nuevos datos
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

    # Retornar el resultado como JSON
    return {
        'statusCode': 200,
        'body': items
    }
