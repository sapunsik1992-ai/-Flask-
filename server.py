from flask import Flask, jsonify, request, Response
from sqlalchemy.exc import IntegrityError

from db import Session, Ad
from errors import HttpError
from schema import CreateAd, UpdateAd, validate

app = Flask(__name__)
app.url_map.strict_slashes = False


def get_ad(ad_id):
    ad = Session().get(Ad, ad_id)
    if ad is None:
        raise HttpError("ad not found", 404)
    return ad


def save_ad(ad):
    session = Session()
    try:
        session.add(ad)
        session.commit()
        session.refresh(ad)
        return ad.dict
    except IntegrityError:
        session.rollback()
        raise HttpError("save error", 400)
    except Exception as e:
        session.rollback()
        raise HttpError(str(e), 500)
    finally:
        session.close()


@app.errorhandler(HttpError)
def error_handler(err):
    return jsonify({"error": err.message}), err.status_code


@app.route("/ads", methods=["GET", "POST"])
def ads():
    if request.method == "POST":
        json_data = request.get_json(silent=True)
        if not json_data:
            raise HttpError("no json data", 400)
        try:
            data = validate(json_data, CreateAd)
        except HttpError as e:
            raise e
        ad = Ad(
            title=data["title"],
            owner=data["owner"],
        )
        if "description" in data and data["description"]:
            ad.description = data["description"]
        ad_data = save_ad(ad)
        return jsonify(ad_data), 201

    session = Session()
    ads_list = session.query(Ad).all()
    result = [a.dict for a in ads_list]
    return jsonify(result)


@app.route("/ads/<int:ad_id>", methods=["GET", "PATCH", "DELETE"])
def ad_detail(ad_id):
    ad = get_ad(ad_id)

    if request.method == "GET":
        return jsonify(ad.dict)

    if request.method == "PATCH":
        json_data = request.get_json(silent=True) or {}
        try:
            data = validate(json_data, UpdateAd)
        except HttpError as e:
            raise e
        if data.get("title") is not None:
            ad.title = data["title"]
        if data.get("description") is not None:
            ad.description = data["description"]
        if data.get("owner") is not None:
            ad.owner = data["owner"]
        ad_data = save_ad(ad)
        return jsonify(ad_data)

    if request.method == "DELETE":
        try:
            session = Session()
            session.delete(ad)
            session.commit()
        except Exception:
            Session().rollback()
            raise HttpError("delete error", 500)
        return jsonify({"message": "deleted"})


HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Expires" content="0">
<title>Объявления</title>
<style>
body { font-family: Arial, sans-serif; max-width: 700px; margin: 30px auto; padding: 0 20px; }
h1 { margin-bottom: 20px; }
h2 { margin-top: 30px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
input, textarea { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
button { padding: 10px 20px; border: none; border-radius: 4px; color: white; cursor: pointer; }
.btn-create { background: #28a745; }
.btn-get { background: #007bff; }
.btn-delete { background: #dc3545; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
td, th { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background: #f5f5f5; }
#result { margin-top: 15px; padding: 10px; background: #f0f0f0; border-radius: 4px; white-space: pre-wrap; font-family: monospace; min-height: 30px; }
</style>
</head>
<body>
<h1>Объявления</h1>

<h2>Создать объявление</h2>
<input type="text" id="title" placeholder="Заголовок">
<textarea id="description" placeholder="Описание" rows="3"></textarea>
<input type="text" id="owner" placeholder="Владелец">
<button class="btn-create" onclick="doCreate()">Создать</button>

<h2>Получить объявление по ID</h2>
<input type="number" id="get_id" placeholder="ID">
<button class="btn-get" onclick="doGet()">Получить</button>

<h2>Получить все объявления</h2>
<button class="btn-get" onclick="doList()">Показать все</button>

<h2>Удалить объявление по ID</h2>
<input type="number" id="del_id" placeholder="ID">
<button class="btn-delete" onclick="doDelete()">Удалить</button>

<h2>Результат</h2>
<div id="result"></div>

<script>
(function() {
    var BASE = window.location.origin;

    function show(text) {
        document.getElementById("result").textContent = text;
    }

    window.doCreate = function() {
        var title = document.getElementById("title").value.trim();
        var desc = document.getElementById("description").value.trim();
        var owner = document.getElementById("owner").value.trim();
        if (!title || !owner) {
            show("Заполните заголовок и владельца");
            return;
        }
        var data = {title: title, owner: owner};
        if (desc) data.description = desc;
        fetch(BASE + "/ads", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        })
        .then(function(r) { return r.json().then(function(j) { return {s: r.status, d: j}; }); })
        .then(function(r) { show("Статус: " + r.s + "\n" + JSON.stringify(r.d, null, 2)); })
        .catch(function(e) { show("Ошибка: " + e.message); });
    };

    window.doGet = function() {
        var id = document.getElementById("get_id").value.trim();
        if (!id) { show("Введите ID"); return; }
        fetch(BASE + "/ads/" + id)
        .then(function(r) { return r.json().then(function(j) { return {s: r.status, d: j}; }); })
        .then(function(r) { show("Статус: " + r.s + "\n" + JSON.stringify(r.d, null, 2)); })
        .catch(function(e) { show("Ошибка: " + e.message); });
    };

    window.doList = function() {
        fetch(BASE + "/ads")
        .then(function(r) { return r.json().then(function(j) { return {s: r.status, d: j}; }); })
        .then(function(r) { show("Статус: " + r.s + "\n" + JSON.stringify(r.d, null, 2)); })
        .catch(function(e) { show("Ошибка: " + e.message); });
    };

    window.doDelete = function() {
        var id = document.getElementById("del_id").value.trim();
        if (!id) { show("Введите ID"); return; }
        fetch(BASE + "/ads/" + id, {method: "DELETE"})
        .then(function(r) { return r.json().then(function(j) { return {s: r.status, d: j}; }); })
        .then(function(r) { show("Статус: " + r.s + "\n" + JSON.stringify(r.d, null, 2)); })
        .catch(function(e) { show("Ошибка: " + e.message); });
    };

    console.log("JS OK");
})();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")


if __name__ == "__main__":
    app.run(port=5000)
