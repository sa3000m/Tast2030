import ast
import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Union

import streamlit as st


st.set_page_config(
    page_title="🧮 آلة حاسبة محترفة",
    page_icon="🧮",
    layout="centered",
)

st.title("🧮 آلة حاسبة محترفة")
st.caption(
    "كل ما تحتاجه للحسابات اليومية والعلمية في واجهة عربية بسيطة وقوية."
)


@dataclass
class HistoryItem:
    description: str
    result: Union[float, int, str]


if "history" not in st.session_state:
    st.session_state["history"] = []

if "basic_result" not in st.session_state:
    st.session_state["basic_result"] = None

if "scientific_result" not in st.session_state:
    st.session_state["scientific_result"] = None

if "expression_result" not in st.session_state:
    st.session_state["expression_result"] = None

if "conversion_result" not in st.session_state:
    st.session_state["conversion_result"] = None


def push_history(description: str, result: Union[float, int, str]) -> None:
    """أضف عملية جديدة إلى السجل مع الحفاظ على آخر 15 عملية فقط."""

    history: List[HistoryItem] = st.session_state.get("history", [])
    if history and history[0].description == description and history[0].result == result:
        return
    history.insert(0, HistoryItem(description, result))
    st.session_state["history"] = history[:15]


# --- الأدوات المساعدة للتعبيرات العلمية ---
AllowedResult = Union[int, float]


ALLOWED_OPERATORS: Dict[type, Callable[[AllowedResult, AllowedResult], AllowedResult]] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a**b,
    ast.Mod: lambda a, b: a % b,
    ast.FloorDiv: lambda a, b: a // b,
}


ALLOWED_UNARY: Dict[type, Callable[[AllowedResult], AllowedResult]] = {
    ast.UAdd: lambda x: +x,
    ast.USub: lambda x: -x,
}


ALLOWED_NAMES = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


ALLOWED_FUNCTIONS: Dict[str, Callable[..., AllowedResult]] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "degrees": math.degrees,
    "radians": math.radians,
    "factorial": lambda x: math.factorial(int(x)),
    "abs": abs,
}


class SafeEval(ast.NodeVisitor):
    """محرك تقييم آمن للتعبيرات الرياضية."""

    def visit(self, node: ast.AST) -> AllowedResult:
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        if isinstance(node, ast.Num):  # type: ignore[deprecated-return]
            return node.n  # type: ignore[return-value]
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("القيم غير الرقمية غير مسموح بها.")
        if isinstance(node, ast.BinOp):
            operator_type = type(node.op)
            if operator_type not in ALLOWED_OPERATORS:
                raise ValueError("عملية غير مسموح بها.")
            left = self.visit(node.left)
            right = self.visit(node.right)
            return ALLOWED_OPERATORS[operator_type](left, right)
        if isinstance(node, ast.UnaryOp):
            operator_type = type(node.op)
            if operator_type not in ALLOWED_UNARY:
                raise ValueError("عملية أحادية غير مسموح بها.")
            return ALLOWED_UNARY[operator_type](self.visit(node.operand))
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("هذا النوع من الدوال غير مسموح.")
            name = node.func.id
            if name not in ALLOWED_FUNCTIONS:
                raise ValueError("دالة غير مدعومة.")
            args = [self.visit(arg) for arg in node.args]
            return ALLOWED_FUNCTIONS[name](*args)
        if isinstance(node, ast.Name):
            if node.id in ALLOWED_NAMES:
                return ALLOWED_NAMES[node.id]
            raise ValueError("المتغير غير معروف.")
        raise ValueError("تعبير غير مدعوم.")


def safe_eval(expression: str) -> AllowedResult:
    try:
        tree = ast.parse(expression, mode="eval")
        evaluator = SafeEval()
        return evaluator.visit(tree)
    except ZeroDivisionError:
        raise ZeroDivisionError("لا يمكن القسمة على صفر.")
    except Exception as exc:  # pragma: no cover - التوضيح للمستخدم النهائي
        raise ValueError("تعذر فهم التعبير، تأكد من صحته.") from exc


