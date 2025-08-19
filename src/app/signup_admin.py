# app/signup_admin.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telethon import TelegramClient
from app.models import get_engine, create_tables, get_session, User

def signup_admin(api_id, api_hash, sessions_dir='sessions'):
    if not os.path.exists(sessions_dir):
        os.makedirs(sessions_dir)

    phone = input("شماره موبایل خود را وارد کنید (مثال: +989123456789): ").strip()
    session_path = os.path.join(sessions_dir, f"{phone}.session")

    client = TelegramClient(session_path, api_id, api_hash)

    async def main():
        await client.start(phone=phone)
        me = await client.get_me()
        print(f"ورود موفق: {me.first_name} ({me.id})")
        # ذخیره در دیتابیس
        engine = get_engine()
        create_tables(engine)
        session = get_session(engine)
        user = session.query(User).filter_by(telegram_id=str(me.id)).first()
        if not user:
            user = User(telegram_id=str(me.id), username=me.username, role='admin')
            session.add(user)
            session.commit()
            print("ادمین در دیتابیس ثبت شد.")
        else:
            print("این کاربر قبلاً ثبت شده است.")
        await client.disconnect()

    import asyncio
    with client:
        asyncio.get_event_loop().run_until_complete(main())

if __name__ == "__main__":
    from app.config import API_ID, API_HASH
    signup_admin(API_ID, API_HASH)
