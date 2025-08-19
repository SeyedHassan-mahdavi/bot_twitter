from telethon import TelegramClient
from app.config import API_ID, API_HASH

SESSION_PATH = "sessions/+989137552590.session"
GROUP_ID = -1002045713309

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)

async def main():
    # لیست چت‌ها رو بگیر و چاپ کن
    print("---- لیست چت‌ها ----")
    async for dialog in client.iter_dialogs():
        print(dialog.name, dialog.id)
    print("-------------------")
    # سعی کن گروه رو بگیری
    try:
        group_entity = await client.get_entity(GROUP_ID)
        print("گروه پیدا شد:", group_entity.title, group_entity.id)
    except Exception as e:
        print("ارور:", e)

with client:
    client.loop.run_until_complete(main())
