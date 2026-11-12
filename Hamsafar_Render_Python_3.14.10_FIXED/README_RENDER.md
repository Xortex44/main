# هم‌سفر من — نسخه آماده انتشار در Render

## تنظیمات Render
- نوع سرویس: Web Service
- Root Directory: خالی (اگر فایل‌ها در ریشه مخزن هستند)
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Python: فایل `.python-version` روی `3.14.10` تنظیم شده است.

## نکته مهم
این پروژه از SQLite در مسیر `instance/hamsafar.db` استفاده می‌کند. فضای دیسک سرویس رایگان Render دائمی نیست؛ بنابراین داده‌های ثبت‌شده (مثل نظرات و عکس‌های آپلودی) ممکن است پس از استقرار مجدد یا جایگزینی نمونه از بین بروند. برای نگهداری دائمی داده‌ها باید دیسک پایدار یا دیتابیس خارجی متصل شود.

پس از انتشار، مسیر `/health` باید پاسخ `{"status":"ok"}` بدهد.
