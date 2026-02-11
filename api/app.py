import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

# Read database settings from environment variables (we will set these in docker compose)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "shiplog")
DB_USER = os.environ.get("DB_USER", "shiplog")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "shiplog")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def init_db():
    # Create table if it doesn't exist
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/logs", methods=["POST"])
def add_log():
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if message == "":
        return jsonify({"error": "message is required"}), 400

    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (message) VALUES (%s);", (message,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"saved": True, "message": message}), 201


@app.route("/logs", methods=["GET"])
def get_logs():
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, message, created_at FROM logs ORDER BY id DESC LIMIT 20;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    logs = []
    for r in rows:
        logs.append({"id": r[0], "message": r[1], "created_at": str(r[2])})

    return jsonify({"logs": logs}), 200


if __name__ == "__main__":
    # Listen on all network interfaces so Docker can access it
    app.run(host="0.0.0.0", port=5000)
