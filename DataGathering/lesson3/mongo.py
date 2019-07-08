from pymongo import MongoClient, errors as mongo_e  # клиент к mongodb
from urllib.parse import quote_plus  # Форматирование пользователя и пароля


DB_URL = 'localhost'
DB_USERNAME = 'root'
DB_PASSWORD = 'root'
SAVE_TO_DB = False  # True - программа будет читать фаил и сохранять в базу. False - будут работать тольк чтение
VAL = {'USD': 63, 'EUR': 72, 'руб.': 1}  # Курсы


def connect_mongodb(db):
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
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    try:
        ids = coll.insert_many(vacancies)
        print(f'Mongo: добавлено {len(ids.inserted_ids)} записей в коллецию {coll_name}')
        return ids.inserted_ids
    except mongo_e.WriteError:
        print('Mongo: ошибка записи')
        return False
    except Exception as e:
        print(f'Mongo: ошибка {e}')


def get_vacancies_more(db, coll_name, compensation):
    vacancies = []
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    for currency, curs in VAL.items():
        for vacancy in coll.find({'$and': [
                                    {'currency': currency},
                                    {'$or': [
                                        {'max': 0},
                                        {'max': {'$gt': compensation/curs}}
                                    ]}
        ]}):
            vacancies.append(vacancy)
    return vacancies


if __name__ == '__main__':
    db_ = connect_mongodb('db')
    if SAVE_TO_DB:
        vacancies_ = load_hh_data_from_file('output.txt')
        if vacancies_:
            save_hh_to_mongodb(db_, 'vacancies', vacancies_)
    for x in get_vacancies_more(db_, 'vacancies', 300000):
        print(x)