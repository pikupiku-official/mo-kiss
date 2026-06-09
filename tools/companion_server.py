"""
mo-kiss Companion Server
========================
KSファイルをスマホのブラウザで閲覧するための読み取り専用Webサーバー。
依存: Python標準ライブラリのみ（Flask不要）

起動方法:
    python tools/companion_server.py

外部アクセス（Cloudflare Tunnel）:
    cloudflared tunnel --url http://localhost:8765
"""

import os
import sys
import hashlib
import hmac
import secrets
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from datetime import datetime

# ── 設定 ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
EVENTS_DIR   = PROJECT_ROOT / "events"
PORT         = 8765

# ログイン認証情報 (変更してください)
AUTH_USER     = "mokiss"
AUTH_PASSWORD = "1919"   # ← 必ず変更してください

# セッション管理 (メモリ上。サーバー再起動でログアウト)
_sessions: dict[str, str] = {}   # token -> username

def _make_token() -> str:
    return secrets.token_hex(32)

def _check_login(user: str, password: str) -> bool:
    ok_u = hmac.compare_digest(user.encode(), AUTH_USER.encode())
    ok_p = hmac.compare_digest(password.encode(), AUTH_PASSWORD.encode())
    return ok_u and ok_p

def _get_session(cookie_header: str) -> str | None:
    """Cookieヘッダーからセッショントークンを取得"""
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == "mksession":
            return _sessions.get(v.strip())
    return None

