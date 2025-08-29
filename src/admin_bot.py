# # admin_bot_conversation.py
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
# from telegram.ext import (
#     Application, CommandHandler, MessageHandler, CallbackQueryHandler,
#     ConversationHandler, filters, ContextTypes
# )
# from app.models import get_engine, get_session, Tweet, Campaign, City
# from sqlalchemy import func
# from datetime import datetime
# import os
# import csv
# import jdatetime
# from datetime import datetime, timedelta
# from app.fetch_tweets import run_crawler
# from telethon import TelegramClient
# from app.config import API_ID, API_HASH

# SESSION_PATH = "sessions/+989137552590.session"
# GROUP_ID = -1002045713309




# BOT_TOKEN = "7981096982:AAEq8oDaFqO0S3syUKExHE97P_tNcf1Zbu8"
# ADMIN_IDS = [5018729099]  # آی‌دی عددی ادمین

# engine = get_engine()
# session = get_session(engine)

# # مراحل گفتگو
# SELECT_CAMPAIGN, DATE_RANGE, FILTERS, CONFIRM = range(4)

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_user.id not in ADMIN_IDS:
#         await update.message.reply_text("⛔️ دسترسی محدود است.")
#         return ConversationHandler.END
#     await update.message.reply_text("سلام! برای دریافت گزارش کمپین دستور /report را بزن.")

# # مرحله ۱: انتخاب کمپین
# async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_user.id not in ADMIN_IDS:
#         await update.message.reply_text("⛔️ دسترسی محدود است.")
#         return ConversationHandler.END

#     campaigns = session.query(Campaign.name).all()
#     if not campaigns:
#         await update.message.reply_text("هیچ کمپینی ثبت نشده.")
#         return ConversationHandler.END

#     # ایجاد دکمه‌ها با callback_data کوتاه و امن
#     keyboard = []
#     campaign_map = {}
#     for i, (campaign_name,) in enumerate(campaigns):
#         key = f"cmp_{i}"
#         keyboard.append([InlineKeyboardButton(campaign_name, callback_data=key)])
#         campaign_map[key] = campaign_name

#     context.user_data["campaign_map"] = campaign_map

#     await update.message.reply_text(
#         "کمپین مورد نظر را انتخاب کن:",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return SELECT_CAMPAIGN

# async def select_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     campaign_key = query.data
#     campaign_map = context.user_data.get("campaign_map", {})

#     campaign_name = campaign_map.get(campaign_key)
#     if not campaign_name:
#         await query.message.reply_text("❌ کمپین نامعتبر است یا منقضی شده.")
#         return ConversationHandler.END

#     context.user_data["campaign"] = campaign_name

#     # مرحله بعد: بازه تاریخی
#     keyboard = [
#         [InlineKeyboardButton("بدون بازه", callback_data="no_date")],
#         [InlineKeyboardButton("روز گذشته", callback_data="last_1")],
#         [InlineKeyboardButton("۳ روز اخیر", callback_data="last_3")],
#         [InlineKeyboardButton("هفته اخیر", callback_data="last_7")],
#         [InlineKeyboardButton("ماه اخیر", callback_data="last_30")],
#         [InlineKeyboardButton("وارد کردن دستی", callback_data="enter_date")]
#     ]

#     await query.message.reply_text(
#         "آیا بازه تاریخی خاصی می‌خواهی؟",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return DATE_RANGE


# async def handle_date_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     today = datetime.today().date()

#     if query.data == "no_date":
#         context.user_data["date_from"] = None
#         context.user_data["date_to"] = None
#         return await ask_filters(query.message, context)

#     elif query.data.startswith("last_"):
#         days = int(query.data.split("_")[1])
#         date_from = today - timedelta(days=days)
#         date_to = today
#         context.user_data["date_from"] = date_from.strftime("%Y-%m-%d")
#         context.user_data["date_to"] = date_to.strftime("%Y-%m-%d")
#         return await ask_filters(query.message, context)

#     elif query.data == "enter_date":
#         await query.message.reply_text("📅 تاریخ شروع را وارد کن (مثال: 1403-04-10):")
#         context.user_data["waiting_for"] = "date_from"
#         return DATE_RANGE



# async def date_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text = update.message.text.strip()

#     if "waiting_for" not in context.user_data:
#         await update.message.reply_text("❗️خطای داخلی. لطفاً از اول شروع کن.")
#         return ConversationHandler.END

#     waiting_for = context.user_data["waiting_for"]

