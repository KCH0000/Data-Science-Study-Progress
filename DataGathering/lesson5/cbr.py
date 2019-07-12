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


def get_currency_code(currency_name: str):
    """
    Функция обращается на сайт cbr и возвращет код валюты переданной в строковом виде
    :param currency_name: международное имя валюты, например USD
    :return:
    """
    currency_name = currency_name.upper()
    url = 'http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL'
    client = Client(url)
    currencies_from_cbr = client.service.EnumValutes(False)._value_1._value_1
    currencies_filtered = [val for val in currencies_from_cbr if val['EnumValutes']['VcharCode'] == currency_name]
    if len(currencies_filtered) == 1:
        return currencies_filtered[0]['EnumValutes']['Vcode']
    else:
        print('Неверное название валюты')
        return False


def get_currency_rate_from_cbr(currency_name: str, start_date='', stop_date=datetime.datetime.today()):
    """
    Функция получает навзание валюты в междунароном виде и возвращает курса между датами.
    Если не указана дата начала, то возвращается курс на даты, то возрвзается курс на сегодня
    Если указана только дата начала, то возвращаются курсы от даты начала на сегодня
    :param currency_name: название валюты
    :param start_date: дата начала
    :param stop_date: дата окончания
    :return:
    """
    currency_name = currency_name.upper()
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
    """
    Функция хранит курсы в базе монго. Получает подготовленный список курсов
    :param db: указтель на базу
    :param coll_name: название коллекции для хранения
    :param currencies_rates: список курсов валют
    :return:
    """
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    # Проверка уникальности индекс Название_валюты + дата_курса
    coll.create_index([('currency', ASCENDING), ('date', ASCENDING)], unique=True)
    committed, passed = 0, 0
    for rate in currencies_rates:
        try:
            coll.insert_one(rate)
            committed += 1
        except mongo_e.DuplicateKeyError:
            passed += 1
            pass
    print(f'MONGO: committed - {committed}, passed - {passed}')


def znal_bi_postelil_bi_solomku(db, coll_name, currency_name: str,
                                start_date, stop_date=datetime.datetime.today().strftime("%Y-%m-%d")):
    """
    Функция причиняет боль и страдание для всех кто ее запускает

    Функция получает из базы максимальные и минимальные курсы для указанной валюты за период. Если данных в базе
    не хватает, то данные предварительно загружаются с сайта ЦБ РФ
    :param db: указатель на базу
    :param coll_name: название коллекции
    :param currency_name: название валюты в международном виде
    :param start_date: дата начала
    :param stop_date: дата окончания
    :return:
    """
    try:
        if coll_name not in db.list_collection_names():
            raise mongo_e.CollectionInvalid
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    currency_name = currency_name.upper()
    last_date = coll.find({'name': currency_name}, {'_id': 0, 'date': 1}).sort('date', -1).limit(1)[0]['date']
    first_date = coll.find({'name': currency_name}, {'_id': 0, 'date': 1}).sort('date', +1).limit(1)[0]['date']
    if start_date < first_date or last_date < start_date:
        rates = get_currency_rate_from_cbr(currency_name, start_date, stop_date)
        save_currencies_rates_to_mongo(db, coll_name, rates)
    prices = coll.find({'$and': [
                    {'name': currency_name},
                    {'date': {'$gte': start_date}},
                    {'date': {'$lte': stop_date}}
        ]}, {'_id': 0})
    if prices:
        best_price = prices.sort('price', -1).limit(1)[0]
        weak_price = prices.sort('price', +1).limit(1)[0]
        return weak_price, best_price
    return False, False


if __name__ == '__main__':
    db_ = connect_mongodb('db')
    v_name = 'usd'
    # v_rates = get_currency_rate_from_cbr('USD', '2017-07-10')
    weak_price, best_price = znal_bi_postelil_bi_solomku(db_, 'currencies', v_name, '2016-06-01')
    if weak_price and best_price:
        print(f'Лучшее время для покупки {weak_price["name"]} {weak_price["date"]} по цене {weak_price["price"]}')
        print(f'Лучшее время для продажи {best_price["name"]} {best_price["date"]} по цене {best_price["price"]}')