# ── HTML スタイル ─────────────────────────────────────────
STYLE = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #1a1a2e; color: #e0e0e0; min-height: 100vh;
  }
  header {
    background: #16213e; padding: 12px 16px;
    display: flex; align-items: center; gap: 10px;
    position: sticky; top: 0; z-index: 100;
    border-bottom: 2px solid #0f3460;
  }
  header h1 { font-size: 1.1rem; color: #e94560; }
  header a  { color: #a0a0c0; text-decoration: none; font-size: 0.85rem; }
  .container { padding: 16px; max-width: 900px; margin: 0 auto; }
  /* ファイル一覧 */
  .file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 10px; margin-top: 12px;
  }
  .file-card {
    background: #16213e; border: 1px solid #0f3460;
    border-radius: 8px; padding: 12px 8px; text-align: center;
    text-decoration: none; color: #c0c0e0;
    transition: background 0.15s;
  }
  .file-card:hover, .file-card:active { background: #0f3460; color: #fff; }
  .file-card .name { font-size: 0.9rem; font-weight: bold; }
  .file-card .size { font-size: 0.7rem; color: #888; margin-top: 4px; }
  /* KSビューア */
  .ks-view {
    background: #16213e; border: 1px solid #0f3460;
    border-radius: 8px; padding: 16px; margin-top: 12px;
    white-space: pre-wrap; font-family: "Courier New", monospace;
    font-size: 0.82rem; line-height: 1.6; overflow-x: auto;
    word-break: break-all;
  }
  .ks-label   { color: #e94560; font-weight: bold; }
  .ks-tag     { color: #4fc3f7; }
  .ks-comment { color: #666; font-style: italic; }
  .ks-dialog  { color: #c8e6c9; }
  /* メタ情報 */
  .meta { font-size: 0.78rem; color: #888; margin-top: 6px; margin-bottom: 4px; }
  .badge {
    display: inline-block; background: #0f3460;
    border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; color: #80b0e0;
  }
  h2 { font-size: 1rem; color: #a0c8f0; margin-bottom: 6px; }
  .back-btn {
    display: inline-block; margin-bottom: 10px;
    background: #0f3460; color: #a0c8f0; border-radius: 6px;
    padding: 6px 14px; text-decoration: none; font-size: 0.85rem;
  }
  .back-btn:hover { background: #e94560; color: #fff; }
  /* ログインフォーム */
  .login-wrap {
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh;
  }
  .login-box {
    background: #16213e; border: 1px solid #0f3460;
    border-radius: 12px; padding: 32px 24px; width: 100%; max-width: 340px;
  }
  .login-box h2 { text-align: center; color: #e94560; margin-bottom: 24px; font-size: 1.3rem; }
  .login-box input {
    display: block; width: 100%; padding: 12px 14px;
    background: #0f1929; border: 1px solid #0f3460; border-radius: 8px;
    color: #e0e0e0; font-size: 1rem; margin-bottom: 14px;
    outline: none;
  }
  .login-box input:focus { border-color: #4fc3f7; }
  .login-box button {
    width: 100%; padding: 13px;
    background: #e94560; border: none; border-radius: 8px;
    color: #fff; font-size: 1rem; font-weight: bold; cursor: pointer;
  }
  .login-box button:hover { background: #c73050; }
  .login-err { color: #e94560; text-align: center; font-size: 0.85rem; margin-top: 12px; }
</style>
"""

# ── HTML生成 ──────────────────────────────────────────────

def fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    return f"{n // 1024}KB"

def ks_highlight(text: str) -> str:
    lines = text.splitlines()
    out = []
    for line in lines:
        esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = line.strip()
        if s.startswith("*"):
            out.append(f'<span class="ks-label">{esc}</span>')
        elif s.startswith("[") or s.startswith("@"):
            out.append(f'<span class="ks-tag">{esc}</span>')
        elif s.startswith(";") or s.startswith("//"):
            out.append(f'<span class="ks-comment">{esc}</span>')
        elif "「" in s or "」" in s or "『" in s or "』" in s:
            out.append(f'<span class="ks-dialog">{esc}</span>')
        else:
            out.append(esc)
    return "\n".join(out)

def page_login(error: bool = False) -> str:
    err_html = '<div class="login-err">ユーザー名またはパスワードが違います</div>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>{STYLE}<title>mo-kiss ログイン</title></head>
<body>
<div class="login-wrap">
  <div class="login-box">
    <h2>mo-kiss</h2>
    <form method="POST" action="/login">
      <input type="text"     name="user"     placeholder="ユーザー名" autocomplete="username">
      <input type="password" name="password" placeholder="パスワード" autocomplete="current-password">
      <button type="submit">ログイン</button>
    </form>
    {err_html}
  </div>
</div>
</body>
</html>"""

def page_index(files: list) -> str:
    cards = ""
    for f in files:
        url = "/ks/" + urllib.parse.quote(f["rel"])
        cards += (
            f'<a class="file-card" href="{url}">'
            f'<div class="name">{f["name"]}</div>'
            f'<div class="size">{fmt_size(f["size"])}</div>'
            f'</a>\n'
        )
    count = len(files)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>{STYLE}<title>mo-kiss KSビューア</title></head>
<body>
<header>
  <h1>mo-kiss</h1>
  <span style="color:#888;font-size:0.85rem">KSビューア（読み取り専用）</span>
  <span style="margin-left:auto"><a href="/logout">ログアウト</a></span>
</header>
<div class="container">
  <h2>イベントファイル一覧</h2>
  <div class="meta">
    <span class="badge">{count}ファイル</span>
    &nbsp;{datetime.now().strftime("%H:%M")} 現在
  </div>
  <div class="file-grid">
{cards}  </div>
</div>
</body>
</html>"""

def page_ks(rel: str, content: str, meta: dict) -> str:
    highlighted = ks_highlight(content)
    lines = content.count("\n") + 1
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>{STYLE}<title>{meta['name']} - mo-kiss</title></head>
<body>
<header>
  <h1>mo-kiss</h1>
  <a href="/">← 一覧</a>
  <span style="margin-left:auto"><a href="/logout">ログアウト</a></span>
</header>
<div class="container">
  <a class="back-btn" href="/">← 一覧に戻る</a>
  <h2>{meta['name']}.ks</h2>
  <div class="meta">
    <span class="badge">{lines}行</span>
    &nbsp;<span class="badge">{fmt_size(meta['size'])}</span>
    &nbsp;更新: {meta['mtime']}
  </div>
  <div class="ks-view">{highlighted}</div>
</div>
</body>
</html>"""

def page_error(code: int, msg: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>{STYLE}<title>Error {code}</title></head>
<body>
<header><h1>mo-kiss</h1></header>
<div class="container" style="padding-top:40px;text-align:center">
  <div style="font-size:3rem">{code}</div>
  <div style="color:#e94560;margin-top:8px">{msg}</div>
  <a class="back-btn" href="/" style="margin-top:20px;display:inline-block">← 一覧に戻る</a>
</div>
</body>
</html>"""

# ── ファイル操作 ──────────────────────────────────────────

def list_ks_files() -> list:
    files = []
    for p in sorted(EVENTS_DIR.glob("**/*.ks")):
        rel = p.relative_to(EVENTS_DIR)
        files.append({
            "name":  p.stem,
            "rel":   str(rel).replace("\\", "/"),
            "size":  p.stat().st_size,
            "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return files

def read_ks_file(rel: str):
    target = (EVENTS_DIR / rel).resolve()
    if not str(target).startswith(str(EVENTS_DIR.resolve())):
        return None, "forbidden"
    if not target.exists():
        return None, "not_found"
    try:
        return target.read_text(encoding="utf-8-sig"), None
    except Exception as e:
        return None, str(e)

# ── HTTPハンドラ ──────────────────────────────────────────

class KSHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {self.address_string()} {fmt % args}")

    # ── 共通ユーティリティ ──

    def send_html(self, html: str, status: int = 200, extra_headers: dict = None):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, location: str, extra_headers: dict = None):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()

    def is_logged_in(self) -> bool:
        return _get_session(self.headers.get("Cookie", "")) is not None

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length > 0 else b""

    # ── GETルーティング ──

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        # ログイン不要
        if path == "/login":
            self.send_html(page_login())
            return
        if path == "/logout":
            cookie = self.headers.get("Cookie", "")
            for part in cookie.split(";"):
                k, _, v = part.strip().partition("=")
                if k == "mksession":
                    _sessions.pop(v.strip(), None)
            self.redirect("/login",
                extra_headers={"Set-Cookie": "mksession=; Max-Age=0; Path=/"})
            return

        # ログイン必須
        if not self.is_logged_in():
            self.redirect("/login")
            return

        if path == "/" or path == "/index.html":
            self.send_html(page_index(list_ks_files()))
        elif path.startswith("/ks/"):
            rel = path[4:]
            if not rel:
                self.send_html(page_error(400, "ファイル名が指定されていません"), 400)
                return
            content, err = read_ks_file(rel)
            if err:
                self.send_html(page_error(404, f"ファイルが見つかりません: {rel}"), 404)
                return
            target = (EVENTS_DIR / rel).resolve()
            meta = {
                "name":  target.stem,
                "size":  target.stat().st_size,
                "mtime": datetime.fromtimestamp(target.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            }
            self.send_html(page_ks(rel, content, meta))
        else:
            self.send_html(page_error(404, "ページが見つかりません"), 404)

    # ── POSTルーティング ──

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path == "/login":
            body = self.read_body().decode("utf-8", errors="replace")
            params = dict(urllib.parse.parse_qsl(body))
            user = params.get("user", "")
            pwd  = params.get("password", "")
            if _check_login(user, pwd):
                token = _make_token()
                _sessions[token] = user
                # セキュアCookie（HTTPS経由のみ送信）
                cookie = f"mksession={token}; Path=/; HttpOnly; SameSite=Lax"
                self.redirect("/", extra_headers={"Set-Cookie": cookie})
            else:
                self.send_html(page_login(error=True), status=401)
        else:
            self.send_html(page_error(404, "Not found"), 404)


# ── エントリポイント ──────────────────────────────────────

def main():
    if not EVENTS_DIR.exists():
        print(f"[ERROR] eventsディレクトリが見つかりません: {EVENTS_DIR}")
        sys.exit(1)

    if AUTH_PASSWORD == "changeme":
        print("=" * 60)
        print("  [WARNING] パスワードが初期値のままです！")
        print("  外部公開前に companion_server.py の")
        print("  AUTH_PASSWORD を変更してください。")
        print("=" * 60)

    server = HTTPServer(("0.0.0.0", PORT), KSHandler)
    print(f"")
    print(f"  mo-kiss Companion Server 起動中")
    print(f"  ローカル: http://localhost:{PORT}")
    print(f"  外部公開: cloudflared tunnel --url http://localhost:{PORT}")
    print(f"")
    print(f"  ログインID:  {AUTH_USER}")
    print(f"  停止: Ctrl+C")
    print(f"")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] サーバー停止")
        server.server_close()

if __name__ == "__main__":
    main()
