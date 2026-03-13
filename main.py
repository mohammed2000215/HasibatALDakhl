"""
حاسبة الدخل - نسخة محدّثة
- إضافة خيار العملة (قديمة / جديدة) في قسم ريع رؤوس الاموال المتداولة
"""

import flet as ft
import math
from datetime import datetime, date


SETTINGS = {
    "nafaqat_default": 3,
    "idara_default":   10,
    "rawatib_default": 10,
    "rasm_idara_pct": 0.10,
    "color_green":      "#2E7D32",
    "color_blue":       "#1565C0",
    "color_red":        "#C62828",
    "color_dark_green": "#006400",
    "color_purple":     "#6A1B9A",
    "color_teal":       "#00695C",
    "color_orange":     "#E65100",
    "arbah_old_exempt": 3_000_000,
    "arbah_old_brackets": [
        (3_000_000,   10_000_000,  0.10),
        (10_000_000,  30_000_000,  0.14),
        (30_000_000,  100_000_000, 0.18),
        (100_000_000, 500_000_000, 0.22),
        (500_000_000, float("inf"), 0.25),
    ],
    "arbah_new_exempt": 30_000,
    "arbah_new_brackets": [
        (30_000,    100_000,      0.10),
        (100_000,   300_000,      0.14),
        (300_000,   1_000_000,    0.18),
        (1_000_000, 5_000_000,    0.22),
        (5_000_000, float("inf"), 0.25),
    ],
}


def make_card(content, color):
    return ft.Container(
        content=content,
        bgcolor=color,
        padding=15,
        border_radius=12,
        margin=ft.margin.symmetric(vertical=5),
    )


def result_row(label, value, size=16):
    return ft.Text(f"{label}: {int(value):,}", color="white", size=size)


def section_title(text, color):
    return ft.Text(text, size=22, weight="bold", color=color, text_align="center")


def num_field(label, value="", hint="", width=None):
    kwargs = dict(
        label=label,
        value=str(value),
        hint_text=hint,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        text_size=16,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=14),
    )
    if width:
        kwargs["width"] = width
    return ft.TextField(**kwargs)


def validate_number(field, label="القيمة"):
    raw = (field.value or "").strip()
    if not raw:
        field.error_text = f"يرجى ادخال {label}"
        field.update()
        return None
    try:
        val = float(raw)
        if val <= 0:
            field.error_text = "يجب ان يكون الرقم اكبر من صفر"
            field.update()
            return None
        field.error_text = None
        field.update()
        return val
    except ValueError:
        field.error_text = "ارقام فقط"
        field.update()
        return None


def calc_arbah_brackets(mablagh, brackets):
    tafaseel = []
    dariba_klia = 0
    for lower, upper, nisba in brackets:
        if mablagh <= lower:
            break
        wia3 = min(mablagh, upper) - lower
        sh_d = math.ceil(round(wia3 * nisba, 8))
        dariba_klia += sh_d
        tafaseel.append({
            "pct": nisba * 100,
            "lower": lower,
            "upper": upper,
            "wia3": wia3,
            "dariba": sh_d,
        })
    return tafaseel, dariba_klia