basic_tab, scientific_tab, expression_tab, conversion_tab, history_tab = st.tabs(
    [
        "العمليات الأساسية",
        "الحاسبة العلمية",
        "تقييم التعبيرات",
        "تحويلات سريعة",
        "سجل العمليات",
    ]
)


with basic_tab:
    st.subheader("عمليات حسابية فورية")
    with st.form("basic_form"):
        col_left, col_right = st.columns(2)
        with col_left:
            number_a = st.number_input("العدد الأول", value=0.0, key="basic_a")
        with col_right:
            number_b = st.number_input("العدد الثاني", value=0.0, key="basic_b")

        operation = st.selectbox(
            "اختر العملية",
            (
                "جمع (+)",
                "طرح (-)",
                "ضرب (×)",
                "قسمة (÷)",
                "قوة (^)",
                "باقي القسمة (%)",
            ),
        )

        submitted = st.form_submit_button("احسب")

    if submitted:
        try:
            if operation == "جمع (+)":
                result = number_a + number_b
                description = f"{number_a} + {number_b}"
            elif operation == "طرح (-)":
                result = number_a - number_b
                description = f"{number_a} - {number_b}"
            elif operation == "ضرب (×)":
                result = number_a * number_b
                description = f"{number_a} × {number_b}"
            elif operation == "قسمة (÷)":
                if number_b == 0:
                    raise ZeroDivisionError
                result = number_a / number_b
                description = f"{number_a} ÷ {number_b}"
            elif operation == "قوة (^)":
                result = number_a**number_b
                description = f"{number_a} ^ {number_b}"
            else:
                if number_b == 0:
                    raise ZeroDivisionError
                result = number_a % number_b
                description = f"{number_a} % {number_b}"

            st.session_state["basic_result"] = (description, result)
            push_history(description, result)
        except ZeroDivisionError:
            st.session_state["basic_result"] = None
            st.error("⚠️ لا يمكن القسمة على صفر، غيّر العدد الثاني.")

    basic_result = st.session_state.get("basic_result")
    if basic_result is not None:
        description, value = basic_result
        st.metric("النتيجة الأخيرة", f"{value:.6g}")
        st.caption(f"التفاصيل: {description}")


with scientific_tab:
    st.subheader("دوال علمية متقدمة")
    with st.form("scientific_form"):
        angle_unit = st.radio("وحدة قياس الزوايا", ("درجات", "راديان"), horizontal=True)
        scientific_function = st.selectbox(
            "اختر الدالة",
            (
                "sin",
                "cos",
                "tan",
                "asin",
                "acos",
                "atan",
                "log",
                "log10",
                "sqrt",
                "exp",
                "factorial",
            ),
        )
        value = st.number_input("أدخل القيمة", value=0.0, key="scientific_value")
        submitted_scientific = st.form_submit_button("نفذ الدالة")

    if submitted_scientific:
        try:
            raw_value = value
            if scientific_function in {"sin", "cos", "tan"} and angle_unit == "درجات":
                raw_value = math.radians(value)
            if scientific_function in {"asin", "acos", "atan"} and angle_unit == "درجات":
                result = math.degrees(ALLOWED_FUNCTIONS[scientific_function](raw_value))
            elif scientific_function == "factorial":
                if value < 0 or int(value) != value:
                    raise ValueError("عامل العدد متاح للأعداد الصحيحة الموجبة فقط.")
                result = ALLOWED_FUNCTIONS[scientific_function](value)
            elif scientific_function in {"log", "log10"} and value <= 0:
                raise ValueError("لا يمكن حساب اللوغاريتم للأعداد السالبة أو الصفر.")
            else:
                result = ALLOWED_FUNCTIONS[scientific_function](raw_value)

            st.session_state["scientific_result"] = (
                scientific_function,
                value,
                angle_unit,
                result,
            )
            push_history(f"{scientific_function}({value})", result)
        except ValueError as error:
            st.session_state["scientific_result"] = None
            st.error(f"⚠️ {error}")

    scientific_result = st.session_state.get("scientific_result")
    if scientific_result is not None:
        func_name, value, unit, result = scientific_result
        st.success(
            f"{func_name}({value}{'°' if unit == 'درجات' else ''}) = {result:.10g}"
        )


