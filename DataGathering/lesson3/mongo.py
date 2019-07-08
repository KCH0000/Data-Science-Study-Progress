from pymongo import MongoClient, errors as mongo_e  # клиент к mongodb
from urllib.parse import quote_plus  # Форматирование пользователя и пароля


DB_URL = 'localhost'
DB_USERNAME = 'root'
DB_PASSWORD = 'root'
SAVE_TO_DB = False


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
    with open(file, 'rt', encoding='utf-8') as input_file:
        for line in input_file:
            i = 0
            if len(line.split('\t')) != 5:
                print(f"error in line {i}\n")
            else:
                parse_line = line.split('\t')
                vacancy = {
                    'name': parse_line[0],
                    'mix': int(parse_line[1]) if parse_line[1] not in ('True', 'False') else bool(parse_line[1]),
                    'max': int(parse_line[2]) if parse_line[2] not in ('True', 'False') else bool(parse_line[2]),
                    'currency': parse_line[3],
                    'url': parse_line[4].replace('\n', '')
                }
                data.append(vacancy)
                i += 1
    return data


def save_hh_to_mongodb(db, vacancies):
    coll_name = 'vacancies'
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


if __name__ == '__main__':
    db_ = connect_mongodb('db')
    vacancies_db = db_['vacancies']
    if SAVE_TO_DB:
        vacancies_ = load_hh_data_from_file('output.txt')
        save_hh_to_mongodb(db_, vacancies_)
