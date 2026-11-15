# -*- coding: utf-8 -*-
"""
Генерация Части 2 курсового проекта (Word, .docx).

Часть 2: контекстно-свободные грамматики — пункты 4-8 задания.
Вариант 13 (seed 5).
"""

import os
import re

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = "Times New Roman"
MONO = "Courier New"

# ---------------------------------------------------------------------------
#  Служебные функции оформления
# ---------------------------------------------------------------------------

TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|_\{[^}]*\}|\^\{[^}]*\})")


def add_rich(par, text, size=14, bold=False, italic=False, font=FONT):
    """Добавляет текст с мини-разметкой:
       **жирный**, `моноширинный`, _{нижний индекс}, ^{верхний индекс}."""
    for chunk in TOKEN.split(text):
        if not chunk:
            continue
        run = par.add_run()
        run.font.name = font
        run.font.size = Pt(size)
        run.bold = bold
        run.italic = italic
        if chunk.startswith("**") and chunk.endswith("**"):
            run.text = chunk[2:-2]
            run.bold = True
        elif chunk.startswith("`") and chunk.endswith("`"):
            run.text = chunk[1:-1]
            run.font.name = MONO
            run.font.size = Pt(size - 4)
        elif chunk.startswith("_{") and chunk.endswith("}"):
            run.text = chunk[2:-1]
            run.font.subscript = True
        elif chunk.startswith("^{") and chunk.endswith("}"):
            run.text = chunk[2:-1]
            run.font.superscript = True
        else:
            run.text = chunk
        # кириллица в rFonts
        rpr = run._element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.append(rf)
        rf.set(qn("w:ascii"), run.font.name)
        rf.set(qn("w:hAnsi"), run.font.name)
        rf.set(qn("w:cs"), run.font.name)


def repeat_header(row):
    """Повторять строку заголовка таблицы на каждой новой странице."""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def no_split(row):
    """Запретить разрыв строки таблицы между страницами."""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    trPr.append(el)


def build_grammar_graph(png_path):
    """Рисует граф грамматики G и сохраняет его в PNG.

    Граф строится по определению из лекции: вершина — символ грамматики,
    дуга X -> Y проводится для каждого вхождения Y в правую часть правила
    с левой частью X. Отдельная вершина ε соответствует правилу H -> ε.

    Рисунок делается кодом (reportlab), а не вставляется готовой картинкой,
    чтобы его можно было перестроить одной командой. Промежуточный PDF
    рендерится в PNG через pypdfium2 (как и проверка страниц отчёта).
    """
    import math
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import cm
    from reportlab.lib import colors as rl_colors

    pdfmetrics.registerFont(TTFont("GTime", r"C:\Windows\Fonts\times.ttf"))
    pdfmetrics.registerFont(TTFont("GTime-I", r"C:\Windows\Fonts\timesi.ttf"))

    W, H = 16.5 * cm, 12.2 * cm
    os.makedirs(os.path.dirname(os.path.abspath(png_path)), exist_ok=True)
    pdf_path = os.path.splitext(png_path)[0] + ".pdf"

    # --- расположение вершин (x, y в см, тип) -------------------------------
    nodes = {
        "S": (2.3, 9.7, "nt"), "A": (5.5, 9.7, "nt"), "B": (5.5, 7.7, "nt"),
        "C": (8.5, 9.7, "nt"), "D": (11.3, 9.7, "nt"), "O": (13.3, 9.7, "nt"),
        "H": (2.3, 7.7, "nt"), "M": (12.9, 5.5, "nt"), "E": (11.7, 11.15, "nt"),
        "F": (13.3, 11.15, "nt"), "T": (9.2, 7.7, "nt"),
        "a": (2.3, 11.15, "t"), "b": (5.5, 11.15, "t"), "c": (5.5, 6.45, "t"),
        "d": (8.5, 11.15, "t"), "f": (14.9, 9.7, "t"), "j": (7.0, 6.9, "t"),
        "h": (10.2, 10.35, "t"),
        "m": (10.9, 7.7, "t"), "v": (14.3, 5.5, "t"),
        "eps": (2.3, 6.55, "eps"),
    }
    useless = {"E", "F", "M", "h", "v"}
    edges = [("S", "a"), ("S", "A"), ("S", "B"), ("S", "H"),
             ("A", "b"), ("A", "C"),
             ("B", "c"), ("B", "A"), ("B", "j"), ("B", "T"),
             ("C", "d"), ("C", "D"),
             ("D", "O"), ("O", "f"), ("H", "eps"),
             ("M", "v"), ("E", "h"), ("E", "F"), ("E", "d"),
             ("T", "m")]

    c = rl_canvas.Canvas(pdf_path, pagesize=(W, H))
    c.setLineJoin(1)

    def rad(name):
        """Радиус, на который нужно укоротить стрелку, чтобы она не входила в вершину."""
        return 0.38 if nodes[name][2] == "nt" else 0.34

    def head(x, y, ux, uy, color, size=0.14):
        """Треугольный наконечник стрелки в точке (x, y), направление (ux, uy)."""
        px, py = -uy, ux
        p1 = (x - size * ux + size * 0.45 * px, y - size * uy + size * 0.45 * py)
        p2 = (x - size * ux - size * 0.45 * px, y - size * uy - size * 0.45 * py)
        c.setFillColor(rl_colors.HexColor(color))
        p = c.beginPath()
        p.moveTo(x * cm, y * cm)
        p.lineTo(p1[0] * cm, p1[1] * cm)
        p.lineTo(p2[0] * cm, p2[1] * cm)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

    def style(color, width, dashed):
        c.setStrokeColor(rl_colors.HexColor(color))
        c.setLineWidth(width)
        if dashed:
            c.setDash([2.4, 1.8])
        else:
            c.setDash()

    def arrow(a, b):
        """Прямая стрелка a -> b с учётом стиля (полезный/бесполезный символ)."""
        x1, y1 = nodes[a][0], nodes[a][1]
        x2, y2 = nodes[b][0], nodes[b][1]
        d = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / d, (y2 - y1) / d
        bad = a in useless or b in useless
        color = "#A6A6A6" if bad else "#1F4E79"
        style(color, 0.9 if bad else 1.1, bad)
        sx, sy = x1 + ux * rad(a), y1 + uy * rad(a)
        ex, ey = x2 - ux * rad(b), y2 - uy * rad(b)
        c.line(sx * cm, sy * cm, ex * cm, ey * cm)
        head(ex, ey, ux, uy, color)

    def curve(points, bad=False):
        """Кривая стрелка по четырём точкам (начало, 2 контрольные, конец)."""
        color = "#A6A6A6" if bad else "#1F4E79"
        style(color, 0.9 if bad else 1.1, bad)
        p = c.beginPath()
        p.moveTo(points[0][0] * cm, points[0][1] * cm)
        p.curveTo(points[1][0] * cm, points[1][1] * cm,
                  points[2][0] * cm, points[2][1] * cm,
                  points[3][0] * cm, points[3][1] * cm)
        c.drawPath(p, stroke=1, fill=0)
        ex, ey = points[3]
        dx, dy = ex - points[2][0], ey - points[2][1]
        d = math.hypot(dx, dy)
        head(ex, ey, dx / d, dy / d, color)

    # --- рёбра ---------------------------------------------------------------
    for src, dst in edges:
        if (src, dst) == ("B", "A"):
            # обратная дуга B -> A: выпуклостью вправо, чтобы не сливалась с S -> B
            curve([(5.66, 8.0), (6.62, 8.15), (6.62, 9.25), (5.66, 9.4)])
        else:
            arrow(src, dst)

    # петля T -> T (левая рекурсия T -> Tm)
    curve([(8.95, 8.0), (8.55, 8.95), (9.85, 8.95), (9.45, 8.0)])

    # --- вершины -------------------------------------------------------------
    def draw_node(name):
        x, y, kind = nodes[name]
        bad = name in useless
        if kind == "nt":
            fill, stroke, text = ("#F7F7F7", "#A6A6A6", "#7F7F7F") if bad else \
                                 ("#E8EFF9", "#1F4E79", "#1F4E79")
            c.setFillColor(rl_colors.HexColor(fill))
            c.setStrokeColor(rl_colors.HexColor(stroke))
            c.setLineWidth(1.0)
            c.setDash([2.4, 1.8] if bad else [])
            c.roundRect((x - 0.43) * cm, (y - 0.31) * cm, 0.86 * cm, 0.62 * cm,
                        0.12 * cm, stroke=1, fill=1)
            c.setDash()
            c.setFillColor(rl_colors.HexColor(text))
            c.setFont("GTime", 12)
            c.drawCentredString(x * cm, (y - 0.13) * cm, name)
            return
        r = 0.34 if kind == "t" else 0.30
        if kind == "eps":
            c.setFillColor(rl_colors.white)
            c.setStrokeColor(rl_colors.HexColor("#1F4E79"))
            c.setLineWidth(1.0)
            c.setDash([1.8, 1.5])
        elif bad:
            c.setFillColor(rl_colors.HexColor("#F7F7F7"))
            c.setStrokeColor(rl_colors.HexColor("#A6A6A6"))
            c.setLineWidth(1.0)
            c.setDash([2.4, 1.8])
        else:
            c.setFillColor(rl_colors.HexColor("#F2F2F2"))
            c.setStrokeColor(rl_colors.HexColor("#404040"))
            c.setLineWidth(1.0)
            c.setDash()
        c.circle(x * cm, y * cm, r * cm, stroke=1, fill=1)
        c.setDash()
        c.setFillColor(rl_colors.HexColor("#7F7F7F" if bad else "#000000"))
        c.setFont("GTime-I", 12)
        c.drawCentredString(x * cm, (y - 0.13) * cm,
                            "ε" if kind == "eps" else name)

    for name in nodes:
        draw_node(name)

    c.showPage()
    c.save()

    import pypdfium2 as pdfium
    from PIL import Image, ImageChops

    page = pdfium.PdfDocument(pdf_path)[0]
    img = page.render(scale=6).to_pil().convert("RGB")
    w, h = img.size
    box = ImageChops.difference(img, Image.new("RGB", (w, h), "white")).getbbox()
    if box:                                  # обрезаем белые поля вокруг графа
        pad = 20
        img = img.crop((max(0, box[0] - pad), max(0, box[1] - pad),
                        min(w, box[2] + pad), min(h, box[3] + pad)))
    img.save(png_path)
    return png_path


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:color"), "auto")
    el.set(qn("w:fill"), color)
    tcPr.append(el)


