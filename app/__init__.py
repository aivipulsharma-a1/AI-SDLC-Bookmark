import os
import sqlite3
from flask import Flask


def get_db_path():
    return os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "bookmarks.db"))


def get_db_connection(db_path=None):
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    conn = get_db_connection(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bookmarks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            url       TEXT    NOT NULL,
            title     TEXT    NOT NULL DEFAULT '',
            created_at DATETIME DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
        );

        CREATE TABLE IF NOT EXISTS tags (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS bookmark_tags (
            bookmark_id INTEGER NOT NULL REFERENCES bookmarks(id) ON DELETE CASCADE,
            tag_id      INTEGER NOT NULL REFERENCES tags(id)      ON DELETE CASCADE,
            PRIMARY KEY (bookmark_id, tag_id)
        );
    """)
    conn.commit()
    conn.close()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

    if test_config is not None:
        app.config.update(test_config)

    db_path = app.config.get("DATABASE_PATH", get_db_path())
    init_db(db_path)

    from .routes import bp
    app.register_blueprint(bp)

    return app
