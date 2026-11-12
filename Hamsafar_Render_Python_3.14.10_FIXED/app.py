# -*- coding: utf-8 -*-
"""هم‌سفر من - برنامه وب با Flask و SQLite"""
import math
import os
import sqlite3
import uuid
from datetime import datetime

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, send_from_directory, url_for)

import data as D

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, instance_path=os.path.join(BASE_DIR, "instance"))
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # حداکثر ۴ مگابایت

os.makedirs(app.instance_path, exist_ok=True)
UPLOAD_DIR = os.path.join(app.instance_path, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, "hamsafar.db")
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}

# مختصات تقریبی برای نقشه شماتیک
COORDS = {
    "tehran": (35.69, 51.39), "esfahan": (32.65, 51.67), "shiraz": (29.59, 52.58),
    "yazd": (31.90, 54.37), "tabriz": (38.08, 46.29), "mashhad": (36.30, 59.60),
    "rasht": (37.28, 49.58),
}

# ------------------------------------------------------------------ دیتابیس


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        target TEXT NOT NULL DEFAULT '',
        name TEXT NOT NULL,
        rating INTEGER NOT NULL,
        text TEXT NOT NULL,
        photo TEXT NOT NULL DEFAULT '',
        created TEXT NOT NULL)""")
    db.commit()
    db.close()


init_db()

# ------------------------------------------------------------------ فیلترها

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@app.template_filter("fa")
def fa(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = f"{v:,}" if isinstance(v, int) else str(v)
    return s.replace(",", "٬").replace(".", "٫").translate(_FA)


@app.template_filter("money")
def money(k):
    k = int(round(k))
    if k <= 0:
        return "رایگان"
    if k >= 1000:
        m = round(k / 1000, 1)
        return f"{fa(m)} میلیون تومان"
    return f"{fa(k)} هزار تومان"


@app.template_filter("fdate")
def fdate(s):
    try:
        return fa(datetime.fromisoformat(s).strftime("%Y/%m/%d"))
    except Exception:
        return s


@app.template_filter("stars")
def stars(n):
    n = int(round(n))
    return "★" * n + "☆" * (5 - n)


def city_image(slug):
    for ext in ("jpg", "jpeg", "webp", "png", "svg"):
        rel = f"img/cities/{slug}.{ext}"
        if os.path.exists(os.path.join(app.static_folder, rel)):
            return url_for("static", filename=rel)
    return ""


@app.context_processor
def inject():
    return {"cities": D.CITIES, "levels": D.LEVELS, "city_image": city_image,
            "articles": D.ARTICLES, "assistant_city": None}


# ------------------------------------------------------------------ نظرات


def rating_stats():
    rows = get_db().execute(
        "SELECT city, AVG(rating) a, COUNT(*) c FROM reviews GROUP BY city").fetchall()
    return {r["city"]: (round(r["a"], 1), r["c"]) for r in rows}


def city_reviews(slug, limit=50):
    return get_db().execute(
        "SELECT * FROM reviews WHERE city=? ORDER BY id DESC LIMIT ?", (slug, limit)).fetchall()


# ------------------------------------------------------------------ صفحات


@app.route("/")
def index():
    return render_template("index.html", stats=rating_stats(), coords=COORDS,
                           matrix=D.km_between)


@app.route("/city/<slug>")
def city(slug):
    c = D.CITY_MAP.get(slug)
    if not c:
        abort(404)
    stats = rating_stats().get(slug)
    targets = [a["name"] for a in c["attractions"]] + [r["name"] for r in c["restaurants"]]
    return render_template("city.html", c=c, reviews=city_reviews(slug), stats=stats,
                           targets=targets, assistant_city=slug)


@app.route("/city/<slug>/review", methods=["POST"])
def add_review(slug):
    c = D.CITY_MAP.get(slug)
    if not c:
        abort(404)
    f = request.form
    if f.get("website"):  # honeypot برای ربات‌ها
        return redirect(url_for("city", slug=slug))
    name = f.get("name", "").strip()[:40]
    text = f.get("text", "").strip()[:1000]
    target = f.get("target", "").strip()
    try:
        rating = int(f.get("rating", "0"))
    except ValueError:
        rating = 0
    valid_targets = {a["name"] for a in c["attractions"]} | {r["name"] for r in c["restaurants"]}
    if target and target not in valid_targets:
        target = ""
    if not name or len(text) < 5 or not 1 <= rating <= 5:
        flash("لطفاً نام، امتیاز (۱ تا ۵) و متن نظر (حداقل ۵ حرف) را وارد کنید.", "err")
        return redirect(url_for("city", slug=slug) + "#reviews")

    photo = ""
    file = request.files.get("photo")
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXT:
            flash("فقط عکس با فرمت jpg، png یا webp پذیرفته می‌شود.", "err")
            return redirect(url_for("city", slug=slug) + "#reviews")
        photo = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(UPLOAD_DIR, photo))

    db = get_db()
    db.execute("INSERT INTO reviews(city,target,name,rating,text,photo,created) VALUES (?,?,?,?,?,?,?)",
               (slug, target, name, rating, text, photo, datetime.now().isoformat(timespec="seconds")))
    db.commit()
    flash("نظر شما ثبت شد. ممنون که تجربه‌تان را به اشتراک گذاشتید!", "ok")
    return redirect(url_for("city", slug=slug) + "#reviews")


@app.route("/uploads/<path:name>")
def uploads(name):
    return send_from_directory(UPLOAD_DIR, name)


@app.errorhandler(413)
def too_big(_):
    flash("حجم عکس بیشتر از ۴ مگابایت است.", "err")
    return redirect(request.referrer or url_for("index"))


@app.route("/favicon.ico")
def favicon():
    return ("", 204)


@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.errorhandler(404)
def not_found(_):
    try:
        return render_template("404.html"), 404
    except Exception:
        return (
            '<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8">'
            '<title>صفحه پیدا نشد</title><h1>صفحه پیدا نشد</h1>'
            '<p>این آدرس وجود ندارد.</p><a href="/">بازگشت به صفحه اصلی</a></html>',
            404,
            {"Content-Type": "text/html; charset=utf-8"},
        )


# ------------------------------------------------------------------ برنامه‌ریز

PACE = {"relaxed": 2, "normal": 3, "busy": 4}


def estimate(c, tier, persons, days, transport):
    daily = D.DAILY_COST[tier] * c["cost_idx"] * persons * days
    rate = D.TRANSPORT[transport][1]
    trans = rate * c["km"] * 2 * persons
    if transport == "plane":
        trans = max(trans, 2500 * persons)
    return int(daily), int(trans)


def build_itinerary(c, tier, days, pace):
    allowed = 3 if tier == 3 else 2
    places = [a for a in c["attractions"] if a["level"] <= allowed]
    foods = [r for r in c["restaurants"] if r["level"] <= tier] or c["restaurants"]
    foods.sort(key=lambda r: abs(r["level"] - tier))
    per = PACE[pace]
    plan, i, f = [], 0, 0
    for d in range(1, min(days, 7) + 1):
        chunk = places[i:i + per]
        i += per
        meals = []
        for _ in range(2):
            meals.append(foods[f % len(foods)])
            f += 1
        plan.append({"day": d, "places": chunk, "meals": meals})
    return plan


def make_plan(form):
    def num(key, default, lo, hi):
        try:
            return max(lo, min(hi, int(form.get(key, default))))
        except ValueError:
            return default

    adults = num("adults", 2, 1, 20)
    kids = num("kids", 0, 0, 20)
    days = num("days", 3, 1, 14)
    budget = num("budget", 20, 1, 1000)  # میلیون تومان
    month = num("month", 1, 1, 12)
    goals = [g_ for g_ in form.getlist("goals") if g_ in D.GOALS]
    transport = form.get("transport", "car")
    if transport not in D.TRANSPORT:
        transport = "car"
    pace = form.get("pace", "normal")
    if pace not in PACE:
        pace = "normal"
    persons = adults + kids * 0.5
    budget_k = budget * 1000

    results = []
    for c in D.CITIES:
        costs = {}
        for t in (1, 2, 3):
            d, tr = estimate(c, t, persons, days, transport)
            costs[t] = {"daily": d, "trans": tr, "total": d + tr}
        tier = 1
        for t in (3, 2, 1):
            if costs[t]["total"] <= budget_k:
                tier = t
                break
        over = costs[tier]["total"] > budget_k
        goal_score = (sum(c["tags"][g_] for g_ in goals) / (5 * len(goals))) if goals else \
            sum(c["tags"][k] for k in D.GOALS) / (5 * len(D.GOALS))
        kid_score = c["tags"]["kids"] / 5 if kids else 0.6
        budget_score = 1.0 if not over else max(0.0, budget_k / costs[1]["total"])
        days_score = min(1.0, days / c["days"])
        month_ok = month in c["best_months"]
        score = (0.45 * goal_score + 0.10 * kid_score + 0.25 * budget_score +
                 0.08 * days_score + 0.12 * (1.0 if month_ok else 0.3))

        reasons = []
        matched = [D.GOALS[g_] for g_ in goals if c["tags"][g_] >= 4]
        if matched:
            reasons.append("برای هدف شما عالی است: " + "، ".join(matched))
        if kids and c["tags"]["kids"] >= 4:
            reasons.append("برای سفر با بچه‌ها مناسب است.")
        if kids and c["tags"]["kids"] <= 2:
            reasons.append("برای بچه‌های کوچک کمی خسته‌کننده است؛ برنامه را آرام‌تر بچینید.")
        reasons.append("ماه انتخابی شما فصل مناسبی است." if month_ok else
                       f"ماه انتخابی بهترین زمان نیست (بهتر: {c['best_season']}).")
        if over:
            reasons.append("بودجه شما برای ارزان‌ترین حالت هم کمی کم است؛ روزها را کمتر کنید یا وسیله ارزان‌تر انتخاب کنید.")
        if days < c["days"]:
            reasons.append(f"برای دیدن کامل این شهر حدود {fa(c['days'])} روز لازم است.")
        results.append({"city": c, "score": round(score * 100), "tier": tier, "over": over,
                        "costs": costs, "reasons": reasons, "month_ok": month_ok,
                        "plan": build_itinerary(c, tier, days, pace)})
    results.sort(key=lambda r: -r["score"])
    form_state = {"adults": adults, "kids": kids, "days": days, "budget": budget, "month": month,
                  "goals": goals, "transport": transport, "pace": pace}
    return results, form_state


@app.route("/planner", methods=["GET", "POST"])
def planner():
    results, state = None, None
    if request.method == "POST":
        results, state = make_plan(request.form)
    return render_template("planner.html", results=results, state=state,
                           goals=D.GOALS, months=D.MONTHS, transports=D.TRANSPORT,
                           pace_labels={"relaxed": "آرام", "normal": "متعادل", "busy": "فشرده"})


# ------------------------------------------------------------------ مقالات و درباره ما


@app.route("/articles")
def articles_page():
    return render_template("articles.html")


@app.route("/articles/<slug>")
def article(slug):
    a = next((x for x in D.ARTICLES if x["slug"] == slug), None)
    if not a:
        abort(404)
    extra = {}
    if slug == "budget":
        example = []
        for t in (1, 2, 3):
            d, tr = estimate(D.CITY_MAP["esfahan"], t, 2, 4, "car")
            example.append({"tier": t, "daily": d, "trans": tr, "total": d + tr})
        extra["example"] = example
        extra["transports"] = D.TRANSPORT
        extra["DAILY"] = D.DAILY_COST
    if slug == "distances":
        extra["matrix"] = D.km_between
    if slug == "experiences":
        extra["stats"] = rating_stats()
        extra["latest"] = get_db().execute(
            "SELECT * FROM reviews ORDER BY id DESC LIMIT 12").fetchall()
    return render_template("article.html", a=a, slug=slug, **extra)


@app.route("/about")
def about():
    return render_template("about.html")


# ------------------------------------------------------------------ دستیار هوشمند

GENERAL_QS = [
    ("g_which", "کدام شهر برای من مناسب‌تر است؟"),
    ("g_budget", "برای بودجه سفر چه چیزهایی را باید حساب کنم؟"),
    ("g_plan", "چطور یک سفر چندشهری را برنامه‌ریزی کنم؟"),
    ("g_kids", "با بچه سفر می‌روم؛ چه نکاتی مهم است؟"),
    ("g_season", "بهترین زمان سفر به هر شهر چه موقع است؟"),
]
CITY_QS = [
    ("c_season", "بهترین فصل سفر به {n} چه موقع است؟"),
    ("c_depart", "بهترین ساعت حرکت از تهران به {n}؟"),
    ("c_km", "فاصله تهران تا {n} چقدر است؟"),
    ("c_stops", "در مسیر تهران تا {n} چه شهرهایی هست؟"),
    ("c_days", "برای {n} چند روز لازم است؟"),
    ("c_budget", "بودجه سفر به {n} حدوداً چقدر است؟"),
    ("c_food", "در {n} چه غذاهایی را حتماً امتحان کنم؟"),
    ("c_near", "فاصله جاذبه‌های {n} از هم چقدر است؟"),
    ("c_kids", "سفر به {n} با بچه چطور است؟"),
    ("c_tips", "یک نکته مهم برای سفر به {n}؟"),
]


def questions_for(slug):
    out = []
    c = D.CITY_MAP.get(slug)
    if c:
        out += [{"id": i, "q": q.format(n=c["name"])} for i, q in CITY_QS]
    out += [{"id": i, "q": q} for i, q in GENERAL_QS if not c or i in ("g_which", "g_plan")]
    return out


def answer_for(slug, qid):
    c = D.CITY_MAP.get(slug)
    n = c["name"] if c else ""
    if qid == "g_which":
        return "بهترین راه این است که پرسش‌نامه «برنامه‌ریز سفر» را پر کنید (تعداد نفرات، بودجه، مدت سفر، هدف). " \
               "من شهرها را بر اساس نیاز شما رتبه‌بندی می‌کنم."
    if qid == "g_budget":
        return "هزینه‌های اصلی: ۱) رفت‌وآمد بین شهرها ۲) اقامت ۳) غذا ۴) حمل‌ونقل درون‌شهری ۵) بلیت بناها و تورها " \
               "۶) سوغات و هزینه‌های پیش‌بینی‌نشده. معمولاً ۱۰ تا ۲۰ درصد برای هزینه‌های ناگهانی کنار بگذارید."
    if qid == "g_plan":
        return "۱) هدف و بودجه را مشخص کنید. ۲) شهرها را به ترتیب مسیر بچینید تا مسیر برگشتی نداشته باشید. " \
               "۳) برای هر شهر حداقل یک شب بمانید. ۴) برای مسیرهای بیش از ۶ ساعت یک توقف میان‌راه بگذارید."
    if qid == "g_kids":
        return "برنامه روزانه را سبک‌تر کنید، هر ۲ تا ۳ ساعت استراحت بگذارید، خوراکی و لباس اضافه ببرید " \
               "و جاذبه‌های فضای باز را در ساعات خنک ببینید."
    if qid == "g_season":
        return "\n".join(f"{x['name']}: {x['best_season']}" for x in D.CITIES)
    if not c:
        return "این سؤال مربوط به یک شهر خاص است؛ ابتدا شهری را انتخاب کنید."
    if qid == "c_season":
        return f"بهترین زمان سفر به {n}: {c['best_season']}."
    if qid == "c_depart":
        return c["best_departure"]
    if qid == "c_km":
        return f"فاصله جاده‌ای تقریبی تهران تا {n} حدود {fa(c['km'])} کیلومتر است (زمان: {c['hours']})."
    if qid == "c_stops":
        lines = [f"• {s[0]} (حدود {fa(s[1])} کیلومتر از تهران): {s[2]}" for s in c["stops"]]
        return "شهرهای مسیر:\n" + "\n".join(lines)
    if qid == "c_days":
        return f"برای دیدن اصلی‌ترین جاذبه‌های {n} حدود {fa(c['days'])} روز پیشنهاد می‌شود."
    if qid == "c_budget":
        lines = []
        for t in (1, 2, 3):
            d, tr = estimate(c, t, 2, c["days"], "car")
            lines.append(f"• {D.LEVELS[t]['name']}: حدود {money(d + tr)}")
        return (f"برآورد برای ۲ نفر، {fa(c['days'])} روز، با خودرو شخصی (رفت‌وبرگشت از تهران):\n"
                + "\n".join(lines) + "\n(قیمت‌ها تقریبی‌اند.)")
    if qid == "c_food":
        top = [r["name"] for r in c["restaurants"][:3]]
        return f"غذاهای معروف: {'، '.join(c['local_food'])}.\nمکان‌های پیشنهادی: {'، '.join(top)}."
    if qid == "c_near":
        return "\n".join("• " + x for x in c["distance_notes"])
    if qid == "c_kids":
        return c["kids"]
    if qid == "c_tips":
        return c["tips"]
    return "متأسفانه جوابی برای این سؤال ندارم."


@app.route("/api/assistant/questions")
def api_questions():
    return jsonify({"questions": questions_for(request.args.get("city", ""))})


@app.route("/api/assistant", methods=["POST"])
def api_assistant():
    body = request.get_json(silent=True) or {}
    return jsonify({"answer": answer_for(body.get("city", ""), body.get("qid", ""))})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
