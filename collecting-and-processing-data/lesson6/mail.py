from pymongo import MongoClient, ASCENDING, errors as mongo_e
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


MAIL = 'georg-1'
DOMAIN = '@list.ru'
PASSWORD = 'Gosha01'
URL = 'https://mail.ru/'

DB_URL = 'localhost'
DB_USERNAME = 'root'
DB_PASSWORD = 'root'


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


def collect_new_mails():
    """
    Функция собираеть новую почту с портала mail.ru
    :return: список новых писеи
    """
    new_mails = []
    # Создание нового окна
    driver = webdriver.Chrome('./chromedriver')  # Для Линукс
    driver.get(URL)

    assert 'Mail.ru' in driver.title
    # Авторизация
    auth_form = driver.find_element_by_id('auth')
    mail_input = auth_form.find_element_by_id('mailbox:login')
    password_input = auth_form.find_element_by_id('mailbox:password')
    domain_select = Select(auth_form.find_element_by_id('mailbox:domain'))

    mail_input.send_keys(MAIL)
    password_input.send_keys(PASSWORD)
    domain_select.select_by_visible_text(DOMAIN)
    auth_form.submit()
    # Переход в на страницу входящих с ожиданием
    WebDriverWait(driver, 10).until(EC.title_contains('Входящие'))
    assert 'Входящие' in driver.title

    main_window = driver.window_handles[0]  # Запонаем основное окно, т.к. писма будет открывать в новой закладке
    mail_table = driver.find_element_by_class_name('dataset__items')
    mails_list = mail_table.find_elements_by_css_selector('a.js-letter-list-item')  # Находим все пиьма в таблице писем
    for mail in mails_list:
        try:
            mail.find_element_by_class_name('ll-rs_is-active')  # Если письмо старое, то его не трогаем.
        except NoSuchElementException:
            continue
        mail.send_keys(Keys.CONTROL + Keys.ENTER)  # Открваем новую закладку
        letter_windows = driver.window_handles[1]
        driver.switch_to.window(letter_windows)
        assert 'Почта' in driver.title
        WebDriverWait(driver, 10). \
            until(EC.presence_of_element_located((By.CLASS_NAME, 'letter__head')))
        letter_head = driver.find_element_by_class_name('letter__header-details')
        letter_author = letter_head.find_element_by_xpath('//div[@class="letter__author"]/'
                                                          'span[@class="letter__contact-item"]').get_attribute('title')
        letter_date = letter_head.find_element_by_xpath('//div[@class="letter__date"]').text
        # @todo Нужно обрабатывать даты с содержианием "Сегодня", "Вчера"
        letter_recipient = letter_head.find_element_by_xpath('//div[@class="letter__recipients letter__recipients_short"]/'
                                                             'span[@class="letter__contact-item"]').get_attribute('title')
        letter_subj = driver.find_element_by_css_selector('h2.thread__subject').text
        try:
            data_id = driver.find_element_by_class_name('thread__letter_single').get_attribute('data-id')
            body_id = f'style_{data_id}_BODY'
            letter_body = driver.find_element_by_id(body_id).text
        except Exception as e:
            letter_body = ''
            print(e)
        new_mails.append({'author': letter_author,
                          'recipient': letter_recipient,
                          'date': letter_date,
                          'subject': letter_subj,
                          'body': letter_body})
        driver.close()
        driver.switch_to.window(main_window)
    driver.close()
    return new_mails


def save_mails_to_mongo(db, coll_name, mails):
    """
    фунция сохраняет письма в указанную коллецию
    :param db: указатель на базу
    :param coll_name: название коллеции
    :param mails: список писеи
    :return:
    """
    try:
        coll = db[coll_name]
    except mongo_e.CollectionInvalid:
        print(f'Mongo: {coll_name} - коллекция недоступна')
        return False
    coll.create_index([('author', ASCENDING),
                       ('date', ASCENDING),
                       ('subject', ASCENDING)], unique=True)
    for mail in mails:
        try:
            coll.insert_one(mail)
        except mongo_e.DuplicateKeyError:
            continue
        except Exception as e:
            print(f'Mongo: ошибка {e}')
            return False
    return True


if __name__ == '__main__':
    db = connect_mongodb('db')
    mails = collect_new_mails()
    if mails:
        save_mails_to_mongo(db, MAIL+DOMAIN, mails)
