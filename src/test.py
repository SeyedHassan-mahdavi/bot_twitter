from telethon import TelegramClient
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import GetRepliesRequest

API_ID = 25600663
API_HASH = 'a0f63b4d47ed34517184d17b64a46d06'
SESSION = 'sessions/+989137552590.session'
GROUP_ID = -1002045713309

client = TelegramClient(SESSION, API_ID, API_HASH)

async def main():
    # 1. گرفتن لیست تاپیک‌ها
    result = await client(GetForumTopicsRequest(
        channel=GROUP_ID,
        offset_date=0,
        offset_id=0,
        offset_topic=0,
        limit=100
    ))
    # 2. پیمایش روی تاپیک‌ها و خوندن پیام‌های هر تاپیک
    for topic in result.topics:
        print(f"\n🧵 تاپیک: {topic.title} | ID: {topic.id} | پیام مادر: {topic.top_message}")
        try:
            replies = await client(GetRepliesRequest(
                peer=GROUP_ID,
                msg_id=topic.id,  # این دقیقاً msg_id مادر همون تاپیکه
                offset_id=0,
                offset_date=0,
                add_offset=0,
                limit=10,     # هر چندتا خواستی بزار (تست)
                max_id=0,
                min_id=0,
                hash=0
            ))
            for m in replies.messages:
                print(f"{m.id} => {m.message}")
        except Exception as e:
            print(f"[!] خطا برای تاپیک {topic.title}: {e}")

with client:
    client.loop.run_until_complete(main())