#     try:
#         # تبدیل تاریخ شمسی به میلادی
#         parts = list(map(int, text.split('-')))
#         if len(parts) != 3:
#             raise ValueError()
#         sh_date = jdatetime.date(parts[0], parts[1], parts[2])
#         miladi_date = sh_date.togregorian()
#     except Exception:
#         await update.message.reply_text("❌ فرمت تاریخ اشتباه است! مثال درست: 1403-04-10")
#         return DATE_RANGE

#     context.user_data[waiting_for] = miladi_date.strftime("%Y-%m-%d")

#     if waiting_for == "date_from":
#         context.user_data["waiting_for"] = "date_to"
#         await update.message.reply_text("📅 تاریخ پایان را وارد کن (مثال: 1403-04-15):")
#         return DATE_RANGE
#     else:
#         context.user_data.pop("waiting_for", None)
#         return await ask_filters(update.message, context)

# # مرحله ۳: فیلتر (شهر یا یوزرنیم)
# async def ask_filters(message, context):
#     keyboard = [
#         [InlineKeyboardButton("بدون فیلتر", callback_data="nofilter")],
#         [InlineKeyboardButton("انتخاب شهر", callback_data="city")],
#         [InlineKeyboardButton("یوزرنیم", callback_data="username")]
#     ]
#     await message.reply_text(
#         "می‌خواهی فیلتر بزنی بر اساس شهر یا یوزرنیم؟",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return FILTERS

# async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     if query.data == "nofilter":
#         context.user_data["city"] = None
#         context.user_data["username"] = None
#         return await show_summary(query.message, context)
#     elif query.data == "city":
#         # لیست شهرها
#         cities = session.query(City.name).all()
#         keyboard = [
#             [InlineKeyboardButton(c[0], callback_data=f"city_{c[0]}")] for c in cities
#         ]
#         await query.message.reply_text("شهر را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
#         return FILTERS
#     elif query.data == "username":
#         await query.message.reply_text("یوزرنیم توییتری را بنویس (مثال: ali123):")
#         context.user_data["waiting_for"] = "username"
#         return FILTERS
#     elif query.data.startswith("city_"):
#         city_name = query.data.replace("city_", "")
#         context.user_data["city"] = city_name
#         context.user_data["username"] = None
#         return await show_summary(query.message, context)

# async def handle_username_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     username = update.message.text.strip()
#     context.user_data["username"] = username
#     return await show_summary(update.message, context)

# # مرحله آخر: خلاصه فیلترها و تایید
# async def show_summary(message, context):
#     c = context.user_data
#     summary = f"""🔎 خلاصه انتخاب‌ها:
# کمپین: {c.get('campaign')}
# بازه تاریخی: {c.get('date_from', '---')} تا {c.get('date_to', '---')}
# شهر: {c.get('city', '---')}
# یوزرنیم: {c.get('username', '---')}

# تایید؟"""
#     keyboard = [
#         [InlineKeyboardButton("تایید و دریافت گزارش", callback_data="confirm")],
#         [InlineKeyboardButton("لغو", callback_data="cancel")]
#     ]
#     await message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
#     return CONFIRM

# def miladi_to_shamsi(date_str):
#     try:
#         dt = datetime.strptime(date_str, "%Y-%m-%d")
#         shamsi = jdatetime.date.fromgregorian(date=dt).strftime("%Y/%m/%d")
#         return shamsi
#     except:
#         return '---'

# async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
    
#     if query.data == "cancel":
#         await query.message.reply_text("لغو شد.")
#         return ConversationHandler.END

#     # پارامترهای انتخابی
#     c = context.user_data
#     campaign, date_from, date_to, city, username = (
#         c.get("campaign"), c.get("date_from"), c.get("date_to"),
#         c.get("city"), c.get("username")
#     )

#     tweets = query_tweets(campaign, date_from, date_to, city, username)
#     if not tweets:
#         await query.message.reply_text("❌ هیچ داده‌ای یافت نشد.")
#         return ConversationHandler.END

#     # جمع‌آوری اطلاعات
#     total_tweets = len(tweets)
#     user_counts = {}
#     for tw in tweets:
#         user_counts[tw.twitter_username] = user_counts.get(tw.twitter_username, 0) + 1

#     unique_users = list(user_counts.keys())
#     shamsi_from = miladi_to_shamsi(date_from) if date_from else '---'
#     shamsi_to = miladi_to_shamsi(date_to) if date_to else '---'

#     txt = f"""📊 گزارش کمپین: {campaign}
# ------------------------------
# 🗓️ بازه: {shamsi_from} تا {shamsi_to}
# 🏙️ شهر: {city or '---'}
# 👤 یوزرنیم خاص: {username or '---'}

# 🔢 تعداد کل توییت‌ها: {total_tweets}
# 👥 تعداد کاربران یکتا: {len(unique_users)}

