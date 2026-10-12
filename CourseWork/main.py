# -*- coding: utf-8 -*-
"""
Курсовой проект по теории автоматов и формальных языков (МАИ).
Часть 1: Реализация детерминированного конечного автомата (ДКА).

Паттерн: ^\\d{5}$
Контекст: if (!Regex.Match(zipCodeTextBox.Text, @"^\\d{5}$").Success)
Язык L: строки, состоящие ровно из 5 десятичных цифр (ZIP-код).

Структура программы соответствует образцу из методических материалов (КП.pdf).
"""

import sys


class FSAutomate:
    """
    Класс конечного автомата (Finite State Automaton).
    Полный эквивалент класса FSAutomate из образца в КП.pdf.
    """

    def __init__(self, states, alphabet, final_states, initial_state):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.final_states = set(final_states)
        self.initial_state = initial_state
        # Функция переходов: delta[(current_state, symbol)] = next_state
        self.rules = {}

    def add_rule(self, from_state, symbol, to_state):
        """Добавление правила перехода delta(from_state, symbol) = to_state."""
        self.rules[(from_state, symbol)] = to_state

    def execute(self, line, verbose=True):
        """
        Посимвольное выполнение автомата на входной строке.
        Выводит пошаговую трассировку аналогично образцу из КП.pdf:
        - Длина строки (Length)
        - Индекс текущего символа (i)
        - Текущее состояние (curr)
        - Принадлежит ли цепочка языку (belongs / doesn't belong)
        """
        curr_state = self.initial_state
        length = len(line)

        if verbose:
            print(f"Length: {length}")

        for i, symbol in enumerate(line):
            next_state = self.rules.get((curr_state, symbol), "qerr")
            if verbose:
                print(f"i: {i + 1} | char: '{symbol}' | {curr_state} -> {next_state}")
            curr_state = next_state

            # Если попали в состояние-ловушку, дальнейшие символы точно не приведут в F
            if curr_state == "qerr" and not verbose:
                break

        is_accepted = curr_state in self.final_states

        if verbose:
            print(f"curr: {curr_state}")
            if is_accepted:
                print("chineSymbol belongs to language")
            else:
                print("chineSymbol doesn't belong to language")

        return is_accepted, curr_state


def create_zipcode_automaton():
    """
    Создание и конфигурирование ДКА для распознавания ^\\d{5}$.
    
    Компоненты автомата M = (Q, Sigma, delta, q0, F):
    - Q = {q0, q1, q2, q3, q4, qf, qerr}
    - Sigma = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
    - q0 — начальное состояние
    - F = {qf} — допускающее состояние
    - qerr — состояние-ловушка для отклонения некорректных цепочек
    """
    states = ["q0", "q1", "q2", "q3", "q4", "qf", "qerr"]
    digits = [str(d) for d in range(10)]
    final_states = ["qf"]
    initial_state = "q0"

    fsa = FSAutomate(states, digits, final_states, initial_state)

    # Правила переходов: каждое состояние считает количество прочитанных цифр
    # q0 - 0 цифр, q1 - 1, q2 - 2, q3 - 3, q4 - 4, qf - ровно 5 цифр
    for digit in digits:
        fsa.add_rule("q0", digit, "q1")
        fsa.add_rule("q1", digit, "q2")
        fsa.add_rule("q2", digit, "q3")
        fsa.add_rule("q3", digit, "q4")
        fsa.add_rule("q4", digit, "qf")
        # Больше 5 цифр -> ловушка
        fsa.add_rule("qf", digit, "qerr")
        fsa.add_rule("qerr", digit, "qerr")

    return fsa


def run_tests(fsa):
    """Автоматическая проверка тестовых наборов данных."""
    print("=" * 60)
    print("ЗАПУСК АВТОТЕСТОВ ДЛЯ ПАТТЕРНА: ^\\d{5}$")
    print("=" * 60)

    test_cases = [
        ("12345", True,  "Ровно 5 цифр (валидный ZIP-код)"),
        ("00000", True,  "Ровно 5 нулей (валидный ZIP-код)"),
        ("98765", True,  "Ровно 5 цифр (валидный ZIP-код)"),
        ("1234",  False, "4 цифры (слишком короткая строка)"),
        ("123456", False, "6 цифр (слишком длинная строка)"),
        ("",      False, "Пустая строка"),
        ("1234a", False, "Буквенный символ в строке"),
        ("12 45", False, "Пробел внутри индекса"),
        ("abcde", False, "Только буквы"),
    ]

    all_passed = True
    for string, expected, comment in test_cases:
        accepted, final_st = fsa.execute(string, verbose=False)
        status = "OK" if accepted == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        res_str = "Принято" if accepted else "Отклонено"
        print(f"[{status}] Вход: '{string}' -> {res_str} ({comment})")

    print("=" * 60)
    if all_passed:
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("ЕСТЬ ОШИБКИ В ТЕСТАХ!")
    print("=" * 60 + "\n")


def main():
    fsa = create_zipcode_automaton()

    # Если передан флаг --test, прогоняем тесты и завершаем работу
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests(fsa)
        return

    print("=" * 60)
    print('Automate 1: "^\\d{5}$" (ZIP-code validator, for ex.: 12345)')
    print("=" * 60)

    # Интерактивный цикл выполнения как в КП.pdf
    while True:
        try:
            line = input('\nEnter line ("^\\d{5}$", for ex.: 12345) to execute\nor "exit" to exit:\n')
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break

        line = line.strip()
        if line.lower() == "exit":
            print("Выход из программы.")
            break

        fsa.execute(line, verbose=True)


if __name__ == "__main__":
    main()
