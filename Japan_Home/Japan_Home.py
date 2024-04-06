## -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")


class Parser:
    links_to_parse = [f'https://omsk.yapdomik.ru/']

    @staticmethod
    def get_sity_by_link(self, link):
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Accept": "*/*"}
        response = requests.get(link, headers=HEADERS)
        print(response)
        soup = BeautifulSoup(response.text, 'html.parser')
        address = list(set([a['href'] for a in soup.select('div.city-select__list a')]))
        address.append(link)
        for url in address:
            try:
                response = requests.get(url=url, headers=HEADERS)
                print(response)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    name = soup.find('div', class_="site-footer__description").find_next('h2').text.split('"')[1]
                    print(name)
                    city_name = soup.find('div', class_="site-footer__address-list").find_all('h2')[1].get_text(strip=True).replace(':', '')
                    # city = city_name[:-1] if city_name.endswith(':') else city_name  // аналогично replace
                    print(city_name)
                    adres = [li.get_text(strip=True).replace('\u200b', '') for li in soup.find('div', class_='site-footer__address-list').find_all('li')]
                    print(adres)
                    phones = soup.find('a', class_="link link--black link--underline").text
                    print(phones)
                    for adress in adres:
                        address = f"{city_name.replace('г.', '').strip()}, {adress}"
                        full_address = f"{name}, {city_name}, {adress}"
                        self.japan_home_address(adres=full_address, phone=phones, name=name, all_address=address)

            except Exception as e:
                print(e)

    def japan_home_address(self, adres, phone, name, all_address):
        url = f'https://search-maps.yandex.ru/v1/?text={adres}&ll=25.321746,55.368328&spn=0.552069,0.400552&lang=ru_RU&apikey={API_KEY}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            # Извлекаем данные из ответа API
            try:
                address = data['features'][0]['properties']['CompanyMetaData']['address']  # Находит адрес указанный в Яндекс картах
                coordinates1 = data['features'][0]['geometry']['coordinates'][1]  # Координаты 1
                coordinates2 = data['features'][0]['geometry']['coordinates'][0]  # Координаты 2
                working_hours = data['features'][0]['properties']['CompanyMetaData']['Hours']['text']  # Режим Работы
                print("Адрес:", address)
                print("Координаты:", f"{coordinates1}, {coordinates2}")
                print("Режим работы:", working_hours)
                japan_info = (
                    {"name": name,
                     "address": all_address,
                     "latlon": [coordinates1, coordinates2],
                     "phones": [phone],
                     "working_hours": [working_hours]}
                )
                self.save_json(japan_info)  # Передаем словарь на сохранение
            except (KeyError, IndexError) as e:
                print(f"Произошла ошибка: {e}")
        else:
            print("Ошибка при обращении к API.")

    # Сохраняем данные в JSON
    def save_json(self, japan_info):
        filename = "japan_home_address.json"
        try:
            with open(filename, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []

            # Проверяем наличие такого же словаря в данных
        if japan_info not in data:
            # Добавляем новый элемент к существующим данным
            data.append(japan_info)

            # Записываем обновленные данные в JSON
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
                print("Информация успешно добавлена в файл.")
        else:
            print("Такая информация уже существует в файле, запись не выполнена.")

    def run(self):
        for link in Parser.links_to_parse:
            self.get_sity_by_link(self, link)


Parser().run()