# 📋 لیست کاربران یکتا:
# """
#     for uname, count in sorted(user_counts.items(), key=lambda x: x[0])[:40]:
#         txt += f"• {uname}: {count} توییت\n"

#     txt += "\n🏆 پرمشارکت‌ترین کاربران (Top 10):\n"
#     for uname, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
#         txt += f"⭐️ {uname}: {count} توییت\n"

#     await query.message.reply_text(txt[:4000])
#     return ConversationHandler.END

# def query_tweets(campaign, date_from, date_to, city, username):
#     q = session.query(Tweet).join(Campaign).join(City)
#     if campaign:
#         q = q.filter(Campaign.name == campaign)
#     if date_from:
#         try:
#             q = q.filter(Tweet.datetime >= datetime.strptime(date_from, "%Y-%m-%d"))
#         except:
#             pass
#     if date_to:
#         try:
#             q = q.filter(Tweet.datetime <= datetime.strptime(date_to, "%Y-%m-%d"))
#         except:
#             pass
#     if city:
#         q = q.filter(City.name == city)
#     if username:
#         q = q.filter(Tweet.twitter_username == username)
#     return q.all()

# async def crawl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_user.id not in ADMIN_IDS:
#         await update.message.reply_text("⛔️ فقط ادمین می‌تونه این دستور رو اجرا کنه.")
#         return

#     await update.message.reply_text("🔄 در حال اجرای کرالر، لطفاً صبر کنید...")

#     client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
#     async with client:
#         count = await run_crawler(session, client, GROUP_ID)

#     await update.message.reply_text(f"✅ کرال کامل شد.\n📥 {count} توییت جدید ثبت شد.")


# def main():
#     logging.basicConfig(level=logging.INFO)
#     app = Application.builder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("report", report_entry)],
#         states={
#             SELECT_CAMPAIGN: [CallbackQueryHandler(select_campaign)],
#             DATE_RANGE: [
#                 CallbackQueryHandler(handle_date_range),
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, date_range_text)
#             ],
#             FILTERS: [
#                 CallbackQueryHandler(handle_filters),
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_text)
#             ],
#             CONFIRM: [CallbackQueryHandler(confirm_report)]
#         },
#         fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("لغو شد."))],
#         allow_reentry=True,
#     )

#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("list_campaigns", report_entry))
#     app.add_handler(conv_handler)
#     app.add_handler(CommandHandler("crawl", crawl_command))
#     app.run_polling()

# if __name__ == "__main__":
#     main()







# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     Application, CommandHandler, MessageHandler, CallbackQueryHandler,
#     ConversationHandler, filters, ContextTypes
# )
# from app.models import get_engine, get_session, Tweet, Campaign, City
# import jdatetime
# from datetime import datetime, timedelta
# from app.fetch_tweets import run_crawler
# from telethon import TelegramClient
# from app.config import API_ID, API_HASH

# SESSION_PATH = "sessions/+989137552590.session"
# GROUP_ID = -1002045713309

# BOT_TOKEN = "7981096982:AAEq8oDaFqO0S3syUKExHE97P_tNcf1Zbu8"
# ADMIN_IDS = [5018729099]  # آی‌دی عددی ادمین

# engine = get_engine()
# session = get_session(engine)

# SELECT_CAMPAIGN, DATE_RANGE, FILTERS, CONFIRM = range(4)

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_user.id not in ADMIN_IDS:
#         await update.message.reply_text("⛔️ دسترسی محدود است.")
#         return ConversationHandler.END
#     await update.message.reply_text("سلام! برای دریافت گزارش کمپین دستور /report را بزن.")

# async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_user.id not in ADMIN_IDS:
#         await update.message.reply_text("⛔️ دسترسی محدود است.")
#         return ConversationHandler.END

#     campaigns = session.query(Campaign.name).all()
#     if not campaigns:
#         await update.message.reply_text("هیچ کمپینی ثبت نشده.")
#         return ConversationHandler.END

#     keyboard = []
#     campaign_map = {}
#     for i, (campaign_name,) in enumerate(campaigns):
#         key = f"cmp_{i}"
#         keyboard.append([InlineKeyboardButton(campaign_name, callback_data=key)])
#         campaign_map[key] = campaign_name

#     context.user_data["campaign_map"] = campaign_map

#     await update.message.reply_text(
#         "کمپین مورد نظر را انتخاب کن:",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return SELECT_CAMPAIGN

# async def select_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     campaign_key = query.data
#     campaign_map = context.user_data.get("campaign_map", {})

#     campaign_name = campaign_map.get(campaign_key)
#     if not campaign_name:
#         await query.message.reply_text("❌ کمپین نامعتبر است یا منقضی شده.")
#         return ConversationHandler.END

