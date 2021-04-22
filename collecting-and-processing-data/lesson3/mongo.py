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


def load_hh_data_from_file(file):
    """
    Функция получает название файла, с форматированные данными, и преобразует данные
    в список объектов ваканский. Если фаил будет открыт с ошибкой, то функция возвращает False
    :param file: название файла
    :return: list - список ваканский0
    """
    data = []
    try:
        with open(file, 'rt', encoding='utf-8') as input_file:
            for line in input_file:
                i = 0
                if len(line.split('\t')) != 5:  # В качестве разделителя в файле использется табуляция
                    # Если результат парсинга не равен количеству полей, то запис будет пропущена.
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
    """
    Функция получает указатель на буду mongo, имя коллекции и список вакансий, и пытается сохранить в коллецию.
    Так же функция создает уникальный индекс по полю url, и каждый раз проверяет его наличие.
    Печатает количество успешно добавленных записей и колическов пропущенных.
    Возавращет True, если хотя бы одна запись была успешно добавлена, иначе False
    :param db: Указатель на базу данных
    :param coll_name: Название коллекции
    :param vacancies: список вакансий
    :return: boolean
    """
    success, errors = 0, 0
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    coll.create_index([('url', ASCENDING)], unique=True)  # Провека наличия уникальног индекса
    for vacancy in vacancies:
        try:
            coll.insert_one(vacancy)  # Добалевние идет по эелементам, а не сразу списком
            success += 1
        except mongo_e.DuplicateKeyError:
            # print(f'Mongo: запись уже существуе \n {vacancy} ')
            errors += 1
        except Exception as e:
            print(f'Mongo: ошибка {e}')
            return False
    print(f'Mongo: добавлено {success}, пропущено {errors} в коллекции {coll_name}')
    return True


def get_vacancies_more(db, coll_name, compensation, max_empty=True):
    """
    Функция получает указатель на базу, название коллекции, верхнюю границу заплаты и возвращает вакасии,
    у которых верняя граница зарплаты выше целевой.
    Фукнция по-умолчанию так же возращает вакансии у которых верхяя граница не указана.
    Функция пытается учеть валюту в которой указана зарплата приводя ее к рублевому эквиваленту.
    :param db: указатель на базу данных
    :param coll_name: название коллекции по которой будет прозводиться запрос
    :param compensation: верхняя граница запрлаты
    :param max_empty: параметр по которому выводят зарплаты без верхей границы. True-выводить, False-пропускать
    :return: список вакансий удовлетворящих условию
    """
    vacancies = []
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return []
    for currency in VAL:  # Поиск просходит по известным валютам, иначе невозможно привести к рублю
        curs = get_currency_price(db, 'currency', currency)  # Запрос в коллекцию последнего курса
        if not curs:  # Если курс валюты неизвестен, то запрос пропускается
            continue
        query = {'$and': [         # Запрашиваем записи у которых
                    {'currency': currency},  # Целева валюта AND
                    {'$or': [
                        {'max': 0 if max_empty else -1},  # Запралта указака или нет в зависимости от параметра OR
                        {'max': {'$gt': compensation/curs}}  # Запралата больше целевого значения
                        ]}
        ]}
        for vacancy in coll.find(query):
            vacancies.append(vacancy)
    return vacancies


def save_current_currency(db, coll_name):
    """
    Функция получате указать на базу данных и название целевой коллекции для сохранниея.
    Функция проверяет собирались ли сегодня курса USD и EUR, если да, то завершает свою работу, если нет,
    то собирает курс текущего дня с сайта banki.ru и сохраняте в базу.
    :param db: указатель на базу данных
    :param coll_name: имя коллекции для сохранения
    :return: ничего не возращает
    """
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    # Проверка уникальности индекс Название_валюты + дата_курса
    coll.create_index([('currency', ASCENDING), ('date', ASCENDING)], unique=True)
    try:
        # У базовой валюты курс всегда 1, если он сегодня обновлялся, то считается, что другие курсы обновлены
        coll.insert_one({'currency': 'RUR',
                         'price': 1,
                         'date': datetime.datetime.today().strftime("%Y-%m-%d")})
    except mongo_e.DuplicateKeyError:
        print('Mongo: курсы уже получены')
        return
    # Начало парсинга курсов с сайта banki.ru
    # todo: вынести в отделдную фунцию
    html = requests.get('https://www.banki.ru/products/currency/cash/moskva/').text
    soup = bs(html, 'lxml')
    for val in soup.select('.currency-table__bordered-row'):
        currency_name = re.findall('\w+', val.find('td', {'class': 'currency-table__large-text'}).text)[0]
        currency_price = float(
            re.findall('\S+', val.find('div', {'class': 'currency-table__large-text'}).text)[0].replace(',', '.'))
        try:
            coll.insert_one({'currency': currency_name,  # Название валюты
                             'price': currency_price,  # Текущий курс
                             'date': datetime.datetime.today().strftime("%Y-%m-%d")})  # Дата обновления
        except mongo_e.DuplicateKeyError:
            print(f'Mongo: курсы {currency_name} уже получен')
        except Exception as e:
            print('Mongo: ошибка базы данных при сохранеии валют ', e)


def get_currency_price(db, coll_name, currency):
    """
    Функиця получает указатель на базу, название коллекции, где хранятся текущие курсы и название валюты
    Возвращает текущий курс относительно базовой валюты
    :param db: указатель на валюту
    :param coll_name: навание коллеции с курсами
    :param currency: идентификатор валюты
    :return: курс валюты
    """
    try:
        if coll_name not in db.list_collection_names():
            raise mongo_e.CollectionInvalid
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    try:
        last_price = coll.find({'currency': currency},  # находим последнюю запись с нужно валютой
                               {'_id': 0, 'price': 1}).sort('date', -1).limit(1)[0]['price']
        return float(last_price)
    except Exception as e:
        print('Mongo: ошибка БД ', e)
        return False


if __name__ == '__main__':
    # Для того, чтобы не мучать НН каждый раз, использоваться будет сохраненный вариант парсиннга из файлов
    # Список вакансий получаемый из файла и с сайта НН аналогичек по структуре, поэтому без разницы от куда
    # Все это сохранять в базу

    db_ = connect_mongodb('db')
    if SAVE_TO_DB:
        vacancies_ = load_hh_data_from_file('output.txt')
        if vacancies_:
            save_hh_to_mongodb(db_, 'vacancies', vacancies_)
    save_current_currency(db_, 'currency')
    for x in get_vacancies_more(db_, 'vacancies', 180000, max_empty=False):
        print(x)

