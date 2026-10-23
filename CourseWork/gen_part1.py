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
    HRFlowable, PageBreak, Flowable, KeepTogether
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
        # Cambria используется только для математических знаков (∈, ∉, ∪, ⇒, ∀),
        # которых нет в Times New Roman
        "MathRu":         "cambria.ttc",
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
SYM_FONT    = "MathRu" if os.path.exists(os.path.join(FONT_DIR, "cambria.ttc")) else None
MATH_GLYPHS = "∈∉∪⇒∀⊆"

def fsym(text, size=13):
    """Оборачивает математические знаки в Cambria: в Times New Roman их нет.
    Кегль на 1 pt меньше основного, чтобы значки не выглядели крупнее текста."""
    if not SYM_FONT:
        return text
    for ch in MATH_GLYPHS:
        if ch in text:
            text = text.replace(ch, f'<font name="{SYM_FONT}" size="{size}">{ch}</font>')
    return text

def make_styles():
    styles = {}

    styles["title"] = ParagraphStyle(
        "title", fontName=BOLD_FONT, fontSize=14,
        alignment=TA_CENTER, spaceAfter=8, leading=18
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", fontName=BASE_FONT, fontSize=14,
        alignment=TA_CENTER, spaceAfter=4, leading=18
    )
    styles["h1"] = ParagraphStyle(
        "h1", fontName=BOLD_FONT, fontSize=14,
        alignment=TA_LEFT, spaceBefore=16, spaceAfter=8, leading=20
    )
    styles["h2"] = ParagraphStyle(
        "h2", fontName=BOLD_FONT, fontSize=14,
        alignment=TA_LEFT, spaceBefore=12, spaceAfter=6, leading=20
    )
    styles["h1"].keepWithNext = 1
    styles["h2"].keepWithNext = 1
    styles["body"] = ParagraphStyle(
        "body", fontName=BASE_FONT, fontSize=14,
        alignment=TA_JUSTIFY, spaceAfter=5, leading=19,
        firstLineIndent=18
    )
    styles["body_noindent"] = ParagraphStyle(
        "body_noindent", fontName=BASE_FONT, fontSize=14,
        alignment=TA_LEFT, spaceAfter=5, leading=19
    )
    styles["formula"] = ParagraphStyle(
        "formula", fontName=BASE_FONT, fontSize=14,
        alignment=TA_LEFT, spaceAfter=4, leading=19,
        leftIndent=24
    )
    styles["centered"] = ParagraphStyle(
        "centered", fontName=BASE_FONT, fontSize=14,
        alignment=TA_CENTER, spaceAfter=6, leading=18
    )
    styles["caption"] = ParagraphStyle(
        "caption", fontName=BASE_FONT, fontSize=14,
        alignment=TA_CENTER, spaceBefore=4, spaceAfter=10, leading=18
    )
    styles["tbl_cell"] = ParagraphStyle(
        "tbl_cell", fontName=BASE_FONT, fontSize=14,
        alignment=TA_CENTER, leading=17
    )
    styles["tbl_head"] = ParagraphStyle(
        "tbl_head", fontName=BOLD_FONT, fontSize=14,
        alignment=TA_CENTER, leading=17, textColor=colors.white
    )
    styles["rule_cell"] = ParagraphStyle(
        "rule_cell", fontName=BASE_FONT, fontSize=14,
        alignment=TA_LEFT, leading=17
    )
    styles["tbl_left"] = ParagraphStyle(
        "tbl_left", fontName=BASE_FONT, fontSize=14,
        alignment=TA_LEFT, leading=17
    )

    # Переносы по-русски (если установлен pyphen) — убирает «дыры» в выключке.
    # В ячейках таблиц переносы отключены: там они выглядят неряшливо.
    try:
        import pyphen  # noqa: F401
        for name, st in styles.items():
            if name.startswith("tbl_") or name == "rule_cell":
                continue
            st.hyphenationLang = "ru_RU"
            st.embeddedHyphenation = 1
    except ImportError:
        pass

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

    col_w = [2.4*cm] + [2.2*cm] * (n - 1)
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

