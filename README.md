# bot_twiter_shamsa

بات تلگرامی. ساختار استاندارد: `src/` برای کد، `.env` فقط روی سرور، `requirements.txt` برای وابستگی‌ها.

## پیش‌نیازها
- Python 3.10+ (پیشنهادی)
- دسترسی به یک توکن بات تلگرام

## نصب و اجرا (محلی/سرور)
```bash
# 1) کلون ریپو و ورود به پوشه
git clone <PRIVATE-REPO-URL> bot_twiter
cd bot_twiter

# 2) ساخت venv و نصب پکیج‌ها
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3) ساخت فایل env از روی نمونه
cp .env.example .env
# سپس مقادیر حساس را در .env وارد کنید

# 4) اجرا (فایل اصلی داخل src قرار دارد)
python src/admin_bot.py