def setup(doc):
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(14)
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), FONT)

    pf = st.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    pf.first_line_indent = Cm(1.25)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for s in doc.sections:
        s.left_margin = Cm(3)
        s.right_margin = Cm(1.5)
        s.top_margin = Cm(2)
        s.bottom_margin = Cm(2)


class Doc:
    def __init__(self):
        self.doc = Document()
        setup(self.doc)

    # ------------------------------------------------------------------ текст
    def p(self, text="", align="just", indent=True, bold=False, italic=False,
          size=14, space_before=0, space_after=0):
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.line_spacing = 1.5
        pf.space_before = Pt(space_before)
        pf.space_after = Pt(space_after)
        pf.first_line_indent = Cm(1.25) if indent else Cm(0)
        pf.alignment = {"just": WD_ALIGN_PARAGRAPH.JUSTIFY,
                        "left": WD_ALIGN_PARAGRAPH.LEFT,
                        "center": WD_ALIGN_PARAGRAPH.CENTER,
                        "right": WD_ALIGN_PARAGRAPH.RIGHT}[align]
        add_rich(par, text, size=size, bold=bold, italic=italic)
        return par

    def h1(self, text):
        par = self.p(text, align="left", indent=False, bold=True,
                     space_before=14, space_after=6)
        par.paragraph_format.keep_with_next = True
        return par

    def h2(self, text):
        par = self.p(text, align="left", indent=False, bold=True,
                     space_before=10, space_after=4)
        par.paragraph_format.keep_with_next = True
        return par

    def formula(self, text):
        """Строка формулы: без абзацного отступа, с отступом слева."""
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.line_spacing = 1.5
        pf.left_indent = Cm(1.25)
        pf.first_line_indent = Cm(0)
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_rich(par, text)
        return par

    def note(self, text):
        """Врезка «Замечание» курсивом."""
        return self.p(text, align="just", indent=True, italic=True)

    def code(self, lines, size=10):
        for ln in lines:
            par = self.doc.add_paragraph()
            pf = par.paragraph_format
            pf.line_spacing = 1.0
            pf.space_before = Pt(0)
            pf.space_after = Pt(0)
            pf.left_indent = Cm(0.5)
            pf.first_line_indent = Cm(0)
            run = par.add_run(ln if ln else " ")
            run.font.name = MONO
            run.font.size = Pt(size)
        self.p("", indent=False, space_after=6)

    def table(self, headers, rows, widths=None, font_size=12,
              align="center", header_fill="DCE6F1"):
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = t.rows[0].cells
        repeat_header(t.rows[0])
        for i, h in enumerate(headers):
            hdr[i].text = ""
            par = hdr[i].paragraphs[0]
            par.paragraph_format.first_line_indent = Cm(0)
            par.paragraph_format.line_spacing = 1.0
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_rich(par, h, size=font_size, bold=True)
            shade(hdr[i], header_fill)
        for row in rows:
            new_row = t.add_row()
            no_split(new_row)
            cells = new_row.cells
            for i, val in enumerate(row):
                cells[i].text = ""
                par = cells[i].paragraphs[0]
                par.paragraph_format.first_line_indent = Cm(0)
                par.paragraph_format.line_spacing = 1.0
                par.alignment = {"center": WD_ALIGN_PARAGRAPH.CENTER,
                                 "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
                add_rich(par, str(val), size=font_size)
        if widths:
            for r in t.rows:
                for i, w in enumerate(widths):
                    r.cells[i].width = Cm(w)
        # Короткие таблицы не разрываем; длинные — можно, но заголовок
        # повторяется на новой странице (repeat_header), а первая строка
        # данных остаётся вместе с заголовком.
        keep_all = len(rows) <= 22
        for idx, r in enumerate(t.rows):
            if not keep_all and idx > 1:
                continue
            for c in r.cells:
                for par in c.paragraphs:
                    par.paragraph_format.keep_with_next = True
        gap = self.doc.add_paragraph()
        gp = gap.paragraph_format
        gp.line_spacing = 1.0
        gp.space_before = Pt(0)
        gp.space_after = Pt(0)
        gp.first_line_indent = Cm(0)
        gap.add_run().font.size = Pt(6)
        return t

    def caption(self, text):
        return self.p(text, align="center", indent=False, size=12,
                      space_before=2, space_after=8)

    def figure(self, path, width_cm=15.6, caption=None):
        """Вставить рисунок по центру страницы (с подписью под ним)."""
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.first_line_indent = Cm(0)
        pf.line_spacing = 1.0
        pf.space_before = Pt(6)
        pf.space_after = Pt(2)
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.keep_with_next = True
        par.add_run().add_picture(path, width=Cm(width_cm))
        if caption:
            self.caption(caption)

    def page_break(self):
        """Разрыв страницы в конце последнего абзаца (без пустой страницы)."""
        self.doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)

    def save(self, path):
        self.doc.save(path)


# ---------------------------------------------------------------------------
#  Титульный лист
# ---------------------------------------------------------------------------

def title_page(d):
    for _ in range(1):
        d.p("", indent=False)
    d.p("Московский авиационный институт", align="center", indent=False, bold=True)
    d.p("(национальный исследовательский университет)", align="center", indent=False)
    d.p("", indent=False)
    d.p("Институт «Компьютерные науки и прикладная математика»",
        align="center", indent=False)
    for _ in range(4):
        d.p("", indent=False)
    d.p("Курсовой проект", align="center", indent=False, bold=True)
    d.p("«Теория автоматов и формальные языки»", align="center", indent=False)
    d.p("VII семестр", align="center", indent=False)
    d.p("", indent=False)
    d.p("Часть 2", align="center", indent=False, bold=True)
    for _ in range(4):
        d.p("", indent=False)
    d.p("Студент: Колесник Д.С.", align="left", indent=False)
    d.p("Группа: М8О-413Б-23", align="left", indent=False)
    d.p("Руководитель: к.т.н., доцент ОЦ 8 Киндинова В.В.",
        align="left", indent=False)
    d.p("", indent=False)
    d.p("Оценка:", align="left", indent=False)
    d.p("Дата:", align="left", indent=False)
    for _ in range(3):
        d.p("", indent=False)
    d.p("Москва — 2026", align="center", indent=False)
    d.page_break()


# ---------------------------------------------------------------------------
#  Содержательная часть
# ---------------------------------------------------------------------------

