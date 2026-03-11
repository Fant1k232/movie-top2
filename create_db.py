import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# ── New tables ──────────────────────────────────────────────

cur.execute("""
CREATE TABLE IF NOT EXISTS news(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    image TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS articles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    image TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS ratings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
    ip TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(movie_id, ip)
)
""")

# ── Sample news ─────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM news")
if cur.fetchone()[0] == 0:
    news = [
        ("Вийшов трейлер нового фільму Крістофера Нолана",
         "Режисер «Інтерстеллар» та «Начала» представив перший офіційний трейлер свого нового проєкту. Фанати вже в захваті від атмосфери та візуального стилю стрічки.",
         "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg"),
        ("Оскар 2025: повний список номінантів",
         "Американська кіноакадемія оголосила номінантів на премію Оскар. Цього року серед фаворитів кілька несподіваних імен і дебютних робіт.",
         "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"),
        ("Сиквел «Безумного Макса» офіційно підтверджено",
         "Студія Warner Bros. оголосила про початок виробництва нової частини культової пост-апокаліптичної франшизи. Джордж Міллер повертається до режисерського крісла.",
         "https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg"),
    ]
    cur.executemany("INSERT INTO news(title,content,image) VALUES(?,?,?)", news)

# ── Sample articles ─────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM articles")
if cur.fetchone()[0] == 0:
    articles = [
        ("10 фільмів, які змінили кінематограф назавжди",
         "Від «Громадянина Кейна» до «Матриці» — ці стрічки перевернули уявлення про те, яким може бути кіно. Розповідаємо, чому кожен із них став поворотним моментом в історії сьомого мистецтва.",
         "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"),
        ("Як читати мову кіно: путівник для глядача",
         "Кожен кут камери, кожен колір кадру — це не випадковість. Розповідаємо про основи кінематографічної мови, які допоможуть вам дивитися фільми глибше і отримувати більше задоволення.",
         "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg"),
        ("Найкращі науково-фантастичні фільми десятиліття",
         "Фантастика 2010-х та 2020-х подарувала нам справжні шедеври жанру. Від камерних психологічних драм до масштабних космічних епопей — добірка найкращого, що запропонував жанр за останні роки.",
         "https://image.tmdb.org/t/p/w500/uluhlXubGu1VxU63X9VHCLWDAYP.jpg"),
    ]
    cur.executemany("INSERT INTO articles(title,content,image) VALUES(?,?,?)", articles)

conn.commit()
conn.close()
print("DB updated successfully")