def make_table(styles, header, rows, widths, aligns=None):
    """Универсальная таблица: тёмная шапка, чередующийся фон, сетка."""
    def tc(text, is_head=False, align="CENTER"):
        st = styles["tbl_head"] if is_head else (styles["tbl_left"] if align == "LEFT" else styles["tbl_cell"])
        return Paragraph(text, st)

    data = [[tc(h, True) for h in header]]
    for r in rows:
        data.append([tc(cell, False, "LEFT" if aligns and aligns[i] == "LEFT" else "CENTER")
                     for i, cell in enumerate(r)])

    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4057")),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF0FB")]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


class DFADiagram(Flowable):
    """Векторная диаграмма ДКА для ^\\d{5}$ — рисуется кодом, без картинок."""

    W = 16 * cm
    H = 5.6 * cm
    R = 0.66 * cm
    Y = 4.25 * cm

    def __init__(self):
        super().__init__()
        self.width = self.W
        self.height = self.H
        xs = [1.55 * cm + i * 2.62 * cm for i in range(6)]
        self.states = list(zip(["0", "1", "2", "3", "4", "f"], xs))

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def _head(self, x1, y1, x2, y2, size=0.16 * cm):
        """Линия со стрелкой на конце (x2, y2)."""
        c = self.canv
        dx, dy = x2 - x1, y2 - y1
        d = (dx * dx + dy * dy) ** 0.5 or 1.0
        ux, uy = dx / d, dy / d
        bx, by = x2 - ux * size, y2 - uy * size
        c.setLineWidth(0.8)
        c.line(x1, y1, bx, by)
        pth = c.beginPath()
        pth.moveTo(x2, y2)
        pth.lineTo(bx - uy * size * 0.40, by + ux * size * 0.40)
        pth.lineTo(bx + uy * size * 0.40, by - ux * size * 0.40)
        pth.close()
        c.drawPath(pth, stroke=0, fill=1)

    def _state(self, cx, cy, sub, final=False):
        c = self.canv
        c.setLineWidth(0.9)
        c.circle(cx, cy, self.R, stroke=1, fill=0)
        if final:
            c.circle(cx, cy, self.R - 0.10 * cm, stroke=1, fill=0)
        size, subsize = 9.5, 6.5
        c.setFont(BASE_FONT, size)
        w1 = c.stringWidth("q", BASE_FONT, size)
        c.setFont(BASE_FONT, subsize)
        w2 = c.stringWidth(sub, BASE_FONT, subsize)
        x = cx - (w1 + w2) / 2.0
        c.setFont(BASE_FONT, size)
        c.drawString(x, cy - size * 0.32, "q")
        c.setFont(BASE_FONT, subsize)
        c.drawString(x + w1, cy - size * 0.30, sub)

    def _label(self, x, y, text):
        self.canv.setFont(BASE_FONT, 6.6)
        self.canv.drawCentredString(x, y, text)

    def draw(self):
        c = self.canv
        R, Y = self.R, self.Y
        xs = [x for _, x in self.states]

        self._head(0.20 * cm, Y, xs[0] - R, Y)          # вход
        for i in range(5):                               # q0..qf
            x1, x2 = xs[i] + R, xs[i + 1] - R
            self._head(x1, Y, x2, Y)
            self._label((x1 + x2) / 2.0, Y + 0.10 * cm, "0..9")
        for sub, x in self.states:
            self._state(x, Y, sub, final=(sub == "f"))

        xe, ye = xs[5], 1.75 * cm                        # qf -> qerr
        self._head(xs[5], Y - R, xe, ye + R)
        c.setFont(BASE_FONT, 6.6)
        c.drawString(xe + 0.12 * cm, (Y + ye) / 2.0, "0..9")
        self._state(xe, ye, "err")

        ax, ay = xe - 0.20 * cm, ye - R * 0.97         # петля qerr
        bx, by = xe + 0.20 * cm, ye - R * 0.97
        c1x, c1y = xe - 0.40 * cm, ye - 1.30 * cm
        c2x, c2y = xe + 0.40 * cm, ye - 1.30 * cm
        pth = c.beginPath()
        pth.moveTo(ax, ay)
        pth.curveTo(c1x, c1y, c2x, c2y, bx, by)
        c.setLineWidth(0.8)
        c.drawPath(pth, stroke=1, fill=0)
        self._head(c2x, c2y, bx, by)                    # стрелка по касательной
        c.setFont(BASE_FONT, 6.6)
        c.drawString(xe + 0.52 * cm, ye - 1.10 * cm, "0..9")


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
        return Paragraph(fsym(text), S[style])

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
        p('<b>Паттерн:</b> <font name="CourRu" size="12">if (!Regex.Match(zipCodeTextBox.Text, @"^\\d{5}$").Success)</font>', "body_noindent"),
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
        p("   <b>A → Ba</b>   или   <b>A → a</b>,   где A, B ∈ V<sub>N</sub>, a ∈ V<sub>T</sub>.", "formula"),
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
        [Paragraph(f"<b>{lhs}</b>", S["tbl_cell"]), Paragraph(f"{lhs} → {rhs}", S["rule_cell"])]
        for lhs, rhs in rules
    ]
    rt = Table(rules_data, colWidths=[3.2*cm, 12.4*cm])
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
        p("Здесь запись вида «A → 0 | 1 | ... | 9» и «B → A0 | A1 | ... | A9» является компактной "
          "формой записи для десяти отдельных продукций: B → A0, B → A1, ..., B → A9."),
        sp(4),
        p("Семантика нетерминалов (накопление префикса распознанной длины):"),
        p("* <b>A</b> — порождает цепочку из ровно 1 цифры (начальный этап вывода);", "body_noindent"),
        p("* <b>B</b> — накапливает цепочку из ровно 2 цифр (B → Ad);", "body_noindent"),
        p("* <b>C</b> — накапливает цепочку из ровно 3 цифр (C → Bd);", "body_noindent"),
        p("* <b>D</b> — накапливает цепочку из ровно 4 цифр (D → Cd);", "body_noindent"),
        p("* <b>S</b> — целевой нетерминал: цепочка из ровно 5 цифр (S → Dd).", "body_noindent"),
        sp(6),
        p("<b>Пример цепочки вывода</b> для слова «12345» (вывод идёт от целевого символа S):"),
        sp(2),
        p("S ⇒ D5 ⇒ C45 ⇒ B345 ⇒ A2345 ⇒ 12345", "formula"),
        sp(6),
        p("Поскольку все правила имеют вид A → Ba или A → a, грамматика G<sub>L</sub> "
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
        p("1. Вводится новое начальное состояние q<sub>0</sub> (которое ∉ V<sub>N</sub>): начальное состояние автомата q<sub>0</sub>."),
        p("2. Каждому нетерминалу из V<sub>N</sub> сопоставляется состояние автомата:"),
        p("   A → q<sub>1</sub>,   B → q<sub>2</sub>,   C → q<sub>3</sub>,   D → q<sub>4</sub>,   S → q<sub>f</sub>", "formula"),
        p("3. Для каждого правила вида A → a (a ∈ V<sub>T</sub>) задаётся переход из начального состояния: δ(q<sub>0</sub>, a) = A (то есть δ(q<sub>0</sub>, d) = q<sub>1</sub>)."),
        p("4. Для каждого правила вида Y → Xa (X, Y ∈ V<sub>N</sub>, a ∈ V<sub>T</sub>) задаётся переход: δ(X, a) = Y:"),
        p("   δ(A, d) = B  ⇒  δ(q<sub>1</sub>, d) = q<sub>2</sub><br/>"
          "   δ(B, d) = C  ⇒  δ(q<sub>2</sub>, d) = q<sub>3</sub><br/>"
          "   δ(C, d) = D  ⇒  δ(q<sub>3</sub>, d) = q<sub>4</sub><br/>"
          "   δ(D, d) = S  ⇒  δ(q<sub>4</sub>, d) = q<sub>f</sub>", "formula"),
        p("5. Целевой нетерминал S становится допускающим состоянием автомата: F = {S} = {q<sub>f</sub>}."),
        p("6. Для обеспечения полной определённости функции переходов вводится состояние‑ловушка q<sub>err</sub>: δ(q<sub>f</sub>, d) = q<sub>err</sub>, δ(q<sub>err</sub>, d) = q<sub>err</sub>."),
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
        p("2. Для любого состояния q ∈ Q и любого входного символа d ∈ Σ функция δ(q, d) однозначно "
          "определяет не более одного следующего состояния."),
        sp(4),
        p("В полученном автомате для каждого состояния и каждого символа d существует <b>ровно один</b> "
          "переход. Следовательно, автомат <b>уже является ДКА</b>. Отдельное выполнение алгоритма "
          "детерминизации для него не требуется, однако ниже этот алгоритм применён формально — чтобы "
          "показать, что он приводит ровно к тому же автомату."),
        sp(4),

        KeepTogether([
            p("Диаграмма переходов ДКА", "h2"),
            sp(2),
            DFADiagram(),
            p("Рис. 1. Диаграмма переходов ДКА M: двойным кружком обозначено допускающее состояние "
              "q<sub>f</sub>, каждая дуга помечена любой цифрой d ∈ {0..9}.", "caption"),
        ]),
        sp(6),

        p("<b>Примеры трассировки работы ДКА:</b>", "body_noindent"),
        sp(3),
        p("1) Вход «12345» (ровно 5 цифр):", "body_noindent"),
        p("q<sub>0</sub> --[1]--&gt; q<sub>1</sub> --[2]--&gt; q<sub>2</sub> --[3]--&gt; "
          "q<sub>3</sub> --[4]--&gt; q<sub>4</sub> --[5]--&gt; q<sub>f</sub>   "
          "<b>[Цепочка допущена: q<sub>f</sub> ∈ F]</b>", "formula"),
        sp(3),
        p("2) Вход «1234» (4 цифры — неполная цепочка):", "body_noindent"),
        p("q<sub>0</sub> --[1]--&gt; q<sub>1</sub> --[2]--&gt; q<sub>2</sub> --[3]--&gt; "
          "q<sub>3</sub> --[4]--&gt; q<sub>4</sub>   "
          "<b>[Цепочка отклонена: q<sub>4</sub> ∉ F]</b>", "formula"),
        sp(3),
        p("3) Вход «123456» (6 цифр — избыточная длина):", "body_noindent"),
        p("q<sub>0</sub> --[1]--&gt; q<sub>1</sub> --[2]--&gt; q<sub>2</sub> --[3]--&gt; "
          "q<sub>3</sub> --[4]--&gt; q<sub>4</sub> --[5]--&gt; q<sub>f</sub> --[6]--&gt; q<sub>err</sub>   "
          "<b>[Цепочка отклонена: q<sub>err</sub> ∉ F]</b>", "formula"),
    ]

    # ── Пункт 2.3. НКА -> ДКА (метод подмножеств) ─────────────────────────────
    story += [
        sp(5),
        p("Преобразование НКА в ДКА (метод подмножеств)", "h2"),
        sp(2),
        p("Недетерминированный конечный автомат (НКА) отличается от ДКА тем, что по одному и тому же "
          "входному символу из состояния может быть несколько переходов — сразу в несколько состояний. "
          "НКА задаётся пятёркой M = (K, T, δ, H, S), где K — конечное множество состояний, T — входной "
          "алфавит, δ — отображение K × T во множество подмножеств K, H ⊆ K — множество начальных "
          "состояний, S ⊆ K — множество заключительных состояний. Запись δ(A, t) = "
          "{B<sub>1</sub>, B<sub>2</sub>, …, B<sub>n</sub>} означает, что из состояния A по символу t "
          "можно перейти в любое из состояний B<sub>i</sub>."),
        sp(4),
        p("Класс языков, допускаемых НКА, совпадает с классом языков, допускаемых ДКА, поэтому по любому "
          "НКА можно построить эквивалентный ему ДКА. Для этого применяется <b>метод подмножеств</b>:"),
        p("1. Состояниями ДКА M′ объявляются все подмножества множества K. Каждое состояние "
          "записывается в виде [A<sub>1</sub>A<sub>2</sub> … A<sub>n</sub>], где A<sub>i</sub> ∈ K."),
        p("2. Функция переходов: δ′([A<sub>1</sub> … A<sub>n</sub>], t) = [B<sub>1</sub> … B<sub>m</sub>], "
          "где [B<sub>1</sub> … B<sub>m</sub>] — объединение всех состояний, в которые ведут переходы "
          "δ(A<sub>i</sub>, t) для i = 1 … n."),
        p("3. Начальное состояние: если H = {H<sub>1</sub>, …, H<sub>k</sub>}, то "
          "H′ = [H<sub>1</sub> … H<sub>k</sub>]."),
        p("4. Заключительные состояния: все состояния вида [… S<sub>i</sub> …], содержащие хотя бы одно "
          "заключительное состояние S<sub>i</sub> ∈ S."),
        p("Замечание: состояния из K′, недостижимые из начального, можно не рассматривать."),
        sp(4),
        p("Применим алгоритм к автомату, построенному в п. 2. Таблицу заполняем построчно, начиная "
          "с начального состояния; каждое новое подмножество добавляем в конец таблицы:"),
        sp(4),
        make_table(S,
                   ["Состояние НКА", "δ′ по любой цифре d", "Обозначение в ДКА"],
                   [["[q<sub>0</sub>]",   "[q<sub>1</sub>]",   "q<sub>0</sub>"],
                    ["[q<sub>1</sub>]",   "[q<sub>2</sub>]",   "q<sub>1</sub>"],
                    ["[q<sub>2</sub>]",   "[q<sub>3</sub>]",   "q<sub>2</sub>"],
                    ["[q<sub>3</sub>]",   "[q<sub>4</sub>]",   "q<sub>3</sub>"],
                    ["[q<sub>4</sub>]",   "[q<sub>f</sub>]",   "q<sub>4</sub>"],
                    ["[q<sub>f</sub>]",   "[q<sub>err</sub>]", "q<sub>f</sub>"],
                    ["[q<sub>err</sub>]", "[q<sub>err</sub>]", "q<sub>err</sub>"]],
                   [5.2*cm, 6.2*cm, 4.6*cm]),
        sp(6),
        p("Все полученные подмножества оказались одноэлементными. Это объясняется тем, что в грамматике "
          "G<sub>L</sub> нет правил с совпадающими правыми частями, поэтому соответствующий ей НКА "
          "изначально детерминирован. Метод подмножеств в этом случае не меняет автомат, а только "
          "подтверждает результат п. 2: построенный ДКА M′ совпадает с M, число состояний остаётся "
          "равным 7."),
        sp(4),
        p("Если правые части правил совпадают (например, A → Bb и B → Bb, как в примере из методических "
          "указаний), то в таблице появляется состояние из нескольких элементов, например [BS]. Оно "
          "считается заключительным, так как содержит заключительное состояние S. В этом и состоит суть "
          "метода: несколько состояний НКА «склеиваются» в одно состояние ДКА, после чего разбор "
          "становится детерминированным."),
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
        p("Состояние q ∈ Q называется <b>достижимым</b>, если существует хотя бы одно входное слово w ∈ Σ*, "
          "такое что δ*(q<sub>0</sub>, w) = q. В противном случае состояние является недостижимым."),
        sp(4),
        p("Выполним алгоритм поиска достижимых состояний (BFS) из начального состояния q<sub>0</sub>:"),
        p("* Шаг 0: U<sub>0</sub> = {q<sub>0</sub>}", "formula"),
        p("* Шаг 1: U<sub>1</sub> = U<sub>0</sub> ∪ δ(q<sub>0</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>}", "formula"),
        p("* Шаг 2: U<sub>2</sub> = U<sub>1</sub> ∪ δ(q<sub>1</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>}", "formula"),
        p("* Шаг 3: U<sub>3</sub> = U<sub>2</sub> ∪ δ(q<sub>2</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>}", "formula"),
        p("* Шаг 4: U<sub>4</sub> = U<sub>3</sub> ∪ δ(q<sub>3</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>}", "formula"),
        p("* Шаг 5: U<sub>5</sub> = U<sub>4</sub> ∪ δ(q<sub>4</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>, q<sub>f</sub>}", "formula"),
        p("* Шаг 6: U<sub>6</sub> = U<sub>5</sub> ∪ δ(q<sub>f</sub>, d) = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>, q<sub>f</sub>, q<sub>err</sub>}", "formula"),
        p("* Шаг 7: U<sub>7</sub> = U<sub>6</sub> ∪ δ(q<sub>err</sub>, d) = U<sub>6</sub> (стабилизация).", "formula"),
        sp(4),
        p("<b>Результат:</b> множество достижимых состояний равно всему Q (все 7 состояний достижимы). "
          "Недостижимых состояний нет."),
        sp(4),

        p("3.2. Алгоритм минимизации методом таблицы различимости", "h2"),
        p("Два состояния p и q называются <b>различимыми</b>, если существует цепочка w ∈ Σ*, "
          "которая переводит одно из них в допускающее состояние, а другое — в недопускающее."),
        sp(4),
        p("<b>Шаг 1 (базовое разбиение).</b> Любая пара состояний (p, q), где p ∈ F, "
          "а q ∉ F, очевидно различима пустой цепочкой ε (|ε| = 0)."),
        p("Поскольку F = {q<sub>f</sub>}, а множество нефинальных состояний Q \\ F = {q<sub>0</sub>, q<sub>1</sub>, q<sub>2</sub>, q<sub>3</sub>, q<sub>4</sub>, q<sub>err</sub>}, "
          "все пары (q<sub>f</sub>, q<sub>i</sub>) для любого q<sub>i</sub> ≠ q<sub>f</sub> помечаются как различимые (символ <b>X</b>)."),
        sp(6),

        p("<b>Шаг 2 (итерационное распространение различимости).</b> "
          "Для каждой пары (p, q) проверяем: если для входного символа d пара (δ(p, d), δ(q, d)) уже помечена как различимая, "
          "то и пара (p, q) помечается как различимая."),
        sp(4),
        p("Проверка пар:"),
        p("* Пара (q<sub>4</sub>, q<sub>err</sub>): δ(q<sub>4</sub>, d) = q<sub>f</sub>, δ(q<sub>err</sub>, d) = q<sub>err</sub>. "
          "Пара (q<sub>f</sub>, q<sub>err</sub>) помечена на шаге 1 ⇒ пара (q<sub>4</sub>, q<sub>err</sub>) <b>различима (X)</b>.", "formula"),
        p("* Пара (q<sub>3</sub>, q<sub>4</sub>): δ(q<sub>3</sub>, d) = q<sub>4</sub>, δ(q<sub>4</sub>, d) = q<sub>f</sub>. "
          "Пара (q<sub>4</sub>, q<sub>f</sub>) помечена на шаге 1 ⇒ пара (q<sub>3</sub>, q<sub>4</sub>) <b>различима (X)</b>.", "formula"),
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
          "и 1 состояние‑ловушка для цепочек длины &gt; n)."),
    ]

    # ── Пункт 3.3. Мур и Хопкрофт ──────────────────────────────────────────────
    story += [
        sp(5),
        p("3.3. Алгоритм Мура и алгоритм Хопкрофта", "h2"),
        sp(2),
        p("Описанный в п. 3.2 метод таблицы различимости известен как <b>алгоритм Мура</b>. Он "
          "относится к алгоритмам последовательного уточнения разбиения: сначала все состояния делятся "
          "на допускающие и недопускающие, а затем на каждом шаге классы дробятся, если хотя бы для "
          "одного входного символа их состояния попадают в разные классы. Процесс повторяется до "
          "стабилизации разбиения; состояния, оставшиеся в одном классе, эквивалентны и сливаются. "
          "Трудоёмкость — O(|Σ|·n<super>2</super>), зато каждый шаг нагляден и легко проверяется "
          "вручную по таблице различимости."),
        sp(4),
        p("<b>Алгоритм Хопкрофта</b> решает ту же задачу и строит то же самое минимальное разбиение, "
          "но организует уточнение иначе: разбиение хранится как набор классов, а для расщепления "
          "используется очередь «расщепителей» — пар (класс, входной символ). Класс делится только "
          "тогда, когда этого требует очередной расщепитель, поэтому трудоёмкость снижается до "
          "O(|Σ|·n·log n). Выигрыш заметен на автоматах с сотнями и тысячами состояний."),
        sp(4),
        make_table(S,
                   ["Критерий", "Алгоритм Мура", "Алгоритм Хопкрофта"],
                   [["Идея", "последовательное уточнение разбиения, таблица различимости",
                     "разбиение с очередью расщепителей"],
                    ["Трудоёмкость", "O(|Σ|·n<super>2</super>)", "O(|Σ|·n·log n)"],
                    ["Проверка вручную", "простая: видна каждая пара состояний",
                     "труднее: нужно аккуратно вести очередь"],
                    ["Результат", "минимальный ДКА", "минимальный ДКА"]],
                   [4.2*cm, 5.6*cm, 6.2*cm], aligns=["LEFT", "LEFT", "LEFT"]),
        sp(6),
        p("<b>Почему выбран алгоритм Мура.</b> Автомат в данной работе имеет всего n = 7 состояний "
          "и один входной символ, поэтому оба алгоритма дают результат за считанные шаги, а "
          "асимптотический выигрыш Хопкрофта на таких значениях не проявляется. При этом таблица "
          "различимости позволяет предъявить проверяемое обоснование минимальности: непосредственно "
          "видно, что различима каждая пара состояний. Для автомата с сотнями состояний "
          "предпочтительнее был бы алгоритм Хопкрофта."),
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