def intro(d):
    d.h1("Часть 2. Контекстно-свободные грамматики и магазинный автомат")
    d.p("Настоящая часть курсового проекта соответствует пунктам 4–8 задания и посвящена "
        "преобразованию контекстно-свободной (КС) грамматики и построению "
        "магазинного автомата (МП-автомата):")
    d.formula("4) устранить из КС-грамматики бесполезные символы и ε-правила;")
    d.formula("5) устранить из КС-грамматики цепные правила и левую рекурсию;")
    d.formula("6) определить форму КС-грамматики и сделать её приведение;")
    d.formula("7) спроектировать МП-автомат для приведённой КС-грамматики;")
    d.formula("8) реализовать МП-автомат для приведённой КС-грамматики.")
    d.p("Все преобразования выполняются по варианту задания (seed 5, вариант № 13) и "
        "сопровождаются проверкой: результат каждого шага подтверждается программой "
        "`CourseWork/part2.py`, реализующей соответствующие алгоритмы.")


def section1(d):
    d.h1("1. Исходная контекстно-свободная грамматика")
    d.p("Вариант задания задаёт грамматику")
    d.formula("G = (V_{T}, V_{N}, P, S),")
    d.formula("V_{T} = {a, b, c, d, f, ε, v, h, m, j},")
    d.formula("V_{N} = {S, A, B, C, D, O, H, M, E, F, T},")
    d.formula("S — начальный (целевой) символ грамматики.")
    d.p("Множество правил вывода P:")
    d.formula("A → bC      B → cA      C → dD      D → O")
    d.formula("O → f       S → aABH    H → ε")
    d.formula("M → v       E → hFd     B → jT")
    d.formula("T → Tm      T → m")

    d.h2("1.1. Замечание о символе ε в списке терминалов")
    d.p("В выданном варианте символ ε указан в списке терминальных символов. Это "
        "недочёт генератора вариантов: по определению грамматики G = (V_{T}, V_{N}, P, S) "
        "терминальный алфавит V_{T} состоит из символов, которые не заменяются ни одним "
        "правилом вывода, а пустая цепочка ε не является символом алфавита и не может быть "
        "терминалом.")
    d.p("Фактически ε в задании обозначает пустую правую часть правила H → ε, то есть "
        "правило с пустой правой частью (ε-правило). Поэтому далее полагаем")
    d.formula("V_{T} = {a, b, c, d, f, v, h, m, j},   ε ∉ V_{T},")
    d.p("а запись H → ε трактуется как правило с пустой правой частью и отражает тот факт, "
        "что нетерминал H выводит пустую цепочку.")

    d.h2("1.2. Свойства исходной грамматики")
    d.p("Каждое правило имеет вид A → β, где A ∈ V_{N}, β ∈ (V_{T} ∪ V_{N})*. Следовательно, "
        "грамматика G является контекстно-свободной (тип 2 по классификации Хомского). "
        "Наличие правила H → ε означает, что G является укорачивающей (допускает правила "
        "с пустой правой частью) и не является неукорачивающей.")
    d.p("Терминальные символы: a, b, c, d, f, v, h, m, j. Нетерминальные символы: "
        "S, A, B, C, D, O, H, M, E, F, T. Как видно из правил, символ F не имеет ни одного "
        "правила в левой части, а нетерминалы M и E не используются ни в одном правиле, "
        "ведущем из S — это первый признак того, что грамматика содержит бесполезные символы "
        "(п. 4).")
    d.p("Заметим также, что правило T → Tm является правилом с левой рекурсией, а правило "
        "D → O — цепным правилом. Эти особенности устраняются в п. 5.")

    d.h2("1.3. Пример вывода в исходной грамматике")
    d.p("Покажем, что цепочка abdfcbdf принадлежит языку L(G). Вывод (заменяемый символ "
        "подчёркивается порядком записи, вывод не является левосторонним):")
    d.formula("S ⇒ aABH ⇒ abCBH ⇒ abdDBH ⇒ abdOBH ⇒ abdfBH ⇒")
    d.formula("⇒ abdfcAH ⇒ abdfcbCH ⇒ abdfcbdDH ⇒")
    d.formula("⇒ abdfcbdOH ⇒ abdfcbdfH ⇒ abdfcbdf.")
    d.p("Аналогично выводится цепочка abdfjm:")
    d.formula("S ⇒ aABH ⇒ abCBH ⇒ abdDBH ⇒ abdOBH ⇒ abdfBH ⇒")
    d.formula("⇒ abdfjTH ⇒ abdfjmH ⇒ abdfjm.")
    d.p("Таким образом, язык грамматики содержит, как минимум, цепочки abdfcbdf и abdfjm. "
        "Полное описание языка будет получено после приведения грамматики (п. 4).")


