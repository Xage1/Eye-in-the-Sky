import inspect, socket, time
host = "api.openweathermap.org"
for fam, label in ((socket.AF_UNSPEC, "any"), (socket.AF_INET, "ipv4"), (socket.AF_INET6, "ipv6")):
    s = time.perf_counter()
    try:
        r = socket.getaddrinfo(host, 443, fam, socket.SOCK_STREAM); res = f"{len(r)} addrs"
    except Exception as e:
        res = f"ERR {type(e).__name__}"
    print(f"DNS {label:5s} {(time.perf_counter()-s)*1000:8.0f} ms  {res}")
import httpx
for url in ("https://api.openweathermap.org/", "https://example.com/"):
    s = time.perf_counter()
    try:
        res = httpx.get(url, timeout=20).status_code
    except Exception as e:
        res = f"ERR {type(e).__name__}"
    print(f"GET {url:36s} {(time.perf_counter()-s)*1000:8.0f} ms  {res}")
from app.controllers import skyController as sc
from app.utils import astronomy as au
for label, fn in (("sc.get_sky_visibility", sc.get_sky_visibility), ("au.get_visibility_forecast", au.get_visibility_forecast)):
    print("\n#####", label)
    print("\n".join(l for l in inspect.getsource(fn).splitlines() if len(l) < 200))