with expression_tab:
    st.subheader("حل تعبير رياضي كامل")
    with st.form("expression_form"):
        expression = st.text_input(
            "أدخل التعبير الرياضي (مثال: 2*sin(pi/4) + log(10))",
            key="expression_input",
        )
        submitted_expression = st.form_submit_button("احسب التعبير")

    if submitted_expression:
        if expression:
            try:
                value = safe_eval(expression)
                st.session_state["expression_result"] = (expression, value)
                push_history(expression, value)
            except Exception as error:
                st.session_state["expression_result"] = None
                st.error(f"⚠️ {error}")
        else:
            st.warning("أدخل تعبيرًا أولًا من فضلك.")

    expression_result = st.session_state.get("expression_result")
    if expression_result is not None:
        expression_text, value = expression_result
        st.info(f"{expression_text} = {value:.12g}")

    with st.expander("الدوال والثوابت المتاحة"):
        st.markdown(
            """
            **الدوال:** `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `log`,
            `log10`, `exp`, `degrees`, `radians`, `factorial`, `abs`

            **الثوابت:** `pi`, `e`, `tau`

            **العمليات:** جمع (+)، طرح (-)، ضرب (*), قسمة (/), أس (**), باقي (%), قسمة صحيحة (//)
            """
        )


with conversion_tab:
    st.subheader("تحويلات وحدات سريعة")
    with st.form("conversion_form"):
        conversion_type = st.selectbox(
            "نوع التحويل",
            (
                "درجة ↔ راديان",
                "السنتيمتر ↔ المتر",
                "الكيلوجرام ↔ الجرام",
                "الدرجة المئوية ↔ الفهرنهايت",
            ),
        )

        value = st.number_input("القيمة", value=0.0, key="conversion_value")
        submitted_conversion = st.form_submit_button("حوّل الآن")

    if submitted_conversion:
        if conversion_type == "درجة ↔ راديان":
            degrees = value
            radians = math.radians(value)
            st.session_state["conversion_result"] = (
                ("بالدرجات", degrees, "{:.4f}"),
                ("بالراديان", radians, "{:.6f}"),
            )
            push_history(f"تحويل درجات {degrees}", radians)
        elif conversion_type == "السنتيمتر ↔ المتر":
            centimeters = value
            meters = value / 100
            st.session_state["conversion_result"] = (
                ("متر", meters, "{:.6f}"),
                ("سنتيمتر", centimeters, "{:.4f}"),
            )
            push_history(f"تحويل طول {centimeters} سم", meters)
        elif conversion_type == "الكيلوجرام ↔ الجرام":
            kilograms = value
            grams = value * 1000
            st.session_state["conversion_result"] = (
                ("كيلوجرام", kilograms, "{:.4f}"),
                ("جرام", grams, "{:.2f}"),
            )
            push_history(f"تحويل وزن {kilograms} كجم", grams)
        else:
            celsius = value
            fahrenheit = (value * 9 / 5) + 32
            st.session_state["conversion_result"] = (
                ("°C", celsius, "{:.2f}"),
                ("°F", fahrenheit, "{:.2f}"),
            )
            push_history(f"تحويل حرارة {celsius}°C", fahrenheit)

    conversion_result = st.session_state.get("conversion_result")
    if conversion_result is not None:
        for label, val, fmt in conversion_result:
            st.metric(label, fmt.format(val))


with history_tab:
    st.subheader("سجل العمليات")
    history: List[HistoryItem] = st.session_state.get("history", [])

    if not history:
        st.info("لم تقم بأي عملية بعد. قم بالحساب لتظهر هنا.")
    else:
        for item in history:
            st.write(f"• **{item.description}** → `{item.result}`")

    if st.button("مسح السجل", type="secondary"):
        st.session_state["history"] = []
        st.experimental_rerun()