#     context.user_data["campaign"] = campaign_name

#     keyboard = [
#         [InlineKeyboardButton("بدون بازه", callback_data="no_date")],
#         [InlineKeyboardButton("روز گذشته", callback_data="last_1")],
#         [InlineKeyboardButton("۳ روز اخیر", callback_data="last_3")],
#         [InlineKeyboardButton("هفته اخیر", callback_data="last_7")],
#         [InlineKeyboardButton("ماه اخیر", callback_data="last_30")],
#         [InlineKeyboardButton("وارد کردن دستی", callback_data="enter_date")]
#     ]

#     await query.message.reply_text(
#         "آیا بازه تاریخی خاصی می‌خواهی؟",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return DATE_RANGE

# async def handle_date_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     today = datetime.today().date()

#     if query.data == "no_date":
#         context.user_data["date_from"] = None
#         context.user_data["date_to"] = None
#         return await ask_filters(query.message, context)

#     elif query.data.startswith("last_"):
#         days = int(query.data.split("_")[1])
#         date_from = today - timedelta(days=days)
#         date_to = today
#         context.user_data["date_from"] = date_from.strftime("%Y-%m-%d")
#         context.user_data["date_to"] = date_to.strftime("%Y-%m-%d")
#         return await ask_filters(query.message, context)

#     elif query.data == "enter_date":
#         await query.message.reply_text("📅 تاریخ شروع را وارد کن (مثال: 1403-04-10):")
#         context.user_data["waiting_for"] = "date_from"
#         return DATE_RANGE

# async def date_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     text = update.message.text.strip()
#     if "waiting_for" not in context.user_data:
#         await update.message.reply_text("❗️خطای داخلی. لطفاً از اول شروع کن.")
#         return ConversationHandler.END

#     waiting_for = context.user_data["waiting_for"]
#     try:
#         parts = list(map(int, text.split('-')))
#         if len(parts) != 3:
#             raise ValueError()
#         sh_date = jdatetime.date(parts[0], parts[1], parts[2])
#         miladi_date = sh_date.togregorian()
#     except Exception:
#         await update.message.reply_text("❌ فرمت تاریخ اشتباه است! مثال درست: 1403-04-10")
#         return DATE_RANGE

#     context.user_data[waiting_for] = miladi_date.strftime("%Y-%m-%d")

#     if waiting_for == "date_from":
#         context.user_data["waiting_for"] = "date_to"
#         await update.message.reply_text("📅 تاریخ پایان را وارد کن (مثال: 1403-04-15):")
#         return DATE_RANGE
#     else:
#         context.user_data.pop("waiting_for", None)
#         return await ask_filters(update.message, context)

# async def ask_filters(message, context):
#     keyboard = [
#         [InlineKeyboardButton("بدون فیلتر", callback_data="nofilter")],
#         [InlineKeyboardButton("انتخاب شهر", callback_data="city")],
#         [InlineKeyboardButton("یوزرنیم", callback_data="username")]
#     ]
#     await message.reply_text(
#         "می‌خواهی فیلتر بزنی بر اساس شهر یا یوزرنیم؟",
#         reply_markup=InlineKeyboardMarkup(keyboard)
#     )
#     return FILTERS

# async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     if query.data == "nofilter":
#         context.user_data["city"] = None
#         context.user_data["username"] = None
#         return await show_summary(query.message, context)
#     elif query.data == "city":
#         cities = session.query(City.name).all()
#         keyboard = [
#             [InlineKeyboardButton(c[0], callback_data=f"city_{c[0]}")] for c in cities
#         ]
#         await query.message.reply_text("شهر را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
#         return FILTERS
#     elif query.data == "username":
#         await query.message.reply_text("یوزرنیم توییتری را بنویس (مثال: ali123):")
#         context.user_data["waiting_for"] = "username"
#         return FILTERS
#     elif query.data.startswith("city_"):
#         city_name = query.data.replace("city_", "")
#         context.user_data["city"] = city_name
#         context.user_data["username"] = None
#         return await show_summary(query.message, context)

# async def handle_username_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     username = update.message.text.strip()
#     context.user_data["username"] = username
#     return await show_summary(update.message, context)

# # خلاصه انتخاب و انتخاب نوع گزارش
# async def show_summary(message, context):
#     c = context.user_data
#     summary = f"""🔎 خلاصه انتخاب‌ها:
# کمپین: {c.get('campaign')}
# بازه تاریخی: {c.get('date_from', '---')} تا {c.get('date_to', '---')}
# شهر: {c.get('city', '---')}
# یوزرنیم: {c.get('username', '---')}
# نوع گزارش را انتخاب کن:"""
#     keyboard = [
#         [InlineKeyboardButton("📋 تفصیلی (یوزر محور)", callback_data="confirm_detail")],
#         [InlineKeyboardButton("📊 تجمیعی (بر اساس شهر)", callback_data="confirm_citysum")],
#         [InlineKeyboardButton("لغو", callback_data="cancel")]
#     ]
#     await message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
#     return CONFIRM

