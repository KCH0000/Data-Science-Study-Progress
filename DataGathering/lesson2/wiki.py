from requests import get
import re


def get_link(topic):
    link = "https://ru.wikipedia.org/wiki/" + topic.capitalize()
    return link


def get_topic_page(topic):
    link = get_link(topic)
    html = get(link).text
    return html


def get_topic_text(topic):
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


def get_common_words

if __name__ == "__main__":
    print(get_wiki_links('россия'))
