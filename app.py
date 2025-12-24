from flask import Flask, request, jsonify, redirect, abort
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import (
    urls,
    stats,
    generate_short_id,
    can_create_link,
    register_link_creation,
    register_click,
)

app = Flask(__name__)

# -----------------------
# КЭШИРОВАНИЕ
# -----------------------
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600  # 1 час
cache = Cache(app)

# -----------------------
# ЛИМИТИРОВАНИЕ
# -----------------------
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[]
)


# -----------------------
# POST /shorten
# -----------------------
@limiter.limit("10/day", key_func=lambda: request.json.get("user_id", "anonymous"))
@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    original_url = data["url"]
    user_id = data.get("user_id", "anonymous")

    if not can_create_link(user_id):
        return jsonify({"error": "Link creation limit exceeded"}), 429

    short_id = generate_short_id()

    urls[short_id] = {
        "url": original_url,
        "user_id": user_id
    }

    register_link_creation(user_id)

    return jsonify({"short_id": short_id}), 201


# -----------------------
# GET /<short_id>
# -----------------------
@limiter.limit("100/day", key_func=get_remote_address)
@app.route("/<short_id>", methods=["GET"])
@cache.cached(timeout=3600)
def redirect_to_url(short_id):
    if short_id not in urls:
        abort(404)

    ip_address = get_remote_address()

    if not register_click(short_id, ip_address):
        return jsonify({"error": "Click limit exceeded for this IP"}), 429

    return redirect(urls[short_id]["url"])


# -----------------------
# GET /stats/<short_id>
# -----------------------
@app.route("/stats/<short_id>", methods=["GET"])
def get_stats(short_id):
    if short_id not in urls:
        abort(404)

    return jsonify({
        "clicks": stats[short_id]["clicks"],
        "unique_ips": list(stats[short_id]["ips"])
    })


# -----------------------
# ЗАПУСК
# -----------------------
if __name__ == "__main__":
    app.run(debug=False)
