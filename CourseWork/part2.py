# -*- coding: utf-8 -*-
"""
Курсовой проект по теории автоматов и формальных языков (МАИ).
Часть 2: преобразования КС-грамматики и магазинный автомат (МП-автомат).

Исходная грамматика (вариант 13, seed 5):
    G = ({a, b, c, d, f, eps, v, h, m, j},
         {S, A, B, C, D, O, H, M, E, F, T}, P, S)
    A -> bC     B -> cA     C -> dD     D -> O      O -> f
    S -> aABH   H -> eps    M -> v      E -> hFd
    B -> jT     T -> Tm     T -> m

Замечание: символ eps в списке терминалов — недочёт генератора заданий.
eps не является терминалом, а обозначает пустую цепочку, поэтому правило
H -> eps трактуется как правило с пустой правой частью.

Что делает программа (пункты 4-8 задания):
    1) устраняет бесполезные символы (сначала бесплодные, затем недостижимые);
    2) устраняет eps-правила;
    3) устраняет цепные правила;
    4) устраняет непосредственную левую рекурсию;
    5) строит недетерминированный МП-автомат по приведённой грамматике;
    6) строит детерминированный LL(1)-автомат по управляющей таблице;
    7) проверяет результат на тестовых цепочках.

Структура файла:
    class Grammar  — представление грамматики и все её преобразования;
    class PDA      — модель МП-автомата (конфигурации, переходы, разбор);
    build_pda_from_grammar / build_ll1_pda — построение автоматов M1 и M2;
    cyk            — независимая проверка цепочек (вспомогательная);
    source_grammar / factored_grammar — грамматики варианта;
    main / run_tests — демонстрация и автотесты.

Соглашения:
    eps — обозначение пустой цепочки во внутреннем представлении
          (отдельного символа в алфавите нет);
    $   — маркер конца входной цепочки;
    магазин хранится кортежем, последний элемент — вершина магазина.

Запуск:
    py part2.py            — пошаговые преобразования + работа МП-автомата
    py part2.py --test     — только автотесты
"""

import sys

EPS = "eps"          # пустая цепочка во внутреннем представлении
END = "$"            # маркер конца входной цепочки


