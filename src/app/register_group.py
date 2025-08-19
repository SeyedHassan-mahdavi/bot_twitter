# app/register_group.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telethon import TelegramClient
from app.models import get_engine, get_session, create_tables, User, Group
from app.config import API_ID, API_HASH

def register_group(session_path, api_id, api_hash, group_id):
    client = TelegramClient(session_path, api_id, api_hash)
    engine = get_engine()
    create_tables(engine)
    session = get_session(engine)

    async def main():
        await client.start()
        me = await client.get_me()
        user = session.query(User).filter_by(telegram_id=str(me.id)).first()
        if not user:
            print("کاربر در دیتابیس وجود ندارد!")
            return

        # اینجا آیدی گروه رو مستقیم می‌دیم (int)
        group_entity = await client.get_entity(group_id)
        # ثبت گروه در دیتابیس
        group = session.query(Group).filter_by(group_id=str(group_entity.id)).first()
        if not group:
            group = Group(
                group_id=str(group_entity.id),
                title=getattr(group_entity, "title", ""),
                owner_id=user.id
            )
            session.add(group)
            session.commit()
            print(f"✅ گروه {group.title} با موفقیت ثبت شد.")
        else:
            print("این گروه قبلاً ثبت شده است.")

        await client.disconnect()

    import asyncio
    with client:
        asyncio.get_event_loop().run_until_complete(main())

if __name__ == "__main__":
    # اینجا مسیر فایل سشن و آیدی گروه رو مستقیم بده
    session_path = "sessions/+989137552590.session"
    group_id = -1002045713309   # ← آیدی عددی گروه به صورت int
    register_group(session_path, API_ID, API_HASH, group_id)
