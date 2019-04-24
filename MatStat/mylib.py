from math import factorial as fl
from math import exp, sqrt


# ===== Lesson 1 =====

def C(n: int, k: int):
    """
    Функция возвращает кол-во сочетаний(без учета последовательности) к элементов из n возможных
    n - всего элементов
    k - размер выборки из всех элементов
    """
    return int(fl(n) / (fl(k) * fl(n - k)))


def A(n: int, k: int):
    """
    Функция возвращает кол-во размещений(с учетом последовательности) к элементов из n возможных
    n - всего элементов
    k - размер выборки из всех элементов
    """
    return int(fl(n) / fl(n - k))


def permutations(n: int):
    """
    Функция возвращает кол-во перестановок n элементов
    n - всего элементов
    """
    return int(fl(n))


# ===== Lesson 2 =====

def binom(n: int, k: int, p: float):
    """
    Биномильный закон распределния вероятносей
    Функция возвращет вероятность k наступлени события с А в n независимых испытаниях
    n - количество испытаний
    k - количество наступления события A из n испытаний
    p - вероятность настуления А в каждом из испытаний
    """
    q = 1 - p
    m = n - k
    return C(n, k) * p**k * q**m


def poisson(n: int, m: int, p: float):
    """
    Распределение Пуассона
    Функция возвращет вероятность k наступлени события с А в n независимых испытаниях
    когда веростность наступления А мала, а количество испытаний большое
    n - количество испытаний
    m - количество наступления события A из n испытаний
    p - вероятность настуления А в каждом из испытаний
    """
    lambda_ = n * p
    return (lambda_**m / fl(m)) * exp(-lambda_)


# ===== Lesson 3 =====

def mean(array: list):
    """
    Фунция получает массив значений и возвращет среднее значение
    :param array:
    :return float:
    """
    n = len(array)
    sum_ = 0
    for i in range(n):
        sum_ += array[i]
    return sum_ / n


def sum_of_squares(array: list):
    """
    Фунция получает массив значений и возвращет сумму квадратов отклонения
    :param array:
    :return float:
    """
    n = len(array)
    mean_ = mean(array)
    sum_of_squares_ = 0
    for i in range(n):
        sum_of_squares_ += (array[i] - mean_) ** 2
    return sum_of_squares_


def offset_dispersion(array: list):
    """
    Фунция получает массив значений и возвращет выборочную смещенную дисперсию
    :param array:
    :return float:
    """
    return sum_of_squares(array) / len(array)


def unbiased_dispersion(array: list):
    """
    Фунция получает массив значений и возвращет выборочную несмещенную дисперсию
    :param array:
    :return float:
    """
    return sum_of_squares(array) / (len(array) - 1)


def std_deviation(array: list):
    """
    Фунция получает массив значений и возвращет среднее квадратическое отклонение
    :param array:
    :return float:
    """
    return sqrt(offset_dispersion(array))


def std_unbiased(array: list):
    """
    Фунция получает массив значений и возвращет несмещенное среднее квадратическое отклонение
    :param array:
    :return float:
    """
    return sqrt(unbiased_dispersion(array))