from flask import Blueprint, jsonify, request, render_template, current_app
import urllib.parse

from . import get_db_connection, get_db_path
from .utils import fetch_page_title

bp = Blueprint("main", __name__)

_ALLOWED_URL_SCHEMES = {"http", "https"}


def _db():
    path = current_app.config.get("DATABASE_PATH", get_db_path())
    return get_db_connection(path)


# ---------------------------------------------------------------------------
# Helper: attach tag list to a list of bookmark rows
# ---------------------------------------------------------------------------
def _attach_tags(conn, bookmarks):
    if not bookmarks:
        return []
    ids = [b["id"] for b in bookmarks]
    placeholders = ",".join("?" * len(ids))
    # placeholders is built from len(ids) only — no user input in the SQL string
    rows = conn.execute(
        f"""
        SELECT bt.bookmark_id, t.name
        FROM   bookmark_tags bt
        JOIN   tags t ON t.id = bt.tag_id
        WHERE  bt.bookmark_id IN ({placeholders})
        ORDER  BY t.name
        """,
        ids,
    ).fetchall()

    tag_map: dict = {bid: [] for bid in ids}
    for r in rows:
        tag_map[r["bookmark_id"]].append(r["name"])

    result = []
    for b in bookmarks:
        d = dict(b)
        d["tags"] = tag_map[b["id"]]
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Helper: get-or-create a tag; return its id
# ---------------------------------------------------------------------------
def _get_or_create_tag(conn, name: str) -> int:
    name = name.strip().lower()
    row = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
    return cur.lastrowid


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/api/bookmarks", methods=["GET"])
def list_bookmarks():
    search = request.args.get("q", "").strip()
    tag_filter = request.args.get("tag", "").strip()

    conn = _db()
    try:
        if tag_filter:
            rows = conn.execute(
                """
                SELECT DISTINCT b.*
                FROM   bookmarks b
                JOIN   bookmark_tags bt ON bt.bookmark_id = b.id
                JOIN   tags t           ON t.id = bt.tag_id
                WHERE  t.name = ?
                ORDER  BY b.created_at DESC, b.id DESC
                """,
                (tag_filter.lower(),),
            ).fetchall()
        elif search:
            like = f"%{search}%"
            rows = conn.execute(
                """
                SELECT * FROM bookmarks
                WHERE  title LIKE ? OR url LIKE ?
                ORDER  BY created_at DESC, id DESC
                """,
                (like, like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM bookmarks ORDER BY created_at DESC, id DESC"
            ).fetchall()

        return jsonify(_attach_tags(conn, rows))
    finally:
        conn.close()


@bp.route("/api/bookmarks", methods=["POST"])
def add_bookmark():
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_URL_SCHEMES:
        return jsonify({"error": "url must use http or https scheme"}), 400

    title = (data.get("title") or "").strip()
    if not title:
        title = fetch_page_title(url) or url

    raw_tags = data.get("tags", [])
    if isinstance(raw_tags, str):
        raw_tags = [t for t in raw_tags.split(",") if t.strip()]

    conn = _db()
    try:
        cur = conn.execute(
            "INSERT INTO bookmarks (url, title) VALUES (?, ?)",
            (url, title),
        )
        bookmark_id = cur.lastrowid

        for tag_name in raw_tags:
            tag_name = tag_name.strip()
            if tag_name:
                tag_id = _get_or_create_tag(conn, tag_name)
                conn.execute(
                    "INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_id) VALUES (?, ?)",
                    (bookmark_id, tag_id),
                )

        conn.commit()

        row = conn.execute(
            "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        result = _attach_tags(conn, [row])[0]
        return jsonify(result), 201
    finally:
        conn.close()


@bp.route("/api/bookmarks/<int:bookmark_id>", methods=["DELETE"])
def delete_bookmark(bookmark_id):
    conn = _db()
    try:
        row = conn.execute(
            "SELECT id FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "not found"}), 404

        conn.execute("DELETE FROM bookmark_tags WHERE bookmark_id = ?", (bookmark_id,))
        conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        conn.commit()
        return jsonify({"message": "deleted"}), 200
    finally:
        conn.close()


@bp.route("/api/tags", methods=["GET"])
def list_tags():
    conn = _db()
    try:
        rows = conn.execute(
            """
            SELECT t.name, COUNT(bt.bookmark_id) AS count
            FROM   tags t
            LEFT JOIN bookmark_tags bt ON bt.tag_id = t.id
            GROUP  BY t.id
            ORDER  BY t.name
            """
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()
