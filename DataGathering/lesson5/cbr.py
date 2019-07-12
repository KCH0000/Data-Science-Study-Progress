from pymongo import MongoClient, ASCENDING, errors as mongo_e  # клиент к mongodb
from urllib.parse import quote_plus  # Форматирование пользователя и пароля
from zeep import Client, exceptions as zeep_e
import datetime
# Блок настроек сервера

DB_URL = 'localhost'
DB_USERNAME = 'root'
DB_PASSWORD = 'root'
SAVE_TO_DB = True  # True - программа будет читать фаил и сохранять в базу. False - будут работать только чтение
VAL = ['USD', 'EUR', 'RUR']  # Валюты

# Окончание блока настроек сервера


def connect_mongodb(db):
    """
    Функция получает название базы данных у возвращает указатель на соединение.
    Для авторизации используются глобальные переменные
    :param db: название базы данныхз
    :return: cursor
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


def get_currency_code(currency_name):
    url = 'http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL'
    client = Client(url)
    currencies_from_cbr = client.service.EnumValutes(False)._value_1._value_1
    currencies_filtered = [val for val in currencies_from_cbr if val['EnumValutes']['VcharCode'] == currency_name]
    if len(currencies_filtered) == 1:
        return currencies_filtered[0]['EnumValutes']['Vcode']
    else:
        print('Неверное название валюты')
        return False


def get_currency_rate_from_cbr(currency_name, start_date='', stop_date=datetime.datetime.today()):
    url = 'http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL'
    client = Client(url)
    currency_code = get_currency_code(currency_name)
    if not currency_code:
        return []
    if start_date == '':
        start_date = datetime.datetime(stop_date.year, stop_date.month, stop_date.day)
    try:
        val_rates = client.service.GetCursDynamic(start_date, stop_date, currency_code)._value_1._value_1
    except zeep_e as e:
        print('Ошибка запроса: ', e)
        return []
    except AttributeError as e:
        print('Неверный ответ сервера: ', e)
        return []
    currency_rates = []
    for val_rate in val_rates:
        currency_rates.append({'name': currency_name,
                               'price': float(val_rate['ValuteCursDynamic']['Vcurs']),
                               'date': val_rate['ValuteCursDynamic']['CursDate'].strftime("%Y-%m-%d")
                               })
    return currency_rates


def save_currencies_rates_to_mongo(db, coll_name, currencies_rates):
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    # Проверка уникальности индекс Название_валюты + дата_курса
    coll.create_index([('currency', ASCENDING), ('date', ASCENDING)], unique=True)
    for rate in currencies_rates:
        try:
            coll.insert_one(rate)
        except mongo_e.DuplicateKeyError:
            pass

# get_currency_rate_from_cbr('USD', '2017-07-10')

