from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import sqlite3, hashlib, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production-please")

ADMIN_USERNAME     = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
)

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Будь ласка, увійдіть.", "error")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════
#  PUBLIC ROUTES
# ═══════════════════════════════════════════

@app.route("/")
def index():
    conn = get_db()
    top_movies   = conn.execute(
        "SELECT movies.*, categories.name as category_name, "
        "COALESCE(AVG(ratings.score),0) as avg_rating, COUNT(ratings.id) as rating_count "
        "FROM movies LEFT JOIN categories ON movies.category_id=categories.id "
        "LEFT JOIN ratings ON movies.id=ratings.movie_id "
        "GROUP BY movies.id ORDER BY avg_rating DESC LIMIT 6"
    ).fetchall()
    latest_news     = conn.execute("SELECT * FROM news ORDER BY created_at DESC LIMIT 3").fetchall()
    latest_articles = conn.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT 3").fetchall()
    categories      = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("index.html",
        top_movies=top_movies,
        latest_news=latest_news,
        latest_articles=latest_articles,
        categories=categories)


@app.route("/categories")
def categories():
    conn = get_db()
    cats = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("categories.html", categories=cats)


@app.route("/category/<int:id>")
def movies(id):
    conn = get_db()
    movies = conn.execute(
        "SELECT movies.*, COALESCE(AVG(ratings.score),0) as avg_rating, COUNT(ratings.id) as rating_count "
        "FROM movies LEFT JOIN ratings ON movies.id=ratings.movie_id "
        "WHERE movies.category_id=? GROUP BY movies.id", (id,)
    ).fetchall()
    category = conn.execute("SELECT * FROM categories WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template("movies.html", movies=movies, category=category)


@app.route("/movie/<int:id>")
def movie(id):
    conn = get_db()
    movie = conn.execute(
        "SELECT movies.*, categories.name as category_name, "
        "COALESCE(AVG(ratings.score),0) as avg_rating, COUNT(ratings.id) as rating_count "
        "FROM movies LEFT JOIN categories ON movies.category_id=categories.id "
        "LEFT JOIN ratings ON movies.id=ratings.movie_id "
        "WHERE movies.id=? GROUP BY movies.id", (id,)
    ).fetchone()
    user_ip = request.remote_addr
    user_rating = conn.execute(
        "SELECT score FROM ratings WHERE movie_id=? AND ip=?", (id, user_ip)
    ).fetchone()
    conn.close()
    return render_template("movie.html", movie=movie, user_rating=user_rating)


@app.route("/movie/<int:id>/rate", methods=["POST"])
def rate_movie(id):
    score = request.form.get("score", type=int)
    if not score or not (1 <= score <= 5):
        return jsonify({"error": "invalid"}), 400
    user_ip = request.remote_addr
    conn = get_db()
    conn.execute(
        "INSERT INTO ratings(movie_id, score, ip) VALUES(?,?,?) "
        "ON CONFLICT(movie_id, ip) DO UPDATE SET score=excluded.score",
        (id, score, user_ip)
    )
    conn.commit()
    result = conn.execute(
        "SELECT COALESCE(AVG(score),0) as avg, COUNT(*) as cnt FROM ratings WHERE movie_id=?", (id,)
    ).fetchone()
    conn.close()
    return jsonify({"avg": round(result["avg"], 1), "count": result["cnt"]})


# ── News ──────────────────────────────────────────────────────

@app.route("/news")
def news():
    conn = get_db()
    all_news = conn.execute("SELECT * FROM news ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("news.html", news_list=all_news)


@app.route("/news/<int:id>")
def news_item(id):
    conn = get_db()
    item = conn.execute("SELECT * FROM news WHERE id=?", (id,)).fetchone()
    related = conn.execute("SELECT * FROM news WHERE id!=? ORDER BY created_at DESC LIMIT 3", (id,)).fetchall()
    conn.close()
    return render_template("news_item.html", item=item, related=related)


# ── Articles ──────────────────────────────────────────────────

@app.route("/articles")
def articles():
    conn = get_db()
    all_articles = conn.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("articles.html", articles=all_articles)


@app.route("/articles/<int:id>")
def article(id):
    conn = get_db()
    item = conn.execute("SELECT * FROM articles WHERE id=?", (id,)).fetchone()
    related = conn.execute("SELECT * FROM articles WHERE id!=? ORDER BY created_at DESC LIMIT 3", (id,)).fetchall()
    conn.close()
    return render_template("article_item.html", item=item, related=related)


# ═══════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
            session["admin_logged_in"] = True
            next_url = request.args.get("next") or url_for("admin")
            flash("Ласкаво просимо!", "success")
            return redirect(next_url)
        flash("Невірний логін або пароль.", "error")
    return render_template("login.html")


@app.route("/admin/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ═══════════════════════════════════════════
#  ADMIN — Movies
# ═══════════════════════════════════════════

@app.route("/admin")
@login_required
def admin():
    conn = get_db()
    movies = conn.execute(
        "SELECT movies.*, categories.name as category_name FROM movies "
        "LEFT JOIN categories ON movies.category_id=categories.id"
    ).fetchall()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    news_list  = conn.execute("SELECT * FROM news ORDER BY created_at DESC").fetchall()
    articles   = conn.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin.html", movies=movies, categories=categories,
                           news_list=news_list, articles=articles)


@app.route("/admin/movie/add", methods=["GET", "POST"])
@login_required
def admin_add_movie():
    conn = get_db()
    cats = conn.execute("SELECT * FROM categories").fetchall()
    if request.method == "POST":
        t, d, p, c = (request.form["title"].strip(), request.form["description"].strip(),
                      request.form["poster"].strip(), request.form["category_id"])
        if t:
            conn.execute("INSERT INTO movies(title,description,poster,category_id) VALUES(?,?,?,?)", (t,d,p,c))
            conn.commit(); flash("Фільм додано!", "success"); conn.close()
            return redirect(url_for("admin"))
        flash("Назва обов'язкова.", "error")
    conn.close()
    return render_template("admin_movie_form.html", movie=None, categories=cats, action="add")


@app.route("/admin/movie/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_movie(id):
    conn = get_db()
    movie = conn.execute("SELECT * FROM movies WHERE id=?", (id,)).fetchone()
    cats  = conn.execute("SELECT * FROM categories").fetchall()
    if request.method == "POST":
        t, d, p, c = (request.form["title"].strip(), request.form["description"].strip(),
                      request.form["poster"].strip(), request.form["category_id"])
        if t:
            conn.execute("UPDATE movies SET title=?,description=?,poster=?,category_id=? WHERE id=?", (t,d,p,c,id))
            conn.commit(); flash("Фільм оновлено!", "success"); conn.close()
            return redirect(url_for("admin"))
        flash("Назва обов'язкова.", "error")
    conn.close()
    return render_template("admin_movie_form.html", movie=movie, categories=cats, action="edit")


@app.route("/admin/movie/delete/<int:id>", methods=["POST"])
@login_required
def admin_delete_movie(id):
    conn = get_db()
    conn.execute("DELETE FROM movies WHERE id=?", (id,))
    conn.execute("DELETE FROM ratings WHERE movie_id=?", (id,))
    conn.commit(); conn.close()
    flash("Фільм видалено.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/category/add", methods=["POST"])
@login_required
def admin_add_category():
    name = request.form["name"].strip()
    if name:
        conn = get_db()
        conn.execute("INSERT INTO categories(name) VALUES(?)", (name,))
        conn.commit(); conn.close()
        flash("Категорію додано!", "success")
    else:
        flash("Назва обов'язкова.", "error")
    return redirect(url_for("admin"))


@app.route("/admin/category/delete/<int:id>", methods=["POST"])
@login_required
def admin_delete_category(id):
    conn = get_db()
    conn.execute("DELETE FROM movies WHERE category_id=?", (id,))
    conn.execute("DELETE FROM categories WHERE id=?", (id,))
    conn.commit(); conn.close()
    flash("Категорію видалено.", "success")
    return redirect(url_for("admin"))


# ═══════════════════════════════════════════
#  ADMIN — News
# ═══════════════════════════════════════════

@app.route("/admin/news/add", methods=["GET", "POST"])
@login_required
def admin_add_news():
    if request.method == "POST":
        t, c, img = (request.form["title"].strip(), request.form["content"].strip(),
                     request.form["image"].strip())
        if t:
            conn = get_db()
            conn.execute("INSERT INTO news(title,content,image) VALUES(?,?,?)", (t,c,img))
            conn.commit(); conn.close()
            flash("Новину додано!", "success")
            return redirect(url_for("admin"))
        flash("Заголовок обов'язковий.", "error")
    return render_template("admin_content_form.html", item=None, action="add", type="news")


@app.route("/admin/news/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_news(id):
    conn = get_db()
    item = conn.execute("SELECT * FROM news WHERE id=?", (id,)).fetchone()
    if request.method == "POST":
        t, c, img = (request.form["title"].strip(), request.form["content"].strip(),
                     request.form["image"].strip())
        if t:
            conn.execute("UPDATE news SET title=?,content=?,image=? WHERE id=?", (t,c,img,id))
            conn.commit(); conn.close()
            flash("Новину оновлено!", "success")
            return redirect(url_for("admin"))
        flash("Заголовок обов'язковий.", "error")
    conn.close()
    return render_template("admin_content_form.html", item=item, action="edit", type="news")


@app.route("/admin/news/delete/<int:id>", methods=["POST"])
@login_required
def admin_delete_news(id):
    conn = get_db()
    conn.execute("DELETE FROM news WHERE id=?", (id,))
    conn.commit(); conn.close()
    flash("Новину видалено.", "success")
    return redirect(url_for("admin"))


# ═══════════════════════════════════════════
#  ADMIN — Articles
# ═══════════════════════════════════════════

@app.route("/admin/article/add", methods=["GET", "POST"])
@login_required
def admin_add_article():
    if request.method == "POST":
        t, c, img = (request.form["title"].strip(), request.form["content"].strip(),
                     request.form["image"].strip())
        if t:
            conn = get_db()
            conn.execute("INSERT INTO articles(title,content,image) VALUES(?,?,?)", (t,c,img))
            conn.commit(); conn.close()
            flash("Статтю додано!", "success")
            return redirect(url_for("admin"))
        flash("Заголовок обов'язковий.", "error")
    return render_template("admin_content_form.html", item=None, action="add", type="article")


@app.route("/admin/article/edit/<int:id>", methods=["GET", "POST"])
@login_required
def admin_edit_article(id):
    conn = get_db()
    item = conn.execute("SELECT * FROM articles WHERE id=?", (id,)).fetchone()
    if request.method == "POST":
        t, c, img = (request.form["title"].strip(), request.form["content"].strip(),
                     request.form["image"].strip())
        if t:
            conn.execute("UPDATE articles SET title=?,content=?,image=? WHERE id=?", (t,c,img,id))
            conn.commit(); conn.close()
            flash("Статтю оновлено!", "success")
            return redirect(url_for("admin"))
        flash("Заголовок обов'язковий.", "error")
    conn.close()
    return render_template("admin_content_form.html", item=item, action="edit", type="article")


@app.route("/admin/article/delete/<int:id>", methods=["POST"])
@login_required
def admin_delete_article(id):
    conn = get_db()
    conn.execute("DELETE FROM articles WHERE id=?", (id,))
    conn.commit(); conn.close()
    flash("Статтю видалено.", "success")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
if not os.path.exists("database.db"):
    import create_db