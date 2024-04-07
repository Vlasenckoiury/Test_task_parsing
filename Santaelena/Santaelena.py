## -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup
import requests
import json
from dotenv import load_dotenv
import os

from herepy import GeocoderApi

load_dotenv()
API_KEY = os.getenv("API_KEY")


class Parser:
    links_to_parse = [f'https://www.santaelena.com.co/tiendas-pasteleria/']
    # links_to_parse = [f'https://www.santaelena.com.co/tiendas-pasteleria/tiendas-pastelerias-pereira/']

    @staticmethod
    def get_sity_by_link(self, link):
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Accept": "*/*"}
        response = requests.get(link, headers=HEADERS)
        print(response)
        soup = BeautifulSoup(response.text, 'html.parser')
        self.get_address(link=link)
        if response.status_code == 200:
            link = soup.find_all('div', class_="elementor-button-wrapper")
            for links in link:
                li = links.find('a', class_="elementor-button elementor-button-link elementor-size-sm")['href']
                self.get_address(link=li)

    def get_address(self, link):
        try:
            response = requests.get(url=link)
            print(link)
            if response.status_code == 200:
                col = [33, 100, 25, 50]
                soup = BeautifulSoup(response.content, 'html.parser')
                city = soup.find('h1', class_="elementor-heading-title elementor-size-default").text.split()[-1]
                print(city)
                telefon = soup.find('div', class_="tab-pane fade show active").text.strip()
                print(telefon)
                for i in col:
                    try:
                        card = soup.find_all('div', class_=re.compile(f"elementor-column elementor-col-{i} elementor-top-column elementor-element elementor-element"))
                        for item in card:
                            try:
                                name = item.find_all('h3', class_='elementor-heading-title elementor-size-default')
                                names = None
                                name_location = None
                                for h3_tag in name:
                                    name_location = h3_tag.text.replace('  ', ' ').strip()
                                    names = f"Pastelería Santa Elena {name_location.replace("&nbsp;", "").replace('\n', ' ')}"
                                print(names)
                                info = item.find_all('div', class_="elementor-text-editor elementor-clearfix")
                                for i in info:
                                    infos = i.text
                                    address = None
                                    adres_location = None
                                    phones = "No phones"
                                    working_hours = None
                                    pattern_adres = r'(Dirección:.*?Teléfono:|Dirección:.*?Horario de atención:)'
                                    pattern_tel = r'(Teléfono:(.*?)Horario de atención:)'
                                    pattern_hours = r'Horario de atención:(.*?)$'
                                    match_adres = re.search(pattern_adres, infos, re.DOTALL)
                                    match_phones = re.search(pattern_tel, infos, re.DOTALL)
                                    match_working = re.search(pattern_hours, infos, re.DOTALL)
                                    if match_adres:
                                        adres_location = f"{(match_adres.group(1)).replace('Dirección:', '').replace('Horario de atención:', '').replace('Teléfono:', '').strip()}"
                                        address = f"{city}, {adres_location}".replace("\xa0", "").replace('\n', ' ')
                                    print(address)
                                    if match_working:
                                        working_hours = match_working.group(1).strip()
                                    res_work = self.upd_text(working_hours)
                                    print(res_work)
                                    if match_phones:
                                        phones = f"{(match_phones.group(1) or "No phones").replace('Dirección:', '').replace('Horario de atención:', '').replace('Teléfono:', '').replace('Contacto:', '').strip()}"
                                    print(phones)
                                    coordinates = self.get_coordinates(name_location, adres_location)
                                    print(coordinates)
                                    santa_elena = (
                                        {"name": names,
                                         "address": address,
                                         "latlon": [coordinates],
                                         "phones": [phones],
                                         "working_hours": [res_work]}
                                    )
                                    self.save_json(santa_elena=santa_elena)

                            except Exception as e:
                                print(e)

                    except Exception as e:
                        print(e)

        except Exception as e:
            print(e)

    def upd_text(self, working_hours):
        def replace_text(match, replacements):
            return replacements.get(match.group(0).lower(), match.group(0))

        def process_text(text):
            # Словарь с заменами
            day_map = {
                'lunes': 'mon',
                'martes': 'tue',
                'miércoles': 'wed',
                'jueves': 'thu',
                'viernes': 'fri',
                'sábado': 'sat',
                'sábados': 'sat',
                'domingos': 'sun',
                'festivos': 'holidays',
                'incluye': 'includes',
                'prestamos servicio 24 horas': '24-hour service',
            }

            # Паттерн для поиска дней недели и других текстовых фрагментов
            pattern = r'(lunes|martes|miércoles|jueves|viernes|sábado|domingos|festivos|incluye|prestamos servicio 24 horas|sábados)'

            # Замена текстовых фрагментов
            result = re.sub(pattern, lambda match: replace_text(match, day_map), text, flags=re.IGNORECASE)

            # Удаление лишних символов и форматирование
            new_text = result.replace("a.m.", "").replace("a. m.", "").replace("p.m.", "").replace("p.m", "")
            lines = new_text.split('\n')
            for i in range(len(lines)):
                lines[i] = lines[i].replace(':', '', 1).replace('  ', ' ').replace(' a ', ' - ').replace('/', '-').replace("\xa0", "")

            # Объединение строк обратно в одну строку с символом перевода строки
            return ' '.join(lines)

        # Обработка текста
        working_hours = process_text(working_hours)
        return working_hours

    def get_coordinates(self, location, adress):
        full_address = f"{location}, {adress}, Colombia"
        geocoder = GeocoderApi(API_KEY)
        response = geocoder.free_form(full_address)
        response_dict = response.as_dict()
        if response_dict:
            try:
                latitude = response_dict['items'][0]['access'][0]['lat']
                longitude = response_dict['items'][0]['access'][0]['lng']
                return latitude, longitude

            except IndexError:
                return "Не правильный адрес"

            except Exception as e:
                print(e)
        return "Не определились координаты"

    def save_json(self, santa_elena):
        filename = "Pastelería Santa Elena.json"
        try:
            with open(filename, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []

            # Проверяем наличие такого же словаря в данных
        if santa_elena not in data:
            # Добавляем новый элемент к существующим данным
            data.append(santa_elena)

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