# ============================================================================
#  КС-грамматика
# ============================================================================
class Grammar:
    """Контекстно-свободная грамматика G = (N, T, P, S).

    Атрибуты:
        N     — множество нетерминалов (V_N);
        T     — множество терминалов (V_T);
        rules — список правил вида (A, (x1, ..., xn)), где A — левая часть
                (строка), а правая часть — КОРТЕЖ символов; пустой кортеж
                означает правило с пустой правой частью (eps-правило);
        start — начальный (целевой) символ S.

    Правая часть хранится кортежем, а не строкой: при преобразованиях
    приходится вырезать и вставлять отдельные символы, и с кортежем это
    делается без разбора строк.

    Все методы-преобразования возвращают НОВЫЙ объект Grammar и не меняют
    исходный. Поэтому в main() можно напечатать всю цепочку
    G -> G1 -> G2 -> ... и сравнить результаты соседних шагов.
    """

    def __init__(self, nonterminals, terminals, rules, start):
        """Создать грамматику из готовых множеств и списка правил.

        Никаких проверок и преобразований не выполняется: объект считается
        корректной КС-грамматикой (правила уже разобраны на символы).
        """
        self.N = set(nonterminals)
        self.T = set(terminals)
        self.rules = [(lhs, tuple(rhs)) for lhs, rhs in rules]
        self.start = start

    # ------------------------------------------------------------- утилиты
    def copy(self):
        """Полная копия грамматики (список правил копируется отдельно).

        Нужна, чтобы преобразования не портили исходный объект и его можно
        было напечатать ещё раз (например, для проверки результата).
        """
        return Grammar(self.N, self.T, self.rules, self.start)

    def rules_for(self, A):
        """Все правые части правил с левой частью A.

        Используется всюду, где нужно перебрать альтернативы нетерминала.
        Возвращает: список кортежей (возможно, пустой).
        """
        return [rhs for lhs, rhs in self.rules if lhs == A]

    @staticmethod
    def fmt_rhs(rhs):
        """Правая часть правила в читаемом виде.

        Символы склеиваются в строку, пустая цепочка печатается как eps.
        """
        return "".join(rhs) if rhs else EPS

    def ordered_n(self):
        """Нетерминалы в постоянном порядке: сначала S, остальные по алфавиту.

        Нужен, чтобы строки таблиц и вывод на экран не «прыгали» от запуска
        к запуску (множество set порядка не гарантирует).
        """
        return [self.start] + sorted(self.N - {self.start})

    def as_text(self, indent="    "):
        """Правила, сгруппированные по левой части: A -> x | y.

        Возвращает: многострочную строку, готовую к печати.
        """
        out = []
        for A in self.ordered_n():
            alts = [self.fmt_rhs(r) for r in self.rules_for(A)]
            if alts:
                out.append(f"{indent}{A} -> " + " | ".join(alts))
        return "\n".join(out)

    def show(self, title=""):
        """Печать грамматики: множества N, T и все правила.

        Параметры: title — необязательный заголовок перед выводом.
        """
        if title:
            print(f"\n{title}")
        print(f"  N = {{{', '.join(self.ordered_n())}}}")
        print(f"  T = {{{', '.join(sorted(self.T))}}}")
        print("  P:")
        print(self.as_text())

    # --------------------------------------------- 1. бесполезные символы
    def productive(self):
        """Множество продуктивных (не бесплодных) нетерминалов.

        Нетерминал продуктивен, если из него выводится хотя бы одна
        терминальная цепочка. Терминалы продуктивны по определению —
        они сами являются цепочками.

        Алгоритм (шаг 1 приведения, Алгоритм 1 из лекции): нетерминал A
        отмечается, если есть правило A -> α, ВСЕ символы которого уже
        отмечены. Отметки ставятся, пока множество не перестанет расти.

        Возвращает: set продуктивных нетерминалов; N минус результат —
        это бесплодные нетерминалы.
        """
        prod, changed = set(), True
        while changed:
            changed = False
            for A, rhs in self.rules:
                if A in prod:
                    continue
                if all(s in self.T or s in prod for s in rhs):
                    prod.add(A)
                    changed = True
        return prod

    def reachable(self):
        """Множество символов, достижимых из начального символа S.

        Обход графа грамматики: если левая часть правила уже достижима,
        то все символы его правой части тоже достижимы. Повторяем, пока
        множество не перестанет расти.

        Возвращает: set символов (и терминалов, и нетерминалов).
        """
        reach, changed = {self.start}, True
        while changed:
            changed = False
            for A, rhs in self.rules:
                if A in reach:
                    for s in rhs:
                        if s not in reach:
                            reach.add(s)
                            changed = True
        return reach

    def remove_useless(self, verbose=True):
        """Приведение грамматики: удаление бесплодных, затем недостижимых.

        Порядок шагов принципиален (так же в лекции): если сначала удалить
        недостижимые символы, часть бесплодных может «спрятаться» и остаться
        в грамматике, поэтому сначала идут бесплодные.

        Шаги:
            1) удалить бесплодные нетерминалы и все правила с ними;
            2) удалить символы, недостижимые из S, и правила с ними;
            3) начальный символ S остаётся в N всегда — даже если он
               оказался бесплодным (иначе это уже не грамматика).

        Параметры: verbose — печатать найденные бесплодные и недостижимые.
        Возвращает: новую (приведённую) грамматику.
        """
        g = self.copy()

        prod = g.productive()
        dead = sorted(g.N - prod)
        if verbose:
            print(f"  Бесплодные нетерминалы: {dead if dead else 'нет'}")
        g.rules = [(A, r) for A, r in g.rules
                   if A in prod and all(s in g.T or s in prod for s in r)]
        g.N = set(prod) | {g.start}

        reach = g.reachable()
        unreach = sorted((g.N | g.T) - reach)
        if verbose:
            print(f"  Недостижимые символы: {unreach if unreach else 'нет'}")
        g.rules = [(A, r) for A, r in g.rules
                   if A in reach and all(s in reach for s in r)]
        g.N &= reach
        g.T &= reach
        g.N.add(g.start)
        return g

    # --------------------------------------------------------- 2. eps-правила
    def nullable(self):
        """Множество X = {A | A =>* eps}: нетерминалы, выводимые в пустую цепочку.

        Правило с пустой правой частью сразу даёт A ∈ X (all() по пустому
        кортежу истинно). Затем в X добавляются нетерминалы, у которых все
        символы правой части уже лежат в X. Повторяем до неподвижной точки.

        X нужно, чтобы понять, какие вхождения символов можно «вычеркнуть»
        при удалении eps-правил.

        Возвращает: set нетерминалов.
        """
        X, changed = set(), True
        while changed:
            changed = False
            for A, rhs in self.rules:
                if A in X:
                    continue
                if all(s in X for s in rhs):
                    X.add(A)
                    changed = True
        return X

    def remove_epsilon(self, verbose=True, new_start="S0"):
        """Устранение правил с пустой правой частью (eps-правил).

        Алгоритм:
            1) построить X — множество нетерминалов, выводимых в eps;
            2) удалить из грамматики сами eps-правила;
            3) каждое правило B -> α, где встречаются символы из X, заменить
               всеми вариантами с вычеркнутыми вхождениями (2^k вариантов,
               k — число таких вхождений); пустые варианты не добавляются;
            4) если из S выводился eps, добавить новый начальный символ S0
               и правила S0 -> S, S0 -> eps (иначе язык потеряет пустую
               цепочку и станет «почти эквивалентным», а не эквивалентным);
            5) ещё раз удалить бесполезные символы: после удаления правил
               часть нетерминалов может стать бесплодной.

        Параметры:
            verbose   — печатать X и ставшие бесполезными символы;
            new_start — имя нового начального символа.
        Возвращает: (новая грамматика, множество X).
        """
        X = self.nullable()
        if verbose:
            print(f"  X = {{A | A =>* eps}} = {{{', '.join(sorted(X))}}}")
        s_eps = self.start in X
        start = new_start if s_eps else self.start

        new_rules = []
        for A, rhs in self.rules:
            if not rhs:
                continue                       # само eps-правило убираем
            variants = {()}
            for s in rhs:                      # все варианты вычёркивания
                if s in X:
                    variants |= {v + (s,) for v in variants}
                else:
                    variants = {v + (s,) for v in variants}
            for v in variants:
                if v:
                    new_rules.append((A, v))
        if s_eps:
            new_rules += [(start, (self.start,)), (start, ())]

        g = Grammar(self.N | {start}, self.T, new_rules, start)
        g.rules = list(dict.fromkeys(g.rules))
        g = g.remove_useless(verbose=False)
        if verbose:
            dead = sorted(self.N - g.N)
            if dead:
                print(f"  Стали бесполезными: {dead}")
        return g, X

    # ------------------------------------------------------- 3. цепные правила
    def chain_pairs(self):
        """Транзитивное замыкание отношения «A выводит B цепным правилом».

        Цепное правило — правило вида A -> B, где B тоже нетерминал:
        оно ничего не порождает, а только переименовывает символ.

        Пары (A, A) добавляются всегда: они нужны, чтобы при переносе
        правил не потерять собственные (нецепные) правила нетерминала.

        Возвращает: set пар (A, B), для которых A =>* B одними цепными
        правилами.
        """
        pairs = {(A, r[0]) for A, r in self.rules
                 if len(r) == 1 and r[0] in self.N}
        pairs |= {(A, A) for A in self.N}
        changed = True
        while changed:
            changed = False
            for a, b in list(pairs):
                for c, d in list(pairs):
                    if b == c and (a, d) not in pairs:
                        pairs.add((a, d))
                        changed = True
        return pairs

    def remove_chains(self, verbose=True):
        """Устранение цепных правил (правил вида A -> B, где B — нетерминал).

        Алгоритм:
            1) найти все цепные пары (A, B);
            2) удалить из грамматики все цепные правила;
            3) для каждой пары (A, B) скопировать нетерминалу A все НЕцепные
               правила B;
            4) повторно удалить ставшие бесполезными символы.

        Язык не меняется: вывод A => B => α заменяется более коротким A => α.

        Параметры: verbose — печатать найденные цепные пары.
        Возвращает: новую грамматику без цепных правил.
        """
        pairs = self.chain_pairs()
        chains = sorted((a, b) for a, b in pairs if a != b)
        if verbose:
            print("  Цепные пары: " +
                  (", ".join(f"{a} => {b}" for a, b in chains) if chains else "нет"))
        new_rules = [(A, r) for A, r in self.rules
                     if not (len(r) == 1 and r[0] in self.N)]
        for a, b in pairs:
            for rhs in self.rules_for(b):
                if len(rhs) == 1 and rhs[0] in self.N:
                    continue
                if (a, rhs) not in new_rules:
                    new_rules.append((a, rhs))
        g = Grammar(self.N, self.T, new_rules, self.start)
        g = g.remove_useless(verbose=False)
        if verbose:
            dead = sorted(self.N - g.N)
            if dead:
                print(f"  Стали бесполезными: {dead}")
        return g

    # ------------------------------------------------------- 4. левая рекурсия
    def remove_left_recursion(self, verbose=True, suffix="'"):
        """Устранение непосредственной левой рекурсии (правил вида A -> Aα).

        Правило
            A -> Aα1 | ... | Aαm | β1 | ... | βn
        заменяется на
            A  -> β1A' | ... | βnA' | β1 | ... | βn
            A' -> α1A' | ... | αmA' | α1 | ... | αm
        где A' — новый нетерминал (к имени A добавляется суффикс).

        Замена сохраняет язык: A' порождает «хвост» из α, повторённый
        сколько угодно раз. Левая рекурсия исчезает, потому что правила A'
        начинаются не с A', а с α.

        Почему это важно: при левой рекурсии анализатор, пытаясь раскрыть
        A -> Aα, снова и снова выбирает то же правило и зацикливается —
        поэтому без этого шага невозможен ни рекурсивный спуск, ни LL(1).

        Параметры:
            verbose — печатать найденные α и β;
            suffix  — суффикс для имени нового нетерминала.
        Возвращает: новую грамматику без непосредственной левой рекурсии.
        """
        g = self.copy()
        for A in list(g.ordered_n()):
            alphas = [r[1:] for r in g.rules_for(A) if r and r[0] == A]
            betas = [r for r in g.rules_for(A) if not (r and r[0] == A)]
            if not alphas:
                continue
            if verbose:
                print(f"  {A}: alpha = " +
                      ", ".join(Grammar.fmt_rhs(a) for a in alphas) +
                      "; beta = " + ", ".join(Grammar.fmt_rhs(b) for b in betas))
            newA = A + suffix
            while newA in g.N or newA in g.T:
                newA += suffix
            new_rules = [(lhs, rhs) for lhs, rhs in g.rules if lhs != A]
            for b in betas:
                new_rules += [(A, b + (newA,)), (A, b)]
            for a in alphas:
                new_rules += [(newA, a + (newA,)), (newA, a)]
            g.rules = new_rules
            g.N.add(newA)
        return g

    # ---------------------------------------- 5. нормальная форма Хомского
    def to_cnf(self, verbose=True):
        """Приведение к нормальной форме Хомского (A -> a или A -> BC).

        Порядок шагов — алгоритм 6, ровно в том виде, в каком он описан
        в отчёте (порядок важен, шаги не переставляются):

            1) длинные правила: правые части длины > 2 свернуть в бинарные,
               вводя новые нетерминалы Q_1, Q_2, ...;
            2) удалить eps-правила;
            3) удалить цепные правила;
            4) удалить бесполезные символы;
            5) заменить терминалы в правилах длины >= 2 нетерминалами
               X_a, X_b, ... с единственным правилом X_a -> a.

        Почему такой порядок: шаг 1 делается первым, чтобы все последующие
        преобразования работали с правилами длины не больше 2 и уже не
        создавали длинных правых частей. Замена терминалов идёт последней,
        когда окончательно известны все правила и их длины.

        Зачем это нужно: НФ Хомского — вторая нормальная форма, требуемая
        в курсовом проекте, и основа для контрольного разбора CYK (функция
        cyk), не зависящего от МП-автомата.

        Параметры: verbose — печатать каждый шаг и промежуточные грамматики.
        Возвращает: эквивалентную грамматику в НФ Хомского.
        """
        g = self.copy()

        def report(step, title, before, note):
            """Напечатать итог шага приведения (только при verbose=True).

            Параметры: step — номер шага, title — название шага,
            before — правила до шага, note — пояснение к результату.
            """
            if not verbose:
                return
            if before == g.rules:
                print(f"  Шаг {step}. {title}: изменений нет.")
            else:
                print(f"  Шаг {step}. {title}: {note}")
                print(g.as_text("      "))

        if verbose:
            print("  Приведение к нормальной форме Хомского "
                  "(алгоритм 6, пять шагов).")

        # ---- шаг 1: свернуть правые части длины > 2
        before = list(g.rules)
        created = []
        pending = []

        def fold(seq):
            """Свернуть цепочку длины > 2 в бинарные правила (справа налево).

            Возвращает: цепочку длины не больше 2; новые правила складываются
            в список pending, новые нетерминалы — в список created.
            """
            if len(seq) <= 2:
                return list(seq)
            name = f"Q_{len(created) + 1}"
            while name in g.N or name in g.T:
                name += "'"
            created.append(name)
            g.N.add(name)
            tail = fold(seq[1:])
            pending.append((name, tuple(tail)))
            return [seq[0], name]

        g.rules = [(A, tuple(fold(rhs))) for A, rhs in g.rules] + pending
        report(1, "Удаление длинных правил (длина > 2)", before,
               f"правые части свёрнуты в бинарные, введены {', '.join(sorted(created))}")

        # ---- шаг 2: eps-правила
        before = list(g.rules)
        g, nullable = g.remove_epsilon(verbose=False)
        report(2, "Удаление eps-правил", before,
               "нетерминалы, выводившие eps: "
               + (", ".join(sorted(nullable)) if nullable else "—"))

        # ---- шаг 3: цепные правила
        before = list(g.rules)
        g = g.remove_chains(verbose=False)
        report(3, "Удаление цепных правил", before,
               "цепные правила заменены правыми частями своих правил")

        # ---- шаг 4: бесполезные символы
        before = list(g.rules)
        g = g.remove_useless(verbose=False)
        report(4, "Удаление бесполезных символов", before,
               "бесплодные и недостижимые символы удалены")

        # ---- шаг 5: терминалы в правилах длины >= 2
        before = list(g.rules)
        term_nt, new_rules, created_t = {}, [], []

        def term_rule(t):
            """Нетерминал X_a для терминала a и правило X_a -> a.

            Возвращает: имя нетерминала, заменяющего терминал t.
            """
            if t not in term_nt:
                name = "X_" + t                     # X_a -> a, X_b -> b, ...
                while name in g.N or name in g.T:
                    name += "'"
                term_nt[t] = name
                created_t.append(name)
                new_rules.append((name, (t,)))
            return term_nt[t]

        for A, rhs in g.rules:
            if len(rhs) <= 1:
                new_rules.append((A, rhs))
            else:
                new_rules.append(
                    (A, tuple(term_rule(s) if s in g.T else s for s in rhs)))

        g = Grammar(g.N | set(created_t), g.T, new_rules, g.start)
        g.rules = list(dict.fromkeys(g.rules))
        report(5, "Удаление терминалов из правил длины >= 2", before,
               f"введены {', '.join(sorted(created_t))}")
        return g

    def is_cnf(self, verbose=False):
        """Проверка, находится ли грамматика в нормальной форме Хомского.

        НФ Хомского (алгоритм 6 из методических материалов) требует, чтобы
        каждое правило имело один из двух видов:

            A -> a    (один терминал);
            A -> BC   (ровно два нетерминала).

        Такая форма удобна тем, что для неё работает простой контрольный
        разбор методом динамического программирования (функция cyk).

        Параметры: verbose — печатать правила, нарушающие форму.
        Возвращает: True, если все правила имеют вид A -> a или A -> BC.
        """
        ok = True
        for A, rhs in self.rules:
            good = ((len(rhs) == 1 and rhs[0] in self.T) or
                    (len(rhs) == 2 and all(s in self.N for s in rhs)))
            if not good:
                ok = False
                if verbose:
                    print(f"    не в НФ Хомского: {A} -> {self.fmt_rhs(rhs)}")
        return ok

    def is_greibach(self, verbose=False):
        """Проверка, находится ли грамматика в нормальной форме Грейбах.

        Нормальная форма Грейбах (определение 39 из учебного пособия)
        требует, чтобы каждая продукция имела вид

            A -> aα,   где A — нетерминал, a — ТЕРМИНАЛ, α ∈ N*.

        Поэтому проверка сводится к двум условиям:
            1) в грамматике нет правил с пустой правой частью;
            2) первый символ каждой правой части — терминал.

        Второе условие автоматически означает, что грамматика не может быть
        леворекурсивной: правило, начинающееся с нетерминала A, форму не
        нарушает только если этот нетерминал не выводится сам из себя.

        Зачем это нужно: в НФ Грейбах каждый шаг вывода добавляет ровно один
        терминал, поэтому МП-автомат может разворачивать правило сразу по
        очередному символу входа, без ε-переходов на развёртывание.

        Параметры: verbose — печатать правила, нарушающие форму.
        Возвращает: True, если все правила имеют вид A -> aα.
        """
        bad = [(A, rhs) for A, rhs in self.rules
               if not rhs or rhs[0] not in self.T]
        if verbose:
            for A, rhs in bad:
                print(f"    не в НФ Грейбах: {A} -> {self.fmt_rhs(rhs)}")
        return not bad

    # ------------------------------------------------------- 6. FIRST / FOLLOW
    def first_sets(self):
        """Множества FIRST для всех нетерминалов.

        FIRST(A) — множество терминалов, с которых может начинаться цепочка,
        выводимая из A. Если из A выводится пустая цепочка, в множество
        добавляется eps.

        Вычисление — метод неподвижной точки: проходим по правилам и
        добавляем FIRST первых символов правой части, пока множества
        не перестанут меняться.

        Возвращает: dict {нетерминал: set символов}.
        """
        first, changed = {A: set() for A in self.N}, True
        while changed:
            changed = False
            for A, rhs in self.rules:
                if not rhs:
                    if EPS not in first[A]:
                        first[A].add(EPS)
                        changed = True
                    continue
                for s in rhs:
                    if s in self.T:
                        if s not in first[A]:
                            first[A].add(s)
                            changed = True
                        break
                    add = first[s] - {EPS}
                    if not add <= first[A]:
                        first[A] |= add
                        changed = True
                    if EPS not in first[s]:
                        break
                else:
                    if EPS not in first[A]:
                        first[A].add(EPS)
                        changed = True
        return first

    def follow_sets(self, first=None):
        """Множества FOLLOW для всех нетерминалов.

        FOLLOW(A) — множество терминалов, которые могут стоять
        непосредственно справа от A в сентенциальной форме. Для начального
        символа в FOLLOW входит маркер конца цепочки $.

        Правило вывода B -> αAβ даёт: FIRST(β) без eps входит в FOLLOW(A);
        если из β выводится eps, то в FOLLOW(A) входит и FOLLOW(B).

        Параметры: first — уже посчитанные множества FIRST (если None,
        считаются здесь; передают, чтобы не считать дважды).
        Возвращает: dict {нетерминал: set символов}.
        """
        first = first or self.first_sets()
        follow = {A: set() for A in self.N}
        follow[self.start].add(END)
        changed = True
        while changed:
            changed = False
            for A, rhs in self.rules:
                for i, s in enumerate(rhs):
                    if s not in self.N:
                        continue
                    add, tail_nullable = set(), True
                    for x in rhs[i + 1:]:
                        if x in self.T:
                            add.add(x)
                            tail_nullable = False
                            break
                        add |= first[x] - {EPS}
                        if EPS not in first[x]:
                            tail_nullable = False
                            break
                    if tail_nullable:
                        add |= follow[A]
                    if not add <= follow[s]:
                        follow[s] |= add
                        changed = True
        return follow

    @staticmethod
    def first_of(rhs, first):
        """FIRST конкретной цепочки символов (например, правой части правила).

        Возвращает: (множество терминалов, признак того, что цепочка
        выводится в eps). Признак нужен, чтобы при LL(1)-разборе выбрать
        правило по символу, следующему ЗА нетерминалом.
        """
        f = set()
        for s in rhs:
            if s in first:                      # нетерминал
                f |= first[s] - {EPS}
                if EPS not in first[s]:
                    return f, False
            else:
                f.add(s)
                return f, False
        return f, True

    def is_ll1(self, verbose=False):
        """Проверка, является ли грамматика LL(1)-грамматикой.

        LL(1) означает: правило для нетерминала можно выбрать, посмотрев
        ровно один очередной символ входа. Условие: для каждого нетерминала
        множества FIRST его альтернатив не пересекаются (если альтернатива
        выводит eps, вместо FIRST берётся FOLLOW).

        Параметры: verbose — печатать найденные конфликты.
        Возвращает: True, если грамматика LL(1).
        """
        first = self.first_sets()
        follow = self.follow_sets(first)
        ok = True
        for A in self.ordered_n():
            rules = self.rules_for(A)
            sets = []
            for rhs in rules:
                f, nullable = self.first_of(rhs, first)
                if nullable:
                    f |= follow[A]
                sets.append(f)
            for i in range(len(rules)):
                for j in range(i + 1, len(rules)):
                    common = sets[i] & sets[j]
                    if common:
                        ok = False
                        if verbose:
                            syms = ", ".join(sorted(common))
                            print(f"    нетерминал {A}: правила "
                                  f"«{A} -> {self.fmt_rhs(rules[i])}» и "
                                  f"«{A} -> {self.fmt_rhs(rules[j])}» начинаются "
                                  f"с одного символа {syms} — по одному символу "
                                  f"входа выбрать правило нельзя")
        return ok


