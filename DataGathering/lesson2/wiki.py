from requests import get
import re
from collections import Counter


def get_link(topic):
    link = "https://ru.wikipedia.org/wiki/" + topic.capitalize()
    return link


def get_topic_page(topic):
    link = get_link(topic)
    html = get(link).text
    return html


def get_topic_russian_words(topic):
    html_content = get_topic_page(topic)
    words = re.findall("[а-яА-ЯёЁ]{3,}", html_content)
    return words


def get_wiki_links(topic):
    html_content = get_topic_page(topic)
    links = re.findall(r'a href="/wiki/[^:]+" title="(.+?)"', html_content)
    topics = set()
    for link in links:
        topics.add('_'.join(link.split(' ')))
    return topics


def get_common_words(words: list, top=10):
    return Counter(words).most_common(top)


def save_common_words_to_file(words: list, topic_name):
    with open(topic_name+'_cw.txt', 'w') as f_output:
        f_output.write(f'{len(words)} часто встречающихся слов на странице '
                       f'https://ru.wikipedia.org/wiki/{topic_name.capitalize()}'
                       + '\n\n')
        for word in words:
            f_output.write(f'Слово "{word[0]}" встрачается {word[1]} раз' + '\n')


if __name__ == "__main__":
    topic_ = 'россия'
    save_common_words_to_file(get_common_words(get_topic_russian_words(topic_,), 10), topic_)

