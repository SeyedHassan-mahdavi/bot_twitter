# import sys, os, re
# import datetime
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from telethon import TelegramClient
# from app.models import get_engine, get_session, create_tables, Campaign, City, Tweet
# from app.config import API_ID, API_HASH

# SESSION_PATH = "sessions/+989137552590.session"
# GROUP_ID = -1002045713309
# LIMIT = 1000  # تعداد پیام

# client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
# engine = get_engine()
# create_tables(engine)
# session = get_session(engine)

# def extract_twitter_info(url):
#     m = re.match(r'https://(?:x\.com|twitter\.com)/([^/]+)/status/(\d+)', url)
#     if m:
#         return m.group(1), m.group(2)  # username, tweet_id
#     return None, None

# def extract_links_and_campaigns(message):
#     links = re.findall(r'https?://\S+', message)
#     hashtags = re.findall(r'#\w+', message)
#     campaigns = [h.replace('#', '') for h in hashtags]
#     return links, campaigns

# async def main():
#     city_name = "نامشخص"  # اگر اطلاعات شهر نداشتی، این مقدار را استفاده کن
#     city = session.query(City).filter_by(name=city_name).first()
#     if not city:
#         city = City(name=city_name)
#         session.add(city)
#         session.commit()

#     count = 0
#     async for msg in client.iter_messages(GROUP_ID, limit=LIMIT):
#         if not msg.message:
#             continue

#         links, campaigns = extract_links_and_campaigns(msg.message)
#         if not links or not campaigns:
#             continue  # اگر هیچ لینک یا کمپینی نیست، رد کن

#         for campaign_name in campaigns:
#             # کمپین رو پیدا کن یا بساز
#             campaign = session.query(Campaign).filter_by(name=campaign_name).first()
#             if not campaign:
#                 campaign = Campaign(name=campaign_name, hashtag=f"#{campaign_name}")
#                 session.add(campaign)
#                 session.commit()

#             for url in links:
#                 username, tweet_id = extract_twitter_info(url)
#                 if not tweet_id:
#                     continue
#                 # اگر قبلاً در این کمپین ذخیره شده، رد کن
#                 exist = session.query(Tweet).filter_by(campaign_id=campaign.id, tweet_id=tweet_id).first()
#                 if exist:
#                     continue
#                 tweet = Tweet(
#                     campaign_id=campaign.id,
#                     city_id=city.id,
#                     twitter_username=username,
#                     tweet_id=tweet_id,
#                     url=url,
#                     datetime=msg.date
#                 )
#                 session.add(tweet)
#                 count += 1
#         session.commit()
#     print(f"✅ {count} توییت جدید ثبت شد.")

# with client:
#     import asyncio
#     asyncio.get_event_loop().run_until_complete(main())



# import re
# from app.models import Campaign, City, Tweet, Meta
# from sqlalchemy import desc


# def extract_twitter_info(url):
#     m = re.match(r'https://(?:x\.com|twitter\.com)/([^/]+)/status/(\d+)', url)
#     if m:
#         return m.group(1), m.group(2)  # username, tweet_id
#     return None, None


# def extract_links_and_campaigns(message):
#     links = re.findall(r'https?://\S+', message)
#     hashtags = re.findall(r'#\w+', message)
#     campaigns = [h.replace('#', '') for h in hashtags]
#     return links, campaigns


# async def run_crawler(session, client, group_id, limit=1000):
#     """
#     کرالر برای خواندن پیام‌های جدید از گروه تلگرام و ثبت توییت‌ها در دیتابیس.
#     پیام‌ها فقط تا آخرین پیام ثبت‌شده بررسی می‌شوند.
#     """
#     city_name = "نامشخص"
#     city = session.query(City).filter_by(name=city_name).first()
#     if not city:
#         city = City(name=city_name)
#         session.add(city)
#         session.commit()

#     # بررسی آخرین msg_id ثبت‌شده
#     meta = session.query(Meta).filter_by(key="last_msg_id").first()
#     last_msg_id = int(meta.value) if meta else 0

#     count = 0
#     async for msg in client.iter_messages(group_id, limit=limit):
#         if not msg.message or msg.id <= last_msg_id:
#             continue

#         links, campaigns = extract_links_and_campaigns(msg.message)
#         if not links or not campaigns:
#             continue

#         for campaign_name in campaigns:
#             campaign = session.query(Campaign).filter_by(name=campaign_name).first()
#             if not campaign:
#                 campaign = Campaign(name=campaign_name, hashtag=f"#{campaign_name}")
#                 session.add(campaign)
#                 session.commit()

#             for url in links:
#                 username, tweet_id = extract_twitter_info(url)
#                 if not tweet_id:
#                     continue