# ============================================================================
#  Магазинный автомат
# ============================================================================
class PDA:
    """Магазинный автомат M = (Q, Sigma, Gamma, delta, q0, Z0, F).

    Атрибуты:
        Q     — множество состояний;
        Sigma — входной алфавит;
        Gamma — алфавит магазина (терминалы, нетерминалы и Z0);
        delta — функция переходов: delta[(q, a, Z)] = [(q', (z1, ..., zk)), ...];
                при чтении a (или eps) и вершине магазина Z автомат переходит
                в q' и заменяет Z цепочкой z1..zk (z1 — новая вершина);
        q0    — начальное состояние, z0 — начальный символ магазина;
        F     — множество допускающих состояний;
        table — управляющая таблица LL(1); заполняется только для автомата M2.

    Магазин хранится кортежем, где ПОСЛЕДНИЙ элемент — вершина магазина.
    """

    def __init__(self, states, sigma, gamma, delta, q0, z0, final):
        """Создать автомат из готовых множеств и словаря переходов.

        delta передаётся уже заполненным (его строят функции
        build_pda_from_grammar и build_ll1_pda), чтобы класс оставался
        простой моделью и не знал, из какой грамматики он получен.
        """
        self.Q, self.Sigma, self.Gamma = set(states), set(sigma), set(gamma)
        self.delta, self.q0, self.z0, self.F = delta, q0, z0, set(final)
        self.table = {}

    @staticmethod
    def fmt_stack(stack):
        """Магазин в читаемом виде: вершина слева, как принято в учебниках."""
        return "".join(reversed(stack)) if stack else EPS

    def _moves(self, q, symbol, top):
        """Список переходов по тройке (состояние, символ входа, вершина магазина).

        Пустой список означает, что такого перехода нет.
        """
        return self.delta.get((q, symbol, top), [])

    def accepts(self, word, max_steps=50000):
        """Проверка допускания НЕДЕТЕРМИНИРОВАННЫМ автоматом.

        Перебирает конфигурации (состояние, позиция во входе, магазин)
        в ширину и ищет хотя бы один путь, приводящий в допускающее
        состояние после чтения всей цепочки.

        Обход в ширину, а не в глубину: так не бывает зацикливания на
        eps-переходах и первым находится короткий путь разбора.

        Параметры:
            word      — входная цепочка;
            max_steps — предохранитель от зацикливания (предел числа
                        просмотренных конфигураций).
        Возвращает: True, если цепочка допускается.
        """
        start = (self.q0, 0, (self.z0,))
        queue, seen, steps = [start], {start}, 0
        while queue and steps < max_steps:
            q, pos, stack = queue.pop(0)
            steps += 1
            if pos == len(word) and q in self.F:
                return True
            if not stack:
                continue
            look = word[pos] if pos < len(word) else END
            for symbol in (look, EPS):
                for q2, push in self._moves(q, symbol, stack[-1]):
                    # входной символ потребляется только при совпадении с вершиной
                    eats = (symbol not in (EPS, END) and symbol == stack[-1])
                    cfg = (q2, pos + (1 if eats else 0),
                           stack[:-1] + tuple(reversed(push)))
                    if cfg not in seen and len(cfg[2]) <= 300:
                        seen.add(cfg)
                        queue.append(cfg)
        return False

    def run(self, word, verbose=True):
        """Моделирование ДЕТЕРМИНИРОВАННОГО автомата с трассировкой.

        На каждом шаге берётся ровно один переход: сначала по текущему
        символу входа, затем (если такого нет) по eps. Если переходов нет
        или их несколько — автомат останавливается с отказом: детерминированный
        автомат не имеет права выбирать.

        Входной символ считается прочитанным только тогда, когда он совпал
        с вершиной магазина, то есть был «сверен», а не просто просмотрен.

        Параметры:
            word    — входная цепочка;
            verbose — печатать таблицу трассировки (шаг, остаток входа, магазин).
        Возвращает: True, если цепочка допущена.
        """
        q, pos, stack = self.q0, 0, (self.z0,)
        history = [(q, pos, stack)]
        limit = 32 * (len(word) + 8)
        while limit:
            limit -= 1
            if not stack:
                break
            if pos == len(word) and q in self.F:
                break
            top = stack[-1]
            look = word[pos] if pos < len(word) else END
            moves = self._moves(q, look, top)
            symbol = look
            if not moves:
                moves, symbol = self._moves(q, EPS, top), EPS
            if len(moves) != 1:
                break
            q, push = moves[0]
            stack = stack[:-1] + tuple(reversed(push))
            # потребляем входной символ только если он совпал с вершиной магазина
            if symbol not in (EPS, END) and symbol == top:
                pos += 1
            history.append((q, pos, stack))
        accepted = (q in self.F and pos == len(word) and stack == (self.z0,))
        if verbose:
            print(f"\n  Вход: \"{word}\"")
            print("  " + "-" * 66)
            for i, (st, p, stk) in enumerate(history):
                print(f"  {i:2d}. q={st:<3} прочитано: \"{word[:p]}\""
                      f"{'':<2} остаток: \"{word[p:] if p < len(word) else END}\""
                      f"{'':<2} магазин: {self.fmt_stack(stk)}")
            print("  " + "-" * 66)
            print("  РЕЗУЛЬТАТ: " + ("цепочка ПРИНАДЛЕЖИТ языку" if accepted
                                     else "цепочка НЕ принадлежит языку"))
        return accepted


