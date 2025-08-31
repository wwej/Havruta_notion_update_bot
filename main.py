import requests
import hashlib
import os
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Bot
TZ = ZoneInfo("Asia/Taipei")

print("[DEBUG] running main.py from repo")

# 載入 .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
NOTION_URL = os.getenv("NOTION_URL")

HASH_FILE = "last_hash.txt"
bot = Bot(token=TELEGRAM_TOKEN)

def get_notion_content(url):
    """
    抓取 Notion 公開頁面文字內容：
    - 強化 headers
    - 加上 timeout 與重試
    - 詳細 log（status code / 長度）
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.notion.so/",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    for attempt in range(1, 4):  # 最多重試 3 次
        try:
            resp = requests.get(url, headers=headers, allow_redirects=True, timeout=20)
            print(f"[Fetch] attempt={attempt} status={resp.status_code} url={resp.url}")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text(separator="\n")
                print(f"[Fetch] text_length={len(text)}")
                return text
            else:
                print(f"[Fetch] non-200 status, body_len={len(resp.text)}")
        except Exception as e:
            print(f"[Fetch] error on attempt {attempt}: {e}")
    return None

def get_content_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_last_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save_current_hash(hash_value):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        f.write(hash_value)
    print(f"[Hash] saved to {os.path.abspath(HASH_FILE)}")

def send_telegram_message(message):
    try:
        bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)
        print("[TG] message sent")
    except Exception as e:
        print(f"[TG] send error: {e}")

def main():
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[Run] check at {now}")
    print(f"[Run] NOTION_URL={NOTION_URL}")

    content = get_notion_content(NOTION_URL)
    if not content:
        print("[Run] No content fetched; skip hashing & file write.")
        send_telegram_message(f"⚠️ 無法抓取 Notion 頁面（{now}）")
        return

    current_hash = get_content_hash(content)
    last_hash = load_last_hash()
    print(f"[Hash] current={current_hash[:10]}..., last={str(last_hash)[:10] if last_hash else 'None'}")

    if last_hash is None:
        save_current_hash(current_hash)
        send_telegram_message(f"🟢 已建立監看（{now}）。")
        print("[Run] baseline created")
        return

    # 只擷取前 300 字做通知
    snippet = content.strip().replace("\n\n", "\n")
    snippet = (snippet[:300] + "...") if len(snippet) > 300 else snippet

    if current_hash != last_hash:
        send_telegram_message(f"📌 Notion 頁面有更新！\n\n🕒 {now}\n📄 前段內容：\n{snippet}")
        save_current_hash(current_hash)
        print("[Run] changed -> notified & saved hash")
    else:
        send_telegram_message(f"🟢 Notion 無更新（{now}）")
        # ✅ 即使沒變更也確認檔案存在（首次跑時保險）
        if not os.path.exists(HASH_FILE):
            save_current_hash(current_hash)
            print("[Run] no change but hash file created for the first time")
        else:
            print("[Run] no change")

if __name__ == "__main__":
    main()