def section2(d):
    d.h1("2. Устранение бесполезных символов и ε-правил (пункт 4)")

    d.h2("2.1. Теоретические сведения")
    d.p("Определение. Символ x ∈ V_{T} ∪ V_{N} называется недостижимым в грамматике "
        "G = (V_{T}, V_{N}, P, S), если он не появляется ни в одной сентенциальной форме "
        "этой грамматики, то есть ни один вывод из S его не порождает.")
    d.p("Определение. Нетерминал A ∈ V_{N} называется бесплодным, если множество цепочек, "
        "выводимых из него, пусто: {α ∈ V_{T}* | A ⇒* α} = ∅. Бесплодными могут быть только "
        "нетерминалы, поскольку терминал сам является цепочкой.")
    d.p("Недостижимые и бесплодные символы называют бесполезными: они не участвуют в "
        "порождении цепочек языка и могут быть удалены без изменения языка.")
    d.p("Определение. КС-грамматика называется приведённой, если в ней нет недостижимых и "
        "бесплодных символов.")

    d.p("Для нахождения бесполезных символов удобен граф КС-грамматики: каждой вершине "
        "сопоставлен символ из V_{T} ∪ V_{N}, и вершина X соединяется дугой с вершиной Y, "
        "если в грамматике есть правило X → αYβ. Порядок действий в алгоритме приведения "
        "строго фиксирован:")
    d.formula("1) обнаружить и удалить все бесплодные нетерминалы;")
    d.formula("2) обнаружить и удалить все недостижимые символы;")
    d.formula("3) удалить правила, содержащие удалённые символы.")
    graph_png = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "_txt", "grammar_graph.png")
    d.figure(build_grammar_graph(graph_png), width_cm=15.6,
             caption="Рисунок 1. Граф грамматики G. Серым пунктиром показаны бесполезные "
                     "символы: E и F — бесплодные, M, v и h — недостижимые. "
                     "Вершина ε соответствует правилу H → ε.")
    d.note("Замечание. Если поменять шаги 1 и 2 местами, результат не всегда будет "
           "приведённой грамматикой: удаление недостижимых символов может «спрятать» "
           "бесплодные, которые после удаления недостижимых станут достижимыми. Если "
           "начальный символ S окажется бесплодным, удаляются содержащие его правила, а сам "
           "символ S остаётся в V_{N}, так как множество нетерминалов обязано содержать "
           "начальный символ.")

    d.p("Алгоритм 1 (удаление бесплодных символов). 1. Отметить все терминальные вершины "
        "графа. 2. Если в P есть правило A → α, где α состоит только из уже отмеченных "
        "символов, а вершина A не отмечена, — отметить A; повторять шаг 2, пока возможно. "
        "3. Удалить из грамматики неотмеченные символы и правила, их содержащие.")
    d.p("Алгоритм 2 (удаление недостижимых символов). 1. Отметить все вершины, в которые "
        "существует путь из вершины S. 2. Удалить неотмеченные символы и правила, их "
        "содержащие.")

    d.h2("2.2. Применение к грамматике G")
    d.p("Шаг 1 (алгоритм 1). В графе на рисунке 1 отмечаем терминальные вершины "
        "a, b, c, d, f, v, h, m, j. Затем "
        "последовательно отмечаются нетерминалы, у которых все символы правой части уже "
        "отмечены: O (правило O → f), D (D → O), C (C → dD), A (A → bC), H (H → ε — правая "
        "часть пуста, поэтому условие выполнено), T (T → m), B (B → cA и B → jT), "
        "S (S → aABH), M (M → v). Не отмеченными остались F (у него нет ни одного правила) "
        "и E (правило E → hFd содержит F). Следовательно, бесплодными являются нетерминалы "
        "E и F; правило E → hFd удаляется.")
    d.p("Шаг 2 (алгоритм 2). Из вершины S достижимы S, A, B, C, D, H, O, T и терминалы "
        "a, b, c, d, f, m, j. Недостижимыми оказались нетерминал M (правило M → v) и "
        "терминал h, который встречался только в удалённом правиле E → hFd.")
    d.p("Результат шагов 1–2 удобно представить таблицей:")
    d.table(
        ["Символ", "Продуктивен", "Достижим из S", "Результат"],
        [["S, A, B, C, D, O, H, T", "да", "да", "остаются"],
         ["E", "нет", "нет", "удалён (правило E → hFd)"],
         ["F", "нет", "нет", "удалён"],
         ["M", "да", "нет", "удалён (правило M → v)"],
         ["a, b, c, d, f, m, j", "—", "да", "остаются"],
         ["v", "—", "нет", "удалён вместе с M → v"],
         ["h", "—", "нет", "удалён вместе с E → hFd"]],
        widths=[5.0, 2.6, 2.8, 6.0], align="left")
    d.caption("Таблица 1. Результат удаления бесполезных символов")
    d.p("Получена эквивалентная грамматика G_{1} (L(G_{1}) = L(G)):")
    d.formula("G_{1} = ({a, b, c, d, f, m, j}, {S, A, B, C, D, O, H, T}, P_{1}, S),")
    d.formula("P_{1}:  S → aABH    A → bC     B → cA | jT    C → dD")
    d.formula("       D → O         O → f      H → ε           T → Tm | m")
    d.p("В G_{1} все символы продуктивны и достижимы, то есть G_{1} является приведённой "
        "грамматикой; ε-правило H → ε в ней пока сохраняется.")

    d.h2("2.3. Устранение ε-правил: алгоритм")
    d.p("Многие алгоритмы разбора (например, построение автомата, который разбирает цепочку "
        "без возвратов) требуют, чтобы грамматика была неукорачивающей, то есть не содержала "
        "правил с пустой правой частью. Для любой КС-грамматики существует почти "
        "эквивалентная неукорачивающая грамматика: языки отличаются не более чем на пустую "
        "цепочку.")
    d.p("Алгоритм устранения ε-правил:")
    d.formula("1) построить множество X = {A ∈ V_{N} | A ⇒* ε};")
    d.formula("2) удалить из P все правила с пустой правой частью;")
    d.formula("3) если S ∈ X, ввести новый начальный символ S′ и правила S′ → S | ε;")
    d.formula("4) каждое правило B → α_{1}Aα_{2} ... α_{n}Aα_{n+1}, где A ∈ X, заменить")
    d.formula("   всеми 2^{n} правилами, соответствующими всем комбинациям вхождений A;")
    d.formula("5) удалить бесполезные символы и правила, их содержащие.")
    d.p("В методических материалах (алгоритм 4) этот же приём называется методом «устранения "
        "перегородок»: ε-порождающие нетерминалы в правой части считаются перегородками, и "
        "новая грамматика получается вычёркиванием любой их комбинации.")
    d.p("Если S ∉ X, шаг 3 не нужен и язык сохраняется полностью: L(G′) = L(G). Если же из S "
        "выводится ε, то после удаления ε-правил язык теряет пустую цепочку — в материалах "
        "результат алгоритма 4 сформулирован именно так: L(G′) = L(G) \\ {ε}. Новый начальный "
        "символ S′ из шага 3 возвращает ε в язык, поэтому грамматика становится эквивалентной "
        "исходной, а не только «почти эквивалентной».")
    d.note("Замечание. Шаг 4 необходим потому, что если нетерминал A выводит ε, то его "
           "вхождения в правых частях можно «вычеркнуть»: цепочки, где A порождает ε, "
           "должны остаться выводимыми. Если все α_{i} пусты, правило B → ε не включается "
           "в новую грамматику.")

    d.h2("2.4. Применение к грамматике G₁")
    d.p("Шаг 1. Единственное правило с пустой правой частью — H → ε, поэтому X = {H}. "
        "Заметим, что S ∉ X: из S выводимы только цепочки, начинающиеся с терминала a, "
        "поэтому пустая цепочка из S не выводится и новый начальный символ не требуется.")
    d.p("Шаг 2. Удаляем правило H → ε.")
    d.p("Шаг 4. В грамматике G_{1} имеется одно правило с вхождением H: S → aABH. "
        "Вычёркивание H даёт два правила: S → aABH и S → aAB.")
    d.p("Шаг 5. После удаления ε-правила нетерминал H не имеет ни одного правила, то есть "
        "стал бесплодным. Удаляем H и правило S → aABH. Получаем грамматику G_{2}:")
    d.formula("G_{2} = ({a, b, c, d, f, m, j}, {S, A, B, C, D, O, T}, P_{2}, S),")
    d.formula("P_{2}:  S → aAB     A → bC     B → cA | jT")
    d.formula("       C → dD      D → O      O → f      T → Tm | m")
    d.p("Проверка эквивалентности. Пустая цепочка не принадлежит языку исходной грамматики "
        "(любая цепочка, выводимая из S, начинается с терминала a), поэтому удаление "
        "ε-правила не изменило язык: L(G_{2}) = L(G_{1}) = L(G). В G_{2} нет правил с пустой "
        "правой частью, следовательно, G_{2} — неукорачивающая грамматика.")

    d.h2("2.5. Язык грамматики")
    d.p("Из правил G_{2} видно, что нетерминал A выводит единственную цепочку bdf:")
    d.formula("A ⇒ bC ⇒ bdD ⇒ bdO ⇒ bdf,")
    d.p("а нетерминал B — либо cA (то есть cbdf), либо jT (то есть jm^{n}, n ≥ 1). Поэтому")
    d.formula("L(G) = {abdfcbdf} ∪ {abdf j m^{n} | n ≥ 1}.")
    d.p("Язык содержит одну «длинную» цепочку abdfcbdf и бесконечное семейство цепочек "
        "abdfjm, abdfjmm, abdfjmmm, ... Именно эта структура языка определяет вид "
        "МП-автомата, построенного в п. 7.")


def section3(d):
    d.h1("3. Устранение цепных правил и левой рекурсии (пункт 5)")

    d.h2("3.1. Цепные правила: теория")
    d.p("Определение. Правило вида A → B, где A, B ∈ V_{N}, называется цепным (унарным). "
        "Цепное правило не порождает ни одного терминального символа и лишь «переименовывает» "
        "нетерминал, поэтому от цепных правил можно избавиться без изменения языка.")
    d.p("Определение. Упорядоченная пара (A, B) называется цепной парой, если A ⇒* B с "
        "помощью одних только цепных правил (в частности, (A, A) — всегда цепная пара).")
    d.p("Алгоритм устранения цепных правил:")
    d.formula("1) найти множество всех цепных пар — транзитивное замыкание отношения A ⇒ B;")
    d.formula("2) удалить из P все цепные правила;")
    d.formula("3) для каждой цепной пары (A, B) и каждого нецепного правила B → α")
    d.formula("   добавить правило A → α;")
    d.formula("4) удалить бесполезные символы и правила, их содержащие.")

    d.h2("3.2. Применение к грамматике G₂")
    d.p("В грамматике G_{2} единственное цепное правило — D → O. Цепными парами являются "
        "(D, O) и тривиальные пары (X, X). Единственное нецепное правило нетерминала O — "
        "это O → f, поэтому пара (D, O) даёт правило D → f. Заменяем D → O на D → f.")
    d.p("После удаления цепного правила нетерминал O не встречается ни в одной правой части, "
        "то есть стал недостижимым (шаг 4 алгоритма — повторное приведение). Удаляем O и "
        "правило O → f. Получаем грамматику G_{3}:")
    d.formula("G_{3} = ({a, b, c, d, f, m, j}, {S, A, B, C, D, T}, P_{3}, S),")
    d.formula("P_{3}:  S → aAB     A → bC     B → cA | jT")
    d.formula("       C → dD      D → f      T → Tm | m")
    d.p("Язык не изменился: L(G_{3}) = L(G_{2}), так как D по-прежнему выводит f "
        "(D ⇒ f вместо D ⇒ O ⇒ f).")

    d.h2("3.3. Левая рекурсия: теория")
    d.p("Определение. Грамматика содержит непосредственную левую рекурсию, если в ней есть "
        "правило вида A → Aα. Грамматика содержит косвенную левую рекурсию, если "
        "A ⇒^{+} Aα, где первый шаг вывода выполнен не по правилу с левой частью A.")
    d.p("Левая рекурсия недопустима для LL(k)-анализа (разбора цепочки слева направо "
        "с просмотром k очередных символов) и метода рекурсивного спуска: "
        "анализатор, пытаясь развернуть правило A → Aα, снова и снова выбирает то же самое "
        "правило и зацикливается. Устранение непосредственной левой рекурсии выполняется по "
        "формуле: правило")
    d.formula("A → Aα_{1} | ... | Aα_{m} | β_{1} | ... | β_{n},")
    d.p("где ни одна цепочка β_{i} не начинается с A, заменяется двумя группами правил:")
    d.formula("A  → β_{1}A′ | ... | β_{n}A′ | β_{1} | ... | β_{n},")
    d.formula("A′ → α_{1}A′ | ... | α_{m}A′ | α_{1} | ... | α_{m}.")
    d.p("Новый нетерминал A′ порождает «хвост» цепочки: сначала все α, затем, при "
        "необходимости, ещё один хвост. Легко проверить, что язык при таком преобразовании "
        "не меняется, а левая рекурсия исчезает: ни одно правило A′ не начинается с A′.")

    d.h2("3.4. Применение к грамматике G₃")
    d.p("В G_{3} леворекурсивным является правило T → Tm (второе правило T → m левой "
        "рекурсии не содержит). Здесь A = T, α = m, β = m. По формуле получаем:")
    d.formula("T  → mT′ | m,")
    d.formula("T′ → mT′ | m.")
    d.p("Получена грамматика G_{4}:")
    d.formula("G_{4} = ({a, b, c, d, f, m, j}, {S, A, B, C, D, T, T′}, P_{4}, S),")
    d.formula("P_{4}:  S → aAB     A → bC     B → cA | jT")
    d.formula("       C → dD      D → f      T → mT′ | m     T′ → mT′ | m")
    d.p("Проверка: T выводит m, mm, mmm, ... — те же цепочки, что и в G_{3} "
        "(T ⇒ Tm ⇒ Tmm ⇒ ... ⇒ m^{n}). Левая рекурсия устранена, язык сохранён: "
        "L(G_{4}) = L(G_{3}).")


