import requests  # для запросов на сайт
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
        link = name['href']
        list_vacancy.append({
            'name': name.string,  # Название вакансии
            'compensation': compensation.string,  # Заработная плата
            'url': link  # Ссылка на вакансию
        })
    return list_vacancy


def get_all_vacancies(vacancy_search: str):
    """
    Функция получает строку поика вакасий, и возвращает список ввсех ваканский
    :param vacancy_search: старока поиска вакансии
    :return: list объектов вакансий
    """
    all_vacancies = []
    html = get_search_hh(vacancy_search, 0)
    max_pages = get_max_page(html)
    for i in range(max_pages + 1):
        html = get_search_hh(vacancy_search, i)
        vacancies_on_page = get_vacancies_on_page(html)
        all_vacancies += vacancies_on_page
    return all_vacancies


def save_vacancies_to_file(vacancies: list):
    """
    Функсция сохраняет список вакансий а форматированом виде в фаил
    :param vacancies: список объектов вакансий
    :return: none
    """
    with open('output.txt', 'wt', encoding='utf-8') as output_file:
        for vacancy in vacancies:
            output_file.write(f'{vacancy["name"]} - {vacancy["compensation"]} \n')
            output_file.write(f'{vacancy["url"]} \n\n')


if __name__ == "__main__":
    vacancy_name = 'Программист Python'
    all_ = get_all_vacancies(vacancy_name)
    print(len(all_))
    save_vacancies_to_file(all_)
