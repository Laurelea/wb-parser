import traceback
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import psycopg2

connection = psycopg2.connect(
    host='ec2-99-80-200-225.eu-west-1.compute.amazonaws.com',
    port='5432',
    user='gsoxtcmgsqbxbi',
    password='42bd9db46f114e1424c2180635a13daf02b6e08cc8383dcf2ba8973748870b85',
    database='dbfo3d84h3ca49')

cursor = connection.cursor()


itemsToMonitor = {
    'Opletka light pink': ['https://www.wildberries.ru/catalog/8618192/detail.aspx?size=29100958', 5],
    'Opletka bright pink': ['https://www.wildberries.ru/catalog/8618199/detail.aspx?size=29100965', 5],
    'Depil lotion': ['https://www.wildberries.ru/catalog/21370282/detail.aspx?size=54366342', 2],
    'Ghi': ['https://www.wildberries.ru/catalog/12650422/detail.aspx?size=39068569', 2],
    # 'Crocs Black': ['https://www.wildberries.ru/catalog/17970897/detail.aspx?size=49259048'],
    # 'Crocs lilac': ['https://www.wildberries.ru/catalog/18814253/detail.aspx?size=50705766'],
    # 'Bandana fuchsia': ['https://www.wildberries.ru/catalog/28103090/detail.aspx?size=63768471', 2],
    # 'Bandana green': ['https://www.wildberries.ru/catalog/28103081/detail.aspx?size=63768462', 2],
    # 'Bandana violet': ['https://www.wildberries.ru/catalog/33540972/detail.aspx?size=71283651', 2],
    # 'Bandana turkish watermelon': ['https://www.wildberries.ru/catalog/25249076/detail.aspx?size=59107791', 2],
    # 'Dark striped skirt': ['https://www.wildberries.ru/catalog/12261911/detail.aspx?size=38213553', 7]
}

#Читать из ДБ старые данные по мин цене

current_discount = 14

for key, value in itemsToMonitor.items():
    url = value[0]
    maxDiscount = value[1] if len(value) > 1 else None
    name = key
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    price = soup.find('span', class_='price-block__final-price').text.strip().replace(' ₽', '').replace(' ', '')
    print(f'Price: {price}')
    wbTitle = ' / '.join([i.text for i in soup.find('h1', class_='same-part-kt__header').find_all('span')])[:20]
    print(f'wbTitle: {wbTitle}')

    articul = soup.find('span', {'data-link': "text{: selectedNomenclature^cod1S}"}).text
    # for elem in wbTitle:
    #     print('elem: ', elem)
    print(price, wbTitle, articul)
    if maxDiscount:
        minMyPrice = int(price) - int(price) * int(maxDiscount) / 100
    else:
        minMyPrice = int(price) - int(price) * int(current_discount) / 100
    #Добавить условие для мин цены, поменять на UPDATE
    query = """ INSERT INTO wb (articul, wb_title, my_title, min_my_price, min_price_date, url, min_base_price, my_discount, max_discount) 
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (articul) DO UPDATE
      SET articul = excluded.articul, wb_title = excluded.wb_title, min_my_price = excluded.min_my_price
    """
    values = (articul, wbTitle, name, minMyPrice, datetime.now().date(), url, price, current_discount, maxDiscount)

    try:
        cursor.execute(query, values)
        connection.commit()
        count = cursor.rowcount
        print(count, "Record inserted successfully into mobile table")
    except Exception as error:
        traceback.print_exc()

cursor.close()
connection.close()