def section4(d):
    d.h1("4. Определение формы грамматики и её приведение (пункт 6)")

    d.h2("4.1. Форма (класс) грамматики G₄")
    d.p("Определим форму полученной грамматики по основным классификационным признакам.")
    d.p("**По иерархии Хомского.** Каждое правило G_{4} имеет вид A → β, где A ∈ V_{N}, "
        "β ∈ (V_{T} ∪ V_{N})*. Следовательно, G_{4} — контекстно-свободная грамматика "
        "(тип 2). Грамматика не является регулярной (тип 3): правило S → aAB содержит в "
        "правой части два нетерминала, что недопустимо ни для праволинейной, ни для "
        "леволинейной грамматики.")
    d.p("**По укорачиваемости.** В G_{4} нет правил с пустой правой частью, и для каждого "
        "правила A → β выполняется |A| = 1 ≤ |β|. Значит, G_{4} — неукорачивающая "
        "грамматика (и, следовательно, грамматика типа 1 в форме неукорачивающей).")
    d.p("**По левой рекурсии.** G_{4} не содержит ни непосредственной, ни косвенной левой "
        "рекурсии: каждая правая часть начинается с терминала.")
    d.p("**По однозначности.** Грамматика G_{4} однозначна. Во-первых, в ней нет правил "
        "«опасных» видов A → AA | α, A → AαA | β, A → αA | Aβ | γ, A → αA | αAβA | γ, "
        "наличие которых гарантирует неоднозначность. Во-вторых, разбор цепочки "
        "восстанавливается однозначно: для S, A, B, C, D альтернативы начинаются с различных "
        "терминалов, а для T и T′ число применений правила T′ → mT′ однозначно определяется "
        "количеством символов m в цепочке. Для каждой цепочки языка существует единственный "
        "левосторонний вывод.")
    d.p("**По приведённости.** G_{4} является приведённой; доказательство — в п. 4.2.")

    d.h2("4.2. Доказательство приведённости G₄")
    d.p("Проверим для каждого нетерминала продуктивность (существует ли вывод в терминальную "
        "цепочку) и достижимость из S:")
    d.table(
        ["Нетерминал", "Правила", "Продуктивен", "Достижим"],
        [["S", "S → aAB", "да (aAB ⇒* abdfcbdf)", "да (начальный)"],
         ["A", "A → bC", "да (A ⇒* bdf)", "да (S → aAB)"],
         ["B", "B → cA | jT", "да (B ⇒* cbdf, B ⇒* jm)", "да (S → aAB)"],
         ["C", "C → dD", "да (C ⇒* df)", "да (A → bC)"],
         ["D", "D → f", "да (D ⇒ f)", "да (C → dD)"],
         ["T", "T → mT′ | m", "да (T ⇒* m^{n})", "да (B → jT)"],
         ["T′", "T′ → mT′ | m", "да (T′ ⇒* m^{n})", "да (T → mT′)"]],
        widths=[2.6, 4.2, 5.4, 4.2], align="left")
    d.caption("Таблица 2. Проверка продуктивности и достижимости нетерминалов G₄")
    d.p("Все нетерминалы продуктивны и достижимы, все терминалы (a, b, c, d, f, m, j) "
        "встречаются в правых частях правил. В G_{4} отсутствуют ε-правила и цепные правила "
        "(все правила, кроме D → f, содержат не менее двух символов либо терминал и "
        "нетерминал). Следовательно, G_{4} — приведённая КС-грамматика.")
    d.p("Поскольку приведение уже выполнено в п. 4 и п. 5, повторное применение алгоритма "
        "приведения к G_{4} не меняет грамматику. Этот факт проверен программно: функция "
        "`remove_useless` для G_{4} сообщает, что бесплодных нетерминалов и недостижимых "
        "символов нет, и возвращает грамматику, совпадающую с G_{4}.")

    d.h2("4.3. Нормальные формы КС-грамматик")

    d.p("Помимо приведённости, в теории КС-грамматик рассматривают нормальные формы — "
        "ограничения на вид правил. Ограничение может касаться длины правой части или "
        "порядка, в котором в ней идут терминалы и нетерминалы. Для курсового проекта "
        "существенны две формы.")

    d.p("**Нормальная форма Хомского.** Каждое правило имеет вид")
    d.formula("A → a    или    A → BC,    где A, B, C ∈ V_{N}, a ∈ V_{T}.")
    d.p("То есть правая часть — либо ровно один терминал, либо ровно два нетерминала. "
        "Любая КС-грамматика без ε-правил приводится к такой форме (алгоритм 6, метод "
        "«разбиения слов на слоги»): терминалы в длинных правилах заменяются "
        "вспомогательными нетерминалами X_{a} → a, а длинные правые части сворачиваются в "
        "бинарные. НФ Хомского удобна для разбора методом динамического программирования "
        "(алгоритм 7, Кок—Янгер—Касами), где перебираются как раз пары нетерминалов.")

    d.p("**Нормальная форма Грейбах** (определение 39). Каждое правило имеет вид")
    d.formula("A → aα,    где A ∈ V_{N}, a ∈ V_{T}, α ∈ V_{N}*,")
    d.p("то есть правая часть всегда начинается с терминала, а дальше идут только "
        "нетерминалы (возможно, ни одного).")
    d.note("Замечание. Из определения сразу следует, что грамматика в нормальной форме "
           "Грейбах не может быть леворекурсивной: каждая правая часть начинается с "
           "терминала, поэтому правило вида A → Aα в ней невозможно.")

    d.p("**Теорема 40.** Для любой КС-грамматики G, для которой ε ∉ L(G), существует "
        "эквивалентная ей грамматика в нормальной форме Грейбах.")
    d.p("Алгоритм приведения к этой форме состоит из четырёх шагов:")
    d.formula("1) привести грамматику к нормальной форме Хомского (алгоритм 6);")
    d.formula("2) упорядочить и перенумеровать нетерминалы: A_{1} = S, A_{2}, …, A_{n};")
    d.formula("3) подстановкой правых частей (теорема 26) избавиться от правил "
              "A_{i} → A_{j}α при j < i, а левую рекурсию A_{i} → A_{i}α устранить по "
              "теореме 28;")
    d.formula("4) подставлять полученные правые части снизу вверх: A_{n}-правила уже имеют "
              "вид A_{n} → aα, после подстановки в A_{n−1}-правила они тоже получают такой "
              "вид, и так до A_{1} = S.")

    d.p("Такая форма удобна для проектирования автомата: каждый шаг вывода добавляет в "
        "цепочку ровно один терминал, поэтому по грамматике сразу строится МП-автомат без "
        "ε-переходов на развёртывание правил — переход δ(q, a, A) = (q, α) читает очередной "
        "символ входа и заменяет A на α.")

    d.h2("4.4. Приведение G₄ к нормальным формам")

    d.p("**Нормальная форма Хомского.** Правило S → aAB содержит и терминал, и два "
        "нетерминала, поэтому G_{4} НФ Хомского не имеет. Приведение по алгоритму 6 даёт "
        "грамматику")
    d.formula("S → X_{a}Q_{1},   A → X_{b}C,   B → X_{c}A | X_{j}T,   C → X_{d}D,   D → f,")
    d.formula("Q_{1} → AB,   T → X_{m}T′ | m,   T′ → X_{m}T′ | m,")
    d.formula("X_{a} → a,   X_{b} → b,   X_{c} → c,   X_{d} → d,   X_{j} → j,   X_{m} → m.")
    d.p("Здесь X_{a}, …, X_{m} — нетерминалы, введённые вместо терминалов, а Q_{1} — "
        "вспомогательный нетерминал, которым свёрнута длинная правая часть. Эта форма "
        "используется только для контрольного разбора цепочек (функция `cyk`), для "
        "проектирования автомата она не нужна.")

    d.p("**Нормальная форма Грейбах.** Проверим G_{4} по определению 39: выпишем все её "
        "правила и посмотрим на первый символ правой части.")
    d.table(
        ["Правило G₄", "Первый символ", "Остаток α", "Вид A → aα"],
        [["S → aAB", "a — терминал", "AB", "да"],
         ["A → bC", "b — терминал", "C", "да"],
         ["B → cA | jT", "c, j — терминалы", "A | T", "да"],
         ["C → dD", "d — терминал", "D", "да"],
         ["D → f", "f — терминал", "ε (пусто)", "да"],
         ["T → mT′ | m", "m — терминал", "T′ | ε", "да"],
         ["T′ → mT′ | m", "m — терминал", "T′ | ε", "да"]],
        widths=[4.0, 4.6, 3.4, 3.2], align="left")
    d.caption("Таблица 3. Проверка правил G₄ по определению нормальной формы Грейбах")
    d.p("Все правила начинаются с терминала, а остаток правой части состоит только из "
        "нетерминалов или пуст. Значит, G_{4} **уже имеет нормальную форму Грейбах**, и "
        "приведение сводится к проверке: ни один из четырёх шагов алгоритма выполнять не "
        "нужно. Это же подтверждает программа: функция `is_greibach` для G_{4} возвращает "
        "True, а для грамматики в НФ Хомского — False.")
    d.note("Замечание. Грамматика G_{5} из п. 5.3 в НФ Грейбах не находится: после левой "
           "факторизации в ней появилось правило T_{1} → ε. Для построения автомата M_{1} "
           "это не требуется — он строится по G_{4}.")

    d.h2("4.5. Итоговая приведённая грамматика")
    d.p("Таким образом, в результате выполнения пунктов 4–6 получена приведённая "
        "неукорачивающая однозначная КС-грамматика без левой рекурсии, которая к тому же "
        "уже имеет нормальную форму Грейбах:")
    d.formula("G_{4} = ({a, b, c, d, f, m, j}, {S, A, B, C, D, T, T′}, P_{4}, S),")
    d.formula("P_{4}:  S → aAB     A → bC     B → cA | jT")
    d.formula("       C → dD      D → f      T → mT′ | m     T′ → mT′ | m")
    d.p("Именно эта грамматика используется в п. 7 для проектирования МП-автомата.")