# def miladi_to_shamsi(date_str):
#     try:
#         dt = datetime.strptime(date_str, "%Y-%m-%d")
#         shamsi = jdatetime.date.fromgregorian(date=dt).strftime("%Y/%m/%d")
#         return shamsi
#     except:
#         return '---'

# async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     c = context.user_data
#     campaign, date_from, date_to, city, username = (
#         c.get("campaign"), c.get("date_from"), c.get("date_to"),
#         c.get("city"), c.get("username")
#     )

#     if query.data == "cancel":
#         await query.message.reply_text("لغو شد.")
#         return ConversationHandler.END

#     if query.data == "confirm_detail":
#         tweets = query_tweets(campaign, date_from, date_to, city, username)
#         if not tweets:
#             await query.message.reply_text("❌ هیچ داده‌ای یافت نشد.")
#             return ConversationHandler.END

#         total_tweets = len(tweets)
#         user_counts = {}
#         for tw in tweets:
#             user_counts[tw.twitter_username] = user_counts.get(tw.twitter_username, 0) + 1

#         unique_users = list(user_counts.keys())
#         shamsi_from = miladi_to_shamsi(date_from) if date_from else '---'
#         shamsi_to = miladi_to_shamsi(date_to) if date_to else '---'

#         txt = f"""📊 گزارش کمپین: {campaign}
# ------------------------------
# 🗓️ بازه: {shamsi_from} تا {shamsi_to}
# 🏙️ شهر: {city or '---'}
# 👤 یوزرنیم خاص: {username or '---'}

# 🔢 تعداد کل توییت‌ها: {total_tweets}
# 👥 تعداد کاربران یکتا: {len(unique_users)}

# 📋 لیست کاربران یکتا:
# """
#         for uname, count in sorted(user_counts.items(), key=lambda x: x[0])[:40]:
#             txt += f"• {uname}: {count} توییت\n"

#         txt += "\n🏆 پرمشارکت‌ترین کاربران (Top 10):\n"
#         for uname, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
#             txt += f"⭐️ {uname}: {count} توییت\n"

#         await query.message.reply_text(txt[:4000])
#         return ConversationHandler.END

#     if query.data == "confirm_citysum":
#         tweets = query_tweets(campaign, date_from, date_to, None, username)
#         if not tweets:
#             await query.message.reply_text("❌ هیچ داده‌ای یافت نشد.")
#             return ConversationHandler.END

#         # شمارش بر اساس شهر
#         city_stats = {}
#         for t in tweets:
#             city_name = t.city.name if t.city else "نامشخص"
#             if city_name not in city_stats:
#                 city_stats[city_name] = {"count": 0, "users": set()}
#             city_stats[city_name]["count"] += 1
#             city_stats[city_name]["users"].add(t.twitter_username)

#         shamsi_from = miladi_to_shamsi(date_from) if date_from else '---'
#         shamsi_to = miladi_to_shamsi(date_to) if date_to else '---'

#         txt = f"""📊 گزارش تجمیعی بر اساس شهر
# -----------------------------
# کمپین: {campaign}
# 🗓️ بازه: {shamsi_from} تا {shamsi_to}

# 🏙️ آمار شهرها:
# """
#         for c, v in sorted(city_stats.items(), key=lambda x: -x[1]['count']):
#             txt += f"• {c}: {v['count']} توییت، {len(v['users'])} کاربر یکتا\n"
#         await query.message.reply_text(txt[:4000])
#         return ConversationHandler.END

# def query_tweets(campaign, date_from, date_to, city, username):
#     q = session.query(Tweet).join(Campaign).join(City)
#     if campaign:
#         q = q.filter(Campaign.name == campaign)
#     if date_from:
#         try:
#             q = q.filter(Tweet.datetime >= datetime.strptime(date_from, "%Y-%m-%d"))
#         except:
#             pass
#     if date_to:
#         try:
#             q = q.filter(Tweet.datetime <= datetime.strptime(date_to, "%Y-%m-%d"))
#         except:
#             pass
#     if city:
#         q = q.filter(City.name == city)
#     if username:
#         q = q.filter(Tweet.twitter_username == username)
#     return q.all()

