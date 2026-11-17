"""Zamanı gelen Reels'i Instagram'a yayınlar. GitHub Actions her 30 dakikada bir çalıştırır.
Erişim anahtarı yalnızca IG_TOKEN adlı GitHub gizli değişkeninden okunur."""
import json, os, sys, time, datetime, urllib.request, urllib.parse, urllib.error

TOKEN = os.environ["IG_TOKEN"]
API = "https://graph.facebook.com/v21.0"
IG_USER = "17841448020450351"  # @maskeninardimedya
FORCE = os.environ.get("FORCE_CODE", "").strip()
HERE = os.path.dirname(os.path.abspath(__file__))


def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params)
    url = f"{API}/{path}"
    req = urllib.request.Request(url + "?" + data) if method == "GET" else \
        urllib.request.Request(url, data=data.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print("API hatası:", e.code, e.read().decode()[:500])
        raise


now_tr = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
sched = json.load(open(os.path.join(HERE, "schedule.json")))
done_path = os.path.join(HERE, "published.json")
done = json.load(open(done_path)) if os.path.exists(done_path) else {}

if FORCE:
    due = [p for p in sched if p["code"] == FORCE]
else:
    due = [p for p in sched if p["code"] not in done and
           datetime.datetime.strptime(p["at"], "%Y-%m-%d %H:%M") <= now_tr]
if not due:
    print("Şu an yayınlanacak Reels yok:", now_tr.strftime("%Y-%m-%d %H:%M"))
    sys.exit(0)

p = due[0]  # her çalışmada en fazla bir Reels
print("Yayınlanıyor:", p["code"], p["at"])
c = call("POST", f"{IG_USER}/media", media_type="REELS", video_url=p["video_url"],
         caption=p["caption"], share_to_feed="true")
cid = c["id"]
for _ in range(60):
    time.sleep(10)
    st = call("GET", cid, fields="status_code,status")
    print("durum:", st.get("status_code"))
    if st.get("status_code") == "FINISHED":
        break
    if st.get("status_code") in ("ERROR", "EXPIRED"):
        sys.exit("Video işlenemedi: " + json.dumps(st))
pub = call("POST", f"{IG_USER}/media_publish", creation_id=cid)
print("YAYINLANDI:", p["code"], pub)
done[p["code"]] = {"media_id": pub.get("id"), "at": now_tr.strftime("%Y-%m-%d %H:%M")}
json.dump(done, open(done_path, "w"), indent=1)
