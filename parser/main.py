import requests
from bs4 import BeautifulSoup
import pandas as pd

url = 'https://iotvega.com/product'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')
items = soup.find_all('div', class_='product-item')

data = []

for n, i in enumerate(items, start=1):
    itemName = i.find(itemprop="name").text.strip()
    itemPrice = i.find(itemprop='price').text.strip()

    data.append([n, itemPrice, itemName])

    formatted_output = f'{n}: {itemPrice} за {itemName}'
    print(formatted_output)

df = pd.DataFrame(data, columns=['Номер', 'Цена', 'Наименование'])

df.to_excel('output.xlsx')
