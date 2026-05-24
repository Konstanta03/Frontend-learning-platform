import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.sqlite3')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'zip', 'txt'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'frontend-learning-secret-key')
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

MODULES = [
    {
        'title': 'Вступ до front-end розробки',
        'short': 'Що таке front-end, сайт, браузер та як працює клієнтська частина.',
        'theory': [
            'Front-end розробка охоплює все, що користувач бачить у браузері: структуру сторінки, її оформлення та інтерактивну поведінку.',
            'Будь-який сайт завантажує HTML-документ, таблицю стилів CSS і JavaScript-код для взаємодії.',
            'Браузер читає HTML як структуру, CSS як правила оформлення, а JavaScript як логіку взаємодії.'
        ],
        'example': 'Приклад: сторінка ліцею відображає текст і меню завдяки HTML, кольори та шрифти завдяки CSS, а інтерактивні форми працюють через JavaScript.'
    },
    {
        'title': 'HTML: структура вебсторінки',
        'short': 'Теги, семантика, заголовки, абзаци, списки, посилання, зображення.',
        'theory': [
            'HTML визначає логічну структуру сторінки. Основні елементи — заголовки, абзаци, списки, таблиці та посилання.',
            'Семантичні теги допомагають правильно організувати контент і підвищують доступність сайту.',
            'Грамотна HTML-розмітка полегшує підтримку та подальший розвиток вебпроєкту.'
        ],
        'example': 'Приклад: сторінка «Про школу» може містити заголовок h1, кілька абзаців, список гуртків та посилання на розклад.'
    },
    {
        'title': 'HTML-форми',
        'short': 'Поля введення, кнопки, прапорці, списки, надсилання даних.',
        'theory': [
            'Форми дозволяють користувачу взаємодіяти із сайтом: вводити текст, обирати варіанти, надсилати повідомлення.',
            'Основні елементи форм — input, textarea, select, option, label та button.',
            'Для кожного поля важливо правильно вказувати атрибути name, type, placeholder та required.'
        ],
        'example': 'Приклад: форма реєстрації може містити поля для імені, пошти, пароля та кнопку «Зареєструватися».'
    },
    {
        'title': 'CSS: оформлення сторінки',
        'short': 'Селектори, кольори, фони, відступи, шрифти та оформлення блоків.',
        'theory': [
            'CSS задає зовнішній вигляд сторінки: кольори, шрифти, рамки, тіні, відступи та розташування елементів.',
            'Селектори дозволяють застосовувати стилі до тегів, класів та ідентифікаторів.',
            'Для якісного дизайну важливо зберігати єдину палітру, читабельну типографіку та логічну ієрархію блоків.'
        ],
        'example': 'Приклад: кнопка може мати синій фон, білий текст, заокруглені краї та тінь при наведенні.'
    },
    {
        'title': 'Flexbox і Grid',
        'short': 'Сучасні способи розміщення елементів на сторінці.',
        'theory': [
            'Flexbox зручний для розміщення елементів в одному напрямку — по горизонталі або вертикалі.',
            'CSS Grid підходить для складніших макетів, де потрібно працювати одночасно з рядками та стовпцями.',
            'Обидва підходи допомагають створювати адаптивні та акуратні інтерфейси без зайвого коду.'
        ],
        'example': 'Приклад: картки курсів на сторінці можна вирівняти через Flexbox, а складну сітку каталогу — через CSS Grid.'
    },
    {
        'title': 'Адаптивний дизайн',
        'short': 'Як зробити сайт зручним на телефоні, планшеті та комп’ютері.',
        'theory': [
            'Адаптивний дизайн означає, що сайт підлаштовується під різні розміри екранів.',
            'Для цього використовують медіазапити, гнучкі блоки та відносні одиниці вимірювання.',
            'Хороший адаптивний сайт зберігає читабельність тексту, доступність кнопок і логіку навігації.'
        ],
        'example': 'Приклад: на комп’ютері меню відображається горизонтально, а на телефоні перетворюється на кнопку-бургер.'
    },
    {
        'title': 'Основи JavaScript',
        'short': 'Змінні, типи даних, умови, цикли, функції.',
        'theory': [
            'JavaScript додає сторінці логіку та поведінку: реакцію на кліки, перевірку форм, зміну тексту й стилів.',
            'Основні елементи мови — змінні, умови, цикли, функції та об’єкти.',
            'Розуміння базової логіки JavaScript є ключем до створення інтерактивних вебінтерфейсів.'
        ],
        'example': 'Приклад: при натисканні кнопки «Показати відповідь» JavaScript відкриває прихований блок із поясненням.'
    },
    {
        'title': 'DOM і події',
        'short': 'Як JavaScript працює з елементами сторінки.',
        'theory': [
            'DOM — це об’єктна модель документа, тобто подання HTML-сторінки у вигляді дерева елементів.',
            'JavaScript може знаходити елементи DOM, змінювати їх текст, стилі, атрибути та обробляти події.',
            'Події — це дії користувача або системи: клік, введення тексту, наведення курсора, завантаження сторінки.'
        ],
        'example': 'Приклад: після кліку на кнопку можна змінити заголовок сторінки або показати модальне вікно.'
    },
    {
        'title': 'Проєктування інтерфейсу',
        'short': 'Принципи UI/UX, візуальна ієрархія, зручність користувача.',
        'theory': [
            'UI — це зовнішній вигляд інтерфейсу, а UX — логіка взаємодії та зручність користувача.',
            'Добрий інтерфейс має зрозумілу структуру, помітні кнопки дії та достатню контрастність.',
            'При проєктуванні важливо враховувати шлях користувача: що він бачить першим і як виконує потрібну дію.'
        ],
        'example': 'Приклад: на сторінці курсу кнопка «Почати тест» має бути помітною, а блок із прогресом — доступним без зайвих переходів.'
    },
    {
        'title': 'Публікація та перевірка сайту',
        'short': 'Підготовка проєкту, тестування і розміщення.',
        'theory': [
            'Після завершення розробки сайт потрібно перевірити: валідність коду, адаптивність і відсутність помилок у посиланнях та формах.',
            'Перед публікацією варто оптимізувати зображення, прибрати зайвий код і перевірити роботу на різних пристроях.',
            'Публікувати сайт можна на безкоштовних платформах або власному сервері.'
        ],
        'example': 'Приклад: перед здачею проєкту учень перевіряє, чи всі кнопки працюють і чи немає помилок у тексті.'
    }
]