# async def crawl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if update.effective_user.id not in ADMIN_IDS:
#         await update.message.reply_text("⛔️ فقط ادمین می‌تونه این دستور رو اجرا کنه.")
#         return

#     await update.message.reply_text("🔄 در حال اجرای کرالر، لطفاً صبر کنید...")

#     client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
#     async with client:
#         count = await run_crawler(session, client, GROUP_ID)

#     await update.message.reply_text(f"✅ کرال کامل شد.\n📥 {count} توییت جدید ثبت شد.")

# def main():
#     logging.basicConfig(level=logging.INFO)
#     app = Application.builder().token(BOT_TOKEN).build()

#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("report", report_entry)],
#         states={
#             SELECT_CAMPAIGN: [CallbackQueryHandler(select_campaign)],
#             DATE_RANGE: [
#                 CallbackQueryHandler(handle_date_range),
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, date_range_text)
#             ],
#             FILTERS: [
#                 CallbackQueryHandler(handle_filters),
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_text)
#             ],
#             CONFIRM: [CallbackQueryHandler(confirm_report)]
#         },
#         fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("لغو شد."))],
#         allow_reentry=True,
#     )

#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("list_campaigns", report_entry))
#     app.add_handler(conv_handler)
#     app.add_handler(CommandHandler("crawl", crawl_command))
#     app.run_polling()

# if __name__ == "__main__":
#     main()




# admin_bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from app.models import get_engine, get_session, Tweet, Campaign, City
import jdatetime
from datetime import datetime, timedelta
from app.fetch_tweets import run_crawler
from telethon import TelegramClient
from app.config import API_ID, API_HASH


SESSION_PATH = "sessions/+989137552590.session"
GROUP_ID = -1002045713309

BOT_TOKEN = "7981096982:AAEq8oDaFqO0S3syUKExHE97P_tNcf1Zbu8"
ADMIN_IDS = [5018729099,233482937,663040344]  # آی‌دی عددی ادمین

engine = get_engine()
session = get_session(engine)

SELECT_CAMPAIGN, SEARCH_CAMPAIGN, DATE_RANGE, FILTERS, CONFIRM = range(5)
PAGE_SIZE = 12

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ دسترسی محدود است.")
        return ConversationHandler.END
    await update.message.reply_text("سلام! برای دریافت گزارش کمپین دستور /report را بزن.")

async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ دسترسی محدود است.")
        return ConversationHandler.END
    context.user_data["page"] = 0
    context.user_data["search_term"] = None
    return await show_campaigns(update.message, context)

