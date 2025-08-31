import requests
import hashlib
import os
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot

# 載入 .env 環境變數
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
NOTION_URL = os.getenv("NOTION_URL")

# Hash 記錄檔路徑
HASH_FILE = "last_hash.txt"

# 初始化 Telegram Bot
bot = Bot(token=TELEGRAM_TOKEN)

def get_notion_content(url):
    """取得 Notion 公開頁面 HTML 內容（純文字）"""
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()  # 取出文字內容即可
    except Exception as e:
        print(f"❌ 抓取 Notion 頁面失敗: {e}")
        return None

def get_content_hash(text):
    """回傳文字內容的 hash 值"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_last_hash():
    """讀取上次 hash"""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    return None

def save_current_hash(hash_value):
    """儲存當前 hash"""
    with open(HASH_FILE, "w") as f:
        f.write(hash_value)

def send_telegram_message(message):
    """傳送 Telegram 訊息"""
    try:
        bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)
    except Exception as e:
        print(f"❌ 傳送 Telegram 訊息失敗: {e}")

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"📡 檢查時間：{now}")
    content = get_notion_content(NOTION_URL)

    if content is None:
        send_telegram_message(f"⚠️ 無法抓取 Notion 頁面（{now}）")
        return

    current_hash = get_content_hash(content)
    last_hash = load_last_hash()

    if current_hash != last_hash:
        snippet = content[:300] + "..." if len(content) > 300 else content
        message = f"📌 Notion 頁面有更新！\n\n🕒 {now}\n📄 前段內容：\n{snippet}"
        send_telegram_message(message)
        save_current_hash(current_hash)
        print("✅ 有變更，已發送通知")
    else:
        send_telegram_message(f"🟢 Notion 無更新（{now}）")
        print("✅ 無變更，已發送通知")

if __name__ == "__main__":
    main()
# 在 main() 裡抓到 content 後加上兩行
print(f"Fetched Notion content length: {len(content)}")
print(f"Will write hash file to: {os.path.abspath(HASH_FILE)}")
