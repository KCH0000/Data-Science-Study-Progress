import json
import requests


def get_city(find_str):
    locale = 'ru'
    url = f'http://autocomplete.travelpayouts.com/places2?locale={locale}&' \
        f'types[]=city&' \
        f'term={find_str}'
    get = requests.get(url)
    answer = json.loads(get.text)
    return answer


def get_prices(origin_, destination_, one_way=True):
    url = f'http://min-prices.aviasales.ru/calendar_preload?' \
        f'origin={origin_}&' \
        f'destination={destination_}' \
        f'&one_way={one_way}'
    get = requests.get(url)
    answer = json.loads(get.text)
    return answer['best_prices']


def get_iata(city):
    return city['code']


def get_city_vi(city):
    return city['cases']['vi']


def get_city_ro(city):
    return city['cases']['ro']


def ask_city():
    while True:
        find_str = input("Ведите название города: ")
        cities = get_city(find_str)
        if len(cities) == 1:
            return cities[0]
        if 0 < len(cities) <= 5:
            print("Выберите город:")
            i = 1
            for city in cities:
                print(f'{city["name"]} - {i}')
                i += 1
            num = int(input("Номер города: "))
            if num in range(1, len(cities) + 1):
                return cities[num - 1]
            else:
                print('Неверный ввод')
        else:
            print("Уточните город")


if __name__ == "__main__":
    print('Город ОТПРАВЛЕНИЯ')
    origin = ask_city()
    print(f'Вы летите из {get_city_ro(origin)}')
    print('Город НАЗНАЧЕНИЯ')
    destination = ask_city()
    print(f'Вы летите {get_city_vi(destination)}')
    prices = get_prices(get_iata(origin), get_iata(destination))
    best_price = sorted(prices, key=lambda x: x['value'])[0]
    print(f'Из {get_city_ro(origin)} {get_city_vi(destination)} '
          f'лучше всего лететь {best_price["depart_date"]} '
          f'по цене {best_price["value"]}')
