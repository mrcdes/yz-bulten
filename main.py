import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from googleapiclient.discovery import build

# ─── AYARLAR (GitHub Secrets'tan okunur) ──────────────────────────────────────
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
GMAIL_USER      = os.environ["GMAIL_USER"]       # gönderen@gmail.com
GMAIL_PASS      = os.environ["GMAIL_PASS"]       # Gmail Uygulama Şifresi
TO_EMAIL        = os.environ["TO_EMAIL"]         # alici@gmail.com

# ─── ARAMA SORGU LİSTESİ ──────────────────────────────────────────────────────
QUERIES = [
    "yapay zeka teknoloji 2025",
    "artificial intelligence news",
    "AI machine learning latest",
    "ChatGPT Gemini Claude yeni",
    "deep learning robotics 2025",
]

def search_youtube(youtube, query, max_results=3):
    """Belirtilen sorgu için YouTube'da son 24 saatin videolarını arar."""
    published_after = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        order="date",
        publishedAfter=published_after,
        maxResults=max_results,
        relevanceLanguage="tr",   # Türkçe öncelikli, yabancı da gelir
    )
    response = request.execute()
    return response.get("items", [])

def get_top_videos(youtube, total=5):
    """Tüm sorgulardan video toplar, tekrarları kaldırır ve ilk 5'i döner."""
    seen_ids = set()
    videos = []

    for query in QUERIES:
        items = search_youtube(youtube, query)
        for item in items:
            vid_id = item["id"]["videoId"]
            if vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)
            snippet = item["snippet"]
            videos.append({
                "title":     snippet["title"],
                "channel":   snippet["channelTitle"],
                "published": snippet["publishedAt"][:10],
                "url":       f"https://www.youtube.com/watch?v={vid_id}",
                "thumbnail": snippet["thumbnails"]["high"]["url"],
                "description": snippet.get("description", "")[:150],
            })
        if len(videos) >= total:
            break

    return videos[:total]

def build_html(videos):
    """Güzel bir HTML e-posta şablonu oluşturur."""
    today = datetime.now().strftime("%d %B %Y")
    rows = ""
    for i, v in enumerate(videos, 1):
        rows += f"""
        <tr>
          <td style="padding:20px 0; border-bottom:1px solid #eee;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="40" style="font-size:28px; font-weight:bold;
                    color:#6366f1; vertical-align:top; padding-right:12px;">{i}</td>
                <td>
                  <a href="{v['url']}" style="font-size:16px; font-weight:bold;
                     color:#1a1a2e; text-decoration:none;">{v['title']}</a><br>
                  <span style="font-size:13px; color:#888;">📺 {v['channel']}
                    &nbsp;|&nbsp; 📅 {v['published']}</span><br>
                  <p style="font-size:13px; color:#555; margin:6px 0 10px;">
                    {v['description']}…</p>
                  <a href="{v['url']}"
                     style="background:#6366f1; color:#fff; padding:8px 18px;
                            border-radius:6px; text-decoration:none;
                            font-size:13px; font-weight:bold;">
                    ▶ İzle
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f4f9;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#f4f4f9; padding:30px 0;">
        <tr><td align="center">
          <table width="620" cellpadding="0" cellspacing="0"
                 style="background:#ffffff; border-radius:12px;
                        box-shadow:0 4px 20px rgba(0,0,0,.08); overflow:hidden;">

            <!-- HEADER -->
            <tr>
              <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);
                         padding:30px 36px; color:#fff;">
                <h1 style="margin:0;font-size:22px;">🤖 Günlük Yapay Zeka Haberleri</h1>
                <p style="margin:6px 0 0; opacity:.85; font-size:14px;">
                  {today} • En Güncel 5 YouTube Videosu
                </p>
              </td>
            </tr>

            <!-- VİDEOLAR -->
            <tr>
              <td style="padding:10px 36px 30px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                  {rows}
                </table>
              </td>
            </tr>

            <!-- FOOTER -->
            <tr>
              <td style="background:#f8f8ff; padding:20px 36px;
                         text-align:center; font-size:12px; color:#aaa;">
                Bu e-posta GitHub Actions tarafından otomatik gönderilmiştir.<br>
                Powered by YouTube Data API &amp; Python 🐍
              </td>
            </tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    return html

def send_email(subject, html_body):
    """Gmail SMTP üzerinden HTML e-posta gönderir."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = TO_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())
    print(f"✅ E-posta gönderildi → {TO_EMAIL}")

def main():
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY,
                cache_discovery=False)
    print("🔍 YouTube'da aranıyor…")
    videos = get_top_videos(youtube, total=5)

    if not videos:
        print("⚠️  Bugün uygun video bulunamadı.")
        return

    print(f"✅ {len(videos)} video bulundu.")
    html    = build_html(videos)
    subject = f"🤖 Günlük YZ Videoları | {datetime.now().strftime('%d.%m.%Y')}"
    send_email(subject, html)

if __name__ == "__main__":
    main()
