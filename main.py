import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
GMAIL_USER      = os.environ["GMAIL_USER"]
GMAIL_PASS      = os.environ["GMAIL_PASS"]
TO_EMAIL        = os.environ["TO_EMAIL"]

QUERIES = [
    "yapay zeka 2026",
    "artificial intelligence news 2026",
    "ChatGPT Gemini Claude",
    "AI robotics latest",
    "machine learning 2026",
]

def get_youtube():
    return build(
        "youtube", "v3",
        developerKey=YOUTUBE_API_KEY,
        cache_discovery=False,
        http=httplib2.Http()
    )

def search_videos(youtube, query):
    published_after = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    res = youtube.search().list(
        q=query, part="snippet", type="video",
        order="date", publishedAfter=published_after,
        maxResults=3
    ).execute()
    return res.get("items", [])

def get_top5():
    youtube = get_youtube()
    seen, videos = set(), []
    for q in QUERIES:
        for item in search_videos(youtube, q):
            vid = item["id"]["videoId"]
            if vid in seen: continue
            seen.add(vid)
            s = item["snippet"]
            videos.append({
                "title": s["title"],
                "channel": s["channelTitle"],
                "date": s["publishedAt"][:10],
                "url": f"https://www.youtube.com/watch?v={vid}",
                "desc": s.get("description","")[:120],
            })
        if len(videos) >= 5: break
    return videos[:5]

def build_html(videos):
    today = datetime.now().strftime("%d %B %Y")
    rows = ""
    for i, v in enumerate(videos, 1):
        rows += f"""<tr><td style="padding:16px 0;border-bottom:1px solid #eee;">
        <b style="color:#6366f1;">{i}.</b>
        <a href="{v['url']}" style="font-size:15px;font-weight:bold;color:#1a1a2e;text-decoration:none;">
        {v['title']}</a><br>
        <span style="font-size:12px;color:#888;">📺 {v['channel']} | 📅 {v['date']}</span><br>
        <p style="font-size:12px;color:#555;margin:4px 0;">{v['desc']}</p>
        <a href="{v['url']}" style="background:#6366f1;color:#fff;padding:6px 14px;
        border-radius:5px;text-decoration:none;font-size:12px;">▶ İzle</a>
        </td></tr>"""
    return f"""<html><body style="font-family:Arial;background:#f4f4f9;padding:20px;">
    <div style="max-width:600px;margin:auto;background:#fff;border-radius:10px;overflow:hidden;">
    <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:24px;color:#fff;">
    <h2 style="margin:0;">🤖 Günlük YZ Videoları</h2>
    <p style="margin:4px 0 0;opacity:.85;">{today}</p></div>
    <div style="padding:16px 24px;"><table width="100%">{rows}</table></div>
    <div style="background:#f8f8ff;padding:14px;text-align:center;font-size:11px;color:#aaa;">
    Otomatik gönderildi • YouTube Data API + Python</div>
    </div></body></html>"""

def send_email(html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🤖 YZ Videoları | {datetime.now().strftime('%d.%m.%Y')}"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
    print(f"✅ Gönderildi → {TO_EMAIL}")

def main():
    print("🔍 Aranıyor...")
    videos = get_top5()
    if not videos:
        print("⚠️ Video bulunamadı.")
        return
    print(f"✅ {len(videos)} video bulundu.")
    send_email(build_html(videos))

if __name__ == "__main__":
    main()
```

Ayrıca **`requirements.txt`** dosyasını da güncelle:
```
google-api-python-client==2.118.0
httplib2
