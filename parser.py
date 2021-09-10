import traceback
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import psycopg2
import pandas as pd
import lxml

itemsToAdd = {
    # 'Opletka light pink': ['https://www.wildberries.ru/catalog/8618192/detail.aspx?size=29100958', 5],
    # 'Opletka bright pink': ['https://www.wildberries.ru/catalog/8618199/detail.aspx?size=29100965', 5],
    # 'Depil lotion': ['https://www.wildberries.ru/catalog/21370282/detail.aspx?size=54366342', 2],
    # 'Ghi': ['https://www.wildberries.ru/catalog/12650422/detail.aspx?size=39068569', 2],
    # 'Crocs Black': ['https://www.wildberries.ru/catalog/17970897/detail.aspx?size=49259048'],
    # 'Crocs lilac': ['https://www.wildberries.ru/catalog/18814253/detail.aspx?size=50705766'],
    # 'Bandana fuchsia': ['https://www.wildberries.ru/catalog/28103090/detail.aspx?size=63768471', 2],
    # 'Bandana green': ['https://www.wildberries.ru/catalog/28103081/detail.aspx?size=63768462', 2],
    # 'Bandana violet': ['https://www.wildberries.ru/catalog/33540972/detail.aspx?size=71283651', 2],
    # 'Bandana turkish watermelon': ['https://www.wildberries.ru/catalog/25249076/detail.aspx?size=59107791', 2],
    # 'Dark striped skirt': ['https://www.wildberries.ru/catalog/12261911/detail.aspx?size=38213553', 7]
}

class Parser:
    def __init__(self, current_discount=12):
        pd.set_option('display.max_rows', 1000)
        pd.set_option('display.max_columns', 1000)
        pd.set_option("display.colheader_justify", "center")
        pd.set_option('display.width', 600)
        pd.set_option('max_colwidth', 30)
        pd.set_option('display.expand_frame_repr', False)

        self.connection = psycopg2.connect(
            host='ec2-99-80-200-225.eu-west-1.compute.amazonaws.com',
            port='5432',
            user='gsoxtcmgsqbxbi',
            password='42bd9db46f114e1424c2180635a13daf02b6e08cc8383dcf2ba8973748870b85',
            database='dbfo3d84h3ca49')

        self.current_discount = current_discount


    def get_db_data(self):
        try:
            itemsFromDB_df = pd.read_sql_query('''select * from wb''', self.connection)
        except Exception:
            traceback.print_exc()
        else:
            return itemsFromDB_df

    def insert_new(self, current_discount):
        cursor = self.connection.cursor()
        for key, value in itemsToAdd.items():
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
            print(price, wbTitle, articul)
            if maxDiscount:
                minMyPrice = int(price) - int(price) * int(maxDiscount) / 100
            else:
                minMyPrice = int(price) - int(price) * int(current_discount) / 100
            query = """ INSERT INTO wb (articul, wb_title, my_title, min_my_price, min_price_date, url, min_base_price, my_discount, max_discount) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (articul) DO UPDATE
              SET articul = excluded.articul, wb_title = excluded.wb_title, min_my_price = excluded.min_my_price
            """
            values = (articul, wbTitle, name, minMyPrice, datetime.now().date(), url, price, current_discount, maxDiscount)

            try:
                cursor.execute(query, values)
                self.connection.commit()
            except Exception:
                traceback.print_exc()
        cursor.close()

    # insert_new(current_discount)

    def update_prices(self):
        current_discount = self.current_discount
        myDB = self.get_db_data()
        cursor = self.connection.cursor()
        for date, row in myDB.T.iteritems():
            url = row['url']
            min_my_price = row['min_my_price']
            max_discount = row['max_discount']
            item_id = row['item_id']
            my_title = row['my_title']
            min_base_price = row['min_base_price']
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            base_price = int(soup.find('span', class_='price-block__final-price').text.strip().replace(' ₽', '').replace(' ', ''))
            if base_price == None:
                continue
            if pd.isna(max_discount):
                current_min_price = round(base_price - (base_price * current_discount) / 100)
            else:
                current_min_price = round(base_price - (base_price * max_discount) / 100)
                # Check current discount on item:
                if current_min_price < min_my_price:
                    current_item_discount = int(input(f"Enter current discount for item {url}:\n"))
                    if current_item_discount != max_discount:
                        current_min_price = round(base_price - (base_price * current_item_discount) / 100)
            #Update:
            if current_min_price < min_my_price or base_price < min_base_price:
                query = '''
                    UPDATE wb
                    SET min_my_price = %s, my_discount = %s, min_price_date = current_date, min_base_price = %s
                    WHERE item_id = %s
                '''
                cursor.execute(query, (min(current_min_price, min_my_price), current_discount, min(min_base_price, base_price), item_id))
                self.connection.commit()
                print(f'\nDB data changed for: {my_title}. Min price changed from {min_my_price} to {min(current_min_price, min_my_price)}, min base price changed from {min_base_price} to {min(min_base_price, base_price)}')
        cursor.close()
        print('update_prices finished')
        return True
    # update_prices(current_discount)
    def close_connection(self):
        self.connection.close()

if __name__ == '__main__':

    print('Parser запущен сам по себе')

    current_discount = int((input('Enter current discount: ')))
    parser = Parser(current_discount)
    raise SystemExit(parser.update_prices(current_discount))
else:
    print('Parser импортирован в другой модуль.')