def section5(d):
    d.h1("5. Проектирование МП-автомата (пункт 7)")

    d.h2("5.1. Определение и свойства МП-автомата")
    d.p("Магазинный автомат (МП-автомат) — это распознаватель, соответствующий по "
        "порождающей мощности контекстно-свободным грамматикам. Он задаётся семёркой")
    d.formula("M = (Q, Σ, Γ, δ, q_{0}, Z_{0}, F),")
    d.p("где Q — конечное множество состояний; Σ — входной алфавит; Γ — алфавит магазина; "
        "q_{0} ∈ Q — начальное состояние; Z_{0} ∈ Γ — начальный символ магазина; F ⊆ Q — "
        "множество допускающих состояний; δ — функция переходов")
    d.formula("δ: Q × (Σ ∪ {ε}) × Γ → 2^{Q × Γ*}.")
    d.p("Запись δ(q, a, Z) ∋ (q′, γ) означает: находясь в состоянии q, читая входной символ a "
        "(или не читая ничего при a = ε) и видя на вершине магазина символ Z, автомат может "
        "перейти в состояние q′ и заменить Z цепочкой γ (первый символ γ становится новой "
        "вершиной магазина). Конфигурация автомата — это тройка (q, w, γ), где q — текущее "
        "состояние, w — непрочитанная часть входной цепочки, γ — содержимое магазина. "
        "Допускание возможно двумя способами: по конечному состоянию (после чтения всей "
        "цепочки автомат находится в допускающем состоянии) и по пустому магазину. Оба "
        "способа эквивалентны.")
    d.p("В отличие от конечного автомата, МП-автомат недетерминирован по своей природе: "
        "в общем случае по одному и тому же символу возможно несколько переходов. "
        "Детерминированные МП-автоматы допускают лишь подкласс КС-языков, однако для "
        "построенной грамматики такой автомат существует, и он построен в п. 5.3.")

    d.h2("5.2. Недетерминированный МП-автомат по грамматике G₄")
    d.p("Воспользуемся канонической конструкцией, моделирующей левосторонний вывод. "
        "Автомат содержит три состояния: q_{0} (начало работы), q (рабочее состояние) и "
        "q_{f} (допускание). Алфавит магазина — Γ = V_{T} ∪ V_{N} ∪ {Z_{0}}. Переходы:")
    d.formula("1) δ(q_{0}, ε, Z_{0}) = (q, SZ_{0})   — начальная инициализация магазина;")
    d.formula("2) δ(q, ε, A) ∋ (q, α)  для каждого правила A → α грамматики G_{4};")
    d.formula("3) δ(q, a, a) = (q, ε)  для каждого терминала a ∈ V_{T};")
    d.formula("4) δ(q, $, Z_{0}) = (q_{f}, Z_{0})  — конец разбора ($ — маркер конца цепочки).")
    d.p("Правила группы 2 разворачивают нетерминал на вершине магазина в правую часть "
        "соответствующего правила; правила группы 3 «сверяют» терминал на вершине магазина "
        "с очередным символом входа; правило 4 фиксирует успешное завершение разбора. "
        "Итоговый автомат:")
    d.formula("M_{1} = ({q_{0}, q, q_{f}}, {a, b, c, d, f, m, j}, {a, b, c, d, f, m, j} ∪")
    d.formula("∪ {S, A, B, C, D, T, T′} ∪ {Z_{0}}, δ, q_{0}, Z_{0}, {q_{f}}).")
    d.p("Это вариант конструкции, приведённой в лекции (п. 3.3.1). В лекции тот же автомат "
        "записан короче: одно состояние q, начальный символ грамматики сразу помещается в "
        "магазин, а цепочка допускается по пустому магазину:")
    d.formula("ψ(ε, U, q) = {(β, q)} для каждого правила U → β;")
    d.formula("ψ(x, x, q) = {(ε, q)} для каждого терминала x ∈ V_{T}.")
    d.p("Здесь использован эквивалентный вариант с конечным состоянием (определения 5.1 и 5.2): "
        "состояние q_{0} кладёт S в магазин, а состояние q_{f} сигнализирует об успешном "
        "завершении. Оба признака приёма — по конечному состоянию и по пустому магазину — "
        "эквивалентны, поэтому язык от выбора варианта не зависит. Порядок аргументов у ψ "
        "взят из лекции: входной символ, вершина магазина, состояние.")
    d.p("Функция переходов δ (все строки, кроме первой и последней, соответствуют правилам "
        "грамматики):")
    d.table(
        ["Переход", "Значение", "Переход", "Значение"],
        [["δ(q_{0}, ε, Z_{0})", "(q, SZ_{0})", "δ(q, ε, D)", "(q, f)"],
         ["δ(q, ε, S)", "(q, aAB)", "δ(q, ε, T)", "(q, mT′), (q, m)"],
         ["δ(q, ε, A)", "(q, bC)", "δ(q, ε, T′)", "(q, mT′), (q, m)"],
         ["δ(q, ε, B)", "(q, cA), (q, jT)", "δ(q, ε, C)", "(q, dD)"],
         ["δ(q, a, a)", "(q, ε)", "δ(q, b, b)", "(q, ε)"],
         ["δ(q, c, c)", "(q, ε)", "δ(q, d, d)", "(q, ε)"],
         ["δ(q, f, f)", "(q, ε)", "δ(q, j, j)", "(q, ε)"],
         ["δ(q, m, m)", "(q, ε)", "δ(q, $, Z_{0})", "(q_{f}, Z_{0})"]],
        widths=[3.6, 3.4, 3.4, 4.6], align="left", font_size=11)
    d.caption("Таблица 4. Функция переходов недетерминированного МП-автомата M₁")
    d.p("Недетерминизм проявляется в правилах для B и T (по два перехода). Пример работы "
        "автомата на цепочке abdfjm (магазин записан вершиной влево):")
    d.formula("(q_{0}, abdfjm, Z_{0}) ⊢ (q, abdfjm, SZ_{0}) ⊢ (q, abdfjm, aABZ_{0}) ⊢")
    d.formula("⊢ (q, bdfjm, ABZ_{0}) ⊢ (q, bdfjm, bCBZ_{0}) ⊢ (q, dfjm, CBZ_{0}) ⊢")
    d.formula("⊢ (q, dfjm, dDBZ_{0}) ⊢ (q, fjm, DBZ_{0}) ⊢ (q, fjm, fBZ_{0}) ⊢")
    d.formula("⊢ (q, jm, BZ_{0}) ⊢ (q, jm, jTZ_{0}) ⊢ (q, m, TZ_{0}) ⊢")
    d.formula("⊢ (q, m, mZ_{0}) ⊢ (q, ε, Z_{0}) ⊢ (q_{f}, ε, Z_{0}).")
    d.p("Цепочка допущена: автомат прочитал всю входную цепочку и оказался в состоянии q_{f}. "
        "Для цепочки abdf вывод обрывается в конфигурации (q, ε, BZ_{0}): магазин не пуст, "
        "а вход исчерпан — цепочка не допускается.")

    d.h2("5.3. Детерминированный LL(1)-автомат")
    d.p("Построенный автомат M_{1} недетерминирован. Чтобы получить детерминированный "
        "автомат, проверим грамматику на свойство LL(1). Это свойство означает, что выбор "
        "правила для нетерминала A однозначно определяется одним символом входной цепочки — "
        "первым символом цепочки, выводимой из правой части правила.")
    d.p("Управляющая таблица строится по двум вспомогательным множествам символов:")
    d.p("FIRST(A) — множество терминалов, с которых может начинаться цепочка, "
        "выводимая из A.")
    d.p("FOLLOW(A) — множество терминалов, которые могут стоять непосредственно справа "
        "от A в цепочке вывода; для начального символа в это множество входит и маркер "
        "конца цепочки $.")
    d.p("Правило выбирается так: если очередной символ входа входит в FIRST правой части "
        "правила, берётся это правило; если правая часть выводит ε, вместо FIRST "
        "используется FOLLOW нетерминала.")
    d.p("Вычислим эти множества для G_{4}. У нетерминалов T и T′ обе альтернативы "
        "(mT′ и m) начинаются с одного и того же терминала m, поэтому множества FIRST "
        "пересекаются: грамматика G_{4} не является LL(1)-грамматикой.")
    d.p("Применим левую факторизацию: вынесем общий префикс m за скобки. Правило "
        "T → mT′ | m заменяется на")
    d.formula("T → mT_{1},      T_{1} → ε | T′,")
    d.p("а поскольку T′ порождает тот же язык, что и T (m^{+}), нетерминал T_{1} порождает "
        "m^{*}, то есть")
    d.formula("T_{1} → mT_{1} | ε.")
    d.p("Получена грамматика G_{5}:")
    d.formula("G_{5}:  S → aAB     A → bC     B → cA | jT")
    d.formula("       C → dD      D → f      T → mT_{1}     T_{1} → mT_{1} | ε")
    d.note("Замечание. ε-правило T_{1} → ε появилось в результате факторизации (в п. 4 "
           "ε-правила устранялись для получения неукорачивающей грамматики). Это правило не "
           "создаёт конфликта: FOLLOW(T_{1}) = {$}, поэтому выбор между T_{1} → mT_{1} и "
           "T_{1} → ε по первому символу однозначен.")
    d.p("Множества FIRST и FOLLOW для G_{5}:")
    d.table(
        ["Нетерминал", "FIRST", "FOLLOW"],
        [["S", "{a}", "{$}"],
         ["A", "{b}", "{c, j}"],
         ["B", "{c, j}", "{$}"],
         ["C", "{d}", "{c, j}"],
         ["D", "{f}", "{c, j}"],
         ["T", "{m}", "{$}"],
         ["T_{1}", "{m, ε}", "{$}"]],
        widths=[3.2, 5.0, 5.0], align="center")
    d.caption("Таблица 5. Множества FIRST и FOLLOW грамматики G₅")
    d.p("Управляющая таблица M (строка — нетерминал, столбец — очередной входной символ; "
        "прочерк означает синтаксическую ошибку):")
    d.table(
        ["", "a", "b", "c", "d", "f", "j", "m", "$"],
        [["S", "aAB", "—", "—", "—", "—", "—", "—", "—"],
         ["A", "—", "bC", "—", "—", "—", "—", "—", "—"],
         ["B", "—", "—", "cA", "—", "—", "jT", "—", "—"],
         ["C", "—", "—", "—", "dD", "—", "—", "—", "—"],
         ["D", "—", "—", "—", "—", "f", "—", "—", "—"],
         ["T", "—", "—", "—", "—", "—", "—", "mT_{1}", "—"],
         ["T_{1}", "—", "—", "—", "—", "—", "—", "mT_{1}", "ε"]],
        widths=[2.2, 1.9, 1.9, 1.9, 1.9, 1.9, 1.9, 2.0, 1.6], font_size=11)
    d.caption("Таблица 6. Управляющая таблица LL(1)-анализатора")
    d.p("Детерминированный автомат отличается от M_{1} только тем, что для нетерминала на "
        "вершине магазина переход выбирается по таблице 6 — по очередному входному символу, "
        "и для каждой пары (нетерминал, символ) существует не более одного перехода:")
    d.formula("M_{2} = ({q_{0}, q, q_{f}}, {a, b, c, d, f, m, j}, Γ, δ, q_{0}, Z_{0}, {q_{f}}),")
    d.formula("Γ = {a, b, c, d, f, m, j} ∪ {S, A, B, C, D, T, T_{1}} ∪ {Z_{0}},")
    d.formula("δ(q, a, A) = (q, rhs)  ⇔  M[A, a] = rhs  (таблица 6),")
    d.formula("δ(q, a, a) = (q, ε),   δ(q_{0}, ε, Z_{0}) = (q, SZ_{0}),")
    d.formula("δ(q, $, Z_{0}) = (q_{f}, Z_{0}).")
    d.p("Трассировка работы M_{2} на цепочке abdfcbdf приведена в таблице 7. В каждой " 
        "строке таблицы показано применение очередного правила грамматики и сверка " 
        "порождённого им терминала с очередным символом входа (состояние q опущено, " 
        "магазин записан вершиной влево):")
    d.table(
        ["Шаг", "Магазин", "Остаток входа", "Действие"],
        [["0", "Z_{0}", "abdfcbdf", "начальная конфигурация"],
         ["1", "SZ_{0}", "abdfcbdf", "δ(q_{0}, ε, Z_{0}) = (q, SZ_{0})"],
         ["2", "ABZ_{0}", "bdfcbdf", "S → aAB, сверка a"],
         ["3", "CBZ_{0}", "dfcbdf", "A → bC, сверка b"],
         ["4", "DBZ_{0}", "fcbdf", "C → dD, сверка d"],
         ["5", "BZ_{0}", "cbdf", "D → f, сверка f"],
         ["6", "AZ_{0}", "bdf", "B → cA, сверка c"],
         ["7", "CZ_{0}", "df", "A → bC, сверка b"],
         ["8", "DZ_{0}", "f", "C → dD, сверка d"],
         ["9", "Z_{0}", "$", "D → f, сверка f"],
         ["10", "Z_{0}", "$", "δ(q, $, Z_{0}) = (q_{f}, Z_{0})"]],
        widths=[1.4, 4.4, 3.6, 6.4], align="left", font_size=11)
    d.caption("Таблица 7. Трассировка LL(1)-автомата на цепочке abdfcbdf")
    d.p("Для цепочки abdf (не принадлежащей языку) автомат после шага «сверка f» оказывается "
        "в конфигурации (q, ε, BZ_{0}): вход исчерпан, а в магазине остался нетерминал B, "
        "который невозможно развернуть по пустому входу. Автомат останавливается в "
        "недопускающем состоянии — цепочка отклоняется.")


