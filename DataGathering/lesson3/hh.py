import requests  # для запросов на сайт
import re  # Парсить максимальную и минимальную зарплату
from bs4 import BeautifulSoup as bs  # Для обработки HTML


def get_search_hh(vacancy: str, page: int, lang=''):
    """
    Функция получает название вакансии, формирует запрос на сайт hh.ru и формирует ответ в видел html
    :param vacancy: srt. Вакансия для поиска
    :param page: int Номер страницы в поиске, по умолчанию 1
    :param lang: str Язык на кором пишет программист. По умолчанию все языки
    :return: str HTML странци
    """
    headers = {'user-agent': "Mozilla/5.0 "
                             "(X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36"}
    if lang != '':
        vacancy = vacancy + '+' + lang
    url = f'https://hh.ru/search/vacancy' \
          f'?area=1' \
          f'&clusters=true' \
          f'&enable_snippets=false' \
          f'&search_field=name' \
          f'&text={vacancy}' \
          f'&only_with_salary=true' \
          f'&page={page}'
    # area - город для поиска. 1 - Москва 2 - Санкт-Петербург
    # clusters - не известно
    # enable_snippets - отключение информации для поисковиков
    # search_field - тип поискового запроса. По умолчанию по имени
    # text - текс запроса. Контитенция слов через +
    # only_with_salary - поиск по вакансиям только с указанием ЗП
    # page - страница результов поиска. Вывести все на одной странице не удалось
    get = requests.get(url, headers=headers)
    return get.text


def get_max_page(html):
    """
    Функция получает html запрос с hh.ru возвращает количество страниц в поиске
    :param html: str HTML страница
    :return: int Количество страниц начиня с 0
    """
    soup = bs(html, 'lxml')
    pages = soup.findAll('a',  {"class": "HH-Pager-Control",
                                "data-qa": "pager-page"})  # ищем все кнопки для перехода по страницам
    if len(pages) == 0:
        return 0  # Если кнопок нет, то страниц 1, т.е 0
    return int(pages[-1]['data-page'])  # Возвращаем номер последней страницы


def parse_compensation(compensation: str):
    """
    Функция получает строку с зарплатой и преобразует ее в минимальную, максимальню, а так же опеделяет валюту зарплат

    :param compensation: строка, которая начинается на до, от или имеет вид min-max , в конце валюта
    :return: минимальная запралат, максимальная, валюта
    """
    min_compensation, max_compensation, currency = 0, 0, False
    if compensation[:2] == 'от':
        min_compensation = int("".join(re.findall("\d+", compensation[2:])))
    if compensation[:2] == 'до':
        max_compensation = int("".join(re.findall("\d+", compensation[2:])))
    if len(compensation.split('-')) == 2:
        compensation_ = compensation.split('-')
        min_compensation = int("".join(re.findall("\d+", compensation_[0])))
        max_compensation = int("".join(re.findall("\d+", compensation_[1])))
    currency = re.findall('\D+', compensation)[-1].replace(" ", "")
    if currency == 'руб.':
        currency = 'RUR'
    return min_compensation, max_compensation, currency


def get_vacancies_on_page(html):
    """
    Функцич получает вакансии на страницы и формирует список вакансий, где в каждом элемете указано название вакансии
    и зарплата максимальная и минимальная
    :param html. Страница результатов поиска
    :return: list. Список вакансий на странице с указанием имени и оплаты труда
    """
    list_vacancy = []
    soup = bs(html, 'lxml')
    vacancies = soup.select('.vacancy-serp-item')
    for vacancy in vacancies:
        name = vacancy.find('a', {"data-qa": "vacancy-serp__vacancy-title"})
        compensation = vacancy.find("div", {"class": "vacancy-serp-item__compensation"})
        link = name['href'].split('?')[0]
        min_compensation, max_compensation, currency = parse_compensation(compensation.string)
        list_vacancy.append({
            'name': name.string,  # Название вакансии
            'min': min_compensation,  # Минимальная оплата
            'max': max_compensation,  # Максимальная оплата
            'currency': currency,  # Валюта вакансии
            'url': link  # Ссылка на вакансию
        })
    return list_vacancy


def get_all_vacancies(vacancy_search: str, lang=''):
    """
    Функция получает строку поика вакасий, и возвращает список ввсех ваканский
    :param lang: язык прокграммирония
    :param vacancy_search: старока поиска вакансии
    :return: list объектов вакансий
    """
    all_vacancies = []
    html = get_search_hh(vacancy_search, 0, lang)
    max_pages = get_max_page(html)
    for i in range(max_pages + 1):
        html = get_search_hh(vacancy_search, i, lang)
        vacancies_on_page = get_vacancies_on_page(html)
        all_vacancies += vacancies_on_page
    return all_vacancies


def save_vacancies_to_file(vacancies: list):
    """
    Функсция сохраняет список вакансий а форматированом виде в фаил с разделителем : для удобной загрузки
    :param vacancies: список объектов вакансий
    :return: none
    """
    with open('output.txt', 'wt', encoding='utf-8') as output_file:
        for vacancy in vacancies:
            line = [vacancy["name"], vacancy["min"], vacancy["max"], vacancy["currency"], vacancy["url"]]
            line_to_write = "\t".join(str(x) for x in line)
            output_file.write(line_to_write + "\n")
            # output_file.write(f'{vacancy["url"]} \n\n')


if __name__ == "__main__":
    vacancy_name = 'Программист'
    lang_ = "Python"
    all_ = get_all_vacancies(vacancy_name, lang_)
    print(len(all_))
    save_vacancies_to_file(all_)