async def show_campaigns(message, context):
    page = context.user_data.get("page", 0)
    search_term = context.user_data.get("search_term")
    if search_term:
        campaigns = session.query(Campaign.name).filter(Campaign.name.ilike(f"%{search_term}%")).all()
    else:
        campaigns = session.query(Campaign.name).all()

    if not campaigns:
        await message.reply_text("هیچ کمپینی پیدا نشد.")
        return ConversationHandler.END

    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    campaigns_page = campaigns[start_idx:end_idx]

    keyboard = []
    campaign_map = {}
    for i, (campaign_name,) in enumerate(campaigns_page):
        key = f"cmp_{start_idx+i}"
        keyboard.append([InlineKeyboardButton(campaign_name, callback_data=key)])
        campaign_map[key] = campaign_name

    nav_buttons = []
    if start_idx > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data="prev_page"))
    if end_idx < len(campaigns):
        nav_buttons.append(InlineKeyboardButton("بعدی ➡️", callback_data="next_page"))
    nav_buttons.append(InlineKeyboardButton("🔍 جستجوی کمپین", callback_data="search_campaign"))
    if search_term:
        nav_buttons.append(InlineKeyboardButton("🔄 نمایش همه", callback_data="show_all_campaigns"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    context.user_data["campaign_map"] = campaign_map
    context.user_data["campaigns_count"] = len(campaigns)

    await message.reply_text(
        "کمپین مورد نظر را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_CAMPAIGN

async def select_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "next_page":
        context.user_data["page"] += 1
        return await show_campaigns(query.message, context)
    elif data == "prev_page":
        context.user_data["page"] -= 1
        return await show_campaigns(query.message, context)
    elif data == "search_campaign":
        await query.message.reply_text("نام یا بخشی از نام کمپین را بنویس:")
        context.user_data["waiting_for_search"] = True
        return SEARCH_CAMPAIGN
    elif data == "show_all_campaigns":
        context.user_data["search_term"] = None
        context.user_data["page"] = 0
        return await show_campaigns(query.message, context)
    else:
        campaign_map = context.user_data.get("campaign_map", {})
        campaign_name = campaign_map.get(data)
        if not campaign_name:
            await query.message.reply_text("❌ کمپین نامعتبر است یا منقضی شده.")
            return ConversationHandler.END
        context.user_data["campaign"] = campaign_name
        return await show_date_range(query.message, context)

async def search_campaign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_search"):
        await update.message.reply_text("خطای داخلی. لطفاً مجدداً تلاش کن.")
        return ConversationHandler.END
    search_term = update.message.text.strip()
    context.user_data["search_term"] = search_term
    context.user_data["page"] = 0
    context.user_data["waiting_for_search"] = False
    return await show_campaigns(update.message, context)

async def show_date_range(message, context):
    keyboard = [
        [InlineKeyboardButton("بدون بازه", callback_data="no_date")],
        [InlineKeyboardButton("روز گذشته", callback_data="last_1")],
        [InlineKeyboardButton("۳ روز اخیر", callback_data="last_3")],
        [InlineKeyboardButton("هفته اخیر", callback_data="last_7")],
        [InlineKeyboardButton("ماه اخیر", callback_data="last_30")],
        [InlineKeyboardButton("وارد کردن دستی", callback_data="enter_date")]
    ]
    await message.reply_text(
        "آیا بازه تاریخی خاصی می‌خواهی؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DATE_RANGE

async def handle_date_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    today = datetime.today().date()

    if query.data == "no_date":
        context.user_data["date_from"] = None
        context.user_data["date_to"] = None
        return await ask_filters(query.message, context)
    elif query.data.startswith("last_"):
        days = int(query.data.split("_")[1])
        date_from = today - timedelta(days=days)
        date_to = today
        context.user_data["date_from"] = date_from.strftime("%Y-%m-%d")
        context.user_data["date_to"] = date_to.strftime("%Y-%m-%d")
        return await ask_filters(query.message, context)
    elif query.data == "enter_date":
        await query.message.reply_text("📅 تاریخ شروع را وارد کن (مثال: 1403-04-10):")
        context.user_data["waiting_for"] = "date_from"
        return DATE_RANGE

async def date_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "waiting_for" not in context.user_data:
        await update.message.reply_text("❗️خطای داخلی. لطفاً از اول شروع کن.")
        return ConversationHandler.END

    waiting_for = context.user_data["waiting_for"]
    try:
        parts = list(map(int, text.split('-')))
        if len(parts) != 3:
            raise ValueError()
        sh_date = jdatetime.date(parts[0], parts[1], parts[2])
        miladi_date = sh_date.togregorian()
    except Exception:
        await update.message.reply_text("❌ فرمت تاریخ اشتباه است! مثال درست: 1403-04-10")
        return DATE_RANGE

    context.user_data[waiting_for] = miladi_date.strftime("%Y-%m-%d")

    if waiting_for == "date_from":
        context.user_data["waiting_for"] = "date_to"
        await update.message.reply_text("📅 تاریخ پایان را وارد کن (مثال: 1403-04-15):")
        return DATE_RANGE
    else:
        context.user_data.pop("waiting_for", None)
        return await ask_filters(update.message, context)

async def ask_filters(message, context):
    keyboard = [
        [InlineKeyboardButton("بدون فیلتر", callback_data="nofilter")],
        [InlineKeyboardButton("انتخاب شهر", callback_data="city")],
        [InlineKeyboardButton("یوزرنیم", callback_data="username")]
    ]
    await message.reply_text(
        "می‌خواهی فیلتر بزنی بر اساس شهر یا یوزرنیم؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return FILTERS

async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "nofilter":
        context.user_data["city"] = None
        context.user_data["username"] = None
        return await show_summary(query.message, context)
    elif query.data == "city":
        cities = session.query(City.name).all()
        keyboard = [
            [InlineKeyboardButton(c[0], callback_data=f"city_{c[0]}")] for c in cities
        ]
        await query.message.reply_text("شهر را انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))
        return FILTERS
    elif query.data == "username":
        await query.message.reply_text("یوزرنیم توییتری را بنویس (مثال: ali123):")
        context.user_data["waiting_for"] = "username"
        return FILTERS
    elif query.data.startswith("city_"):
        city_name = query.data.replace("city_", "")
        context.user_data["city"] = city_name
        context.user_data["username"] = None
        return await show_summary(query.message, context)

async def handle_username_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    context.user_data["username"] = username
    return await show_summary(update.message, context)


async def show_summary(message, context):
    c = context.user_data
    # اگر تاریخ وارد شده باشه، تبدیلش کن
    shamsi_from = miladi_to_shamsi(c.get('date_from')) if c.get('date_from') else '---'
    shamsi_to = miladi_to_shamsi(c.get('date_to')) if c.get('date_to') else '---'
    summary = f"""🔎 خلاصه انتخاب‌ها:
کمپین: {c.get('campaign')}
بازه تاریخی: {shamsi_from} تا {shamsi_to}
شهر: {c.get('city', '---')}
یوزرنیم: {c.get('username', '---')}
نوع گزارش را انتخاب کن:"""
    keyboard = [
        [InlineKeyboardButton("📋 تفصیلی (یوزر محور)", callback_data="confirm_detail")],
        [InlineKeyboardButton("📊 تجمیعی (بر اساس شهر)", callback_data="confirm_citysum")],
        [InlineKeyboardButton("لغو", callback_data="cancel")]
    ]
    await message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

def miladi_to_shamsi(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        shamsi = jdatetime.date.fromgregorian(date=dt).strftime("%Y/%m/%d")
        return shamsi
    except:
        return '---'

async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    c = context.user_data
    campaign, date_from, date_to, city, username = (
        c.get("campaign"), c.get("date_from"), c.get("date_to"),
        c.get("city"), c.get("username")
    )

    if query.data == "cancel":
        await query.message.reply_text("لغو شد.")
        return ConversationHandler.END

    if query.data == "confirm_citysum":
        tweets = query_tweets(campaign, date_from, date_to, None, username)
        if not tweets:
            await query.message.reply_text("❌ هیچ داده‌ای یافت نشد.")
            return ConversationHandler.END

        city_stats = {}
        for t in tweets:
            city_name = t.city.name if t.city else "نامشخص"
            if city_name not in city_stats:
                city_stats[city_name] = {"count": 0, "users": set()}
            city_stats[city_name]["count"] += 1
            city_stats[city_name]["users"].add(t.twitter_username)

        shamsi_from = miladi_to_shamsi(date_from) if date_from else '---'
        shamsi_to = miladi_to_shamsi(date_to) if date_to else '---'

        # ------------------ ساخت گزارش متنی
        txt = f"""📊 گزارش تجمیعی بر اساس شهر
-----------------------------
کمپین: {campaign or '---'}
🗓️ بازه: {shamsi_from} تا {shamsi_to}

🏙️ آمار شهرها:
"""
        for cname, v in sorted(city_stats.items(), key=lambda x: -x[1]['count']):
            txt += f"• {cname}: {v['count']} توییت، {len(v['users'])} اکانت\n"
        await query.message.reply_text(txt[:4000])


        return ConversationHandler.END

def query_tweets(campaign, date_from, date_to, city, username):
    q = session.query(Tweet).join(Campaign).join(City)
    if campaign:
        q = q.filter(Campaign.name == campaign)
    if date_from:
        try:
            # تبدیل رشته به datetime با ساعت صفر
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            q = q.filter(Tweet.datetime >= dt_from)
        except Exception as e:
            print('date_from parsing error:', e)
    if date_to:
        try:
            # برای شمول کامل روز، روز بعد را بگیر و < بزن
            dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            q = q.filter(Tweet.datetime < dt_to)
        except Exception as e:
            print('date_to parsing error:', e)
    if city:
        q = q.filter(City.name == city)
    if username:
        q = q.filter(Tweet.twitter_username == username)

    # کد دیباگ برای مشاهده نتیجه کوئری و مقادیر تاریخ:
    tweets = q.all()
    print(f"Query Params: campaign={campaign}, date_from={date_from}, date_to={date_to}, city={city}, username={username}")
    print(f"Tweets found: {len(tweets)}")
    for t in tweets[:5]:  # فقط ۵ تا اولی برای دیباگ
        print('TWEET:', t.tweet_id, t.datetime, t.twitter_username)
    return tweets

async def crawl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ فقط ادمین می‌تونه این دستور رو اجرا کنه.")
        return

    await update.message.reply_text("🔄 در حال اجرای کرالر، لطفاً صبر کنید...")

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    async with client:
        count = await run_crawler(session, client, GROUP_ID)

    await update.message.reply_text(f"✅ کرال کامل شد.\n📥 {count} توییت جدید ثبت شد.")

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("report", report_entry)],
        states={
            SELECT_CAMPAIGN: [CallbackQueryHandler(select_campaign)],
            SEARCH_CAMPAIGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_campaign)],
            DATE_RANGE: [
                CallbackQueryHandler(handle_date_range),
                MessageHandler(filters.TEXT & ~filters.COMMAND, date_range_text)
            ],
            FILTERS: [
                CallbackQueryHandler(handle_filters),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_text)
            ],
            CONFIRM: [CallbackQueryHandler(confirm_report)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("لغو شد."))],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list_campaigns", report_entry))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("crawl", crawl_command))
    app.run_polling()

if __name__ == "__main__":
    main()