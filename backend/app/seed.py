"""Наполнение демо-данными: полный демо-курс Python и C++, задачи, экзамены.

Запуск: python -m app.seed
Идемпотентно: если демо-учитель уже есть, ничего не делает.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.content import Course, CourseLanguage, Lesson, Level, LevelName, Module
from app.models.exam import (
    Exam,
    ExamPracticalProblem,
    ExamTheoryConfig,
    StudentLevelAccess,
)
from app.models.problem import Problem, ProblemSource, ProblemTag, ProblemTest
from app.models.quiz import (
    LessonProgress,
    LessonQuestion,
    ProgressStatus,
    Question,
    QuestionType,
)
from app.models.submission import SolvedSource, StudentSolvedProblem
from app.models.user import StudentProfile, TeacherProfile, User, UserRole

# .local — зарезервированный домен, его отклоняет email-валидатор, поэтому example.com
TEACHER_EMAIL = "teacher@example.com"
STUDENT_EMAIL = "student@example.com"
DEMO_PASSWORD = "password123"


# --- Помощники для описания вопросов мини-квиза ------------------------------

def sc(prompt, options, correct, expl=None):
    """single_choice: один правильный вариант (индекс)."""
    return {
        "type": QuestionType.single_choice, "prompt_md": prompt, "options": options,
        "correct_answer": {"correct": correct}, "explanation_md": expl,
    }


def mc(prompt, options, correct, expl=None):
    """multiple_choice: несколько правильных (список индексов)."""
    return {
        "type": QuestionType.multiple_choice, "prompt_md": prompt, "options": options,
        "correct_answer": {"correct": correct}, "explanation_md": expl,
    }


def sa(prompt, accepted, expl=None):
    """short_answer: свободный ответ (регистр/пробелы не важны)."""
    return {
        "type": QuestionType.short_answer, "prompt_md": prompt, "options": None,
        "correct_answer": {"accepted": accepted}, "explanation_md": expl,
    }


def co(prompt, accepted, expl=None):
    """code_output: что выведет код (регистр важен)."""
    return {
        "type": QuestionType.code_output, "prompt_md": prompt, "options": None,
        "correct_answer": {"accepted": accepted}, "explanation_md": expl,
    }


# --- Учебная программа --------------------------------------------------------

CURRICULUM = [
    {
        "title": "Python с нуля",
        "language": CourseLanguage.python,
        "description": "От первой строки кода до алгоритмов: переменные, циклы, "
                       "коллекции, функции и рекурсия.",
        "levels": [
            {
                "name": LevelName.beginner,
                "modules": [
                    {
                        "title": "Основы",
                        "lessons": [
                            {
                                "title": "Первая программа и вывод",
                                "content_md": (
                                    "# Первая программа\n\n"
                                    "Программа на Python — это последовательность команд. "
                                    "Главная команда для вывода на экран — `print`.\n\n"
                                    "```python\n"
                                    "print(\"Привет, мир!\")\n"
                                    "print(\"Мне\", 12, \"лет\")\n"
                                    "```\n\n"
                                    "`print` выводит значения через пробел и переходит на "
                                    "новую строку. Текст берут в кавычки — это **строка**.\n\n"
                                    "> Запустите пример в песочнице ниже и поменяйте текст."
                                ),
                                "quiz": [
                                    co("Что выведет `print(1, 2, 3)`?", ["1 2 3"],
                                       "`print` разделяет аргументы пробелом."),
                                    sc("Какой командой выводят текст на экран?",
                                       ["input()", "print()", "output()"], 1),
                                ],
                            },
                            {
                                "title": "Переменные и ввод",
                                "content_md": (
                                    "# Переменные и ввод\n\n"
                                    "Переменная хранит значение. Данные от пользователя читают "
                                    "функцией `input()` — она всегда возвращает **строку**, "
                                    "поэтому числа оборачивают в `int()`.\n\n"
                                    "```python\n"
                                    "name = input()\n"
                                    "n = int(input())\n"
                                    "print(\"Привет,\", name)\n"
                                    "print(n * 2)\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Какой тип возвращает `input()`?",
                                       ["int", "str", "float"], 1,
                                       "`input` всегда возвращает строку."),
                                    sa("Какой функцией строку `'5'` превратить в число?",
                                       ["int", "int()"]),
                                ],
                            },
                            {
                                "title": "Числа и арифметика",
                                "content_md": (
                                    "# Числа и арифметика\n\n"
                                    "Python умеет `+ - * /`, а ещё целочисленное деление `//`, "
                                    "остаток `%` и возведение в степень `**`.\n\n"
                                    "```python\n"
                                    "print(7 // 2)   # 3\n"
                                    "print(7 % 2)    # 1\n"
                                    "print(2 ** 10)  # 1024\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет `print(7 // 2)`?", ["3"]),
                                    co("Что выведет `print(7 % 3)`?", ["1"]),
                                    sc("Что означает оператор `**`?",
                                       ["умножение", "степень", "деление"], 1),
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Условия и циклы",
                        "lessons": [
                            {
                                "title": "Условия if / else",
                                "content_md": (
                                    "# Условия\n\n"
                                    "`if` выполняет код, если условие истинно. `elif` и `else` — "
                                    "другие ветки. Блоки задаются отступами.\n\n"
                                    "```python\n"
                                    "n = int(input())\n"
                                    "if n > 0:\n"
                                    "    print(\"положительное\")\n"
                                    "elif n < 0:\n"
                                    "    print(\"отрицательное\")\n"
                                    "else:\n"
                                    "    print(\"ноль\")\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Какая ветка выполнится, если все условия ложны?",
                                       ["if", "elif", "else"], 2),
                                    sc("Чем задаются блоки кода в Python?",
                                       ["скобками {}", "отступами", "точкой с запятой"], 1),
                                ],
                            },
                            {
                                "title": "Циклы while и for",
                                "content_md": (
                                    "# Циклы\n\n"
                                    "`for` перебирает элементы, `range(n)` даёт числа `0..n-1`. "
                                    "`while` повторяет, пока условие истинно.\n\n"
                                    "```python\n"
                                    "s = 0\n"
                                    "for i in range(1, 5):\n"
                                    "    s += i\n"
                                    "print(s)  # 1+2+3+4 = 10\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет код:\n```python\ns=0\nfor i in "
                                       "range(1,5):\n    s+=i\nprint(s)\n```", ["10"]),
                                    sc("Сколько чисел даёт `range(5)`?",
                                       ["4", "5", "6"], 1, "0,1,2,3,4 — пять чисел."),
                                    sa("Какое ключевое слово досрочно прерывает цикл?",
                                       ["break"]),
                                ],
                            },
                            {
                                "title": "Строки",
                                "content_md": (
                                    "# Строки\n\n"
                                    "Строку можно индексировать (`s[0]`), брать срезы "
                                    "(`s[1:3]`), узнавать длину (`len(s)`) и собирать через "
                                    "f-строки.\n\n"
                                    "```python\n"
                                    "s = \"Python\"\n"
                                    "print(s[0], s[-1])   # P n\n"
                                    "print(len(s))        # 6\n"
                                    "print(f\"Язык: {s}\")\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет `print(len('abc'))`?", ["3"]),
                                    sc("Что вернёт `'hello'[0]`?",
                                       ["'h'", "'o'", "'hello'"], 0),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "name": LevelName.intermediate,
                "modules": [
                    {
                        "title": "Коллекции",
                        "lessons": [
                            {
                                "title": "Списки",
                                "content_md": (
                                    "# Списки\n\n"
                                    "Список хранит упорядоченный набор значений. Добавляют "
                                    "`append`, перебирают циклом, длину дают `len`.\n\n"
                                    "```python\n"
                                    "a = [3, 1, 2]\n"
                                    "a.append(5)\n"
                                    "a.sort()\n"
                                    "print(a)        # [1, 2, 3, 5]\n"
                                    "print(sum(a))   # 11\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет `print(sum([1,2,3]))`?", ["6"]),
                                    sc("Каким методом добавить элемент в конец списка?",
                                       ["add", "append", "push"], 1),
                                    co("Что выведет:\n```python\na=[3,1,2]\na.sort()\n"
                                       "print(a)\n```", ["[1, 2, 3]"]),
                                ],
                            },
                            {
                                "title": "Словари и множества",
                                "content_md": (
                                    "# Словари и множества\n\n"
                                    "Словарь хранит пары «ключ → значение». Множество — набор "
                                    "уникальных элементов.\n\n"
                                    "```python\n"
                                    "d = {\"a\": 1, \"b\": 2}\n"
                                    "print(d[\"a\"])         # 1\n"
                                    "s = set([1, 1, 2, 3])\n"
                                    "print(len(s))         # 3\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Сколько элементов в `set([1,1,2,3])`?", ["3"]),
                                    sc("Что хранит словарь?",
                                       ["только числа", "пары ключ-значение",
                                        "уникальные значения"], 1),
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Функции и алгоритмы",
                        "lessons": [
                            {
                                "title": "Функции",
                                "content_md": (
                                    "# Функции\n\n"
                                    "Функция — переиспользуемый блок кода. Объявляют через "
                                    "`def`, результат возвращают `return`.\n\n"
                                    "```python\n"
                                    "def square(x):\n"
                                    "    return x * x\n\n"
                                    "print(square(5))   # 25\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет `print(square(4))` для функции из урока?",
                                       ["16"]),
                                    sc("Какое слово возвращает результат из функции?",
                                       ["return", "yield", "give"], 0),
                                ],
                            },
                            {
                                "title": "Сортировка и lambda",
                                "content_md": (
                                    "# Сортировка\n\n"
                                    "`sorted` возвращает новый отсортированный список. Параметр "
                                    "`key` задаёт правило, часто через `lambda`.\n\n"
                                    "```python\n"
                                    "words = [\"bb\", \"a\", \"ccc\"]\n"
                                    "print(sorted(words, key=len))   # ['a', 'bb', 'ccc']\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Что делает `sorted`?",
                                       ["меняет исходный список",
                                        "возвращает новый отсортированный список",
                                        "удаляет дубликаты"], 1),
                                    sa("Каким словом создают анонимную функцию?", ["lambda"]),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "name": LevelName.advanced,
                "modules": [
                    {
                        "title": "Алгоритмы",
                        "lessons": [
                            {
                                "title": "Рекурсия",
                                "content_md": (
                                    "# Рекурсия\n\n"
                                    "Рекурсивная функция вызывает саму себя. Обязателен "
                                    "базовый случай, иначе вычисление не остановится.\n\n"
                                    "```python\n"
                                    "def fact(n):\n"
                                    "    if n <= 1:\n"
                                    "        return 1\n"
                                    "    return n * fact(n - 1)\n\n"
                                    "print(fact(5))   # 120\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет `print(fact(4))`?", ["24"]),
                                    sc("Что обязательно нужно в рекурсии?",
                                       ["цикл", "базовый случай", "массив"], 1),
                                ],
                            },
                            {
                                "title": "Бинарный поиск",
                                "content_md": (
                                    "# Бинарный поиск\n\n"
                                    "В **отсортированном** массиве элемент ищут, деля отрезок "
                                    "пополам на каждом шаге. Это `O(log n)`.\n\n"
                                    "```python\n"
                                    "def bsearch(a, x):\n"
                                    "    lo, hi = 0, len(a) - 1\n"
                                    "    while lo <= hi:\n"
                                    "        mid = (lo + hi) // 2\n"
                                    "        if a[mid] == x:\n"
                                    "            return mid\n"
                                    "        if a[mid] < x:\n"
                                    "            lo = mid + 1\n"
                                    "        else:\n"
                                    "            hi = mid - 1\n"
                                    "    return -1\n\n"
                                    "print(bsearch([1,3,5,7,9], 7))  # 3\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Какая сложность у бинарного поиска?",
                                       ["O(n)", "O(log n)", "O(n^2)"], 1),
                                    sc("Что требуется для бинарного поиска?",
                                       ["отсортированный массив", "любой массив",
                                        "множество"], 0),
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },
    {
        "title": "C++ с нуля",
        "language": CourseLanguage.cpp,
        "description": "Синтаксис C++, ввод-вывод, контейнеры STL и классические "
                       "алгоритмы для олимпиад.",
        "levels": [
            {
                "name": LevelName.beginner,
                "modules": [
                    {
                        "title": "Основы C++",
                        "lessons": [
                            {
                                "title": "Первая программа",
                                "content_md": (
                                    "# Первая программа на C++\n\n"
                                    "Программа начинается с функции `main`. Вывод — через "
                                    "`std::cout` и оператор `<<`.\n\n"
                                    "```cpp\n"
                                    "#include <iostream>\n"
                                    "using namespace std;\n\n"
                                    "int main() {\n"
                                    "    cout << \"Привет, мир!\" << endl;\n"
                                    "    return 0;\n"
                                    "}\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("С какой функции начинается программа на C++?",
                                       ["start", "main", "begin"], 1),
                                    sc("Каким оператором выводят в `cout`?",
                                       ["<<", ">>", "->"], 0),
                                ],
                            },
                            {
                                "title": "Переменные и ввод",
                                "content_md": (
                                    "# Переменные и ввод\n\n"
                                    "Тип указывают явно: `int`, `double`, `string`. "
                                    "Ввод — через `std::cin`.\n\n"
                                    "```cpp\n"
                                    "#include <iostream>\n"
                                    "using namespace std;\n\n"
                                    "int main() {\n"
                                    "    int a, b;\n"
                                    "    cin >> a >> b;\n"
                                    "    cout << a + b << endl;\n"
                                    "}\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Каким потоком читают ввод?",
                                       ["cout", "cin", "cerr"], 1),
                                    sa("Какой тип используют для целых чисел в C++?", ["int"]),
                                ],
                            },
                            {
                                "title": "Условия",
                                "content_md": (
                                    "# Условия\n\n"
                                    "`if / else` работают привычно; сравнение — `==`, `<`, "
                                    "`>`. Равенство проверяют двойным `==`.\n\n"
                                    "```cpp\n"
                                    "int n; cin >> n;\n"
                                    "if (n % 2 == 0) cout << \"even\";\n"
                                    "else cout << \"odd\";\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Ввод `4` → что выведет пример из урока?", ["even"]),
                                    sc("Как проверить равенство в C++?",
                                       ["=", "==", "equals"], 1),
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Циклы",
                        "lessons": [
                            {
                                "title": "Циклы for и while",
                                "content_md": (
                                    "# Циклы\n\n"
                                    "`for` со счётчиком и `while` повторяют действия.\n\n"
                                    "```cpp\n"
                                    "int s = 0;\n"
                                    "for (int i = 1; i <= 4; i++) s += i;\n"
                                    "cout << s;   // 10\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет пример из урока?", ["10"]),
                                    sc("Сколько раз выполнится `for (int i=0;i<5;i++)`?",
                                       ["4", "5", "6"], 1),
                                    sa("Какое слово прерывает цикл досрочно?", ["break"]),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "name": LevelName.intermediate,
                "modules": [
                    {
                        "title": "Контейнеры STL",
                        "lessons": [
                            {
                                "title": "vector",
                                "content_md": (
                                    "# Вектор\n\n"
                                    "`vector` — динамический массив из STL. Добавляют "
                                    "`push_back`, размер даёт `size()`.\n\n"
                                    "```cpp\n"
                                    "#include <vector>\n"
                                    "vector<int> a = {3, 1, 2};\n"
                                    "a.push_back(5);\n"
                                    "cout << a.size();   // 4\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Каким методом добавить элемент в `vector`?",
                                       ["add", "push_back", "append"], 1),
                                    co("Размер вектора `{3,1,2}` после `push_back(5)`?", ["4"]),
                                ],
                            },
                            {
                                "title": "string",
                                "content_md": (
                                    "# Строки\n\n"
                                    "`string` хранит текст; длину дают `size()`/`length()`, "
                                    "доступ по индексу — `s[i]`.\n\n"
                                    "```cpp\n"
                                    "#include <string>\n"
                                    "string s = \"Code\";\n"
                                    "cout << s.size() << \" \" << s[0];  // 4 C\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет `s.size()` для `\"Code\"`?", ["4"]),
                                    sc("Как получить первый символ строки `s`?",
                                       ["s[0]", "s(0)", "s.first"], 0),
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Функции",
                        "lessons": [
                            {
                                "title": "Функции и ссылки",
                                "content_md": (
                                    "# Функции\n\n"
                                    "У функции есть тип возвращаемого значения и параметры. "
                                    "Ссылка `&` позволяет менять переданный аргумент.\n\n"
                                    "```cpp\n"
                                    "int square(int x) { return x * x; }\n"
                                    "cout << square(6);   // 36\n"
                                    "```"
                                ),
                                "quiz": [
                                    co("Что выведет `square(6)`?", ["36"]),
                                    sc("Что задаёт `&` у параметра функции?",
                                       ["копию", "ссылку", "указатель на массив"], 1),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "name": LevelName.advanced,
                "modules": [
                    {
                        "title": "Алгоритмы и STL",
                        "lessons": [
                            {
                                "title": "sort и жадные алгоритмы",
                                "content_md": (
                                    "# Сортировка\n\n"
                                    "`std::sort` сортирует диапазон за `O(n log n)`. Часто это "
                                    "первый шаг жадных решений.\n\n"
                                    "```cpp\n"
                                    "#include <algorithm>\n"
                                    "vector<int> a = {5, 2, 4, 1};\n"
                                    "sort(a.begin(), a.end());\n"
                                    "// 1 2 4 5\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Какая сложность у `std::sort`?",
                                       ["O(n)", "O(n log n)", "O(n^2)"], 1),
                                    sc("Что передают в `sort`?",
                                       ["begin и end", "только размер", "индекс"], 0),
                                ],
                            },
                            {
                                "title": "Бинарный поиск",
                                "content_md": (
                                    "# Бинарный поиск\n\n"
                                    "В отсортированном массиве `binary_search` проверяет "
                                    "наличие элемента за `O(log n)`.\n\n"
                                    "```cpp\n"
                                    "vector<int> a = {1, 3, 5, 7};\n"
                                    "bool ok = binary_search(a.begin(), a.end(), 5);  // true\n"
                                    "```"
                                ),
                                "quiz": [
                                    sc("Что нужно для бинарного поиска?",
                                       ["отсортированный массив", "любой массив", "стек"], 0),
                                    sc("Сложность бинарного поиска?",
                                       ["O(log n)", "O(n)", "O(1)"], 0),
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },
]


# --- Задачи (авторские, проверяются в серверном sandbox) ---------------------

PROBLEMS = [
    {
        "title": "A + B", "rating": 800, "tags": ["math", "implementation"],
        "statement_md": "Даны два целых числа *a* и *b*. Выведите их сумму.",
        "tests": [("2 3\n", "5\n", True), ("10 20\n", "30\n", True),
                  ("-5 5\n", "0\n", False), ("1000000 1\n", "1000001\n", False)],
    },
    {
        "title": "Площадь прямоугольника", "rating": 800, "tags": ["math", "implementation"],
        "statement_md": "Даны стороны прямоугольника *a* и *b*. Выведите его площадь.",
        "tests": [("3 4\n", "12\n", True), ("5 5\n", "25\n", False),
                  ("1 100\n", "100\n", False)],
    },
    {
        "title": "Максимум из двух", "rating": 800, "tags": ["implementation"],
        "statement_md": "Даны два числа. Выведите большее из них.",
        "tests": [("3 7\n", "7\n", True), ("10 2\n", "10\n", False),
                  ("4 4\n", "4\n", False)],
    },
    {
        "title": "Чётное число", "rating": 800, "tags": ["implementation"],
        "statement_md": "Дано целое число *n*. Выведите `YES`, если оно чётное, иначе `NO`.",
        "tests": [("4\n", "YES\n", True), ("7\n", "NO\n", False), ("0\n", "YES\n", False)],
    },
    {
        "title": "Сумма до N", "rating": 900, "tags": ["math"],
        "statement_md": "Дано число *n*. Выведите сумму `1 + 2 + ... + n`.",
        "tests": [("5\n", "15\n", True), ("1\n", "1\n", False), ("100\n", "5050\n", False)],
    },
    {
        "title": "Сумма цифр числа", "rating": 900, "tags": ["implementation", "math"],
        "statement_md": "Дано натуральное число *n*. Выведите сумму его цифр.",
        "tests": [("123\n", "6\n", True), ("1000\n", "1\n", False), ("99\n", "18\n", False)],
    },
    {
        "title": "Максимум массива", "rating": 900, "tags": ["implementation"],
        "statement_md": "В первой строке число *n*, во второй — *n* целых чисел. "
                        "Выведите максимальное.",
        "tests": [("3\n1 5 3\n", "5\n", True), ("1\n42\n", "42\n", False),
                  ("5\n-1 -2 -3 -4 -5\n", "-1\n", False)],
    },
    {
        "title": "Факториал", "rating": 1000, "tags": ["math"],
        "statement_md": "Дано число *n* (0 ≤ n ≤ 12). Выведите *n*! (факториал).",
        "tests": [("3\n", "6\n", True), ("5\n", "120\n", False),
                  ("0\n", "1\n", False), ("1\n", "1\n", False)],
    },
    {
        "title": "Разворот строки", "rating": 1000, "tags": ["strings"],
        "statement_md": "Дана строка. Выведите её символы в обратном порядке.",
        "tests": [("hello\n", "olleh\n", True), ("abc\n", "cba\n", False),
                  ("a\n", "a\n", False)],
    },
    {
        "title": "Палиндром", "rating": 1100, "tags": ["strings", "implementation"],
        "statement_md": "Дана строка. Выведите `YES`, если она читается одинаково в обе "
                        "стороны, иначе `NO`.",
        "tests": [("level\n", "YES\n", True), ("hello\n", "NO\n", False),
                  ("a\n", "YES\n", False)],
    },
    {
        "title": "НОД", "rating": 1100, "tags": ["math", "number theory"],
        "statement_md": "Даны два натуральных числа *a* и *b*. Выведите их наибольший "
                        "общий делитель.",
        "tests": [("12 18\n", "6\n", True), ("7 13\n", "1\n", False),
                  ("100 75\n", "25\n", False)],
    },
    {
        "title": "Количество делителей", "rating": 1200, "tags": ["math"],
        "statement_md": "Дано число *n*. Выведите количество его натуральных делителей.",
        "tests": [("6\n", "4\n", True), ("1\n", "1\n", False), ("12\n", "6\n", False)],
    },
]


# --- Экзамены на переход между уровнями --------------------------------------
# theory: (course_title, level_name, module_title, num_questions)

EXAMS = [
    {
        "title": "Экзамен: Python Beginner → Intermediate",
        "from": ("Python с нуля", LevelName.beginner),
        "target": ("Python с нуля", LevelName.intermediate),
        "duration": 3600, "threshold": 0.7,
        "practical": ["A + B", "Сумма до N", "Чётное число"],
        "theory": [("Python с нуля", LevelName.beginner, "Основы", 3),
                   ("Python с нуля", LevelName.beginner, "Условия и циклы", 2)],
    },
    {
        "title": "Экзамен: Python Intermediate → Advanced",
        "from": ("Python с нуля", LevelName.intermediate),
        "target": ("Python с нуля", LevelName.advanced),
        "duration": 4200, "threshold": 0.7,
        "practical": ["Максимум массива", "Разворот строки", "НОД"],
        "theory": [("Python с нуля", LevelName.intermediate, "Коллекции", 3),
                   ("Python с нуля", LevelName.intermediate, "Функции и алгоритмы", 2)],
    },
    {
        "title": "Экзамен: C++ Beginner → Intermediate",
        "from": ("C++ с нуля", LevelName.beginner),
        "target": ("C++ с нуля", LevelName.intermediate),
        "duration": 3600, "threshold": 0.7,
        "practical": ["Площадь прямоугольника", "Максимум из двух", "Сумма цифр числа"],
        "theory": [("C++ с нуля", LevelName.beginner, "Основы C++", 3),
                   ("C++ с нуля", LevelName.beginner, "Циклы", 2)],
    },
]


def seed(db: Session) -> bool:
    """Возвращает True, если данные созданы; False — если уже были."""
    if db.scalar(select(User).where(User.email == TEACHER_EMAIL)) is not None:
        return False

    teacher = User(
        email=TEACHER_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
        role=UserRole.teacher, email_verified=True,
    )
    student = User(
        email=STUDENT_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
        role=UserRole.student, email_verified=True,
    )
    db.add_all([teacher, student])
    db.flush()
    db.add(TeacherProfile(user_id=teacher.id, display_name="Демо-учитель",
                          bio="Веду курсы Python и C++ на onproger."))
    db.add(StudentProfile(user_id=student.id, codeforces_handle="tourist",
                          streak_count=5, last_active_date=date.today()))

    levels_by_key: dict[tuple, Level] = {}
    modules_by_key: dict[tuple, Module] = {}
    module_lessons: dict[tuple, list[Lesson]] = {}

    # Курсы → уровни → модули → уроки + мини-квизы
    for course_data in CURRICULUM:
        course = Course(title=course_data["title"], language=course_data["language"],
                        description=course_data["description"])
        db.add(course)
        db.flush()
        for li, lvl_data in enumerate(course_data["levels"], 1):
            level = Level(course_id=course.id, name=lvl_data["name"], order_index=li)
            db.add(level)
            db.flush()
            levels_by_key[(course_data["title"], lvl_data["name"])] = level
            for mi, mod_data in enumerate(lvl_data["modules"], 1):
                module = Module(level_id=level.id, title=mod_data["title"], order_index=mi)
                db.add(module)
                db.flush()
                mkey = (course_data["title"], lvl_data["name"], mod_data["title"])
                modules_by_key[mkey] = module
                module_lessons[mkey] = []
                for lsi, lesson_data in enumerate(mod_data["lessons"], 1):
                    lesson = Lesson(
                        module_id=module.id, title=lesson_data["title"],
                        content_md=lesson_data["content_md"], order_index=lsi,
                        created_by=teacher.id,
                    )
                    db.add(lesson)
                    db.flush()
                    module_lessons[mkey].append(lesson)
                    for qi, qd in enumerate(lesson_data.get("quiz", [])):
                        q = Question(
                            module_id=module.id, type=qd["type"], prompt_md=qd["prompt_md"],
                            options=qd["options"], correct_answer=qd["correct_answer"],
                            explanation_md=qd["explanation_md"],
                        )
                        db.add(q)
                        db.flush()
                        db.add(LessonQuestion(lesson_id=lesson.id, question_id=q.id,
                                              order_index=qi))

    # Задачи + тесты
    problems_by_title: dict[str, Problem] = {}
    for pd in PROBLEMS:
        problem = Problem(
            source=ProblemSource.authored, title=pd["title"],
            statement_md=pd["statement_md"], rating=pd["rating"], created_by=teacher.id,
        )
        for tag in pd["tags"]:
            problem.tags.append(ProblemTag(tag=tag))
        db.add(problem)
        db.flush()
        for oi, (inp, out, sample) in enumerate(pd["tests"]):
            db.add(ProblemTest(problem_id=problem.id, input=inp, expected_output=out,
                               is_sample=sample, order_index=oi))
        problems_by_title[pd["title"]] = problem

    # Экзамены (опубликованы)
    for ed in EXAMS:
        exam = Exam(
            title=ed["title"],
            level_from_id=levels_by_key[ed["from"]].id,
            target_level_id=levels_by_key[ed["target"]].id,
            duration_seconds=ed["duration"], pass_threshold=ed["threshold"],
            created_by=teacher.id, is_published=True,
        )
        db.add(exam)
        db.flush()
        for oi, ptitle in enumerate(ed["practical"], 1):
            db.add(ExamPracticalProblem(exam_id=exam.id, problem_id=problems_by_title[ptitle].id,
                                        order_index=oi, max_score=100))
        for course_title, level_name, module_title, num in ed["theory"]:
            module = modules_by_key[(course_title, level_name, module_title)]
            db.add(ExamTheoryConfig(exam_id=exam.id, module_id=module.id, num_questions=num))

    # Демо-прогресс ученика: открытые уровни, решённые задачи, пройденные уроки
    today = datetime.now(timezone.utc)
    for (course_title, level_name), level in levels_by_key.items():
        if level_name == LevelName.beginner:
            db.add(StudentLevelAccess(student_id=student.id, level_id=level.id,
                                      unlocked=True, exam_passed=False))

    solved_titles = ["A + B", "Площадь прямоугольника", "Чётное число",
                     "Сумма до N", "Максимум из двух"]
    for i, title in enumerate(solved_titles):
        db.add(StudentSolvedProblem(
            student_id=student.id, problem_id=problems_by_title[title].id,
            source=SolvedSource.local,
            solved_at=today - timedelta(days=len(solved_titles) - 1 - i),
        ))

    done_lessons = module_lessons[("Python с нуля", LevelName.beginner, "Основы")]
    for lesson in done_lessons:
        db.add(LessonProgress(student_id=student.id, lesson_id=lesson.id,
                              status=ProgressStatus.completed, quiz_score=100,
                              completed_at=today))

    db.commit()
    return True


def main() -> None:
    db = SessionLocal()
    try:
        created = seed(db)
        print("Демо-данные созданы." if created else "Демо-данные уже существуют.")
        if created:
            print(f"Учитель: {TEACHER_EMAIL} / {DEMO_PASSWORD}")
            print(f"Ученик:  {STUDENT_EMAIL} / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