#                 exist = session.query(Tweet).filter_by(campaign_id=campaign.id, tweet_id=tweet_id).first()
#                 if exist:
#                     continue

#                 tweet = Tweet(
#                     campaign_id=campaign.id,
#                     city_id=city.id,
#                     twitter_username=username,
#                     tweet_id=tweet_id,
#                     url=url,
#                     datetime=msg.date
#                 )
#                 session.add(tweet)
#                 count += 1

#         # بعد از هر پیام، آپدیت کنیم آخرین msg_id را
#         if not meta:
#             meta = Meta(key="last_msg_id", value=str(msg.id))
#             session.add(meta)
#         else:
#             meta.value = str(max(msg.id, int(meta.value)))

#         session.commit()

#     return count


# app/fetch_tweets.py
import sys, os, re
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telethon import TelegramClient
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import GetRepliesRequest
from app.models import get_engine, get_session, create_tables, Campaign, City, Tweet, Meta
from app.config import API_ID, API_HASH

SESSION_PATH = "sessions/+989137552590.session"
GROUP_ID = -1002045713309
LIMIT_PER_TOPIC = 100

def extract_twitter_info(url):
    m = re.match(r'https://(?:x\.com|twitter\.com)/([^/]+)/status/(\d+)', url)
    return (m.group(1), m.group(2)) if m else (None, None)

def extract_links_and_campaigns(message):
    links = re.findall(r'https?://\S+', message)
    campaigns = [h.replace('#', '') for h in re.findall(r'#\w+', message)]
    return links, campaigns

async def run_crawler(session, client, group_id, limit_per_topic=100):
    print(f"🔵 دریافت تاپیک‌ها ...")
    try:
        forum_topics = await client(GetForumTopicsRequest(
            channel=group_id,
            offset_date=0,
            offset_id=0,
            offset_topic=0,
            limit=100
        ))
    except Exception as e:
        print(f"[!] خطا در دریافت تاپیک‌ها: {e}")
        return

    for topic in forum_topics.topics:
        topic_id = topic.id
        topic_title = topic.title
        top_msg_id = topic.top_message
        print(f"\n🔵 شهر: {topic_title} | TOPIC_MSG_ID: {top_msg_id}")

        meta_key = f"last_msg_id_topic_{topic_id}"
        meta = session.query(Meta).filter_by(key=meta_key).first()
        last_msg_id = int(meta.value) if meta else 0

        city = session.query(City).filter_by(name=topic_title).first()
        if not city:
            city = City(name=topic_title)
            session.add(city)
            session.commit()

        try:
            result = await client(GetRepliesRequest(
                peer=group_id,
                msg_id=topic.id,  # همینجاست که باید top_message رو بدی
                offset_id=0,
                offset_date=0,
                add_offset=0,
                limit=limit_per_topic,
                max_id=0,
                min_id=0,
                hash=0
            ))
        except Exception as e:
            print(f"[!] خطا برای تاپیک {topic_title}: {e}")
            continue

        count_this_topic = 0
        max_found_msg_id = last_msg_id
        for m in result.messages:
            if not m.message or m.id <= last_msg_id:
                continue
            links, campaigns = extract_links_and_campaigns(m.message)
            if not links or not campaigns:
                continue
            for campaign_name in campaigns:
                campaign = session.query(Campaign).filter_by(name=campaign_name).first()
                if not campaign:
                    campaign = Campaign(name=campaign_name, hashtag=f"#{campaign_name}")
                    session.add(campaign)
                    session.commit()
                for url in links:
                    username, tweet_id = extract_twitter_info(url)
                    if not tweet_id:
                        continue
                    exist = session.query(Tweet).filter_by(campaign_id=campaign.id, tweet_id=tweet_id).first()
                    if exist:
                        continue
                    tweet = Tweet(
                        campaign_id=campaign.id,
                        city_id=city.id,
                        twitter_username=username,
                        tweet_id=tweet_id,
                        url=url,
                        datetime=m.date
                    )
                    session.add(tweet)
                    count_this_topic += 1
                    print(f"✅ ثبت توییت جدید ({topic_title}): {url}")
            max_found_msg_id = max(max_found_msg_id, m.id)

        if max_found_msg_id > last_msg_id:
            if not meta:
                meta = Meta(key=meta_key, value=str(max_found_msg_id))
                session.add(meta)
            else:
                meta.value = str(max_found_msg_id)
            session.commit()

        print(f"🔸 مجموع ثبت جدید این تاپیک: {count_this_topic}")

# ---- اجرای برنامه ----
if __name__ == "__main__":
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    engine = get_engine()
    create_tables(engine)
    session = get_session(engine)

    with client:
        client.loop.run_until_complete(run_crawler(session, client, GROUP_ID, LIMIT_PER_TOPIC))
