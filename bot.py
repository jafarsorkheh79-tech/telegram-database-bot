import os
import sqlite3
import json
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio

# 🔧 از Environment Variables می‌خونه (Railway اینجوری کار می‌کنه)
BOT_TOKEN = os.getenv("BOT_TOKEN", "توکن_تو_اینجا_بذار_موقت")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # آیدی تو

# دیتابیس
conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS main_data 
                 (id INTEGER PRIMARY KEY, row_data TEXT, searchable_text TEXT)''')
conn.commit()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🟢 /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 سلام!\n\n"
        "📤 فقط ادمین فایل CSV رو بفرسته\n"
        "🔍 بعد همه میتونن جستجو کنن\n"
        "مثلا بنویس: علی یا 09123456789"
    )

# 📤 آپلود CSV
@dp.message(F.document, lambda m: m.from_user.id == ADMIN_ID)
async def upload_csv(message: types.Message):
    try:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, "temp.csv")
        
        df = pd.read_csv("temp.csv")
        cursor.execute("DELETE FROM main_data")
        
        for _, row in df.iterrows():
            row_json = row.to_json(force_ascii=False)
            searchable = " ".join([str(v) for v in row.values if pd.notna(v)])
            cursor.execute(
                "INSERT INTO main_data (row_data, searchable_text) VALUES (?, ?)",
                (row_json, searchable)
            )
        conn.commit()
        
        await message.answer(
            f"✅ **{len(df)} ردیف** ذخیره شد!\n"
            f"📌 ستون‌ها: {', '.join(list(df.columns)[:5])}"
        )
        os.remove("temp.csv")
        
    except Exception as e:
        await message.answer(f"❌ خطا: {str(e)}")

# 🔍 جستجو
@dp.message(F.text)
async def search(message: types.Message):
    query = message.text.strip()
    if query.startswith("/"):
        return
    
    cursor.execute(
        "SELECT row_data FROM main_data WHERE searchable_text LIKE ? LIMIT 5",
        (f"%{query}%",)
    )
    results = cursor.fetchall()
    
    if not results:
        await message.answer(f"🔍 نتیجه‌ای برای '{query}' نبود")
        return
    
    for result in results:
        row = json.loads(result[0])
        response = "📊 نتیجه:\n\n"
        for key, val in row.items():
            if pd.notna(val) and str(val).strip():
                response += f"**{key}**: {val}\n"
        await message.answer(response, parse_mode="Markdown")

# 🏃 اجرا
async def main():
    print("🤖 Railway Bot در حال اجراست...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())