def build_pda_from_grammar(g, q0="q0", q="q", qf="qf"):
    """Построение недетерминированного МП-автомата по КС-грамматике.

    Используется каноническая конструкция, моделирующая левосторонний вывод,
    с допусканием по конечному состоянию. Для каждого правила A -> α
    добавляется переход delta(q, eps, A) = (q, α): нетерминал на вершине
    магазина заменяется правой частью правила. Для каждого терминала a
    добавляется переход delta(q, a, a) = (q, eps), который сверяет символ
    входа с вершиной магазина и снимает её.

    Переходы автомата:
        delta(q0, eps, Z0) = (q, S Z0)   — положить начальный символ в магазин;
        delta(q, eps, A)   = (q, α)      — развернуть нетерминал по правилу;
        delta(q, a, a)     = (q, eps)    — сверить и снять терминал;
        delta(q, $, Z0)    = (qf, Z0)    — конец разбора.

    Автомат получается недетерминированным: у нетерминалов с несколькими
    правилами (здесь B и T) по одному символу возможно несколько переходов.

    Параметры:
        g       — грамматика;
        q0, q, qf — имена начального, рабочего и допускающего состояний.
    Возвращает: объект PDA.
    """
    delta = {}
    delta.setdefault((q0, EPS, "Z0"), []).append((q, (g.start, "Z0")))
    for A, rhs in g.rules:
        delta.setdefault((q, EPS, A), []).append((q, rhs))
    for a in g.T:
        delta.setdefault((q, a, a), []).append((q, ()))
    delta.setdefault((q, END, "Z0"), []).append((qf, ("Z0",)))
    return PDA({q0, q, qf}, g.T, g.N | g.T | {"Z0"}, delta, q0, "Z0", {qf})