PRACTICALS = [
    ('Створити HTML-сторінку з інформацією про себе', 'Підготуйте сторінку з заголовком, абзацом, списком інтересів та посиланням на улюблений сайт.'),
    ('Додати зображення та посилання', 'Створіть сторінку з двома зображеннями, підписами і кнопкою переходу на іншу сторінку.'),
    ('Створити форму зворотного зв’язку', 'Розробіть форму з полями ім’я, електронна пошта, повідомлення і кнопкою відправлення.'),
    ('Оформити сторінку за допомогою CSS', 'Додайте кольори, фон, шрифти, відступи і стилізовану кнопку.'),
    ('Створити картку курсу через Flexbox', 'Побудуйте картку з назвою, описом, кнопкою та вирівнюванням елементів через Flexbox.'),
    ('Зробити адаптивний блок', 'Підготуйте блок, який коректно відображається на телефоні та комп’ютері.'),
    ('Створити JavaScript-кнопку зміни тексту', 'Напишіть кнопку, яка змінює текст заголовка або показує повідомлення.'),
    ('Реалізувати міні-калькулятор', 'Створіть форму для введення двох чисел і кнопку обчислення суми.'),
    ('Підготувати міні-проєкт навчального сайту', 'Створіть невеликий сайт з декількома блоками, меню та базовою взаємодією.')
]

def make_test(title, questions):
    return {'title': title, 'questions': questions}

