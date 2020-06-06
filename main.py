import requests
import os
from dotenv import load_dotenv
from itertools import count
from terminaltables import AsciiTable

LANGS = ['Javascript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'C', 'Go']


def get_vacancies_hh(text, page=0, per_page=100):
    url = 'https://api.hh.ru/vacancies'
    payload = {
        'text': text,
        'specialization': '1.221',
        'area': '1',
        'period': '30',
        'page': page,
        'per_page': per_page
    }
    resp = requests.get(url, params=payload)
    resp.raise_for_status()
    decoded_resp = resp.json()
    return decoded_resp


def get_vacancies_sj(secret_key, text, page=0, count=100):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': secret_key
    }
    payload = {
        'town': 4,
        'catalogues': 48,
        'keyword': text,
        'page': page,
        'count': count
    }
    resp = requests.get(url, headers=headers, params=payload)
    resp.raise_for_status()
    decoded_resp = resp.json()
    return decoded_resp


def predict_salary(salary_from, salary_to):
    if salary_from is not None and salary_to is not None:
        avg_salary = int((salary_from + salary_to) / 2)
    elif salary_from is None:
        avg_salary = int(salary_to * 0.8)
    elif salary_to is None:
        avg_salary = int(salary_from * 1.2)
    return avg_salary


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if salary is None:
        avg_salary = None
    elif salary['currency'] != 'RUR':
        avg_salary = None
    else:
        salary_from = salary['from']
        salary_to = salary['to']
        avg_salary = predict_salary(salary_from, salary_to)
    return avg_salary


def predict_rub_salary_sj(vacancy):
    if vacancy['payment'] is None:
        avg_salary = None
    elif vacancy['currency'] != 'rub':
        avg_salary = None
    else:
        if vacancy['payment_from'] == 0:
            salary_from = None
        else:
            salary_from = vacancy['payment_from']
        if vacancy['payment_to'] == 0:
            salary_to = None
        else:
            salary_to = vacancy['payment_to']
        avg_salary = predict_salary(salary_from, salary_to)
    return avg_salary


def get_hh_vacancies_stats_by_lang(text):
    pages = []

    for page in count(0):
        decoded_resp = get_vacancies_hh(text, page)
        pages.append(decoded_resp['items'])
        if page >= decoded_resp['pages']:
            vacancies_found = decoded_resp['found']
            break

    vacancies_processed = 0
    average_salary = 0

    for page in pages:
        for vacancy in page:
            salary = predict_rub_salary_hh(vacancy)
            if salary is not None:
                vacancies_processed += 1
                average_salary += salary
    average_salary = int(average_salary / vacancies_processed)

    return vacancies_found, vacancies_processed, average_salary


def get_sj_vacancies_stats_by_lang(secret_key, text):
    pages = []

    for page in count(0):
        decoded_resp = get_vacancies_sj(secret_key, text, page)
        pages.append(decoded_resp['objects'])
        if not decoded_resp['more']:
            vacancies_found = decoded_resp['total']
            break
        else:
            continue

    vacancies_processed = 0
    average_salary = 0

    for page in pages:
        for vacancy in page:
            salary = predict_rub_salary_sj(vacancy)
            if salary is not None:
                vacancies_processed += 1
                average_salary += salary
        average_salary = int(average_salary / vacancies_processed)

    return vacancies_found, vacancies_processed, average_salary


def get_all_hh_prog_vacancies_stats():
    title = 'HeadHunter Moscow'
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for lang in LANGS:
        text = 'Программист ' + lang
        vacancies_found, vacancies_processed, average_salary = get_hh_vacancies_stats_by_lang(text)
        table_data.append([lang, vacancies_found, vacancies_processed, average_salary])
    return table_data, title


def get_all_sj_prog_vacancies_stats(secret_key):
    title = 'SuperJob Moscow'
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for lang in LANGS:
        text = 'Программист ' + lang
        vacancies_found, vacancies_processed, average_salary = get_sj_vacancies_stats_by_lang(secret_key, text)
        table_data.append([lang, vacancies_found, vacancies_processed, average_salary])
    return table_data, title


def create_table(table_data, title):
    table_instance = AsciiTable(table_data, title)
    return table_instance.table


def main():
    load_dotenv()
    secret_key = os.getenv('SUPERJOB_SECRET_KEY')
    tables = [[get_all_sj_prog_vacancies_stats(secret_key)], [get_all_hh_prog_vacancies_stats()]]
    for table in tables:
        table_data = table[0][0]
        title = table[0][1]
        print(create_table(table_data, title))


if __name__ == "__main__":
    main()