def build_ll1_pda(g, q0="q0", q="q", qf="qf"):
    """Построение детерминированного LL(1)-автомата по грамматике.

    Отличие от недетерминированного автомата: пара (нетерминал, очередной
    символ входа) однозначно задаёт правило. Управляющая таблица строится
    по множествам FIRST и FOLLOW:
        M[A, a] = α, если a ∈ FIRST(α);
        M[A, a] = α, если из α выводится eps и a ∈ FOLLOW(A).

    По этой таблице заполняются и переходы delta, и поле table (чтобы
    таблицу можно было напечатать в отчёте).

    Требование: грамматика должна быть LL(1) — это проверяет метод is_ll1
    (для G4 он даёт False, для G5 — True).

    Параметры:
        g         — грамматика (обычно G5);
        q0, q, qf — имена начального, рабочего и допускающего состояний.
    Возвращает: объект PDA с заполненным полем table.
    """
    first = g.first_sets()
    follow = g.follow_sets(first)
    delta = {}
    table = {}
    for A in g.ordered_n():
        for rhs in g.rules_for(A):
            f, nullable = g.first_of(rhs, first)
            targets = set(f) | (follow[A] if nullable else set())
            for a in targets:
                delta.setdefault((q, a, A), []).append((q, rhs))
                table[(A, a)] = rhs
    for a in g.T:
        delta.setdefault((q, a, a), []).append((q, ()))
    delta.setdefault((q0, EPS, "Z0"), []).append((q, (g.start, "Z0")))
    delta.setdefault((q, END, "Z0"), []).append((qf, ("Z0",)))
    pda = PDA({q0, q, qf}, g.T, g.N | g.T | {"Z0"}, delta, q0, "Z0", {qf})
    pda.table = table
    return pda


