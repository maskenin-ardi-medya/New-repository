"""Bugünün (Türkiye saati) Reels'ini Instagram'a yayınlar. GitHub Actions tarafından çalıştırılır.
Erişim anahtarı yalnızca IG_TOKEN adlı GitHub gizli değişkeninden okunur."""
import json, os, sys, time, datetime, urllib.request, urllib.parse

TOKEN = os.environ["IG_TOKEN"]
API = "https://graph.facebook.com/v21.0"
IG_USER = "17841448020450351"  # @maskeninardimedya
FORCE = os.environ.get("FORCE_CODE", "").strip()


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print("API hatası:", e.code, e.read().decode()[:500])
        raise


today = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d")
sched = json.load(open(os.path.join(os.path.dirname(__file__), "schedule.json")))
items = [p for p in sched if (p["code"] == FORCE if FORCE else p["date"] == today)]
if not items:
    print("Bugün paylaşım yok:", today)
    sys.exit(0)

done_path = os.path.join(os.path.dirname(__file__), "published.json")
done = json.load(open(done_path)) if os.path.exists(done_path) else {}

for p in items:
    if p["code"] in done and not FORCE:
        print("Zaten yayınlandı:", p["code"])
        continue
    c = call("POST", f"{IG_USER}/media", media_type="REELS", video_url=p["video_url"],
             caption=p["caption"], share_to_feed="true")
    cid = c["id"]
    for _ in range(60):
        time.sleep(10)
        st = call("GET", cid, fields="status_code,status")
        print("durum:", st)
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            sys.exit("Video işlenemedi: " + json.dumps(st))
    pub = call("POST", f"{IG_USER}/media_publish", creation_id=cid)
    print("YAYINLANDI:", p["code"], pub)
    done[p["code"]] = {"media_id": pub.get("id"), "at": datetime.datetime.utcnow().isoformat()}
    json.dump(done, open(done_path, "w"), indent=1)
