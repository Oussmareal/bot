import os
print("Starting bot...")

session = os.getenv("SESSION_NAME")
if session:
    print("Session Loaded Successfully")
else:
    print("Error: SESSION_NAME is empty!")


from telethon import TelegramClient, events
import asyncio
import json
import logging
import re  # مكتبة التعبيرات النمطية لإزالة المنشن

# ✅ إعداد السجل لتسجيل الأخطاء والأنشطة
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ بيانات تسجيل الدخول إلى تيليجرام
api_id = 26037708
api_hash = '769da9951dfadb6113f3afbf33209d4d'
bot_token = 'your_bot_token'  # ضع توكن البوت الخاص بك

# ✅ إنشاء الجلسة
client = TelegramClient('multi_group_bot', api_id, api_hash)

# ✅ معرف المسؤول
admin_user_id = 6747574207

# ✅ ملفات تخزين البيانات
GROUPS_FILE = "groups.json"
MESSAGE_MAP_FILE = "message_map.json"

# ✅ تحميل بيانات المجموعات
try:
    with open(GROUPS_FILE, "r") as f:
        group_mapping = {int(k): int(v) for k, v in json.load(f).items()}
except FileNotFoundError:
    group_mapping = {}

# ✅ تحميل معرفات الرسائل للردود
try:
    with open(MESSAGE_MAP_FILE, "r") as f:
        message_map = {tuple(map(int, k.split(","))): v for k, v in json.load(f).items()}
except FileNotFoundError:
    message_map = {}

# ✅ حفظ المجموعات
def save_groups():
    with open(GROUPS_FILE, "w") as f:
        json.dump(group_mapping, f)

# ✅ حفظ معرفات الرسائل
def save_message_map():
    with open(MESSAGE_MAP_FILE, "w") as f:
        json.dump({f"{k[0]},{k[1]}": v for k, v in message_map.items()}, f)

# ✅ إرسال إشعار للإدمن
async def send_admin_notification(message):
    try:
        await client.send_message(admin_user_id, message)
    except Exception as e:
        logging.error(f"❌ خطأ في إرسال الإشعار: {e}")

# ✅ التحكم في تشغيل وإيقاف البوت
bot_running = True

@client.on(events.NewMessage(from_users=admin_user_id, pattern=r'/start'))
async def start(event):
    global bot_running
    bot_running = True
    await event.respond("✅ البوت بدأ في تحويل الرسائل!")

@client.on(events.NewMessage(from_users=admin_user_id, pattern=r'/stop'))
async def stop(event):
    global bot_running
    bot_running = False
    await event.respond("⛔ تم إيقاف تحويل الرسائل مؤقتًا.")

@client.on(events.NewMessage(from_users=admin_user_id, pattern=r'/status'))
async def status(event):
    status_msg = "✅ البوت يعمل!" if bot_running else "⛔ البوت متوقف!"
    await event.respond(status_msg)

@client.on(events.NewMessage(from_users=admin_user_id, pattern=r'/get_id'))
async def get_id(event):
    await event.respond(f"📌 معرف هذه المجموعة هو: {event.chat_id}")

@client.on(events.NewMessage(from_users=admin_user_id, pattern=r'/add_group (-?\d+) (-?\d+)'))
async def add_group(event):
    source_id, target_id = map(int, event.pattern_match.groups())
    if source_id in group_mapping:
        await event.respond("⚠️ هذه المجموعة مضافة بالفعل!")
    else:
        group_mapping[source_id] = target_id
        save_groups()
        await event.respond(f"✅ تمت إضافة المجموعة {source_id} إلى {target_id} بنجاح!")

@client.on(events.NewMessage(from_users=admin_user_id, pattern=r'/remove_group (-?\d+)'))
async def remove_group(event):
    source_id = int(event.pattern_match.group(1))
    if source_id in group_mapping:
        del group_mapping[source_id]
        save_groups()
        await event.respond(f"✅ تمت إزالة المجموعة {source_id} من النظام.")
    else:
        await event.respond("⚠️ هذه المجموعة غير موجودة!")

@client.on(events.NewMessage(from_users=admin_user_id, pattern=r'/list_groups'))
async def list_groups(event):
    if not group_mapping:
        await event.respond("📭 لا توجد مجموعات مضافة بعد.")
    else:
        msg = "📌 المجموعات الحالية:\n"
        for source, target in group_mapping.items():
            msg += f"• {source} → {target}\n"
        await event.respond(msg)

@client.on(events.NewMessage(chats=list(group_mapping.keys())))
async def forward_message(event):
    """إعادة إرسال الرسائل من المصدر إلى الهدف مع دعم الردود ومنع ذكر المستخدمين"""
    if not bot_running:
        return

    source_chat = event.chat_id    
    target_chat = group_mapping.get(source_chat)    
    if not target_chat:  
        return    

    try:  
        reply_to = message_map.get((source_chat, event.reply_to_msg_id)) if event.reply_to_msg_id else None  

        # 🔥 إزالة جميع المنشن (@username) من النصوص
        clean_text = re.sub(r'@\w+', '', event.message.text or '').strip()

        sent_message = None  
        if clean_text and not event.message.media:  
            sent_message = await client.send_message(target_chat, clean_text, reply_to=reply_to)  
        
        elif event.message.photo:  
            file = await client.download_media(event.message.photo)  
            sent_message = await client.send_file(target_chat, file, caption=clean_text, reply_to=reply_to)

        elif event.message.document:  
            sent_message = await client.send_file(target_chat, event.message.document, caption=clean_text, reply_to=reply_to)  
        elif event.message.video:  
            sent_message = await client.send_file(target_chat, event.message.video, caption=clean_text, reply_to=reply_to)  
        elif event.message.audio:  
            sent_message = await client.send_file(target_chat, event.message.audio, caption=clean_text, reply_to=reply_to)  
        elif event.message.voice:  
            sent_message = await client.send_file(target_chat, event.message.voice, caption=clean_text, reply_to=reply_to)  
        elif event.message.sticker:  
            sent_message = await client.send_file(target_chat, event.message.sticker, reply_to=reply_to)  
        elif event.message.gif:  
            sent_message = await client.send_file(target_chat, event.message.gif, reply_to=reply_to)  

        if sent_message:  
            message_map[(source_chat, event.message.id)] = sent_message.id  
            save_message_map()  

        logging.info(f"✅ تم إعادة إرسال الرسالة من {source_chat} إلى {target_chat} بعد إزالة المنشن")  

    except Exception as e:  
        logging.error(f"❌ فشل تحويل الرسالة من {source_chat} إلى {target_chat}: {e}")

async def main():
    async with client:
        await client.start(bot_token=bot_token)
        logging.info("🚀 البوت يعمل الآن وينتظر الرسائل...")
        await send_admin_notification("🚀 البوت بدأ العمل بنجاح!")
        await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())  # تصحيح طريقة تشغيل البوت
    except KeyboardInterrupt:
        logging.info("⛔ تم إيقاف البوت يدويًا.")
        if client.is_connected():
            client.loop.run_until_complete(client.disconnect())
    except Exception as e:
        logging.error(f"❌ خطأ غير متوقع: {e}")