def cyk(grammar_cnf, word):
    """Разбор цепочки алгоритмом CYK по грамматике в НФ Хомского.

    Вспомогательная функция: в задании не требуется и в МП-автомате не
    используется. Нужна как НЕЗАВИСИМАЯ проверка результата — если и
    МП-автомат, и этот разбор дают одинаковый ответ на всех тестовых
    цепочках, значит преобразования грамматики не изменили язык.

    Метод — динамическое программирование: table[i][j] хранит множество
    нетерминалов, из которых выводится подцепочка word[i..j]. Сначала
    заполняются подцепочки длины 1 (по правилам A -> a), затем более
    длинные (по правилам A -> BC).

    Параметры:
        grammar_cnf — грамматика в нормальной форме Хомского;
        word        — проверяемая цепочка.
    Возвращает: True, если цепочка выводится из начального символа.
    """
    n = len(word)
    if n == 0:
        return False
    table = [[set() for _ in range(n)] for _ in range(n)]
    for i, a in enumerate(word):
        for A, rhs in grammar_cnf.rules:
            if rhs == (a,):
                table[i][i].add(A)
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            for k in range(i, j):
                for A, rhs in grammar_cnf.rules:
                    if len(rhs) == 2 and rhs[0] in table[i][k] \
                            and rhs[1] in table[k + 1][j]:
                        table[i][j].add(A)
    return grammar_cnf.start in table[0][n - 1]


# ============================================================================
#  Грамматики варианта
# ============================================================================
def source_grammar():
    """Исходная грамматика варианта 13 (seed 5).

    Возвращает: объект Grammar с правилами из задания; eps-правило H -> eps
    записано пустым кортежем в правой части.
    """
    N = ["S", "A", "B", "C", "D", "O", "H", "M", "E", "F", "T"]
    T = ["a", "b", "c", "d", "f", "v", "h", "m", "j"]
    rules = [
        ("A", ("b", "C")), ("B", ("c", "A")), ("C", ("d", "D")),
        ("D", ("O",)), ("O", ("f",)), ("S", ("a", "A", "B", "H")),
        ("H", ()), ("M", ("v",)), ("E", ("h", "F", "d")),
        ("B", ("j", "T")), ("T", ("T", "m")), ("T", ("m",)),
    ]
    return Grammar(N, T, rules, "S")