def section6(d):
    d.h1("6. Реализация МП-автомата (пункт 8)")

    d.h2("6.1. Структура программы")
    d.p("Программа части 2 реализована в файле `CourseWork/part2.py` на языке Python 3 и "
        "состоит из трёх частей:")
    d.formula("• класс Grammar — представление КС-грамматики и все преобразования:")
    d.formula("  remove_useless, remove_epsilon, remove_chains, remove_left_recursion,")
    d.formula("  to_cnf, is_cnf, is_greibach, first_sets, follow_sets, is_ll1;")
    d.formula("• класс PDA — модель МП-автомата: конфигурации, функция δ, моделирование;")
    d.formula("• функции build_pda_from_grammar и build_ll1_pda — построение автоматов M_{1} "
              "и M_{2};")
    d.formula("• функция cyk — независимая проверка цепочек вспомогательным разбором "
              "по правилам грамматики (с МП-автоматом не связан, нужен только для "
              "перекрёстного контроля);")
    d.formula("• функция run_tests — автоматическая проверка на наборе цепочек.")
    d.p("Программа не использует внешних библиотек. Запуск: `py part2.py` — пошаговый вывод "
        "всех преобразований и трассировка автомата; `py part2.py --test` — только автотесты.")

    d.h2("6.2. Ключевые фрагменты реализации")
    d.p("Устранение ε-правил (множество X и вычёркивание вхождений nullable-символов):")
    d.code([
        "def nullable(self):",
        "    X, changed = set(), True",
        "    while changed:",
        "        changed = False",
        "        for A, rhs in self.rules:",
        "            if A in X: continue",
        "            if all(s in X for s in rhs):   # пустая правая часть: all() = True",
        "                X.add(A); changed = True",
        "    return X",
        "",
        "def remove_epsilon(self, verbose=True, new_start='S0'):",
        "    X = self.nullable()",
        "    s_eps = self.start in X",
        "    start = new_start if s_eps else self.start",
        "    new_rules = []",
        "    for A, rhs in self.rules:",
        "        if not rhs: continue                # само eps-правило убираем",
        "        variants = {()}",
        "        for s in rhs:                       # все варианты вычёркивания",
        "            if s in X: variants |= {v + (s,) for v in variants}",
        "            else:      variants = {v + (s,) for v in variants}",
        "        new_rules += [(A, v) for v in variants if v]",
        "    if s_eps: new_rules += [(start, (self.start,)), (start, ())]",
        "    g = Grammar(self.N | {start}, self.T, new_rules, start)",
        "    return g.remove_useless(verbose=False), X",
    ])
    d.p("Устранение непосредственной левой рекурсии:")
    d.code([
        "def remove_left_recursion(self, verbose=True, suffix=\"'\"):",
        "    g = self.copy()",
        "    for A in list(g.ordered_n()):",
        "        alphas = [r[1:] for r in g.rules_for(A) if r and r[0] == A]",
        "        betas  = [r for r in g.rules_for(A) if not (r and r[0] == A)]",
        "        if not alphas:",
        "            continue",
        "        newA = A + suffix",
        "        while newA in g.N or newA in g.T:",
        "            newA += suffix",
        "        new_rules = [(lhs, rhs) for lhs, rhs in g.rules if lhs != A]",
        "        for b in betas:",
        "            new_rules += [(A, b + (newA,)), (A, b)]",
        "        for a in alphas:",
        "            new_rules += [(newA, a + (newA,)), (newA, a)]",
        "        g.rules = new_rules",
        "        g.N.add(newA)",
        "    return g",
    ])
    d.p("Моделирование МП-автомата с трассировкой конфигураций:")
    d.code([
        "def run(self, word, verbose=True):",
        "    q, pos, stack = self.q0, 0, (self.z0,)",
        "    history = [(q, pos, stack)]",
        "    while True:",
        "        if not stack: break",
        "        if pos == len(word) and q in self.F: break",
        "        top  = stack[-1]",
        "        look = word[pos] if pos < len(word) else END",
        "        moves = self._moves(q, look, top)",
        "        symbol = look",
        "        if not moves:",
        "            moves, symbol = self._moves(q, EPS, top), EPS",
        "        if len(moves) != 1: break       # конфликт => отказ",
        "        q, push = moves[0]",
        "        stack = stack[:-1] + tuple(reversed(push))",
        "        if symbol not in (EPS, END) and symbol == top:",
        "            pos += 1                    # входной символ потреблён",
        "        history.append((q, pos, stack))",
        "    return q in self.F and pos == len(word) and stack == (self.z0,)",
    ])

    d.h2("6.3. Результаты работы и автотесты")
    d.p("Программа подтверждает все преобразования пунктов 4–6: на каждом шаге печатаются "
        "удалённые бесплодные и недостижимые символы, множество X, цепные пары, параметры "
        "α и β левой рекурсии. Затем строятся автоматы M_{1} и M_{2} и выполняется проверка "
        "на наборе цепочек. Ожидаемый ответ вычисляется независимо — по описанию языка "
        "L = {abdfcbdf} ∪ {abdf j m^{n} | n ≥ 1}. Результаты:")
    d.table(
        ["Входная цепочка", "Ожидание", "M₁ (НД)", "M₂ (LL(1))", "Контрольный разбор"],
        [["abdfcbdf", "допустить", "+", "+", "+"],
         ["abdfjm", "допустить", "+", "+", "+"],
         ["abdfjmm", "допустить", "+", "+", "+"],
         ["abdfjmmm", "допустить", "+", "+", "+"],
         ["abdfjmmmm", "допустить", "+", "+", "+"],
         ["abdf", "отклонить", "−", "−", "−"],
         ["abdfj", "отклонить", "−", "−", "−"],
         ["abdfcbdfm", "отклонить", "−", "−", "−"],
         ["abdfjmj", "отклонить", "−", "−", "−"],
         ["abdfcb", "отклонить", "−", "−", "−"],
         ["abdfjc", "отклонить", "−", "−", "−"]],
        widths=[3.6, 2.6, 2.4, 2.6, 4.2], font_size=11)
    d.caption("Таблица 8. Результаты проверки автоматов на тестовых цепочках")
    d.p("Столбец «Контрольный разбор» — результат независимой проверки: та же цепочка "
        "разбирается по правилам грамматики другим алгоритмом (CYK), который не использует "
        "МП-автомат. Совпадение всех трёх столбцов означает, что преобразования грамматики "
        "не изменили язык.")
    d.p("Дополнительно выполнен исчерпывающий перебор всех цепочек длины 0–4 над алфавитом "
        "{a, b, c, d, f, m, j} — всего 2801 цепочка. Ни одна из них не была ошибочно "
        "допущена ни автоматом M_{1}, ни автоматом M_{2}. Итоговая строка отчёта программы:")
    d.code([
        "  [OK  ] Всего проверено 2801 цепочек, ложных допусканий: 0",
        "  ИТОГ: ВСЕ ТЕСТЫ ПРОЙДЕНЫ",
    ], size=9)
    d.p("Таким образом, спроектированные автоматы M_{1} (недетерминированный, по "
        "приведённой грамматике G_{4}) и M_{2} (детерминированный LL(1), по грамматике G_{5}) "
        "корректно распознают язык L(G).")


