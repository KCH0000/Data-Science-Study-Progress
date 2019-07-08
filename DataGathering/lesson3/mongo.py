import requests  # для запросов на сайт
import re  # Парсить максимальную и минимальную зарплату
import datetime  # Дата актулаьности валюты
from bs4 import BeautifulSoup as bs  # Для обработки HTML
from pymongo import MongoClient, ASCENDING, errors as mongo_e  # клиент к mongodb
from urllib.parse import quote_plus  # Форматирование пользователя и пароля

# Блок настроек сервера

DB_URL = 'localhost'
DB_USERNAME = 'root'
DB_PASSWORD = 'root'
SAVE_TO_DB = True  # True - программа будет читать фаил и сохранять в базу. False - будут работать тольк чтение
VAL = ['USD', 'EUR', 'RUR']  # Валюты

# Окончание блока настроек сервера


def connect_mongodb(db):
    """
    Функция получает название
    :param db:
    :return:
    """
    username = quote_plus(DB_USERNAME)
    password = quote_plus(DB_PASSWORD)
    db_url = quote_plus(DB_URL)
    try:
        connection = MongoClient(db_url,
                                 username=username,
                                 password=password)
        return connection[db]
    except mongo_e.ConnectionFailure:
        print('Mongo: База данных недоступна')


def load_hh_data_from_file(file):
    data = []
    try:
        with open(file, 'rt', encoding='utf-8') as input_file:
            for line in input_file:
                i = 0
                if len(line.split('\t')) != 5:
                    print(f"File: error in line {i}\n")
                else:
                    parse_line = line.split('\t')
                    vacancy = {
                        'name': parse_line[0],
                        'min': int(parse_line[1]),
                        'max': int(parse_line[2]),
                        'currency': parse_line[3],
                        'url': parse_line[4].replace('\n', '')
                    }
                    data.append(vacancy)
                    i += 1
        return data
    except IOError as e:
        print('File: ошибка файла ', e)
        return False


def save_hh_to_mongodb(db, coll_name, vacancies):
    success, errors = 0, 0
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    coll.create_index([('url', ASCENDING)], unique=True)
    print(vacancies)
    for vacancy in vacancies:
        try:
            coll.insert_one(vacancy)
            success += 1
        except mongo_e.DuplicateKeyError:
            # print(f'Mongo: запись уже существуе \n {vacancy} ')
            errors += 1
        except Exception as e:
            print(f'Mongo: ошибка {e}')
    print(f'Mongo: добавлено {success}, ошибок {errors} в коллекции {coll_name}')
    return True


def get_vacancies_more(db, coll_name, compensation, max_empty=True):
    vacancies = []
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return []
    for currency in VAL:
        curs = get_currency_price(db, 'currency', currency)
        if not curs:
            continue
        query = {'$and': [
                    {'currency': currency},
                    {'$or': [
                        {'max': 0 if max_empty else -1},
                        {'max': {'$gt': compensation/curs}}
                        ]}
        ]}
        for vacancy in coll.find(query):
            vacancies.append(vacancy)
    return vacancies


def save_current_currency(db, coll_name):
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    coll.create_index([('currency', ASCENDING), ('date', ASCENDING)], unique=True)
    try:
        coll.insert_one({'currency': 'RUR',
                         'price': 1,
                         'date': datetime.datetime.today().strftime("%Y-%m-%d")})
    except mongo_e.DuplicateKeyError:
        print('Mongo: курсы уже получены')
        return
    html = requests.get('https://www.banki.ru/products/currency/cash/moskva/').text
    soup = bs(html, 'lxml')
    for val in soup.select('.currency-table__bordered-row'):
        currency_name = re.findall('\w+', val.find('td', {'class': 'currency-table__large-text'}).text)[0]
        currency_price = float(
            re.findall('\S+', val.find('div', {'class': 'currency-table__large-text'}).text)[0].replace(',', '.'))
        try:
            coll.insert_one({'currency': currency_name,
                             'price': currency_price,
                             'date': datetime.datetime.today().strftime("%Y-%m-%d")})
        except Exception as e:
            print('Mongo: ошибка базы данных при сохранеии валют ', e)


def get_currency_price(db, coll_name, currency):
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    try:
        last_price = coll.find({'currency': currency},
                               {'_id': 0, 'price': 1}).sort('date', -1).limit(1)[0]['price']
        return float(last_price)
    except Exception as e:
        print('Mongo: ошибка БД ', e)
        return False


if __name__ == '__main__':
    db_ = connect_mongodb('db')
    if SAVE_TO_DB:
        vacancies_ = load_hh_data_from_file('output.txt')
        if vacancies_:
            save_hh_to_mongodb(db_, 'vacancies', vacancies_)
    save_current_currency(db_, 'currency')
    for x in get_vacancies_more(db_, 'vacancies', 180000, max_empty=False):
        print(x)