def factored_grammar():
    """Грамматика G5 — G4 после левой факторизации правил T и T'.

    Факторизация нужна, чтобы убрать конфликт LL(1): у T и T' обе
    альтернативы начинались с одного и того же терминала m, поэтому по
    одному символу входа правило выбрать было нельзя. Общий префикс m
    вынесен в отдельное правило: T -> mT1, T1 -> mT1 | eps.

    Возвращает: грамматику, которая является LL(1).
    """
    N = ["S", "A", "B", "C", "D", "T", "T1"]
    T = ["a", "b", "c", "d", "f", "j", "m"]
    rules = [
        ("S", ("a", "A", "B")), ("A", ("b", "C")),
        ("B", ("c", "A")), ("B", ("j", "T")),
        ("C", ("d", "D")), ("D", ("f",)),
        ("T", ("m", "T1")), ("T1", ("m", "T1")), ("T1", ()),
    ]
    return Grammar(N, T, rules, "S")


def in_language(word):
    """Эталонный ответ: принадлежность цепочки языку, без всякого разбора.

    Язык грамматики: L = {abdfcbdf} U {abdf j m^n | n >= 1}.
    Функция написана «по описанию языка», независимо от автоматов, —
    именно поэтому её можно использовать как эталон в тестах.

    Параметры: word — проверяемая цепочка.
    Возвращает: True, если цепочка принадлежит языку.
    """
    if word == "abdfcbdf":
        return True
    return (word.startswith("abdfj") and len(word) > 5
            and all(ch == "m" for ch in word[5:]))


# ============================================================================
#  Демонстрация
# ============================================================================
def demo_grammar():
    """Приведённая грамматика G4, собранная из исходной всеми шагами.

    Возвращает: объект Grammar после удаления бесполезных символов,
    eps-правил, цепных правил и левой рекурсии.
    """
    g = source_grammar().remove_useless(verbose=False)
    g = g.remove_epsilon(verbose=False)[0]
    g = g.remove_chains(verbose=False)
    return g.remove_left_recursion(verbose=False)


