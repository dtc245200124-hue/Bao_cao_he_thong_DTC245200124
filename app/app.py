import os
from flask import Flask, jsonify
import psycopg

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Docker Web System</title>
    </head>
    <body>
        <h1>He thong Docker hoat dong!</h1>
        <p>Ung dung Flask dang chay sau Nginx.</p>
        <p><a href="/health">Kiem tra tinh trang</a></p>
        <p><a href="/db-check">Kiem tra co so du lieu</a></p>
    </body>
    </html>
    """


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/db-check")
def db_check():
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            # Fallback sang các biến môi trường lẻ nếu không có DATABASE_URL
            host = os.getenv("POSTGRES_HOST", "db")
            dbname = os.getenv("POSTGRES_DB", "app_db")
            user = os.getenv("POSTGRES_USER", "app_user")
            password = os.getenv("POSTGRES_PASSWORD", "app_password")
            db_url = f"postgresql://{user}:{password}@{host}:5432/{dbname}"

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                return jsonify(database="connected", result=result[0]), 200
    except Exception as e:
        return jsonify(database="error", message=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)