def main(page: ft.Page):
    page.title        = "حاسبة الدخل"
    page.rtl          = True
    page.theme_mode   = ft.ThemeMode.LIGHT
    page.scroll       = ft.ScrollMode.AUTO
    page.padding      = ft.padding.symmetric(horizontal=16, vertical=12)
    page.bgcolor      = "#F5F5F5"
    page.window_width  = 420
    page.window_height = 820

    GREEN      = SETTINGS["color_green"]
    BLUE       = SETTINGS["color_blue"]
    RED        = SETTINGS["color_red"]
    DARK_GREEN = SETTINGS["color_dark_green"]
    PURPLE     = SETTINGS["color_purple"]
    TEAL       = SETTINGS["color_teal"]

    def back_btn(dest):
        return ft.OutlinedButton(
            "العودة للقائمة الرئيسية",
            on_click=dest, width=360, height=46,
            style=ft.ButtonStyle(color=DARK_GREEN),
        )

    def menu_btn(label, color, handler):
        return ft.ElevatedButton(
            label, bgcolor=color, color="white",
            on_click=handler, width=360, height=56,
        )

    def calc_btn(label, color, handler):
        return ft.ElevatedButton(
            label, bgcolor=color, color="white",
            width=360, height=50, on_click=handler,
        )

    # ══════════════════════════════════════
    #  الصفحة الرئيسية
    # ══════════════════════════════════════
    def show_home(e=None):
        page.controls.clear()
        page.add(ft.Column(
            controls=[
                ft.Container(height=20),
                ft.Text("حاسبة الدخل", size=30, weight="bold",
                        color=DARK_GREEN, text_align="center"),
                ft.Container(height=4),
                ft.Text("اختر نوع العملية المراد حسابها",
                        size=15, color="grey", text_align="center"),
                ft.Container(height=24),
                menu_btn("حساب الدخل المقطوع",         GREEN,  show_maqtou3),
                ft.Container(height=10),
                menu_btn("ريع رؤوس الاموال المتداولة",  BLUE,   show_rea3),
                ft.Container(height=10),
                menu_btn("الارباح الحقيقية",             PURPLE, show_arbah),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  1) حساب الدخل المقطوع
    # ══════════════════════════════════════
    def show_maqtou3(e=None):
        page.controls.clear()

        income_f  = num_field("القيمة المراد حسابها", hint="مثال: 500000")
        nafaqat_f = num_field("نسبة النفقات %",  value=SETTINGS["nafaqat_default"], width=110)
        idara_f   = num_field("نسبة الادارة %",  value=SETTINGS["idara_default"],   width=110)
        rawatib_f = num_field("نسبة الرواتب %",  value=SETTINGS["rawatib_default"], width=110)

        years_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="1", label="سنة واحدة"),
                 ft.Radio(value="2", label="سنتين")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="1",
        )
        mult_dd = ft.Dropdown(
            label="مضاعف السنة الثانية", value="1", visible=False,
            options=[ft.dropdown.Option(str(i), f"x {i}") for i in range(1, 6)],
        )
        results_col = ft.Column(spacing=10)

        def on_years_change(e):
            mult_dd.visible = (years_rg.value == "2")
            page.update()
        years_rg.on_change = on_years_change

        def calc(e):
            val = validate_number(income_f, "القيمة")
            if val is None:
                page.update()
                return

            np_r = float(nafaqat_f.value or SETTINGS["nafaqat_default"]) / 100
            ip_r = float(idara_f.value   or SETTINGS["idara_default"])   / 100
            rp_r = float(rawatib_f.value or SETTINGS["rawatib_default"]) / 100

            d1 = math.ceil(val)
            n1 = math.ceil(d1 * np_r)
            i1 = math.ceil(d1 * ip_r)
            r1 = math.ceil(d1 * rp_r)
            t1 = d1 + n1 + i1 + r1

            results_col.controls.clear()
            results_col.controls.append(make_card(ft.Column([
                ft.Text("السنة الاولى", weight="bold", size=18, color="white"),
                result_row("الدخل",   d1),
                result_row("النفقات", n1),
                result_row("الادارة", i1),
                result_row("الرواتب", r1),
                ft.Divider(color="white54"),
                result_row("المجموع", t1, size=17),
            ]), GREEN))

            grand = t1
            if years_rg.value == "2":
                mult = int(mult_dd.value or 1)
                d2 = math.ceil(d1 * mult)
                n2 = math.ceil(d2 * np_r)
                i2 = math.ceil(d2 * ip_r)
                r2 = math.ceil(d2 * rp_r)
                t2 = d2 + n2 + i2 + r2
                grand += t2
                results_col.controls.append(make_card(ft.Column([
                    ft.Text("السنة الثانية", weight="bold", size=18, color="white"),
                    result_row("الدخل",   d2),
                    result_row("النفقات", n2),
                    result_row("الادارة", i2),
                    result_row("الرواتب", r2),
                    ft.Divider(color="white54"),
                    result_row("المجموع", t2, size=17),
                ]), BLUE))

            results_col.controls.append(make_card(
                ft.Text(f"الاجمالي الكلي: {int(grand):,}",
                        weight="bold", size=22, color="white", text_align="center"),
                RED,
            ))
            page.update()

        page.add(ft.Column(
            controls=[
                section_title("حساب الدخل المقطوع", DARK_GREEN),
                ft.Divider(),
                ft.Text("النسب (قابلة للتعديل):", weight="bold", color=DARK_GREEN),
                ft.Row([nafaqat_f, idara_f, rawatib_f], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                income_f,
                ft.Text("عدد السنوات:", weight="bold"),
                years_rg, mult_dd,
                calc_btn("احسب", DARK_GREEN, calc),
                results_col,
                ft.Container(height=16),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  2) ريع رؤوس الاموال المتداولة
    #  ✅ إضافة خيار العملة: قديمة / جديدة
    #
    #  - إذا أدخل المستخدم قيمة بالعملة القديمة:
    #    الحسابات تجري مباشرة، والنتيجة تظهر بالعملتين
    #  - إذا أدخل بالعملة الجديدة:
    #    تُحوَّل القيمة × 100 أولاً ثم تجري الحسابات
    # ══════════════════════════════════════
    def show_rea3(e=None):
        page.controls.clear()

        # --- خيار العملة (جديد) ---
        currency_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="old", label="عملة قديمة"),
                 ft.Radio(value="new", label="عملة جديدة")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="old",
        )
        currency_note = ft.Text(
            "العملة القديمة = الأكبر  |  العملة الجديدة = القديمة ÷ 100",
            size=12, color="grey", italic=True, text_align="center",
        )

        bond_f = num_field("قيمة السند", hint="مثال: 1000000")

        dur_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="1year",  label="سنة واحدة"),
                 ft.Radio(value="custom", label="تحديد تاريخين")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="1year",
        )

        selected_dates = {"bond": None, "today": date.today()}
        date1_display = ft.Text("لم يتم الاختيار بعد", color="grey", size=14, italic=True)
        date2_display = ft.Text(
            f"التاريخ الحالي: {date.today().strftime('%Y-%m-%d')}",
            color=DARK_GREEN, size=14,
        )
        date_error = ft.Text("", color="red", size=13, visible=False)

        def on_bond_date_picked(e):
            if e.control.value:
                selected_dates["bond"] = e.control.value.date()
                date1_display.value  = f"تاريخ السند: {selected_dates['bond'].strftime('%Y-%m-%d')}"
                date1_display.color  = DARK_GREEN
                date1_display.italic = False
                date_error.visible   = False
            page.update()

        def on_today_date_picked(e):
            if e.control.value:
                selected_dates["today"] = e.control.value.date()
                date2_display.value = f"التاريخ الحالي: {selected_dates['today'].strftime('%Y-%m-%d')}"
                date_error.visible  = False
            page.update()

        bond_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            on_change=on_bond_date_picked,
        )
        today_date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
            value=datetime.today(),
            on_change=on_today_date_picked,
        )
        page.overlay.append(bond_date_picker)
        page.overlay.append(today_date_picker)

        def open_bond_picker(e):
            bond_date_picker.open = True
            page.update()

        def open_today_picker(e):
            today_date_picker.open = True
            page.update()

        dates_section = ft.Column(
            controls=[
                ft.Divider(),
                ft.Text("اختر تاريخ السند:", weight="bold", size=14),
                ft.Row([
                    ft.ElevatedButton("اختر التاريخ", bgcolor=TEAL, color="white",
                                      on_click=open_bond_picker, height=42),
                    date1_display,
                ], spacing=12),
                ft.Container(height=4),
                ft.Text("اختر التاريخ الحالي:", weight="bold", size=14),
                ft.Row([
                    ft.ElevatedButton("اختر التاريخ", bgcolor=TEAL, color="white",
                                      on_click=open_today_picker, height=42),
                    date2_display,
                ], spacing=12),
                date_error,
            ],
            visible=False, spacing=8,
        )
        results_col = ft.Column(spacing=10)

        def on_dur_change(e):
            dates_section.visible = (dur_rg.value == "custom")
            page.update()
        dur_rg.on_change = on_dur_change

        # ── بناء بطاقة النتائج ──────────────────────────────────────────
        def _build_rea3_card(title_text, qima_orig, omla,
                              rasm, idara, faida,
                              tr=None, sana=None, ashhur=None, ayam=None,
                              rs=None, ra=None, rd=None,
                              is_multi=False):
            """
            omla: "old" → القيمة المدخلة بالعملة القديمة
                  "new" → القيمة المدخلة بالعملة الجديدة

            جميع الأرقام المحسوبة (faida, rasm, idara, tr, rs, ra, rd)
            هي بالعملة القديمة دائماً (لأن الحساب يجري على القيمة ×100).
            عند عرضها للمستخدم:
              - عملة قديمة → اعرض كما هي
              - عملة جديدة → اقسم على 100 قبل العرض
            """
            div = 100 if omla == "new" else 1

            def v(x):
                return math.ceil(x / div)

            if is_multi:
                total_nihai = v(math.ceil(tr + idara))
            else:
                total_nihai = v(math.ceil(rasm + idara))

            omla_label = "عملة قديمة" if omla == "old" else "عملة جديدة"
            subtitle = ft.Text(
                f"العملة المدخلة: {omla_label}",
                color="white70", size=13, italic=True,
            )

            if is_multi:
                rows = [
                    ft.Text(title_text, weight="bold", size=17, color="white"),
                    subtitle,
                    result_row("قيمة السند",               math.ceil(qima_orig)),
                    result_row("الفائدة (10%)",             v(math.ceil(faida))),
                    result_row("الرسم الاساسي",             v(rasm)),
                    ft.Text(
                        f"المدة: {sana} سنة  /  {ashhur} شهر  /  {ayam} يوم",
                        color="white", size=14,
                    ),
                    ft.Divider(color="white54"),
                    result_row("رسم السنوات",               v(rs)),
                    result_row("رسم الاشهر",                v(ra)),
                    result_row("رسم الايام",                v(rd)),
                    result_row("مجموع الرسوم",              v(tr)),
                    result_row("رسم الادارة المحلية (10%)",  v(idara)),
                    ft.Divider(color="white54"),
                ]
            else:
                rows = [
                    ft.Text(title_text, weight="bold", size=17, color="white"),
                    subtitle,
                    result_row("قيمة السند",               math.ceil(qima_orig)),
                    result_row("الفائدة (10%)",             v(math.ceil(faida))),
                    result_row("الرسم (10% من الفائدة)",    v(rasm)),
                    result_row("رسم الادارة المحلية (10%)",  v(idara)),
                    ft.Divider(color="white54"),
                ]

            # ✅ عملة قديمة → يظهر بالعملتين | عملة جديدة → يظهر بالجديدة فقط
            if omla == "old":
                total_jadid = math.ceil(total_nihai / 100)
                rows.append(result_row("المجموع الكلي (عملة قديمة)", total_nihai, size=17))
                rows.append(result_row("المجموع الكلي (عملة جديدة)", total_jadid, size=17))
            else:
                rows.append(result_row("المجموع الكلي (عملة جديدة)", total_nihai, size=17))

            return make_card(ft.Column(rows), TEAL)

        def calc(e):
            qima_raw = validate_number(bond_f, "قيمة السند")
            if qima_raw is None:
                page.update()
                return

            omla = currency_rg.value

            # إذا كانت القيمة بالعملة الجديدة → نحوّلها إلى قديمة للحساب
            if omla == "new":
                qima = qima_raw * 100   # تحويل إلى عملة قديمة
            else:
                qima = qima_raw

            faida = qima * 0.10
            rasm  = math.ceil(faida * 0.10)
            results_col.controls.clear()

            if dur_rg.value == "1year":
                idara = math.ceil(rasm * 0.10)
                results_col.controls.append(
                    _build_rea3_card(
                        "ريع راس المال - سنة واحدة",
                        qima_orig=qima_raw, omla=omla,
                        faida=faida, rasm=rasm, idara=idara,
                    )
                )
            else:
                if selected_dates["bond"] is None:
                    date_error.value   = "يرجى اختيار تاريخ السند"
                    date_error.visible = True
                    page.update()
                    return

                d1 = selected_dates["bond"]
                d2 = selected_dates["today"]

                if d2 <= d1:
                    date_error.value   = "يجب ان يكون التاريخ الحالي بعد تاريخ السند"
                    date_error.visible = True
                    page.update()
                    return

                date_error.visible = False
                delta  = (d2 - d1).days
                sana   = delta // 365
                ashhur = (delta % 365) // 30
                ayam   = (delta % 365) % 30
                rs     = rasm * sana
                ra     = math.ceil((rasm * ashhur) / 12)
                rd     = math.ceil((rasm * ayam) / 365)
                tr     = rs + ra + rd
                idara  = math.ceil(tr * 0.10)

                results_col.controls.append(
                    _build_rea3_card(
                        "ريع راس المال - مدة مخصصة",
                        qima_orig=qima_raw, omla=omla,
                        faida=faida, rasm=rasm, idara=idara,
                        tr=tr, sana=sana, ashhur=ashhur, ayam=ayam,
                        rs=rs, ra=ra, rd=rd, is_multi=True,
                    )
                )

            page.update()

        page.add(ft.Column(
            controls=[
                section_title("ريع رؤوس الاموال المتداولة", BLUE),
                ft.Divider(),
                ft.Text("نوع العملة المدخلة:", weight="bold", color=BLUE),
                currency_rg,
                currency_note,
                ft.Divider(),
                bond_f,
                ft.Text("مدة السند:", weight="bold"),
                dur_rg,
                dates_section,
                calc_btn("احسب", BLUE, calc),
                results_col,
                ft.Container(height=16),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    # ══════════════════════════════════════
    #  3) الارباح الحقيقية
    # ══════════════════════════════════════
    def show_arbah(e=None):
        page.controls.clear()

        currency_rg = ft.RadioGroup(
            content=ft.Row(
                [ft.Radio(value="new", label="عملة جديدة"),
                 ft.Radio(value="old", label="عملة قديمة")],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="new",
        )
        income_f    = num_field("القيمة المراد حسابها", hint="مثال: 17000000")
        results_col = ft.Column(spacing=10)

        def calc(e):
            mablagh = validate_number(income_f, "القيمة")
            if mablagh is None:
                page.update()
                return

            omla    = currency_rg.value
            maffy   = SETTINGS["arbah_old_exempt"]   if omla == "old" else SETTINGS["arbah_new_exempt"]
            sharaeh = SETTINGS["arbah_old_brackets"] if omla == "old" else SETTINGS["arbah_new_brackets"]
            rasm_idara_pct = SETTINGS["rasm_idara_pct"]

            results_col.controls.clear()

            if mablagh <= maffy:
                results_col.controls.append(make_card(
                    ft.Text(
                        f"المبلغ ({int(mablagh):,})\n"
                        f"ضمن الحد المعفى ({int(maffy):,})\n"
                        f"لا ضريبة مستحقة",
                        color="white", size=16, text_align="center",
                    ),
                    GREEN,
                ))
                page.update()
                return

            tafaseel, dariba_klia = calc_arbah_brackets(mablagh, sharaeh)
            rasm_idara  = math.ceil(dariba_klia * rasm_idara_pct)
            total_qabla = dariba_klia + rasm_idara

            if omla == "old":
                total_nihai = math.ceil(total_qabla / 100)
            else:
                total_nihai = total_qabla

            rows = [
                ft.Text("الارباح الحقيقية - تفصيل الشرائح",
                        weight="bold", size=18, color="white"),
                result_row("المبلغ الكلي", math.ceil(mablagh)),
                result_row("الحد المعفى",  maffy),
                ft.Divider(color="white54"),
            ]

            for i, sh in enumerate(tafaseel, 1):
                upper_str = (f"{int(sh['upper']):,}"
                             if sh["upper"] != float("inf") else "فما فوق")
                rows.append(ft.Text(
                    f"الشريحة {i}  ({sh['pct']:.0f}%)"
                    f"  من {int(sh['lower']):,}  الى {upper_str}",
                    color="white70", size=13,
                ))
                rows.append(ft.Text(
                    f"    الوعاء: {int(sh['wia3']):,}"
                    f"   |   الضريبة: {int(sh['dariba']):,}",
                    color="white", size=14,
                ))

            rows += [
                ft.Divider(color="white54"),
                result_row("مجموع الضريبة", dariba_klia, size=17),
                result_row(f"رسم الادارة المحلية ({int(rasm_idara_pct * 100)}%)",
                           rasm_idara, size=16),
            ]

            if omla == "old":
                rows.append(ft.Text(
                    f"المجموع قبل التحويل: {int(total_qabla):,}",
                    color="white70", size=14,
                ))
                rows.append(ft.Text(
                    "(مقسوم على 100 - تحويل للعملة الجديدة)",
                    color="white60", size=13,
                ))

            rows.append(ft.Divider(color="white54"))
            rows.append(ft.Text(
                f"المجموع النهائي للضريبة: {int(total_nihai):,}",
                weight="bold", size=19, color="white",
            ))

            results_col.controls.append(make_card(ft.Column(rows), PURPLE))
            page.update()

        page.add(ft.Column(
            controls=[
                section_title("الارباح الحقيقية", PURPLE),
                ft.Divider(),
                ft.Text("نوع العملة:", weight="bold"),
                currency_rg,
                income_f,
                calc_btn("احسب", PURPLE, calc),
                results_col,
                ft.Container(height=16),
                back_btn(show_home),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12, expand=True,
        ))
        page.update()

    show_home()


if __name__ == "__main__":
    ft.app(target=main)