def interactive():
    """Интерактивный режим: разбор введённых цепочек по шагам.

    Пользователь вводит цепочку, программа печатает пошаговую трассировку
    детерминированного автомата M2 (что лежит в магазине и что осталось
    на входе), сообщает, принадлежит ли цепочка языку, и перепроверяет
    ответ двумя независимыми способами: недетерминированным автоматом M1
    и разбором CYK по грамматике в НФ Хомского. Пустая строка — выход.
    """
    g4 = demo_grammar()
    g5 = factored_grammar()
    nd = build_pda_from_grammar(g4)
    det = build_ll1_pda(g5)
    cnf = g4.to_cnf(verbose=False)

    print("=" * 70)
    print("ИНТЕРАКТИВНЫЙ РЕЖИМ: проверка цепочек")
    print("=" * 70)
    print(f"  Алфавит: {', '.join(sorted(g4.T))}")
    print("  Язык:    L(G) = {abdfcbdf} ∪ {abdf j m^n | n >= 1}")
    print("  Введите цепочку и нажмите Enter. Пустая строка — выход.")
    while True:
        try:
            word = input("\nЦепочка: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not word:
            break
        unknown = sorted(set(word) - g4.T)
        if unknown:
            print(f"  В цепочке есть символы, которых нет в алфавите: "
                  f"{', '.join(unknown)}")
            continue
        det.run(word, verbose=True)
        print(f"  Перепроверка: недетерминированный M1 — "
              f"{'допускает' if nd.accepts(word) else 'не допускает'}, "
              f"разбор CYK по НФ Хомского — "
              f"{'допускает' if cyk(cnf, word) else 'не допускает'}.")


def main():
    """Демонстрация работы программы.

    Печатает исходную грамматику, затем по шагам все преобразования
    (G -> G1 -> G2 -> G3 -> G4 -> G5), приведение к обеим нормальным формам,
    таблицы FIRST/FOLLOW, переходы недетерминированного автомата,
    управляющую таблицу LL(1) и трассировку разбора нескольких цепочек.
    В конце всегда запускает автотесты.

    Ключи запуска:
        --test        — только автотесты, без пошагового вывода;
        --interactive — интерактивный режим проверки введённых цепочек.
    """
    args = sys.argv[1:]
    if args and args[0] in ("--interactive", "-i"):
        interactive()
        return
    tests_only = "--test" in args

    if not tests_only:
        g0 = source_grammar()
        g0.show("Исходная грамматика G:")

        print("\n" + "=" * 70)
        print("ПУНКТ 4. Бесполезные символы и eps-правила")
        print("=" * 70)
        print(f"  Продуктивные: {sorted(g0.productive())}")
        print(f"  Недостижимые: {sorted((g0.N | g0.T) - g0.reachable())}")
        g1 = g0.remove_useless()
        g1.show("G1 — после удаления бесполезных символов:")
        g2, X = g1.remove_epsilon()
        g2.show("G2 — после удаления eps-правил:")

        print("\n" + "=" * 70)
        print("ПУНКТ 5. Цепные правила и левая рекурсия")
        print("=" * 70)
        g3 = g2.remove_chains()
        g3.show("G3 — после удаления цепных правил:")
        g4 = g3.remove_left_recursion()
        g4.show("G4 — после устранения левой рекурсии (приведённая):")

        print("\n" + "=" * 70)
        print("ПУНКТ 6. Форма грамматики и приведение к нормальным формам")
        print("=" * 70)
        g4.remove_useless().show("Проверка приведения G4:")
        print("\n  Форма G4: контекстно-свободная (тип 2), неукорачивающая,")
        print("  приведённая, однозначная, без левой рекурсии.")

        print("\n  Нормальная форма Хомского (каждое правило A -> a или A -> BC).")
        print("  G4 в этой форме не находится: в ней есть правила вида S -> aAB")
        print("  (терминал и два нетерминала), A -> bC и т. п. Выполняем приведение:")
        cnf = g4.to_cnf()
        cnf.show("\n  Получена грамматика G_H в нормальной форме Хомского:")

        print("\n  Нормальная форма Грейбах: каждое правило имеет вид A -> aα,")
        print("  где a — терминал, α — цепочка нетерминалов (возможно, пустая).")
        print("  G4 уже имеет эту форму: каждая правая часть начинается")
        print("  с терминала, поэтому приведение не требуется — только проверка.")
        print("    все правила G4 начинаются с терминала — "
              + ("да" if g4.is_greibach() else "нет") + ".")

        print("\n" + "=" * 70)
        print("ПУНКТ 7. Проектирование МП-автомата")
        print("=" * 70)
        print("  Сначала проверим, годится ли G4 для детерминированного LL(1)-разбора.")
        print("  Проверка G4 на LL(1)-грамматику:")
        ll1_ok = g4.is_ll1(verbose=True)
        print("    Вывод: G4 " + ("является" if ll1_ok else "не является")
              + " LL(1)-грамматикой.")
        if not ll1_ok:
            print("    Чтобы разбор был детерминированным, применяем левую факторизацию:")
            print("    общий префикс m у правил T -> mT' | m выносится в отдельное правило.")
        g5 = factored_grammar()
        g5.show("  G5 — грамматика после левой факторизации:")
        print(f"  Проверка: G5 является LL(1)-грамматикой — "
              f"{'да' if g5.is_ll1() else 'нет'}.")
        pda = build_pda_from_grammar(g4)
        print("  Недетерминированный МП-автомат по G4 (состояния q0, q, qf):")
        for key, moves in sorted(pda.delta.items()):
            q, sym, top = key
            s = "eps" if sym == EPS else sym
            for q2, push in moves:
                print(f"    d({q}, {s}, {top}) = ({q2}, "
                      f"{''.join(push) if push else EPS})")

        ll1 = build_ll1_pda(g5)
        print("\n  Управляющая таблица детерминированного LL(1)-автомата:")
        cols = sorted(g5.T) + [END]
        print("    " + "A".ljust(4) + "".join(c.ljust(10) for c in cols))
        for A in g5.ordered_n():
            row = "    " + A.ljust(4)
            for c in cols:
                rhs = ll1.table.get((A, c))
                row += (Grammar.fmt_rhs(rhs) if rhs is not None else "-").ljust(10)
            print(row)

        print("\n" + "=" * 70)
        print("ПУНКТ 8. Реализация: работа автоматов")
        print("=" * 70)
        for w in ["abdfcbdf", "abdfjm", "abdfjmmm", "abdf", "abdfcbdfm"]:
            ll1.run(w)

    run_tests()


def run_tests():
    """Автотесты: сверка автоматов, разбора и эталонного описания языка.

    Проверяется три вещи:
        1) обе грамматики дают тот же язык, что и эталон in_language;
        2) недетерминированный автомат, LL(1)-автомат и разбор CYK дают
           одинаковые ответы на наборе «сложных» цепочек;
        3) ни один автомат не допускает ошибочно короткие цепочки —
           полный перебор всех цепочек длины 0..4 над алфавитом G4 (2801 шт.).

    Возвращает: True, если все проверки прошли.
    """
    print("\n" + "=" * 70)
    print("АВТОТЕСТЫ")
    print("=" * 70)

    g4 = demo_grammar()
    g5 = factored_grammar()
    nd = build_pda_from_grammar(g4)
    det = build_ll1_pda(g5)
    cnf = g4.to_cnf(verbose=False)

    print(f"  1. Терминалы после приведения: {sorted(g4.T)}")
    print(f"  2. Нетерминалы после приведения: {sorted(g4.N)}")
    print("  3. Формы грамматик:")
    print(f"     G4  — нормальная форма Грейбах:   {'да' if g4.is_greibach() else 'нет'}")
    print(f"     G_H — нормальная форма Хомского:  {'да' if cnf.is_cnf() else 'нет'}")
    print(f"     G5  — LL(1)-грамматика:           {'да' if g5.is_ll1() else 'нет'}")

    ok_all = True

    def check_true(name, condition):
        """Проверить утверждение и напечатать итог в виде понятной фразы."""
        nonlocal ok_all
        if not condition:
            ok_all = False
        print(f"  [{'OK  ' if condition else 'FAIL'}] {name}")

    check_true("Эталон: abdfcbdf принадлежит языку", in_language("abdfcbdf"))
    check_true("Эталон: abdfjmmmm принадлежит языку", in_language("abdfjmmmm"))
    check_true("G4 не является грамматикой в нормальной форме Хомского",
               not g4.is_cnf())
    check_true("G4 уже имеет нормальную форму Грейбах", g4.is_greibach())
    check_true("G_H находится в нормальной форме Хомского", cnf.is_cnf())
    check_true("G5 является LL(1)-грамматикой", g5.is_ll1())

    cases = ["abdfcbdf", "abdfjm", "abdfjmm", "abdfjmmmm",
             "abdf", "abdfj", "abdfcbdfm", "abdfcbdfx", "abdfjmj",
             "abdfcb", "dfcbdf", "abdfjc"]

    def check_word(word):
        """Сверить ответы трёх способов разбора с эталоном и напечатать строку."""
        nonlocal ok_all
        expected = in_language(word)
        m1 = nd.accepts(word)
        m2 = det.run(word, verbose=False)
        cyk_ok = cyk(cnf, word)
        good = (m1 == m2 == cyk_ok == expected)
        if not good:
            ok_all = False
        word_or_no = lambda flag: "допускает" if flag else "не допускает"
        print(f"  [{'OK  ' if good else 'FAIL'}] \"{word}\": "
              f"M1 — {word_or_no(m1)}, M2 — {word_or_no(m2)}, "
              f"CYK — {word_or_no(cyk_ok)}; эталон — {word_or_no(expected)}")

    for w in cases:
        check_word(w)

    # исчерпывающая проверка всех цепочек длины 0..4 над алфавитом G4
    alphabet = sorted(g4.T)
    print(f"  4. Перебор всех цепочек длины 0..4 над {alphabet}:")
    from itertools import product
    total = bad = 0
    for length in range(5):
        for tup in product(alphabet, repeat=length):
            w = "".join(tup)
            total += 1
            if nd.accepts(w) or det.run(w, verbose=False):
                bad += 1
                print(f"     Ложное допускание: \"{w}\"")
    check_true(f"Перебор {total} цепочек: ни одна не допущена ошибочно", bad == 0)

    print("-" * 70)
    print("ИТОГ: " + ("ВСЕ ТЕСТЫ ПРОЙДЕНЫ" if ok_all else "ЕСТЬ ОШИБКИ"))
    return ok_all


if __name__ == "__main__":
    main()
