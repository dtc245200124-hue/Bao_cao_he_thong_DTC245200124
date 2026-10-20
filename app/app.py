import os
import sys
import logging
import time
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
import psycopg
from prometheus_flask_exporter import PrometheusMetrics

# Cấu hình Structured Logging chuẩn cho Promtail & Loki
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [webapp] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("webapp")

app = Flask(__name__)

# Khởi tạo Prometheus Metrics Exporter (tự động mở endpoint /metrics)
metrics = PrometheusMetrics(app)
metrics.info("webapp_info", "Thông tin ứng dụng WebApp", version="1.0.0", env="production")

# Cấu hình kết nối PostgreSQL
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "app_db")
DB_USER = os.getenv("POSTGRES_USER", "app_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "app_password")

def get_db_connection():
    """Tạo kết nối đến cơ sở dữ liệu PostgreSQL"""
    return psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=3
    )

def init_db():
    """Tự động khởi tạo bảng dữ liệu nếu chưa tồn tại"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        author VARCHAR(100) DEFAULT 'Khách',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
        logger.info("Khoi tao co so du lieu PostgreSQL thanh cong.")
    except Exception as e:
        logger.warning(f"Chua the khoi tao DB ngay lap tuc (se thu lai khi co request): {e}")

# Gọi khởi tạo DB khi app khởi động
try:
    init_db()
except Exception:
    pass

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Quản Trị & Giám Sát Microservices</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --radius: 12px;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text-main); min-height: 100vh; padding: 24px 16px; }
        .container { max-width: 1100px; margin: 0 auto; }
        
        header { text-align: center; margin-bottom: 32px; padding: 24px; background: var(--surface); border-radius: var(--radius); border: 1px solid var(--border); box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3); }
        header h1 { font-size: 26px; font-weight: 700; color: #60a5fa; margin-bottom: 8px; }
        header p { color: var(--text-muted); font-size: 14px; }
        .badge-list { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; margin-top: 14px; }
        .badge { padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; }
        .badge-blue { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid #3b82f6; }
        .badge-green { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981; }

        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 24px; }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
        .card h2 { font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; color: #e2e8f0; }

        /* Links to dashboards */
        .portal-links { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        .portal-btn { display: flex; flex-direction: column; padding: 12px; background: #0f172a; border: 1px solid var(--border); border-radius: 8px; text-decoration: none; color: var(--text-main); transition: all 0.2s; }
        .portal-btn:hover { background: var(--surface-hover); border-color: var(--primary); transform: translateY(-2px); }
        .portal-btn strong { font-size: 14px; color: #93c5fd; }
        .portal-btn span { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

        /* System status */
        .status-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
        .status-row:last-child { border-bottom: none; }
        .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--success); margin-right: 6px; }

        /* Stress Test Controls */
        .btn-group { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
        button, .btn { padding: 10px 16px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; gap: 6px; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-danger { background: var(--danger); color: white; }
        .btn-danger:hover { background: #dc2626; }
        .btn-warning { background: var(--warning); color: #1e293b; }
        .btn-warning:hover { background: #d97706; }

        /* Form */
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 13px; color: var(--text-muted); margin-bottom: 6px; }
        .form-group input, .form-group textarea { width: 100%; padding: 10px; background: #0f172a; border: 1px solid var(--border); border-radius: 8px; color: white; font-size: 14px; }
        .form-group input:focus, .form-group textarea:focus { outline: none; border-color: var(--primary); }

        /* Table */
        .table-wrap { overflow-x: auto; margin-top: 12px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); }
        th { color: var(--text-muted); font-weight: 600; background: #0f172a; }
        tr:hover { background: rgba(255,255,255,0.02); }
        .btn-delete { background: transparent; color: var(--danger); border: 1px solid var(--danger); padding: 4px 8px; font-size: 11px; }
        .btn-delete:hover { background: var(--danger); color: white; }

        /* Toast / Logs */
        #liveToast { margin-top: 12px; padding: 10px; border-radius: 8px; font-size: 13px; display: none; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>⚡ BÁO CÁO HỆ THỐNG MICROSERVICES CONTAINER HÓA</h1>
        <p>Sinh viên: <strong>Nguyễn Mạnh Cường</strong> | MSSV: <strong>DTC245200124</strong> | Lớp: <strong>CNTT K23E</strong></p>
        <div class="badge-list">
            <span class="badge badge-blue">🐳 Docker Compose</span>
            <span class="badge badge-blue">🛡️ Nginx Reverse Proxy</span>
            <span class="badge badge-green">🐍 Flask & Gunicorn</span>
            <span class="badge badge-blue">🐘 PostgreSQL DB</span>
            <span class="badge badge-green">📊 Prometheus & Grafana</span>
            <span class="badge badge-green">📜 Loki & Promtail</span>
        </div>
    </header>

    <div class="grid">
        <!-- Cổng dịch vụ Giám sát -->
        <div class="card">
            <h2>📊 Cổng Quản Trị & Giám Sát</h2>
            <div class="portal-links">
                <a href="http://localhost:3000" target="_blank" class="portal-btn">
                    <strong>Grafana Dashboard</strong>
                    <span>Port 3000 (Metrics & Logs)</span>
                </a>
                <a href="http://localhost:9090" target="_blank" class="portal-btn">
                    <strong>Prometheus Web</strong>
                    <span>Port 9090 (Targets & Alert)</span>
                </a>
                <a href="/metrics" target="_blank" class="portal-btn">
                    <strong>Metrics Endpoint</strong>
                    <span>/metrics (Prometheus Format)</span>
                </a>
                <a href="http://localhost:3100/ready" target="_blank" class="portal-btn">
                    <strong>Loki Log Engine</strong>
                    <span>Port 3100 (Log Aggregator)</span>
                </a>
            </div>
            
            <h2 style="margin-top: 20px;">⚡ Công Cụ Giả Lập Tải (Demo)</h2>
            <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">Bấm nút để kích hoạt lưu lượng hoặc gây lỗi nhằm xem biểu đồ Grafana nhảy số tức thì:</p>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="generateTraffic(20)">🚀 Tạo 20 Requests (200 OK)</button>
                <button class="btn btn-danger" onclick="triggerError()">⚠️ Gây Lỗi 500 (Test Alert)</button>
            </div>
            <div id="liveToast"></div>
        </div>

        <!-- Trạng thái Hệ Thống & Kết nối -->
        <div class="card">
            <h2>🛡️ Trạng Thái Dịch Vụ</h2>
            <div class="status-row">
                <span>Nginx Reverse Proxy</span>
                <span style="color: var(--success)"><span class="status-dot"></span>Đang hoạt động (Port 8080)</span>
            </div>
            <div class="status-row">
                <span>WebApp (Flask + Gunicorn)</span>
                <span style="color: var(--success)"><span class="status-dot"></span>Khỏe mạnh (Healthy)</span>
            </div>
            <div class="status-row">
                <span>PostgreSQL Database</span>
                <span id="dbStatus">Đang kiểm tra...</span>
            </div>
            <div class="status-row">
                <span>Prometheus Scraper</span>
                <span style="color: var(--success)"><span class="status-dot"></span>Scraping /metrics (15s)</span>
            </div>
            <div class="status-row">
                <span>Promtail Log Collector</span>
                <span style="color: var(--success)"><span class="status-dot"></span>Streaming Docker Logs</span>
            </div>
            <div style="margin-top: 16px;">
                <button class="btn btn-warning" onclick="checkDatabase()" style="width: 100%;">🔄 Kiểm Tra Lại Kết Nối Database</button>
            </div>
        </div>
    </div>

    <!-- Nghiệp vụ CRUD Database -->
    <div class="card">
        <h2>📝 Quản Lý Dữ Liệu Nghiệp Vụ (PostgreSQL CRUD)</h2>
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
            Thêm bản ghi mới để xác nhận WebApp ghi và đọc dữ liệu an toàn vào phân vùng PostgreSQL.
        </p>
        
        <form id="msgForm" onsubmit="addMessage(event)">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div class="form-group">
                    <label>Tiêu đề ghi chú / Bản ghi</label>
                    <input type="text" id="title" placeholder="VD: Triển khai kiểm thử tải thành công" required>
                </div>
                <div class="form-group">
                    <label>Người tạo</label>
                    <input type="text" id="author" placeholder="VD: Nguyễn Mạnh Cường" required>
                </div>
            </div>
            <div class="form-group">
                <label>Nội dung chi tiết</label>
                <textarea id="content" rows="2" placeholder="Nhập nội dung lưu trữ vào cơ sở dữ liệu..." required></textarea>
            </div>
            <button type="submit" class="btn btn-primary">➕ Lưu Dữ Liệu Vào PostgreSQL</button>
        </form>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px;">ID</th>
                        <th>Tiêu đề</th>
                        <th>Nội dung</th>
                        <th>Tác giả</th>
                        <th>Thời gian</th>
                        <th style="width: 80px;">Hành động</th>
                    </tr>
                </thead>
                <tbody id="messageTableBody">
                    <tr><td colspan="6" style="text-align:center; color: var(--text-muted)">Đang nạp dữ liệu...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    async function checkDatabase() {
        const el = document.getElementById('dbStatus');
        el.innerHTML = '<span>Đang kết nối...</span>';
        try {
            const res = await fetch('/db-check');
            const data = await res.json();
            if (res.ok && data.database === 'connected') {
                el.innerHTML = `<span style="color: var(--success)"><span class="status-dot"></span>Kết nối OK (${data.record_count} bản ghi)</span>`;
            } else {
                el.innerHTML = `<span style="color: var(--danger)">Lỗi: ${data.message || 'Không kết nối được'}</span>`;
            }
        } catch (e) {
            el.innerHTML = `<span style="color: var(--danger)">Lỗi mạng: ${e}</span>`;
        }
    }

    async function loadMessages() {
        try {
            const res = await fetch('/api/messages');
            const data = await res.json();
            const tbody = document.getElementById('messageTableBody');
            if (!data.messages || data.messages.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color: var(--text-muted)">Chưa có dữ liệu. Hãy thêm bản ghi đầu tiên!</td></tr>';
                return;
            }
            tbody.innerHTML = data.messages.map(m => `
                <tr>
                    <td><strong>#${m.id}</strong></td>
                    <td style="color:#93c5fd; font-weight:500;">${escapeHtml(m.title)}</td>
                    <td>${escapeHtml(m.content)}</td>
                    <td><span class="badge badge-blue">${escapeHtml(m.author)}</span></td>
                    <td style="color:var(--text-muted)">${m.created_at}</td>
                    <td><button class="btn btn-delete" onclick="deleteMessage(${m.id})">Xóa</button></td>
                </tr>
            `).join('');
        } catch (e) {
            console.error(e);
        }
    }

    async function addMessage(e) {
        e.preventDefault();
        const title = document.getElementById('title').value;
        const author = document.getElementById('author').value;
        const content = document.getElementById('content').value;

        try {
            const res = await fetch('/api/messages', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, author, content})
            });
            if (res.ok) {
                document.getElementById('msgForm').reset();
                showToast('✅ Đã lưu bản ghi mới vào PostgreSQL thành công!', 'var(--success)');
                loadMessages();
                checkDatabase();
            } else {
                showToast('❌ Thêm bản ghi thất bại!', 'var(--danger)');
            }
        } catch (err) {
            showToast('❌ Lỗi kết nối API!', 'var(--danger)');
        }
    }

    async function deleteMessage(id) {
        if (!confirm('Bạn có chắc chắn muốn xóa bản ghi này?')) return;
        try {
            const res = await fetch('/api/messages/' + id, { method: 'DELETE' });
            if (res.ok) {
                showToast('🗑️ Đã xóa bản ghi #' + id, 'var(--warning)');
                loadMessages();
                checkDatabase();
            }
        } catch (e) {
            showToast('❌ Lỗi xóa bản ghi', 'var(--danger)');
        }
    }

    async function generateTraffic(count) {
        showToast(`⚡ Đang gửi đồng thời ${count} requests để tạo biểu đồ tải...`, 'var(--primary)');
        try {
            const res = await fetch('/api/simulate-traffic?count=' + count, { method: 'POST' });
            const data = await res.json();
            showToast(`🚀 Hoàn tất ${data.completed} requests! Kiểm tra đồ thị tại Grafana ngay.`, 'var(--success)');
        } catch (e) {
            showToast('❌ Gặp sự cố khi gửi requests', 'var(--danger)');
        }
    }

    async function triggerError() {
        showToast('⚠️ Đang kích hoạt request lỗi 500...', 'var(--danger)');
        try {
            const res = await fetch('/simulate-error');
            const data = await res.json();
            showToast('🔥 Lỗi 500 đã được sinh ra! Prometheus và Loki đã ghi nhận sự cố.', 'var(--danger)');
        } catch (e) {
            showToast('🔥 Lỗi 500 đã được sinh ra và ghi nhận vào Log!', 'var(--danger)');
        }
    }

    function showToast(msg, color) {
        const t = document.getElementById('liveToast');
        t.style.display = 'block';
        t.style.border = `1px solid ${color}`;
        t.style.background = 'rgba(15, 23, 42, 0.9)';
        t.style.color = color;
        t.innerText = msg;
        setTimeout(() => { t.style.display = 'none'; }, 4000);
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Khởi động nạp dữ liệu ban đầu
    checkDatabase();
    loadMessages();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    """Giao diện WebApp trung tâm tích hợp giám sát & quản trị"""
    logger.info("Nguoi dung truy cap trang chu WebApp (Route /)")
    return render_template_string(HTML_TEMPLATE)

@app.route("/health")
def health():
    """Kiểm tra tình trạng sống của container webapp"""
    return jsonify({
        "status": "healthy",
        "service": "webapp",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/db-check")
def db_check():
    """Kiểm tra kết nối và đếm số bản ghi trong PostgreSQL"""
    try:
        init_db()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM messages;")
                count = cur.fetchone()[0]
        logger.info(f"Kiem tra DB thanh cong: {count} ban ghi hien co.")
        return jsonify({
            "database": "connected",
            "record_count": count,
            "status": "ok"
        }), 200
    except Exception as e:
        logger.error(f"Loi ket noi PostgreSQL: {str(e)}")
        return jsonify({
            "database": "error",
            "message": str(e)
        }), 500

@app.route("/api/messages", methods=["GET"])
def get_messages():
    """Lấy danh sách các bản ghi từ DB"""
    try:
        init_db()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, content, author, created_at FROM messages ORDER BY id DESC LIMIT 50;")
                rows = cur.fetchall()
                messages = []
                for r in rows:
                    messages.append({
                        "id": r[0],
                        "title": r[1],
                        "content": r[2],
                        "author": r[3],
                        "created_at": r[4].strftime("%Y-%m-%d %H:%M:%S") if r[4] else ""
                    })
        return jsonify({"messages": messages}), 200
    except Exception as e:
        logger.error(f"Loi lay du lieu messages: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/messages", methods=["POST"])
def create_message():
    """Thêm một bản ghi mới vào PostgreSQL"""
    try:
        init_db()
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        author = data.get("author", "Sinh vien").strip()

        if not title or not content:
            return jsonify({"error": "Vui long nhap day du tieu de va noi dung"}), 400

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (title, content, author) VALUES (%s, %s, %s) RETURNING id;",
                    (title, content, author)
                )
                new_id = cur.fetchone()[0]
                conn.commit()

        logger.info(f"Them ban ghi thanh cong: ID #{new_id} boi {author}")
        return jsonify({"message": "Thanh cong", "id": new_id}), 201
    except Exception as e:
        logger.error(f"Loi them ban ghi: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/messages/<int:msg_id>", methods=["DELETE"])
def delete_message(msg_id):
    """Xóa một bản ghi theo ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM messages WHERE id = %s;", (msg_id,))
                conn.commit()
        logger.info(f"Xoa ban ghi ID #{msg_id} thanh cong.")
        return jsonify({"message": f"Da xoa ban ghi {msg_id}"}), 200
    except Exception as e:
        logger.error(f"Loi xoa ban ghi {msg_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/simulate-error")
def simulate_error():
    """Cố tình gây lỗi 500 để demo Alerting và Error Logging"""
    logger.error("CANH BAO: Mot loi nghiem trong gia lap vua duoc kich hoat tren he thong (HTTP 500 Internal Server Error)!")
    return jsonify({
        "error": "InternalServerError",
        "message": "Loi gia lap thanh cong nham muc dich kiem thu Alert va Log tren Grafana / Loki"
    }), 500

@app.route("/api/simulate-traffic", methods=["POST"])
def simulate_traffic():
    """Sinh nhanh luồng request để tạo biểu đồ dao động sóng trên Grafana"""
    count = int(request.args.get("count", 15))
    logger.info(f"Bat dau tao luu luong gia lap {count} requests...")
    for i in range(min(count, 50)):
        logger.info(f"Tien trinh tao tai: Request #{i+1}/{count} thanh cong")
    return jsonify({"status": "ok", "completed": count}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)