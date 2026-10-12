# -*- coding: utf-8 -*-
"""
Генерация Части 1 курсовой работы по теории автоматов.
Паттерн: ^\\d{5}$ (ZIP-код — ровно 5 десятичных цифр)
Полная поддержка кириллицы и математических индексов без неизвестных глифов.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

FONT_DIR = r"C:\Windows\Fonts"

def register_fonts():
    fonts = {
        "TimesRu":        "times.ttf",
        "TimesRu-Bold":   "timesbd.ttf",
        "TimesRu-Italic": "timesi.ttf",
        "CourRu":         "cour.ttf",
        "CourRu-Bold":    "courbd.ttf",
    }
    for name, fname in fonts.items():
        path = os.path.join(FONT_DIR, fname)
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
    return "TimesRu"

BASE_FONT   = register_fonts()
BOLD_FONT   = "TimesRu-Bold"
ITALIC_FONT = "TimesRu-Italic"
MONO_FONT   = "CourRu"

def make_styles():
    styles = {}

    styles["title"] = ParagraphStyle(
        "title", fontName=BOLD_FONT, fontSize=14,
        alignment=TA_CENTER, spaceAfter=6, leading=18
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", fontName=BASE_FONT, fontSize=12,
        alignment=TA_CENTER, spaceAfter=4, leading=16
    )
    styles["h1"] = ParagraphStyle(
        "h1", fontName=BOLD_FONT, fontSize=13,
        alignment=TA_LEFT, spaceBefore=14, spaceAfter=6, leading=18
    )
    styles["h2"] = ParagraphStyle(
        "h2", fontName=BOLD_FONT, fontSize=12,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=4, leading=16
    )
    styles["body"] = ParagraphStyle(
        "body", fontName=BASE_FONT, fontSize=12,
        alignment=TA_JUSTIFY, spaceAfter=4, leading=16,
        firstLineIndent=18
    )
    styles["body_noindent"] = ParagraphStyle(
        "body_noindent", fontName=BASE_FONT, fontSize=12,
        alignment=TA_LEFT, spaceAfter=4, leading=16
    )
    styles["formula"] = ParagraphStyle(
        "formula", fontName=BASE_FONT, fontSize=11,
        alignment=TA_LEFT, spaceAfter=3, leading=15,
        leftIndent=24
    )
    styles["centered"] = ParagraphStyle(
        "centered", fontName=BASE_FONT, fontSize=12,
        alignment=TA_CENTER, spaceAfter=4, leading=16
    )
    styles["tbl_cell"] = ParagraphStyle(
        "tbl_cell", fontName=BASE_FONT, fontSize=11,
        alignment=TA_CENTER, leading=13
    )
    styles["tbl_head"] = ParagraphStyle(
        "tbl_head", fontName=BOLD_FONT, fontSize=11,
        alignment=TA_CENTER, leading=13, textColor=colors.white
    )
    styles["rule_cell"] = ParagraphStyle(
        "rule_cell", fontName=BASE_FONT, fontSize=11,
        alignment=TA_LEFT, leading=14
    )
    return styles

def make_dka_table(styles):
    def tc(text, is_head=False):
        return Paragraph(text, styles["tbl_head"] if is_head else styles["tbl_cell"])

    header = [tc("Состояние", True), tc("Символ d (0-9)", True)]
    rows = [
        [tc("-&gt; q<sub>0</sub>"), tc("q<sub>1</sub>")],
        [tc("q<sub>1</sub>"),       tc("q<sub>2</sub>")],
        [tc("q<sub>2</sub>"),       tc("q<sub>3</sub>")],
        [tc("q<sub>3</sub>"),       tc("q<sub>4</sub>")],
        [tc("q<sub>4</sub>"),       tc("q<sub>f</sub> *")],
        [tc("* q<sub>f</sub>"),     tc("q<sub>err</sub>")],
        [tc("q<sub>err</sub>"),     tc("q<sub>err</sub>")],
    ]
    data = [header] + rows
    t = Table(data, colWidths=[7*cm, 7*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4057")),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF0FB")]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    return t

def make_distinguish_table(styles):
    def tc(text, is_head=False):
        return Paragraph(text, styles["tbl_head"] if is_head else styles["tbl_cell"])

    states_raw = [
        "q<sub>0</sub>", "q<sub>1</sub>", "q<sub>2</sub>",
        "q<sub>3</sub>", "q<sub>4</sub>", "q<sub>f</sub>", "q<sub>err</sub>"
    ]
    mark = "X"
    n = len(states_raw)

    # Классическая нижнетреугольная таблица: столбцы q0..qf, строки q1..qerr
    data = [[tc("", True)] + [tc(s, True) for s in states_raw[:-1]]]
    for i in range(1, n):
        row = [tc(states_raw[i], True)]
        for j in range(n - 1):
            if j >= i:
                row.append(tc(""))
            else:
                row.append(tc(mark))
        data.append(row)

    col_w = [2.2*cm] + [1.8*cm] * (n - 1)
    t = Table(data, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4057")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#2E4057")),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#EAF0FB")]),
    ]))
    return t

def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=3*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        title="Курсовой проект. Часть 1",
        author="МАИ"
    )

    S = make_styles()
    story = []

    def p(text, style="body"):
        return Paragraph(text, S[style])

    def sp(n=6):
        return Spacer(1, n)

    def hr():
        return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#AAAAAA"), spaceAfter=4)

    # ── Титульная / заглавная часть ──────────────────────────────────────────
    story += [
        p("Московский авиационный институт", "subtitle"),
        p("(национальный исследовательский университет)", "subtitle"),
        sp(2),
        p("Институт «Компьютерные науки и прикладная математика»", "subtitle"),
        sp(16),
        p("КУРСОВОЙ ПРОЕКТ", "title"),
        p("по дисциплине «Теория автоматов и формальных языков»", "subtitle"),
        sp(6),
        p("Часть 1", "title"),
        sp(24),
        p("<b>Вариант задания:</b> паттерн №4 из раздела 8 («Проверка пользовательского ввода»)", "body_noindent"),
        sp(2),
        p('<b>Паттерн:</b> <font name="CourRu">if (!Regex.Match(zipCodeTextBox.Text, @"^\\d{5}$").Success)</font>', "body_noindent"),
        sp(2),
        p("<b>Регулярное выражение:</b> ^\\d{5}$", "body_noindent"),
        p("<b>Описание языка:</b> цепочки из ровно пяти десятичных цифр (ZIP-код)", "body_noindent"),
        sp(60),
        p("Москва — 2026", "centered"),
        PageBreak(),
    ]

    # ── Пункт 1. Грамматика ───────────────────────────────────────────────────
    story += [
        p("1. Проектирование регулярной леволинейной грамматики", "h1"),
        hr(),
        p("Заданный паттерн <b>^\\d{5}$</b> описывает регулярный язык L над терминальным алфавитом "
          "V<sub>T</sub> = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}, порождающий цепочки, состоящие "
          "ровно из пяти десятичных цифр (ZIP-код)."),
        sp(4),
        p("По требованию задания проектируется <b>леволинейная грамматика</b> G<sub>L</sub> = (V<sub>T</sub>, V<sub>N</sub>, P, S). "
          "В леволинейной грамматике все правила вывода имеют канонический вид:"),
        p("   <b>A -&gt; Ba</b>   или   <b>A -&gt; a</b>,   где A, B принадлежат V<sub>N</sub>, a принадлежит V<sub>T</sub>.", "formula"),
        sp(4),
        p("В леволинейной грамматике цепочка в процессе вывода нарастает слева направо (нетерминал порождает префикс слова, "
          "к которому справа приписывается очередной терминал)."),
        sp(4),
        p("Определим формальные компоненты леволинейной грамматики G<sub>L</sub>:"),
        p("* <b>V<sub>T</sub></b> = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9} — терминальный алфавит;", "body_noindent"),
        p("* <b>V<sub>N</sub></b> = {S, A, B, C, D} — множество нетерминальных символов;", "body_noindent"),
        p("* <b>S</b> — целевой (начальный) нетерминал грамматики.", "body_noindent"),
        sp(6),
        p("<b>Множество правил вывода (продукций) P:</b>", "body_noindent"),
        sp(4),
    ]

    rules = [
        ("A", "0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9"),
        ("B", "A0 | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9"),
        ("C", "B0 | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | B9"),
        ("D", "C0 | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9"),
        ("S", "D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9"),
    ]
    rules_data = [
        [Paragraph("Нетерминал", S["tbl_head"]), Paragraph("Правила вывода (леволинейные)", S["tbl_head"])]
    ] + [
        [Paragraph(f"<b>{lhs}</b>", S["tbl_cell"]), Paragraph(f"{lhs} -&gt; {rhs}", S["rule_cell"])]
        for lhs, rhs in rules
    ]
    rt = Table(rules_data, colWidths=[3.5*cm, 11.5*cm])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4057")),
        ("ALIGN",      (0, 0), (0, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF0FB")]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING", (1, 1), (1, -1), 8),
    ]))
    story += [rt, sp(4)]

    story += [
        p("Здесь запись вида «A -&gt; 0 | 1 | ... | 9» и «B -&gt; A0 | A1 | ... | A9» является компактной "
          "формой записи для десяти отдельных продукций: B -&gt; A0, B -&gt; A1, ..., B -&gt; A9."),
        sp(4),
        p("Семантика нетерминалов (накопление префикса распознанной длины):"),
        p("* <b>A</b> — порождает цепочку из ровно 1 цифры (начальный этап вывода);", "body_noindent"),
        p("* <b>B</b> — накапливает цепочку из ровно 2 цифр (B -&gt; Ad);", "body_noindent"),
        p("* <b>C</b> — накапливает цепочку из ровно 3 цифр (C -&gt; Bd);", "body_noindent"),
        p("* <b>D</b> — накапливает цепочку из ровно 4 цифр (D -&gt; Cd);", "body_noindent"),
        p("* <b>S</b> — целевой нетерминал: цепочка из ровно 5 цифр (S -&gt; Dd).", "body_noindent"),
        sp(6),
        p("<b>Пример цепочки вывода</b> для слова «12345» (вывод идёт от целевого символа S):"),
        sp(2),
        p("S =&gt; D5 =&gt; C45 =&gt; B345 =&gt; A2345 =&gt; 12345", "formula"),
        sp(6),
        p("Поскольку все правила имеют вид A -&gt; Ba или A -&gt; a, грамматика G<sub>L</sub> "
          "является <b>леволинейной регулярной</b> (тип 3 по классификации Хомского)."),
    ]

    # ── Пункт 2. Конечный автомат ─────────────────────────────────────────────
    story += [
        sp(5),
        p("2. Преобразование леволинейной грамматики в конечный автомат (КА). Анализ ДКА / НДКА", "h1"),
        hr(),
        p("По каноническому алгоритму преобразования леволинейной грамматики G<sub>L</sub> = (V<sub>T</sub>, V<sub>N</sub>, P, S) "
          "в конечный автомат M = (Q, Σ, δ, q<sub>0</sub>, F):"),
        sp(4),
        p("1. Вводится новое начальное состояние q<sub>0</sub> (которое не принадлежит V<sub>N</sub>): начальное состояние автомата q<sub>0</sub>."),
        p("2. Каждому нетерминалу из V<sub>N</sub> сопоставляется состояние автомата:"),
        p("   A -&gt; q<sub>1</sub>,   B -&gt; q<sub>2</sub>,   C -&gt; q<sub>3</sub>,   D -&gt; q<sub>4</sub>,   S -&gt; q<sub>f</sub>", "formula"),
        p("3. Для каждого правила вида A -&gt; a (a принадлежит V<sub>T</sub>) задаётся переход из начального состояния: δ(q<sub>0</sub>, a) = A (то есть δ(q<sub>0</sub>, d) = q<sub>1</sub>)."),
        p("4. Для каждого правила вида Y -&gt; Xa (X, Y принадлежат V<sub>N</sub>, a принадлежит V<sub>T</sub>) задаётся переход: δ(X, a) = Y:"),
        p("   δ(A, d) = B  =&gt;  δ(q<sub>1</sub>, d) = q<sub>2</sub><br/>"
          "   δ(B, d) = C  =&gt;  δ(q<sub>2</sub>, d) = q<sub>3</sub><br/>"
          "   δ(C, d) = D  =&gt;  δ(q<sub>3</sub>, d) = q<sub>4</sub><br/>"
          "   δ(D, d) = S  =&gt;  δ(q<sub>4</sub>, d) = q<sub>f</sub>", "formula"),
        p("5. Целевой нетерминал S становится допускающим состоянием автомата: F = {S} = {q<sub>f</sub>}."),
        p("6. Для обеспечения полной определённости функции переходов вводится состояние-ловушка q<sub>err</sub>: δ(q<sub>f</sub>, d) = q<sub>err</sub>, δ(q<sub>err</sub>, d) = q<sub>err</sub>."),
        sp(6),

        p("Характеристики полученного автомата M = (Q, Σ, δ, q<sub>0</sub>, F):"),
        p("* <b>Q</b> = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>, q<sub>f</sub>, q<sub>err</sub>} — множество состояний;", "body_noindent"),
        p("* <b>Σ</b> = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9} — входной алфавит (далее обозначен символом d);", "body_noindent"),
        p("* <b>q<sub>0</sub></b> — начальное состояние;", "body_noindent"),
        p("* <b>F</b> = {q<sub>f</sub>} — множество допускающих состояний.", "body_noindent"),
        sp(6),

        p("<b>Таблица переходов конечного автомата:</b>", "body_noindent"),
        sp(4),
        make_dka_table(S),
        sp(6),

        p("<b>Проверка на детерминированность:</b>"),
        p("Автомат называется детерминированным (ДКА), если:"),
        p("1. В нём отсутствуют ε-переходы;"),
        p("2. Для любого состояния q  принадлежит  Q и любого входного символа d  принадлежит  Σ функция δ(q, d) однозначно "
          "определяет не более одного следующего состояния."),
        sp(4),
        p("В полученном автомате для каждого состояния и каждого символа d существует <b>ровно один</b> "
          "переход. Следовательно, автомат <b>уже является ДКА</b>. "
          "Выполнение алгоритма детерминизации (НДКА -&gt; ДКА методом подмножеств) не требуется."),
        sp(4),

        p("Диаграмма переходов ДКА:", "h2"),
        sp(2),
        p("-&gt; (q<sub>0</sub>) --[d]--&gt; (q<sub>1</sub>) --[d]--&gt; (q<sub>2</sub>) --[d]--&gt; "
          "(q<sub>3</sub>) --[d]--&gt; (q<sub>4</sub>) --[d]--&gt; ((q<sub>f</sub>)) --[d]--&gt; "
          "(q<sub>err</sub>) --[d]--&gt; (q<sub>err</sub>)", "formula"),
        sp(2),
        p("<i>Обозначения:</i> -&gt; — вход в начальное состояние; (( )) — допускающее состояние; "
          "[d] — переход по любой цифре d  принадлежит  {0..9}.", "body_noindent"),
        sp(6),

        p("<b>Примеры трассировки работы ДКА:</b>", "body_noindent"),
        sp(3),
        p("1) Вход «12345» (ровно 5 цифр):", "body_noindent"),
        p("q<sub>0</sub> --[1]--&gt; q<sub>1</sub> --[2]--&gt; q<sub>2</sub> --[3]--&gt; "
          "q<sub>3</sub> --[4]--&gt; q<sub>4</sub> --[5]--&gt; q<sub>f</sub>   "
          "<b>[Цепочка допущена: q<sub>f</sub>  принадлежит  F]</b>", "formula"),
        sp(3),
        p("2) Вход «1234» (4 цифры — неполная цепочка):", "body_noindent"),
        p("q<sub>0</sub> --[1]--&gt; q<sub>1</sub> --[2]--&gt; q<sub>2</sub> --[3]--&gt; "
          "q<sub>3</sub> --[4]--&gt; q<sub>4</sub>   "
          "<b>[Цепочка отклонена: q<sub>4</sub>  не принадлежит  F]</b>", "formula"),
        sp(3),
        p("3) Вход «123456» (6 цифр — избыточная длина):", "body_noindent"),
        p("q<sub>0</sub> --[1]--&gt; q<sub>1</sub> --[2]--&gt; q<sub>2</sub> --[3]--&gt; "
          "q<sub>3</sub> --[4]--&gt; q<sub>4</sub> --[5]--&gt; q<sub>f</sub> --[6]--&gt; q<sub>err</sub>   "
          "<b>[Цепочка отклонена: q<sub>err</sub>  не принадлежит  F]</b>", "formula"),
    ]

    # ── Пункт 3. Минимизация ДКА ──────────────────────────────────────────────
    story += [
        sp(5),
        p("3. Минимизация ДКА", "h1"),
        hr(),
        p("Процесс минимизации ДКА состоит из двух последовательных этапов: "
          "удаление недостижимых состояний и слияние эквивалентных (неразличимых) состояний."),
        sp(6),

        p("3.1. Алгоритм устранения недостижимых состояний", "h2"),
        p("Состояние q  принадлежит  Q называется <b>достижимым</b>, если существует хотя бы одно входное слово w  принадлежит  Σ*, "
          "такое что δ*(q<sub>0</sub>, w) = q. В противном случае состояние является недостижимым."),
        sp(4),
        p("Выполним алгоритм поиска достижимых состояний (BFS) из начального состояния q<sub>0</sub>:"),
        p("* Шаг 0: U<sub>0</sub> = {q<sub>0</sub>}", "formula"),
        p("* Шаг 1: U<sub>1</sub> = U<sub>0</sub>  U  δ(q<sub>0</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>}", "formula"),
        p("* Шаг 2: U<sub>2</sub> = U<sub>1</sub>  U  δ(q<sub>1</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>}", "formula"),
        p("* Шаг 3: U<sub>3</sub> = U<sub>2</sub>  U  δ(q<sub>2</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>}", "formula"),
        p("* Шаг 4: U<sub>4</sub> = U<sub>3</sub>  U  δ(q<sub>3</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>}", "formula"),
        p("* Шаг 5: U<sub>5</sub> = U<sub>4</sub>  U  δ(q<sub>4</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>, q<sub>f</sub>}", "formula"),
        p("* Шаг 6: U<sub>6</sub> = U<sub>5</sub>  U  δ(q<sub>f</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>, q<sub>f</sub>, q<sub>err</sub>}", "formula"),
        p("* Шаг 7: U<sub>7</sub> = U<sub>6</sub>  U  δ(q<sub>err</sub>, d) = U<sub>6</sub> (стабилизация).", "formula"),
        sp(4),
        p("<b>Результат:</b> множество достижимых состояний равно всему Q (все 7 состояний достижимы). "
          "Недостижимых состояний нет."),
        sp(4),

        p("3.2. Алгоритм минимизации методом таблицы различимости", "h2"),
        p("Два состояния p и q называются <b>различимыми</b>, если существует цепочка w  принадлежит  Σ*, "
          "которая переводит одно из них в допускающее состояние, а другое — в недопускающее."),
        sp(4),
        p("<b>Шаг 1 (базовое разбиение).</b> Любая пара состояний (p, q), где одно состояние принадлежит F, "
          "а второе не принадлежит F, очевидно различима пустой цепочкой ε (|ε| = 0)."),
        p("Поскольку F = {q<sub>f</sub>}, а множество нефинальных состояний Q \\ F = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>, q<sub>err</sub>}, "
          "все пары (q<sub>f</sub>, q<sub>i</sub>) для любого q<sub>i</sub> ≠ q<sub>f</sub> помечаются как различимые (символ <b>X</b>)."),
        sp(6),

        p("<b>Шаг 2 (итерационное распространение различимости).</b> "
          "Для каждой пары (p, q) проверяем: если для входного символа d пара (δ(p, d), δ(q, d)) уже помечена как различимая, "
          "то и пара (p, q) помечается как различимая."),
        sp(4),
        p("Проверка пар:"),
        p("* Пара (q<sub>4</sub>, q<sub>err</sub>): δ(q<sub>4</sub>, d) = q<sub>f</sub>, δ(q<sub>err</sub>, d) = q<sub>err</sub>. "
          "Пара (q<sub>f</sub>, q<sub>err</sub>) помечена на шаге 1 -&gt; пара (q<sub>4</sub>, q<sub>err</sub>) <b>различима (X)</b>.", "formula"),
        p("* Пара (q<sub>3</sub>, q<sub>4</sub>): δ(q<sub>3</sub>, d) = q<sub>4</sub>, δ(q<sub>4</sub>, d) = q<sub>f</sub>. "
          "Пара (q<sub>4</sub>, q<sub>f</sub>) помечена на шаге 1 -&gt; пара (q<sub>3</sub>, q<sub>4</sub>) <b>различима (X)</b>.", "formula"),
        p("* Аналогично по индукции цепочки переходов различают все пары (q<sub>i</sub>, q<sub>j</sub>) при i ≠ j, "
          "так как состояния q<sub>i</sub> и q<sub>j</sub> требуют разного количества цифр до попадания в q<sub>f</sub>.", "formula"),
        sp(6),

        p("<b>Таблица различимости состояний</b> (X — состояния различимы, пустота — диагональ):", "body_noindent"),
        sp(4),
        make_distinguish_table(S),
        sp(6),

        p("<b>Вывод по минимизации:</b>"),
        p("Все пары различных состояний автомата оказались различимыми. "
          "Следовательно, ни одна пара состояний не может быть эквивалентна или объединена. "
          "Построенный ДКА уже является <b>минимальным</b>."),
        sp(4),
        p("Минимальный автомат содержит <b>7 состояний</b>: q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, "
          "q<sub>3</sub>, q<sub>4</sub>, q<sub>f</sub>, q<sub>err</sub>."),
        sp(4),
        p("Этот результат строго согласуется с фундаментальной теоремой теории автоматов: "
          "для языка слов фиксированной длины n над алфавитом Σ размерность минимального ДКА "
          "составляет в точности n + 2 состояния (n состояний счётчика длины, 1 допускающее состояние "
          "и 1 состояние-ловушка для цепочек длины &gt; n)."),
    ]

    doc.build(story)
    
    # Если присутствует официальный титульный лист title_page.pdf — заменяем первую страницу
    title_pdf = os.path.join(os.path.dirname(output_path), "title_page.pdf")
    if os.path.exists(title_pdf):
        import pypdf
        tr = pypdf.PdfReader(title_pdf)
        br = pypdf.PdfReader(output_path)
        writer = pypdf.PdfWriter()
        writer.add_page(tr.pages[0])
        for page in br.pages[1:]:
            writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
        print(f"Титульный лист заменен из: {title_pdf}")

    print(f"PDF успешно создан: {output_path}")

if __name__ == "__main__":
    out = r"c:\Users\user\Documents\AutomataTheory\CourseWork\Part1.pdf"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build_pdf(out)
