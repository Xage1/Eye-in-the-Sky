"""
Entry point for the Wispbyte server (it runs /home/container/main.py).
Loads .env, optionally opens the ngrok tunnel, then starts the API with the scheduled jobs.
"""
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
# packages installed by the panel with "pip install --prefix .local"
for p in (ROOT / ".local" / "lib").glob("python3*/site-packages"):
    sys.path.insert(0, str(p))


def load_env(path: Path) -> int:
    n = 0
    if not path.exists():
        return 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        if k and k not in os.environ:
            os.environ[k] = v
            n += 1
    return n


def start_tunnel(port: int) -> None:
    token = os.environ.get("NGROK_AUTHTOKEN")
    domain = os.environ.get("NGROK_DOMAIN")
    if not token or not domain:
        print("[eyesky] no tunnel configured (NGROK_AUTHTOKEN / NGROK_DOMAIN missing)", flush=True)
        return
    time.sleep(20)  # let the API come up first
    try:
        from pyngrok import conf, ngrok
        bin_dir = ROOT / ".ngrok"
        bin_dir.mkdir(exist_ok=True)
        cfg = conf.PyngrokConfig(ngrok_path=str(bin_dir / "ngrok"), auth_token=token)
        conf.set_default(cfg)
        t = ngrok.connect(port, "http", domain=domain)
        print("[eyesky] tunnel up: " + str(t.public_url), flush=True)
    except Exception as exc:  # the API keeps running on the raw IP:port if this fails
        print("[eyesky] tunnel failed: " + str(exc), flush=True)


def main() -> None:
    n = load_env(ROOT / ".env")
    port = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or 8000)
    print("[eyesky] loaded %d settings from .env, starting on port %d" % (n, port), flush=True)
    threading.Thread(target=start_tunnel, args=(port,), daemon=True).start()
    import uvicorn
    uvicorn.run("app.lite_main:app", host="0.0.0.0", port=port, workers=1, log_level="info")


if __name__ == "__main__":
    main()
