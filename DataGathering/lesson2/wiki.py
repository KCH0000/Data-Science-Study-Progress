from requests import get
import re
from collections import Counter


def get_link(topic_: str):
    """
    Функция получает название топика на википедии и возвращает ссылку заменяя пробелы
    на знак подчеркивания
    :param topic_: str
    :return: srt
    """
    topic_ = '_'.join(topic_.split(' '))
    link = "https://ru.wikipedia.org/wiki/" + topic_
    return link


def get_topic_page(topic_: str):
    """
    Функция получает ссылку на html ресуср вы возвращает GET запрос в виде строки
    :param topic_: str
    :return: str
    """
    link = get_link(topic_)
    html = get(link).text
    return html


def get_topic_russian_words(topic_: str):
    """
    Функция получает ссылку на html ресурс и вызвращается список слове
    русском языке встречаюшиеся в на странице
    :param topic_: str
    :return: list
    """
    html_content = get_topic_page(topic_)
    words = re.findall("[а-яА-ЯёЁ]{3,}", html_content)
    return words


def get_wiki_links(topic_: str):
    """
    Функция получает ссылку на html страницу по адресу https://ru.wikipedia.org/wiki/
    Находит все ссылки топики упомянутые в статье и возвращет в виде
    списка названий топиков
    :param topic_:str
    :return: list
    """
    html_content = get_topic_page(topic_)
    links = re.findall(r'a href="/wiki/[^:]+" title="(.+?)"', html_content)
    topics = set()
    for link in links:
        topics.add(link)
    return list(topics)


def get_common_words(words: list, top=10):
    """
    Фурнкция получает списков слов, и количество популярных слов для возврата
    Возвращает список кортежей, где первый элемет слов, а второй количество вхождений
    в исходный список. Сортируется по убыванию
    :param words: list
    :param top: int
    :return: tuple
    """
    return Counter(words).most_common(top)


def save_common_words_to_file(words: list, topic_name: str):
    """
    Функция получает список кортежей часто входимых слов
    и сохраняет в файл в форматированом виде.
    :param words:
    :param topic_name:
    :return:
    """
    topic_name = topic_name.replace('/\\?<>*|', '')
    with open(topic_name+'_cw.txt', 'wt', encoding="utf-8") as f_output:
        f_output.write(f'{len(words)} часто встречающихся слов на странице '
                       f'https://ru.wikipedia.org/wiki/{topic_name}'
                       + '\n\n')
        for word in words:
            f_output.write(f'Слово "{word[0]}" встрачается {word[1]} раз' + '\n')


def save_page_to_file(page_: str, topic_name: str):
    """
    Функция получает html страцицу и сохраняет ее в фаил
    :param page_: srt
    :param topic_name: str
    :return:
    """
    topic_name = topic_name.replace('/\\?<>*|', '')
    with open(topic_name + "_page.html", 'wt', encoding="utf-8") as f_output:
        f_output.write(page_)


if __name__ == "__main__":
    topic_main = 'Россия'
    save_common_words_to_file(get_common_words(get_topic_russian_words(topic_main,), 10), topic_main)
    topics_ = get_wiki_links(topic_main)
    for topic in topics_[:2]:
        page = get_topic_page(topic)
        save_page_to_file(page, topic)