def conclusion(d):
    d.h1("Заключение")
    d.p("В части 2 курсового проекта по варианту № 13 (seed 5) выполнены все пункты задания:")
    d.formula("4) из КС-грамматики удалены бесполезные символы (бесплодные E, F и "
              "недостижимые M, h, v) и ε-правило H → ε — получена грамматика G_{2};")
    d.formula("5) удалено цепное правило D → O и устранена левая рекурсия T → Tm — "
              "получена грамматика G_{4};")
    d.formula("6) определена форма грамматики (КС, тип 2; неукорачивающая, приведённая, "
              "однозначная, без левой рекурсии), доказана её приведённость и выполнено "
              "приведение к нормальным формам: G_{4} уже имеет НФ Грейбах, для контроля "
              "построена НФ Хомского;")
    d.formula("7) спроектированы недетерминированный МП-автомат M_{1} (каноническая "
              "конструкция по G_{4}) и детерминированный LL(1)-автомат M_{2} (по G_{5});")
    d.formula("8) автоматы реализованы в программе CourseWork/part2.py и проверены на "
              "тестовых наборах и полном переборе коротких цепочек.")
    d.p("Язык грамматики имеет вид L(G) = {abdfcbdf} ∪ {abdf j m^{n} | n ≥ 1}. Все "
        "преобразования сохраняют язык, что подтверждено как аналитически, так и "
        "программно: для контрольных цепочек результаты недетерминированного автомата, "
        "LL(1)-автомата и независимого разбора совпадают.")


def build(output_path):
    d = Doc()
    title_page(d)
    intro(d)
    section1(d)
    section2(d)
    section3(d)
    section4(d)
    section5(d)
    section6(d)
    conclusion(d)
    d.save(output_path)
    print(f"DOCX успешно создан: {output_path}")


if __name__ == "__main__":
    out = r"c:\Users\user\Documents\AutomataTheory\CourseWork\Колесник-413Б-Ч2.docx"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build(out)