TESTS = [
    make_test('Тест 1. Вступ до front-end', [
        ('Що таке front-end?', 'Клієнтська частина сайту|Серверна частина сайту|База даних|Операційна система', '0'),
        ('Що відображається в браузері для користувача?', 'Інтерфейс сайту|Серверні логи|SQL-запити|Конфігурація хостингу', '0'),
        ('Який файл зазвичай відкриває браузер?', 'index.html|server.py|config.json|database.sql', '0'),
        ('Що описує CSS?', 'Оформлення сторінки|Серверну логіку|Роботу бази даних|Паролі користувачів', '0'),
        ('Для чого використовується JavaScript?', 'Для інтерактивної поведінки сторінки|Лише для кольорів|Лише для заголовків|Для друку', '0'),
        ('Яка технологія відповідає за структуру сторінки?', 'HTML|CSS|Photoshop|Excel', '0'),
        ('Що означає UI?', 'User Interface|Universal Internet|User Index|Uniform Input', '0'),
        ('Яка роль браузера?', 'Зчитує та відображає вебсторінку|Пише код|Зберігає оцінки|Створює БД', '0'),
        ('Що таке вебсайт?', 'Набір взаємопов’язаних вебсторінок|Одна картинка|Файл Word|Тільки мобільний застосунок', '0'),
        ('Що вивчає front-end розробник?', 'Створення інтерфейсів сайтів|Ремонт ПК|Монтаж відео|Друк документів', '0')
    ]),
    make_test('Тест 2. HTML-структура', [
        ('Що означає HTML?', 'HyperText Markup Language|Home Tool Markup Language|Hyperlinks and Text Main Language|High Text Machine Language', '0'),
        ('Який тег задає головний заголовок?', '<h1>|<p>|<title>|<div>', '0'),
        ('Який тег для абзацу?', '<p>|<a>|<span>|<section>', '0'),
        ('Який тег створює посилання?', '<a>|<img>|<ul>|<li>', '0'),
        ('Який атрибут потрібен для адреси зображення?', 'src|href|alt|class', '0'),
        ('Який тег для ненумерованого списку?', '<ul>|<ol>|<li>|<list>', '0'),
        ('Що розміщується у <head>?', 'Метадані та підключення ресурсів|Видимий текст|Тільки зображення|Форми', '0'),
        ('Який тег часто використовують як контейнер?', '<div>|<img>|<br>|<hr>', '0'),
        ('Який тег для підвалу сайту?', '<footer>|<bottom>|<section>|<aside>', '0'),
        ('Що покращує структуру документа?', 'Семантичні теги|Випадкові класи|Зображення|Порожні теги', '0')
    ]),
    make_test('Тест 3. HTML-форми', [
        ('Який тег створює форму?', '<form>|<input>|<label>|<fieldset>', '0'),
        ('Який тип input для електронної пошти?', 'email|mailbox|text-email|login', '0'),
        ('Який атрибут робить поле обов’язковим?', 'required|must|need|validate', '0'),
        ('Який тег для багаторядкового введення?', '<textarea>|<input>|<select>|<option>', '0'),
        ('Який елемент створює список вибору?', '<select>|<input>|<button>|<datalist>', '0'),
        ('Для чого використовується label?', 'Підписує поле форми|Створює кнопку|Додає зображення|Вставляє таблицю', '0'),
        ('Який тип input для пароля?', 'password|secret|lock|hidden-text', '0'),
        ('Який тип input для прапорця?', 'checkbox|radio|toggle|switch', '0'),
        ('Що робить кнопка submit?', 'Надсилає форму|Очищає сайт|Закриває браузер|Перефарбовує текст', '0'),
        ('Що варто перевіряти у формах?', 'Коректність введених даних|Лише фон|Тільки файл|Тільки дату', '0')
    ]),
    make_test('Тест 4. CSS-оформлення', [
        ('Що означає CSS?', 'Cascading Style Sheets|Creative Site System|Computer Style Syntax|Colorful Site Sheets', '0'),
        ('Яка властивість задає колір тексту?', 'color|font-color|text-color|foreground', '0'),
        ('Яка властивість задає фон?', 'background|fill|bg-color|canvas', '0'),
        ('Яка властивість задає зовнішні відступи?', 'margin|padding|border|spacing', '0'),
        ('Яка властивість задає внутрішні відступи?', 'padding|margin|indent|inside-space', '0'),
        ('Що таке клас у CSS?', 'Спосіб стилізувати групу елементів|Браузер|Мова|Формат зображення', '0'),
        ('Яким символом позначається клас?', '.|#|@|*', '0'),
        ('Яка властивість змінює шрифт?', 'font-family|text-style|font-set|family-font', '0'),
        ('Яка властивість робить текст жирним?', 'font-weight|text-bold|font-strong|bold-text', '0'),
        ('Для чого потрібен CSS?', 'Для оформлення вебсторінки|Для зберігання файлів|Для серверних запитів|Для друку БД', '0')
    ]),
    make_test('Тест 5. Flexbox і Grid', [
        ('Для чого використовується Flexbox?', 'Для розміщення елементів у ряд або стовпець|Для створення БД|Для форматування PDF|Для шифрування', '0'),
        ('Яка властивість вмикає Flexbox?', 'display: flex|position: flex|layout: flex|float: flex', '0'),
        ('Що робить justify-content?', 'Керує вирівнюванням по головній осі|Змінює колір|Видаляє блок|Створює таблицю', '0'),
        ('Що робить align-items?', 'Вирівнює по поперечній осі|Створює посилання|Додає шрифт|Оновлює сторінку', '0'),
        ('Для чого підходить CSS Grid?', 'Для двовимірних макетів|Лише для тексту|Лише для картинок|Для написання JavaScript', '0'),
        ('Яка властивість задає кількість колонок у Grid?', 'grid-template-columns|grid-columns-count|columns-grid|template-grid', '0'),
        ('Що краще для горизонтального меню?', 'Flexbox|Grid|Тільки таблиця|SVG', '0'),
        ('Що краще для складної сітки?', 'Grid|Flexbox|Тільки float|Тільки border', '0'),
        ('Що дають layout-механізми?', 'Гнучке розміщення блоків|Збереження паролів|Створення серверів|Монтаж відео', '0'),
        ('Що спрощує адаптивний дизайн?', 'Flexbox і Grid|Word і Excel|Paint|PDF', '0')
    ]),
    make_test('Тест 6. Адаптивний дизайн', [
        ('Що таке адаптивний дизайн?', 'Підлаштування сайту під різні екрани|Лише великий шрифт|Сторінка без стилів|Сайт без зображень', '0'),
        ('Що таке медіазапити?', 'CSS-умови для різних розмірів екрана|HTML-форми|JavaScript-цикли|Формат картинок', '0'),
        ('Яка конструкція використовується для медіазапитів?', '@media|@screen|@resize|@responsive', '0'),
        ('Чому важливо перевіряти сайт на телефоні?', 'Щоб він був зручний на малому екрані|Щоб змінити назву|Щоб видалити CSS|Щоб уникнути JS', '0'),
        ('Які одиниці часто використовують для адаптивності?', '%, rem, vw|Тільки px і cm|Тільки km|Лише секунди', '0'),
        ('Що може змінюватися в адаптивному дизайні?', 'Розташування блоків|Лише назва|Тільки favicon|Лише дата', '0'),
        ('Що таке mobile-first?', 'Підхід, де спочатку проектують під телефон|Сайт тільки для мобільних|Заборона на ПК|Спосіб зберігання паролів', '0'),
        ('Який елемент часто перетворюється у бургер-меню?', 'Навігація|Футер|Картинка|Підзаголовок', '0'),
        ('Що перевіряють при адаптації?', 'Читабельність, кнопки, сітку|Лише колір фону|Тільки довжину URL|Тільки назву файлу', '0'),
        ('Навіщо потрібен viewport у meta?', 'Щоб коректно відображати сайт на мобільних|Щоб змінити пароль|Щоб зберегти зображення|Щоб вимкнути CSS', '0')
    ]),
    make_test('Тест 7. Основи JavaScript', [
        ('Для чого використовується JavaScript?', 'Для логіки та інтерактивності|Тільки для стилів|Тільки для HTML|Для друку документів', '0'),
        ('Як оголосити змінну у сучасному JS?', 'let або const|var only|make|define', '0'),
        ('Що таке функція?', 'Блок коду для виконання дії|Колір тексту|HTML-тег|Режим браузера', '0'),
        ('Що робить if?', 'Перевіряє умову|Малює картинку|Вставляє шрифт|Очищає CSS', '0'),
        ('Що таке масив?', 'Колекція значень|Окремий тег|Зображення|Кнопка', '0'),
        ('Що робить цикл?', 'Повторює дію кілька разів|Змінює фон|Завантажує сервер|Робить текст жирним', '0'),
        ('Який оператор використовується для порівняння?', '===|=|->|=>=>', '0'),
        ('Що таке подія click?', 'Натискання на елемент|Зміна кольору автоматично|Створення HTML|Очищення кешу', '0'),
        ('Що повертає console.log?', 'Виводить дані в консоль|Створює кнопку|Змінює CSS|Видаляє сторінку', '0'),
        ('Чому JS важливий у front-end?', 'Робить сторінку інтерактивною|Замінює браузер|Зберігає журнал|Підміняє HTML', '0')
    ]),
    make_test('Тест 8. DOM і події', [
        ('Що таке DOM?', 'Модель документа у вигляді об’єктів|Мова стилів|База даних|Формат архіву', '0'),
        ('Який метод шукає елемент за id?', 'getElementById|queryAllId|findIdNode|selectElementId', '0'),
        ('Що робить addEventListener?', 'Призначає обробник події|Видаляє CSS|Створює БД|Публікує сайт', '0'),
        ('Яка подія спрацьовує при введенні тексту?', 'input|hover|press|layout', '0'),
        ('Що можна змінити через DOM?', 'Текст, атрибути, стилі|Лише назву файла|Тільки браузер|Тільки пароль Wi-Fi', '0'),
        ('Що робить querySelector?', 'Знаходить перший елемент за CSS-селектором|Друкує таблицю|Архівує сайт|Міняє мову браузера', '0'),
        ('Що таке textContent?', 'Властивість тексту елемента|Колір тексту|Тип файлу|Зовнішній відступ', '0'),
        ('Як приховати блок через JS?', 'Змінити display або клас|Лише видалити HTML вручну|Вимкнути комп’ютер|Змінити favicon', '0'),
        ('Що таке подія submit?', 'Надсилання форми|Зміна картинки|Видалення CSS|Сортування таблиці', '0'),
        ('Чому DOM важливий?', 'Дає JavaScript доступ до сторінки|Замінює HTML|Працює тільки на сервері|Містить паролі', '0')
    ]),
    make_test('Тест 9. Проєктування інтерфейсу', [
        ('Що означає UX?', 'Досвід користувача|Універсальний XML|Розширення браузера|Формат шрифту', '0'),
        ('Що означає UI?', 'Інтерфейс користувача|Управління Інтернетом|Мова серверів|База стилів', '0'),
        ('Що таке візуальна ієрархія?', 'Організація елементів за важливістю|Список файлів|Порядок серверів|Вид шрифту', '0'),
        ('Яка кнопка має бути помітною?', 'Основна дія сторінки|Будь-яка випадкова|Кнопка без тексту|Прихована кнопка', '0'),
        ('Чому важлива контрастність тексту?', 'Для читабельності|Для збереження файлів|Для роботи сервера|Для циклів', '0'),
        ('Що таке wireframe?', 'Чернетка макета інтерфейсу|Готовий сервер|Формат PDF|Скрипт перевірки', '0'),
        ('Що не варто робити в інтерфейсі?', 'Перевантажувати сторінку зайвими блоками|Робити заголовок|Додавати кнопку|Організовувати структуру', '0'),
        ('Що має бути в навігації?', 'Зрозумілі назви розділів|Лише іконки без підказок|Випадкові слова|Тільки один пункт', '0'),
        ('Що покращує UX?', 'Логічний шлях користувача|Занадто багато анімацій|Сховані кнопки|Довгі незрозумілі тексти', '0'),
        ('Який інструмент часто використовують для макетів?', 'Figma|Paint|Блокнот|Калькулятор', '0')
    ])
]


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') != role:
                flash('Недостатньо прав доступу.', 'error')
                return redirect(url_for('dashboard'))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username=?', (username,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        flash('Невірний логін або пароль.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        password_confirm = request.form.get('password_confirm', '')
        full_name = request.form['full_name'].strip()
        school_name = request.form.get('school_name', '').strip()
        about_me = request.form.get('about_me', '').strip()

        if not username or not password or not full_name:
            flash('Заповніть обов’язкові поля.', 'error')
            return render_template('register_teacher.html')

        if password != password_confirm:
            flash('Паролі не збігаються.', 'error')
            return render_template('register_teacher.html')

        if query_db('SELECT id FROM users WHERE username=?', (username,), one=True):
            flash('Такий логін уже існує.', 'error')
            return render_template('register_teacher.html')

        execute_db(
            'INSERT INTO users(username, password_hash, role, full_name, class_name, birth_date, school_name, about_me, teacher_id) VALUES(?,?,?,?,?,?,?,?,?)',
            (username, generate_password_hash(password), 'teacher', full_name, '', '', school_name, about_me, None)
        )
        flash('Обліковий запис вчителя створено. Тепер можна увійти.', 'success')
        return redirect(url_for('login'))

    return render_template('register_teacher.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('teacher_dashboard') if session['role'] == 'teacher' else url_for('student_dashboard'))

@app.route('/student')
@role_required('student')
def student_dashboard():
    user = query_db('SELECT * FROM users WHERE id=?', (session['user_id'],), one=True)
    tests = query_db('SELECT * FROM tests ORDER BY id')
    practicals = query_db('SELECT * FROM practical_tasks ORDER BY id')
    submissions = query_db('SELECT ps.*, pt.title FROM practice_submissions ps JOIN practical_tasks pt ON pt.id=ps.task_id WHERE ps.student_id=? ORDER BY ps.id DESC', (session['user_id'],))
    test_results = query_db('SELECT tr.*, t.title FROM test_results tr JOIN tests t ON t.id=tr.test_id WHERE tr.student_id=? ORDER BY tr.id DESC', (session['user_id'],))
    avg_test = round(sum(r['score_percent'] for r in test_results) / len(test_results), 1) if test_results else 0
    avg_practice = round(sum((r['teacher_score'] or 0) for r in submissions) / len(submissions), 1) if submissions else 0
    return render_template('student_dashboard.html', user=user, tests=tests, practicals=practicals, submissions=submissions, test_results=test_results, avg_test=avg_test, avg_practice=avg_practice, modules=MODULES)

@app.route('/student/profile', methods=['POST'])
@role_required('student')
def update_student_profile():
    execute_db('UPDATE users SET class_name=?, birth_date=?, school_name=?, about_me=? WHERE id=?', (request.form.get('class_name', '').strip(), request.form.get('birth_date', '').strip(), request.form.get('school_name', '').strip(), request.form.get('about_me', '').strip(), session['user_id']))
    flash('Анкету збережено.', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/test/<int:test_id>', methods=['GET', 'POST'])
@role_required('student')
def take_test(test_id):
    test = query_db('SELECT * FROM tests WHERE id=?', (test_id,), one=True)
    if not test:
        flash('Тест не знайдено.', 'error')
        return redirect(url_for('student_dashboard'))
    questions = query_db('SELECT * FROM test_questions WHERE test_id=? ORDER BY id', (test_id,))
    if request.method == 'POST':
        total = len(questions)
        correct = 0
        for q in questions:
            if request.form.get(f'q_{q["id"]}', '') == q['correct_answer']:
                correct += 1
        percent = round((correct / total) * 100, 1) if total else 0
        execute_db('INSERT INTO test_results(student_id, test_id, correct_answers, total_questions, score_percent, created_at) VALUES(?,?,?,?,?,?)', (session['user_id'], test_id, correct, total, percent, datetime.now().isoformat()))
        flash(f'Тест завершено. Результат: {percent}%', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('test_page.html', test=test, questions=questions)

@app.route('/practical/<int:task_id>', methods=['GET', 'POST'])
@role_required('student')
def practical_task(task_id):
    task = query_db('SELECT * FROM practical_tasks WHERE id=?', (task_id,), one=True)
    if not task:
        flash('Завдання не знайдено.', 'error')
        return redirect(url_for('student_dashboard'))
    existing = query_db('SELECT * FROM practice_submissions WHERE task_id=? AND student_id=? ORDER BY id DESC', (task_id, session['user_id']), one=True)
    if request.method == 'POST':
        notes = request.form.get('notes', '').strip()
        uploaded_name = existing['file_name'] if existing else None
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Недозволений тип файлу.', 'error')
                return redirect(url_for('practical_task', task_id=task_id))
            filename = f"{session['user_id']}_{task_id}_{secure_filename(file.filename)}"
            file.save(os.path.join(UPLOAD_DIR, filename))
            uploaded_name = filename
        if existing:
            execute_db('UPDATE practice_submissions SET notes=?, file_name=?, submitted_at=?, status=? WHERE id=?', (notes, uploaded_name, datetime.now().isoformat(), 'submitted', existing['id']))
        else:
            execute_db('INSERT INTO practice_submissions(task_id, student_id, notes, file_name, status, teacher_score, teacher_comment, submitted_at) VALUES(?,?,?,?,?,?,?,?)', (task_id, session['user_id'], notes, uploaded_name, 'submitted', None, '', datetime.now().isoformat()))
        flash('Практичне завдання надіслано вчителю на перевірку.', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('practical_page.html', task=task, existing=existing)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

@app.route('/teacher')
@role_required('teacher')
def teacher_dashboard():
    selected_group = request.args.get('group', '').strip()
    teacher_id = session['user_id']

    groups = query_db("SELECT DISTINCT class_name FROM users WHERE role='student' AND teacher_id=? AND class_name IS NOT NULL AND class_name != '' ORDER BY class_name", (teacher_id,))

    if selected_group:
        students = query_db("SELECT * FROM users WHERE role='student' AND teacher_id=? AND class_name=? ORDER BY full_name", (teacher_id, selected_group))
        results = query_db('SELECT tr.*, u.full_name, u.class_name, t.title FROM test_results tr JOIN users u ON u.id=tr.student_id JOIN tests t ON t.id=tr.test_id WHERE u.teacher_id=? AND u.class_name=? ORDER BY tr.id DESC', (teacher_id, selected_group))
        submissions = query_db('SELECT ps.*, u.full_name, u.class_name, pt.title FROM practice_submissions ps JOIN users u ON u.id=ps.student_id JOIN practical_tasks pt ON pt.id=ps.task_id WHERE u.teacher_id=? AND u.class_name=? ORDER BY ps.id DESC', (teacher_id, selected_group))
    else:
        students = query_db("SELECT * FROM users WHERE role='student' AND teacher_id=? ORDER BY class_name, full_name", (teacher_id,))
        results = query_db('SELECT tr.*, u.full_name, u.class_name, t.title FROM test_results tr JOIN users u ON u.id=tr.student_id JOIN tests t ON t.id=tr.test_id WHERE u.teacher_id=? ORDER BY tr.id DESC', (teacher_id,))
        submissions = query_db('SELECT ps.*, u.full_name, u.class_name, pt.title FROM practice_submissions ps JOIN users u ON u.id=ps.student_id JOIN practical_tasks pt ON pt.id=ps.task_id WHERE u.teacher_id=? ORDER BY ps.id DESC', (teacher_id,))

    return render_template('teacher_dashboard.html', students=students, results=results, submissions=submissions, groups=groups, selected_group=selected_group)

@app.route('/teacher/add-student', methods=['POST'])
@role_required('teacher')
def add_student():
    username = request.form['username'].strip()
    if query_db('SELECT id FROM users WHERE username=?', (username,), one=True):
        flash('Такий логін уже існує.', 'error')
        return redirect(url_for('teacher_dashboard'))
    execute_db('INSERT INTO users(username, password_hash, role, full_name, class_name, birth_date, school_name, about_me, teacher_id) VALUES(?,?,?,?,?,?,?,?,?)', (username, generate_password_hash(request.form['password']), 'student', request.form['full_name'].strip(), request.form.get('class_name', '').strip(), '', '', '', session['user_id']))
    flash('Учня додано до вашої групи.', 'success')
    return redirect(url_for('teacher_dashboard', group=request.form.get('class_name', '').strip()))

@app.route('/teacher/delete-student/<int:student_id>', methods=['POST'])
@role_required('teacher')
def delete_student(student_id):
    student = query_db("SELECT * FROM users WHERE id=? AND role='student' AND teacher_id=?", (student_id, session['user_id']), one=True)
    if not student:
        flash('Учня не знайдено або він не належить до вашої групи.', 'error')
        return redirect(url_for('teacher_dashboard'))

    execute_db('DELETE FROM test_results WHERE student_id=?', (student_id,))
    execute_db('DELETE FROM practice_submissions WHERE student_id=?', (student_id,))
    execute_db('DELETE FROM users WHERE id=? AND teacher_id=?', (student_id, session['user_id']))
    flash('Учня видалено з вашої групи.', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/grade/<int:submission_id>', methods=['POST'])
@role_required('teacher')
def grade_submission(submission_id):
    submission = query_db('SELECT ps.id FROM practice_submissions ps JOIN users u ON u.id=ps.student_id WHERE ps.id=? AND u.teacher_id=?', (submission_id, session['user_id']), one=True)
    if not submission:
        flash('Роботу не знайдено або вона не належить вашому учню.', 'error')
        return redirect(url_for('teacher_dashboard'))
    try:
        score_val = int(request.form.get('teacher_score', '0'))
    except ValueError:
        score_val = 0
    execute_db('UPDATE practice_submissions SET teacher_score=?, teacher_comment=?, status=? WHERE id=?', (score_val, request.form.get('teacher_comment', '').strip(), 'graded', submission_id))
    flash('Оцінку за практичне завдання збережено.', 'success')
    return redirect(url_for('teacher_dashboard'))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT NOT NULL,
        class_name TEXT,
        birth_date TEXT,
        school_name TEXT,
        about_me TEXT,
        teacher_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS tests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS test_questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        options TEXT NOT NULL,
        correct_answer TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS test_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        test_id INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        score_percent REAL NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS practical_tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS practice_submissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        notes TEXT,
        file_name TEXT,
        status TEXT,
        teacher_score INTEGER,
        teacher_comment TEXT,
        submitted_at TEXT
    );
    ''')

    user_columns = [row[1] for row in cur.execute('PRAGMA table_info(users)').fetchall()]
    if 'teacher_id' not in user_columns:
        cur.execute('ALTER TABLE users ADD COLUMN teacher_id INTEGER')


    if cur.execute('SELECT COUNT(*) FROM practical_tasks').fetchone()[0] == 0:
        for title, description in PRACTICALS:
            cur.execute('INSERT INTO practical_tasks(title, description) VALUES(?,?)', (title, description))
    if cur.execute('SELECT COUNT(*) FROM tests').fetchone()[0] == 0:
        for test in TESTS:
            cur.execute('INSERT INTO tests(title, description) VALUES(?,?)', (test['title'], 'Підсумковий тест за темою модуля.'))
            test_id = cur.lastrowid
            for q_text, options, correct in test['questions']:
                cur.execute('INSERT INTO test_questions(test_id, question_text, options, correct_answer) VALUES(?,?,?,?)', (test_id, q_text, options, correct))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
