import requests
import boto3
import uuid
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    url_objetivo = "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados"

    response = requests.get(
        "https://app.scrapingbee.com/api/v1/",
        params={
            "api_key": "Q28G9Y461TDRVIEDBS9ZG9UMH4BAWBC70NW133N5KPKY311E9L3SX10PKQVJ2D4L2KI9DJTYY7813CJV",
            "url": url_objetivo,
            "render_js": "true",
            "wait": "5000"  # Esperar 5 segundos para que cargue la tabla
        }
    )

    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página usando ScrapingBee'
        }

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find('table')
    if not table:
        return {
            'statusCode': 404,
            'body': soup.prettify()[:5000]  # Para debug, puedes quitar esto luego
        }

    headers = [th.text.strip() for th in table.find_all('th')]
    rows = []
    for tr in table.find_all('tr')[1:11]:
        cells = tr.find_all('td')
        if len(cells) != len(headers):
            continue
        row_data = {headers[i]: cells[i].text.strip() for i in range(len(cells))}
        row_data['id'] = str(uuid.uuid4())
        rows.append(row_data)

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('SismosIGP')

    scan = table.scan()
    with table.batch_writer() as batch:
        for item in scan.get('Items', []):
            batch.delete_item(Key={'id': item['id']})

    with table.batch_writer() as batch:
        for row in rows:
            batch.put_item(Item=row)

    return {
        'statusCode': 200,
        'body': rows
    }
