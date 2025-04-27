# -*- coding: utf-8 -*-
# ============================================
# ملف بوت تيليجرام لشحن الألعاب - REMA STORE
#
# تعليمات الاستخدام:
# 1. إدارة المشرفين:
#    - لإضافة مشرف جديد: استخدم الأمر 👥 إدارة المشرفين ثم ➕ إضافة مشرف وأرسل @username أو المعرف الرقمي.
#    - لحذف مشرف: في قائمة عرض المشرفين اضغط على الزر بجانب كل مشرف.
# 2. تعديل الأسعار:
#    - من لوحة التحكم، اختر 💰 إدارة الأسعار، ثم اضغط على الفئة المراد تعديلها وأدخل السعر الجديد.
# 3. إدارة الكوبونات:
#    - من لوحة التحكم، اختر 🎟️ إدارة الكوبونات، ثم ➕ إضافة كوبون وادخل الكود وقيمة الخصم.
#    - يطبق الكوبون على أول طلب لكل مستخدم.
# 4. عرض الإحصائيات:
#    - من لوحة التحكم، اختر 📊 الإحصائيات لعرض عدد المستخدمين، الطلبات، المشرفين، الكوبونات الفعالة.
#
# لتشغيل البوت: python PubgStoreBot_Final.py
# ============================================

import telebot
from telebot import types
import random
import pyotp
import time
from datetime import datetime, timedelta
import pytz
import sqlite3
from threading import Timer

# إعدادات البوت
TOKEN = '7995774911:AAFi0STyX4w91O8IiZYYtfQRRoMRAMe4sdk'
ADMIN_CHANNEL = '@remabott'
SUPPORT_TELEGRAM = '@T_J3H'
SUPPORT_WHATSAPP = '+447405971105'
DEV_ACCOUNT = '@S_QlQ'
NEWS_CHANNEL = 'https://t.me/REMA_STORE0'

# إنشاء كائن البوت
bot = telebot.TeleBot(TOKEN)

# قائمة المشرفين المعتمدين
def get_admins():
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    # إنشاء جدول المشرفين إذا لم يكن موجوداً
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        added_by INTEGER,
        added_date TEXT,
        is_active BOOLEAN DEFAULT TRUE
    )
    ''')

    # إضافة المشرف الافتراضي إذا كان الجدول فارغاً
    cursor.execute('SELECT COUNT(*) FROM admins')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO admins (user_id, username, added_by, added_date, is_active)
        VALUES (?, ?, ?, ?, ?)
        ''', (7973933950, 'default_admin', 7973933950, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), True))
        conn.commit()

    # جلب المشرفين النشطين فقط
    cursor.execute('SELECT user_id FROM admins WHERE is_active = TRUE')
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins

def is_admin(user_id):
    return user_id in get_admins()

@bot.message_handler(func=lambda message: message.text == '👥 إدارة المشرفين')
def manage_admins(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ عذراً، هذا الأمر متاح للمشرفين فقط")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin"),
        types.InlineKeyboardButton("📋 عرض المشرفين", callback_data="list_admins"),
        types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_admin")
    )

    bot.send_message(message.chat.id, """
👥 إدارة المشرفين:

• لإضافة مشرف جديد، اضغط على "إضافة مشرف"
• لعرض قائمة المشرفين وإدارتهم، اضغط على "عرض المشرفين"
    """, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'add_admin')
def add_admin_handler(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ عذراً، هذا الأمر متاح للمشرفين فقط")
        return

    msg = bot.send_message(call.message.chat.id, """
👤 الرجاء إرسال معرف المشرف الجديد:
- يمكنك إرسال معرف تيليجرام (مثال: @username)
- أو إرسال الآيدي مباشرة (مثال: 123456789)
    """)
    bot.register_next_step_handler(msg, process_new_admin)

def process_new_admin(message):
    try:
        admin_input = message.text.strip()

        # التحقق من نوع المدخل (معرف أو آيدي)
        if admin_input.startswith('@'):
            # إذا كان معرف، نحاول الحصول على الآيدي
            admin_info = bot.get_chat(admin_input)
            new_admin_id = admin_info.id
            admin_username = admin_input
        else:
            # إذا كان آيدي مباشر
            new_admin_id = int(admin_input)
            admin_username = str(new_admin_id)

        conn = sqlite3.connect('rema_store.db')
        cursor = conn.cursor()

        # التحقق إذا كان المشرف موجود مسبقاً
        cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (new_admin_id,))
        if cursor.fetchone():
            bot.reply_to(message, "⚠️ هذا المستخدم مشرف بالفعل!")
            return

        # إضافة المشرف الجديد
        cursor.execute('''
        INSERT INTO admins (user_id, username, added_by, added_date, is_active)
        VALUES (?, ?, ?, ?, ?)
        ''', (new_admin_id, admin_username, message.from_user.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), True))

        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ تم إضافة المشرف {admin_username} بنجاح")
        manage_admins(message)
    except Exception as e:
        bot.reply_to(message, "❌ حدث خطأ في إضافة المشرف. تأكد من صحة المعرف أو الآيدي")
        manage_admins(message)

@bot.callback_query_handler(func=lambda call: call.data == 'list_admins')
def list_admins_handler(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ عذراً، هذا الأمر متاح للمشرفين فقط")
        return

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, added_date FROM admins WHERE is_active = TRUE')
    admins = cursor.fetchall()
    conn.close()

    if not admins:
        bot.edit_message_text(
            "لا يوجد مشرفين حالياً",
            call.message.chat.id,
            call.message.message_id
        )
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for admin_id, username, added_date in admins:
        btn = types.InlineKeyboardButton(
            f"🗑️ {username} (منذ {added_date.split()[0]})",
            callback_data=f"remove_admin_{admin_id}"
        )
        markup.add(btn)

    markup.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_admin_manage"))

    bot.edit_message_text(
        "👥 قائمة المشرفين الحاليين:\n\nاضغط على المشرف لإزالته",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_admin_'))
def remove_admin_handler(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ عذراً، هذا الأمر متاح للمشرفين فقط")
        return

    admin_id = int(call.data.split('_')[2])

    # لا يمكن إزالة نفسك
    if admin_id == call.from_user.id:
        bot.answer_callback_query(call.id, "⚠️ لا يمكنك إزالة نفسك من قائمة المشرفين")
        return

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE admins SET is_active = FALSE WHERE user_id = ?', (admin_id,))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "✅ تم إزالة المشرف بنجاح")
    list_admins_handler(call)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_admin_manage')
def back_to_admin_manage(call):
    manage_admins(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_admin')
def back_to_admin(call):
    show_admin_panel(call.message.chat.id)

@bot.message_handler(func=lambda message: message.text == '👤 إدارة المستخدمين')
def manage_users(message):
    if not is_admin(message.from_user.id):
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="search_user"),
        types.InlineKeyboardButton("📊 إحصائيات المستخدمين", callback_data="user_stats")
    )

    bot.send_message(message.chat.id, "👤 إدارة المستخدمين:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'search_user')
def search_user(call):
    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(call.message.chat.id, "🔍 أدخل معرف المستخدم أو رقم الهاتف:")
    bot.register_next_step_handler(msg, process_user_search)

def process_user_search(message):
    search_term = message.text

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT user_id, full_name, phone, player_id, registration_date
    FROM users
    WHERE user_id = ? OR phone = ?
    ''', (search_term, search_term))

    user = cursor.fetchone()
    conn.close()

    if user:
        markup = types.InlineKeyboardMarkup()
        block_btn = types.InlineKeyboardButton(
            "🚫 حظر المستخدم" if not user[5] else "✅ إلغاء الحظر",
            callback_data=f"toggle_block_{user[0]}"
        )
        markup.add(block_btn)

        bot.send_message(message.chat.id, f"""
🔍 معلومات المستخدم:

👤 المعرف: {user[0]}
📝 الاسم: {user[1]}
📱 الهاتف: {user[2]}
🎮 ID اللاعب: {user[3]}
📅 تاريخ التسجيل: {user[4]}
        """, reply_markup=markup)
    else:
        bot.reply_to(message, "❌ لم يتم العثور على المستخدم")

def is_admin(user_id):
    """التحقق مما إذا كان المستخدم مشرفاً"""
    return user_id in ADMINS

# إعدادات إضافية
WELCOME_GIF = "https://media.giphy.com/media/welcome.gif"  # رابط GIF الترحيب
DISCOUNT_CODES = {
    "WELCOME10": 10,  # خصم 10%
    "SUMMER25": 25    # خصم 25%
}

import shutil
from datetime import datetime
import os

# إنشاء كائن البوت
bot = telebot.TeleBot(TOKEN)

# وظائف قاعدة البيانات
def backup_database():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = 'db_backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        backup_path = f'{backup_dir}/rema_store_{timestamp}.db'
        shutil.copy2('rema_store.db', backup_path)
        # حذف النسخ الاحتياطية القديمة (الاحتفاظ بآخر 5 نسخ)
        backup_files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')])
        while len(backup_files) > 5:
            os.remove(os.path.join(backup_dir, backup_files.pop(0)))
        print(f"✅ تم إنشاء نسخة احتياطية: {backup_path}")
    except Exception as e:
        print(f"❌ خطأ في النسخ الاحتياطي: {e}")

def init_db():
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    # إنشاء جدول المستخدمين
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        phone TEXT,
        player_id TEXT,
        registration_date TEXT,
        last_used_date TEXT,
        telegram_username TEXT,
        language_code TEXT DEFAULT 'ar',
        is_blocked BOOLEAN DEFAULT FALSE,
        settings TEXT
    )
    ''')

    # إنشاء جدول الطلبات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        game_name TEXT,
        uc_amount TEXT,
        player_id TEXT,
        price INTEGER,
        paid_amount INTEGER,
        payment_method TEXT,
        status TEXT DEFAULT 'pending',
        order_date TEXT,
        completion_date TEXT,
        payment_proof TEXT,
        admin_notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # إنشاء جدول رسائل البوت
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_messages (
        chat_id INTEGER,
        message_id INTEGER,
        is_permanent BOOLEAN DEFAULT FALSE,
        message_type TEXT,
        created_at TEXT,
        PRIMARY KEY (chat_id, message_id)
    )
    ''')

    # إنشاء جدول المكافآت
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rewards (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'bronze',
        last_reward_date TEXT,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (referred_by) REFERENCES users (user_id)
    )
    ''')

    # إنشاء جدول الكوبونات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupons (
        code TEXT PRIMARY KEY,
        discount_type TEXT,
        discount_value INTEGER,
        min_purchase INTEGER,
        max_uses INTEGER,
        current_uses INTEGER DEFAULT 0,
        start_date TEXT,
        end_date TEXT,
        is_active BOOLEAN DEFAULT TRUE
    )
    ''')

    # إنشاء جدول استخدام الكوبونات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupon_usage (
        code TEXT,
        user_id INTEGER,
        order_id INTEGER,
        used_date TEXT,
        discount_amount INTEGER,
        PRIMARY KEY (code, user_id, order_id),
        FOREIGN KEY (code) REFERENCES coupons (code),
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    )
    ''')

    # إنشاء جدول المنتجات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_name TEXT,
        product_name TEXT,
        description TEXT,
        price INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TEXT,
        updated_at TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# قاموس لحفظ بيانات المستخدمين
user_data = {}
otp_secrets = {}
otp_attempts = {}
pending_orders = {}
reminder_timers = {}

# قائمة المشرفين الافتراضية
ADMINS = [7973933950]  # يمكنك إضافة المزيد من المشرفين هنا

# ساعات العمل (8 صباحًا إلى 11 مساءً بتوقيت سوريا)
WORKING_HOURS = {
    'start': 8,
    'end': 23
}

# أسعار UC
UC_PRICES = {
    '60_UC': 11500,
    '120_UC': 23000,
    '180_UC': 34000,
    '325_UC': 56000,
    '660_UC': 112000,
    '1800_UC': 273000,
    '3850_UC': 530000,
    '8100_UC': 1070000
}

# ---------------------------
# وظائف مساعدة
# ---------------------------

def get_current_time():
    damascus_tz = pytz.timezone('Asia/Damascus')
    return datetime.now(damascus_tz)

def is_bot_working_hours():
    now = get_current_time()
    current_hour = now.hour
    return WORKING_HOURS['start'] <= current_hour < WORKING_HOURS['end']

def clean_chat(chat_id, keep_permanent=True):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    if keep_permanent:
        cursor.execute('SELECT message_id FROM bot_messages WHERE chat_id = ? AND is_permanent = FALSE ORDER BY message_id DESC', (chat_id,))
    else:
        cursor.execute('SELECT message_id FROM bot_messages WHERE chat_id = ? ORDER BY message_id DESC', (chat_id,))

    messages = cursor.fetchall()

    for msg_id in messages:
        try:
            bot.delete_message(chat_id, msg_id[0])
            cursor.execute('DELETE FROM bot_messages WHERE chat_id = ? AND message_id = ?', (chat_id, msg_id[0]))
        except:
            pass

    conn.commit()
    conn.close()

def add_to_history(chat_id, message_id, is_permanent=False):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO bot_messages VALUES (?, ?, ?)', (chat_id, message_id, is_permanent))
    conn.commit()
    conn.close()

def delete_user_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

def send_clean_message(chat_id, text, reply_markup=None, parse_mode=None, is_permanent=False):
    clean_chat(chat_id, keep_permanent=True)
    msg = bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    add_to_history(chat_id, msg.message_id, is_permanent)
    return msg

def get_user_data(user_id):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, phone, player_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'full_name': result[0],
            'phone': result[1],
            'player_id': result[2]
        }
    return None

def save_user(user_id, username, full_name, phone, player_id=None):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT OR REPLACE INTO users 
    (user_id, username, full_name, phone, player_id, registration_date, last_used_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, 
        username, 
        full_name, 
        phone, 
        player_id,
        get_current_time().strftime('%Y-%m-%d %H:%M:%S'),
        get_current_time().strftime('%Y-%m-%d %H:%M:%S')
    ))

    conn.commit()
    conn.close()

def create_order(user_id, game_name, uc_amount, player_id, price, paid_amount, payment_method):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO orders (user_id, game_name, uc_amount, player_id, price, paid_amount, payment_method, order_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, game_name, uc_amount, player_id, price, paid_amount, payment_method, 
          get_current_time().strftime('%Y-%m-%d %H:%M:%S')))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return order_id

def get_user_orders(user_id):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT order_id, game_name, uc_amount, status, order_date FROM orders 
    WHERE user_id = ? ORDER BY order_date DESC
    ''', (user_id,))

    orders = cursor.fetchall()
    conn.close()

    return orders

def get_order_status(order_id):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    cursor.execute('SELECT status FROM orders WHERE order_id = ?', (order_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def update_order_status(order_id, status):
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE orders SET status = ?, completion_date = ?
    WHERE order_id = ?
    ''', (status, get_current_time().strftime('%Y-%m-%d %H:%M:%S'), order_id))

    conn.commit()
    conn.close()

def schedule_reminder(chat_id, order_id=None):
    if chat_id in reminder_timers:
        reminder_timers[chat_id].cancel()

    def send_reminder():
        markup = types.InlineKeyboardMarkup()
        if order_id:
            btn = types.InlineKeyboardButton("⚡ إكمال الطلب", callback_data=f"complete_order_{order_id}")
        else:
            btn = types.InlineKeyboardButton("⚡ البدء الآن", callback_data="start_order")
        markup.add(btn)

        send_clean_message(chat_id, "⚡ ما زلت ترغب بإكمال شحن شداتك؟ اضغط هنا لإكمال العملية!", reply_markup=markup)

    reminder_timers[chat_id] = Timer(1800, send_reminder)
    reminder_timers[chat_id].start()

def format_order_id(order_id):
    return f"🆔 #{order_id:06d}"

# ---------------------------
# معالجة الأوامر والرسائل
# ---------------------------

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ عذراً، هذا الأمر متاح للمشرفين فقط")
        return

    show_admin_panel(message.chat.id)

def show_admin_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn1 = types.KeyboardButton('💰 إدارة الأسعار')
    btn2 = types.KeyboardButton('🎟️ إدارة الكوبونات')
    btn3 = types.KeyboardButton('👥 إدارة المشرفين')
    btn4 = types.KeyboardButton('👤 إدارة المستخدمين')
    btn5 = types.KeyboardButton('📊 الإحصائيات')
    btn6 = types.KeyboardButton('🔙 رجوع للقائمة الرئيسية')

    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)

    bot.send_message(chat_id, """
🎮 لوحة تحكم المشرف

اختر أحد الخيارات التالية للتحكم بإعدادات البوت:
    """, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '💰 إدارة الأسعار')
def manage_prices(message):
    if not is_admin(message.from_user.id):
        return

    markup = types.InlineKeyboardMarkup(row_width=1)

    # قراءة الأسعار من قاعدة البيانات
    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS uc_prices
                     (amount TEXT PRIMARY KEY, price INTEGER)''')
    conn.commit()

    # إضافة الأسعار الافتراضية إذا كانت القاعدة فارغة
    cursor.execute('SELECT COUNT(*) FROM uc_prices')
    if cursor.fetchone()[0] == 0:
        for amount, price in UC_PRICES.items():
            cursor.execute('INSERT INTO uc_prices VALUES (?, ?)', (amount, price))
        conn.commit()

    # قراءة الأسعار الحالية
    cursor.execute('SELECT amount, price FROM uc_prices')
    prices = cursor.fetchall()
    conn.close()

    for amount, price in prices:
        btn = types.InlineKeyboardButton(
            f"{amount.replace('_', ' ')} - {price:,} ل.س",
            callback_data=f"edit_price_{amount}"
        )
        markup.add(btn)

    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_admin"))
    bot.send_message(message.chat.id, "💰 اختر السعر المراد تعديله:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def back_to_admin(call):
    show_admin_panel(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_price_'))
def edit_price(call):
    if not is_admin(call.from_user.id):
        return

    uc_amount = call.data.split('_')[2]
    user_data[call.message.chat.id] = {'editing_amount': uc_amount} # Store the UC amount being edited
    msg = bot.send_message(call.message.chat.id, f"💰 أدخل السعر الجديد لـ {uc_amount.replace('_', ' ')}:")
    bot.register_next_step_handler(msg, process_new_price)

def process_new_price(message):
    try:
        new_price = int(message.text)
        if new_price <= 0:
            bot.reply_to(message, "❌ يجب أن يكون السعر أكبر من صفر")
            return

        conn = sqlite3.connect('rema_store.db')
        cursor = conn.cursor()

        # تحديث الأسعار في قاعدة البيانات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS uc_prices (
            amount TEXT PRIMARY KEY,
            price INTEGER DEFAULT 0
        )
        ''')

        # تحديث السعر للفئة المحددة
        cursor.execute('''
        INSERT OR REPLACE INTO uc_prices (amount, price) 
        VALUES (?, ?)
        ''', (user_data[message.chat.id].get('editing_amount'), new_price))

        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ تم تحديث سعر {user_data[message.chat.id].get('editing_amount').replace('_', ' ')} إلى {new_price:,} ل.س")
        manage_prices(message)
    except ValueError:
        bot.reply_to(message, "❌ يرجى إدخال رقم صحيح")
        manage_prices(message)

@bot.message_handler(func=lambda message: message.text == '🎟️ إدارة الكوبونات')
def manage_coupons(message):
    if not is_admin(message.from_user.id):
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة كوبون", callback_data="add_coupon"),
        types.InlineKeyboardButton("📋 عرض الكوبونات", callback_data="list_coupons")
    )

    bot.send_message(message.chat.id, "🎟️ إدارة كوبونات الخصم:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'add_coupon')
def add_coupon(call):
    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(call.message.chat.id, """
🎟️ أدخل معلومات الكوبون بالصيغة التالية:
الكود،نسبة_الخصم
مثال: REMA50،50
    """)
    bot.register_next_step_handler(msg, process_new_coupon)

def process_new_coupon(message):
    try:
        code, discount = message.text.split('،')
        discount = int(discount)

        conn = sqlite3.connect('rema_store.db')
        cursor = conn.cursor()

        # حذف الكوبون القديم إذا وجد
        cursor.execute('DELETE FROM coupons WHERE code = ?', (code.lower(),))

        # إضافة الكوبون الجديد
        cursor.execute('''
        INSERT INTO coupons (code, discount_type, discount_value, is_active, start_date)
        VALUES (?, 'percentage', ?, TRUE, ?)
        ''', (code.lower(), discount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ تم إضافة الكوبون {code} بنسبة خصم {discount}%")
        manage_coupons(message)
    except Exception as e:
        print(f"Error adding coupon: {e}")
        bot.reply_to(message, "❌ صيغة غير صحيحة")
        manage_coupons(message)

@bot.callback_query_handler(func=lambda call: call.data == 'list_coupons')
def list_coupons(call):
    if not is_admin(call.from_user.id):
        return

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code, discount_value, current_uses FROM coupons WHERE is_active = TRUE')
    coupons = cursor.fetchall()
    conn.close()

    if not coupons:
        bot.send_message(call.message.chat.id, "لا توجد كوبونات نشطة")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for code, discount, uses in coupons:
        btn = types.InlineKeyboardButton(
            f"{code} - {discount}% (استخدم {uses} مرة)",
            callback_data=f"edit_coupon_{code}"
        )
        markup.add(btn)

    bot.edit_message_text(
        "🎟️ الكوبونات النشطة:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(commands=['start', 'restart'])
def send_welcome(message):
    if not is_bot_working_hours():
        bot.send_message(message.chat.id, "⏳ عذرًا، البوت مغلق حاليًا\n\nساعات العمل من 8 صباحًا إلى 11 مساءً بتوقيت سوريا")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    btn1 = types.KeyboardButton('🎮 شحن ألعاب')
    btn2 = types.KeyboardButton('📞 تواصل')
    btn3 = types.KeyboardButton('📢 قناة الأخبار')
    btn4 = types.KeyboardButton('🔄 إعادة تشغيل')
    btn5 = types.KeyboardButton('📋 حالة الطلب')
    btn6 = types.KeyboardButton('🎟️ كوبون خصم')
    btn7 = types.KeyboardButton('👤 حسابي')

    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)

    welcome_photo = "https://i.postimg.cc/B6F8qDw8/retro-arcade-gaming-cabinet-night-scene-tsq7vihg9g1ycnv8.webp"  # رابط الصورة
    welcome_msg = """
✨ أهلاً بك في بوت متجر ريما REMA STORE!

🛒 خدماتنا:
🔹 شحن ألعاب سريع وآمن
🔹 أسعار منافسة ومميزة
🔹 دعم فني متواصل 24/7

اختر الخدمة التي تحتاجها عبر الأزرار بالأسفل!

ᴾʳᵒᵍʳᵃᵐᵐⁱⁿᵍ ᵇʸ ᴿᵃˢˢⁱˡ
    """

    try:
        photo = bot.send_photo(message.chat.id, welcome_photo, caption=welcome_msg, reply_markup=markup)
        add_to_history(message.chat.id, photo.message_id, is_permanent=True)
    except Exception as e:
        print(f"Error sending photo: {e}")
        send_clean_message(message.chat.id, welcome_msg, reply_markup=markup, is_permanent=True)

@bot.message_handler(func=lambda message: message.text == '🎟️ كوبون خصم')
def discount_coupon(message):
    markup = types.InlineKeyboardMarkup()
    msg_btn = types.InlineKeyboardButton("💬 إدخال كوبون", callback_data="enter_coupon")
    back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
    markup.add(msg_btn, back_btn)

    send_clean_message(message.chat.id, """
🎟️ كوبونات الخصم:

أدخل الكوبون للحصول على خصم فوري على طلبك القادم!
    """, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'enter_coupon')
def enter_coupon(call):
    chat_id = call.message.chat.id
    msg = send_clean_message(chat_id, "🎟️ الرجاء إدخال كود الكوبون:")
    bot.register_next_step_handler(msg, process_coupon)

def process_coupon(message):
    chat_id = message.chat.id
    coupon_code = message.text.lower()
    user_id = message.from_user.id

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    # التحقق من وجود الكوبون وصلاحيته
    cursor.execute('''
    SELECT discount_value FROM coupons 
    WHERE code = ? AND is_active = TRUE
    ''', (coupon_code,))
    coupon = cursor.fetchone()

    if not coupon:
        send_clean_message(chat_id, "❌ هذا الكوبون غير صالح")
        conn.close()
        return

    # التحقق من استخدام الكوبون سابقاً
    cursor.execute('''
    SELECT COUNT(*) FROM coupon_usage 
    WHERE code = ? AND user_id = ?
    ''', (coupon_code, user_id))
    used_count = cursor.fetchone()[0]

    if used_count > 0:
        send_clean_message(chat_id, "⚠️ عذراً، لقد استخدمت هذا الكوبون من قبل!")
        conn.close()
        return

    discount_value = coupon[0]

    if coupon_code in discounts:
        # حفظ الكوبون للمستخدم
        cursor.execute('''
        INSERT INTO coupon_usage (code, user_id, used_date)
        VALUES (?, ?, ?)
        ''', (coupon_code, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

        markup = types.InlineKeyboardMarkup()
        use_now_btn = types.InlineKeyboardButton("🛍️ استخدم الآن", callback_data="start_order")
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
        markup.add(use_now_btn, back_btn)

        send_clean_message(chat_id, f"""
✅ تم تفعيل الكوبون بنجاح!

💰 نسبة الخصم: {discounts[coupon_code]}%

يمكنك استخدام الخصم الآن في طلبك القادم.
        """, reply_markup=markup)

        # تخزين الخصم في بيانات المستخدم
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['discount'] = discounts[coupon_code]
    else:
        markup = types.InlineKeyboardMarkup()
        try_again_btn = types.InlineKeyboardButton("🔄 حاول مرة أخرى", callback_data="enter_coupon")
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
        markup.add(try_again_btn, back_btn)

        send_clean_message(chat_id, "❌ عذراً، هذا الكوبون غير صالح!", reply_markup=markup)

    conn.close()

@bot.message_handler(func=lambda message: message.text == '📋 حالة الطلب')
def order_status(message):
    user_id = message.from_user.id
    orders = get_user_orders(user_id)

    if not orders:
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
        markup.add(back_btn)

        send_clean_message(message.chat.id, "⚠️ أنت لم تقم بطلب أي طلب بعد!", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for order in orders:
            order_id, game_name, uc_amount, status, order_date = order
            btn = types.InlineKeyboardButton(
                f"{format_order_id(order_id)} - {status}",
                callback_data=f"order_details_{order_id}"
            )
            markup.add(btn)

        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
        markup.add(back_btn)

        send_clean_message(message.chat.id, "📋 اختر الطلب لمعرفة التفاصيل:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('order_details_'))
def show_order_details(call):
    order_id = int(call.data.split('_')[2])
    user_id = call.from_user.id

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT game_name, uc_amount, player_id, price, paid_amount, payment_method, status, order_date
    FROM orders WHERE order_id = ? AND user_id = ?
    ''', (order_id, user_id))

    order = cursor.fetchone()
    conn.close()

    if order:
        game_name, uc_amount, player_id, price, paid_amount, payment_method, status, order_date = order

        status_emojis = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'rejected': '❌'
        }

        details = f"""
📋 تفاصيل الطلب {format_order_id(order_id)}

🎮 اللعبة: {game_name}
💰 الفئة: {uc_amount}
💵 السعر: {price} ل.س
🆔 ID اللاعب: {player_id}
💳 طريقة الدفع: {payment_method}
📅 تاريخ الطلب: {order_date}
🔄 الحالة: {status_emojis.get(status, '')} {status}
        """

        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_orders")
        markup.add(back_btn)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=details,
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(call.id, "⚠️ الطلب غير موجود أو لا يوجد لديك صلاحية لعرضه")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_orders')
def back_to_orders(call):
    order_status(call.message)

@bot.message_handler(func=lambda message: message.text == '🔄 إعادة تشغيل')
def restart_bot(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == '🎮 شحن ألعاب')
def game_charging(message):
    if not is_bot_working_hours():
        bot.send_message(message.chat.id, "⏳ عذرًا، البوت مغلق حاليًا\n\nساعات العمل من 8 صباحًا إلى 11 مساءً بتوقيت سوريا")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)

    btn_pubg = types.InlineKeyboardButton("🎯 شحن PUBG", callback_data="pubg_charging")
    btn_other = types.InlineKeyboardButton("🎮 ألعاب أخرى (قريبًا)", callback_data="coming_soon")
    btn_back = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")

    markup.add(btn_pubg, btn_other, btn_back)

    send_clean_message(message.chat.id, "🎮 اختر نوع الشحن:", reply_markup=markup)

    schedule_reminder(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == 'pubg_charging')
def pubg_charging(call):
    chat_id = call.message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)

    # الحصول على نسبة الخصم إذا وجدت
    discount = user_data.get(chat_id, {}).get('discount', 0)

    uc_prices_list = [
        ("60 UC", "60_UC", 11500),
        ("120 UC", "120_UC", 23000),
        ("180 UC", "180_UC", 34000),
        ("325 UC", "325_UC", 56000),
        ("660 UC", "660_UC", 112000),
        ("1800 UC", "1800_UC", 273000),
        ("3850 UC", "3850_UC", 530000),
        ("8100 UC", "8100_UC", 1070000)
    ]

    for uc_amount, callback, price in uc_prices_list:
        if discount > 0:
            discounted_price = price - (price * discount / 100)
            button_text = f"{uc_amount} - {int(discounted_price):,} ل.س 🎟️"
        else:
            button_text = f"{uc_amount} - {price:,} ل.س"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=callback))

    markup.add(types.InlineKeyboardButton("💰 فئة مخصصة", callback_data="custom_amount"))
    markup.add(types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_games"))

    message_text = "🎯 اختر فئة الشحن لـ PUBG:"
    if discount > 0:
        message_text += f"\n\n🎟️ تم تطبيق خصم {discount}% على جميع الأسعار!"

    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=message_text,
        reply_markup=markup
    )

    schedule_reminder(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.endswith('_UC') or call.data == 'custom_amount')
def handle_uc_selection(call):
    chat_id = call.message.chat.id

    if call.data == 'custom_amount':
        msg = send_clean_message(chat_id, "⌨️ الرجاء إدخال المبلغ المطلوب (بالليرة السورية):")
        bot.register_next_step_handler(msg, process_custom_amount)
    else:
        uc_amount = call.data.split('_')[0]
        price = UC_PRICES.get(call.data, 0)
        user_data[chat_id] = {'uc_amount': uc_amount, 'price': price}

        # التحقق إذا كان المستخدم لديه بيانات مسجلة
        user_info = get_user_data(call.from_user.id)
        if user_info and user_info.get('player_id'):
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn_use_old = types.InlineKeyboardButton("استخدام البيانات السابقة", callback_data="use_old_data")
            btn_new_data = types.InlineKeyboardButton("إدخال بيانات جديدة", callback_data="enter_new_data")
            markup.add(btn_use_old, btn_new_data)

            send_clean_message(chat_id, f"""
🔍 لديك بيانات مسجلة مسبقاً:

👤 الاسم: {user_info['full_name']}
📱 الهاتف: {user_info['phone']}
🆔 ID اللاعب: {user_info['player_id']}

هل تريد استخدام هذه البيانات أم إدخال بيانات جديدة؟
            """, reply_markup=markup)
        else:
            msg = send_clean_message(chat_id, "🔢 الرجاء إدخال ID اللاعب (يجب أن لا يقل عن 9 خانات):")
            bot.register_next_step_handler(msg, process_player_id)

    schedule_reminder(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == 'use_old_data')
def use_old_data(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    user_info = get_user_data(user_id)
    if user_info:
        user_data[chat_id] = {
            'customer_name': user_info['full_name'],
            'phone': user_info['phone'],
            'player_id': user_info['player_id']
        }

        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_phone")
        edit_btn = types.InlineKeyboardButton("✏️ تعديل", callback_data="edit_phone")
        markup.add(confirm_btn, edit_btn)

        current_time = get_current_time().strftime("%H:%M")
        send_clean_message(chat_id, f"""
✅ تم استلام طلبك الساعة {current_time}

ملخص الطلب:

🆔 ID: {user_info['player_id']}
👤 الاسم: {user_info['full_name']}
☎️ رقم الهاتف: {user_info['phone']}

هل كل شيء صحيح?
        """, reply_markup=markup)
    else:
        send_clean_message(chat_id, "⚠️ حدث خطأ في استعادة البيانات، يرجى إدخال البيانات يدوياً")
        msg = send_clean_message(chat_id, "🔢 الرجاء إدخال ID اللاعب (يجب أن لا يقل عن 9 خانات):")
        bot.register_next_step_handler(msg, process_player_id)

    schedule_reminder(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == 'enter_new_data')
def enter_new_data(call):
    chat_id = call.message.chat.id
    msg = send_clean_message(chat_id, "🔢 الرجاء إدخال ID اللاعب (يجب أن لا يقل عن 9 خانات):")
    bot.register_next_step_handler(msg, process_player_id)
    schedule_reminder(chat_id)

def process_custom_amount(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)

    try:
        price = int(message.text)
        user_data[chat_id] = {'uc_amount': 'مخصص', 'price': price}

        msg = send_clean_message(chat_id, "🔢 الرجاء إدخال ID اللاعب (يجب أن لا يقل عن 9 خانات):")
        bot.register_next_step_handler(msg, process_player_id)
    except ValueError:
        send_clean_message(chat_id, "⚠️ الرجاء إدخال رقم صحيح")
        game_charging(message)

    schedule_reminder(chat_id)

def process_player_id(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)
    player_id = message.text

    if not player_id.isdigit() or len(player_id) < 9:
        error_msg = "❌ خطأ في ID اللاعب\n\n✅ يجب أن يحتوي على أرقام فقط ولا يقل عن 9 خانات\nمثال: 123456789"
        bot.send_message(chat_id, error_msg)
        time.sleep(8)  # انتظار 8 ثواني
        game_charging(message)
        return

    user_data[chat_id]['player_id'] = player_id

    markup = types.InlineKeyboardMarkup()
    confirm_btn = types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_player_id")
    edit_btn = types.InlineKeyboardButton("✏️ تعديل", callback_data="edit_player_id")
    markup.add(confirm_btn, edit_btn)

    send_clean_message(chat_id, f"""
✅ ملخص الطلب حتى الآن:

🆔 ID اللاعب: {player_id}

هل كل شيء صحيح?
    """, reply_markup=markup)

    schedule_reminder(chat_id)

@bot.callback_query_handler(func=lambda call: call.data in ['confirm_player_id', 'edit_player_id'])
def handle_player_id_confirmation(call):
    chat_id = call.message.chat.id

    if call.data == 'edit_player_id':
        msg = send_clean_message(chat_id, "🔢 الرجاء إدخال ID اللاعب مرة أخرى:")
        bot.register_next_step_handler(msg, process_player_id)
        return

    msg = send_clean_message(chat_id, f"👤 رائع! الرجاء إدخال اسمك الكامل:")
    bot.register_next_step_handler(msg, process_customer_name)

    schedule_reminder(chat_id)

def process_customer_name(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)
    user_data[chat_id]['customer_name'] = message.text

    msg = send_clean_message(chat_id, f"""
✨ أهلاً بك يا {message.text}!

📱 الرجاء إدخال رقم الهاتف مع الرمز الدولي:
مثال: +963987654321
    """)
    bot.register_next_step_handler(msg, process_phone_number)

    schedule_reminder(chat_id)

def process_phone_number(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)
    phone = message.text

    if not phone.startswith('+') or len(phone) < 11 or len(phone) > 14:
        error_msg = """
❌ رقم الهاتف غير صحيح

✅ تأكد أن الرقم يبدأ بـ + ويتكون من 11 إلى 13 خانة
مثال: +963987654321
        """
        bot.send_message(chat_id, error_msg)
        time.sleep(8)  # انتظار 8 ثواني
        msg = send_clean_message(chat_id, "📱 الرجاء إدخال رقم الهاتف مع الرمز الدولي:")
        bot.register_next_step_handler(msg, process_phone_number)
        return

    user_data[chat_id]['phone'] = phone

    markup = types.InlineKeyboardMarkup()
    confirm_btn = types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_phone")
    edit_btn = types.InlineKeyboardButton("✏️ تعديل", callback_data="edit_phone")
    markup.add(confirm_btn, edit_btn)

    current_time = get_current_time().strftime("%H:%M")
    send_clean_message(chat_id, f"""
✅ تم استلام طلبك الساعة {current_time}

ملخص الطلب:

🆔 ID: {user_data[chat_id].get('player_id', '')}
👤 الاسم: {user_data[chat_id].get('customer_name', '')}
☎️ رقم الهاتف: {phone}

هل كل شيء صحيح?
    """, reply_markup=markup)

    schedule_reminder(chat_id)

@bot.callback_query_handler(func=lambda call: call.data in ['confirm_phone', 'edit_phone'])
def handle_phone_confirmation(call):
    chat_id = call.message.chat.id

    if call.data == 'edit_phone':
        msg = send_clean_message(chat_id, "📱 الرجاء إدخال رقم الهاتف مع الرمز الدولي مرة أخرى:")
        bot.register_next_step_handler(msg, process_phone_number)
        return

    send_otp(chat_id)
    schedule_reminder(chat_id)

def send_otp(chat_id):
    secret = pyotp.random_base32()
    otp_secrets[chat_id] = {
        'secret': secret,
        'timestamp': time.time(),
        'attempts': 0
    }

    totp = pyotp.TOTP(secret, digits=6, interval=180)
    otp_code = totp.now()

    markup = types.InlineKeyboardMarkup()
    resend_btn = types.InlineKeyboardButton("🔄 إعادة إرسال", callback_data="resend_otp")
    markup.add(resend_btn)

    msg = send_clean_message(chat_id, f"""
🔐 رمز التحقق الخاص بك:

{otp_code}

⏳ صلاحية الرمز: 3 دقائق

الرجاء إدخال رمز التحقق:
    """, reply_markup=markup)

    bot.register_next_step_handler(msg, verify_otp)
    schedule_reminder(chat_id)

@bot.callback_query_handler(func=lambda call: call.data =='resend_otp')
def resend_otp(call):
    chat_id = call.message.chat.id
    send_otp(chat_id)
    schedule_reminder(chat_id)

def verify_otp(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)
    user_otp = message.text.strip()

    otp_data = otp_secrets.get(chat_id)

    if not otp_data:
        send_clean_message(chat_id, "⚠️ انتهت صلاحية الجلسة، يرجى البدء من جديد")
        return

    otp_data['attempts'] += 1
    otp_secrets[chat_id] = otp_data

    if otp_data['attempts'] > 3:
        send_clean_message(chat_id, "⚠️ تجاوزت عدد المحاولات المسموح بها، يرجى البدء من جديد")
        del otp_secrets[chat_id]
        return

    totp = pyotp.TOTP(otp_data['secret'], digits=6, interval=180)

    if totp.verify(user_otp):
        send_clean_message(chat_id, "✅ تم التحقق بنجاح!")
        show_payment_options(message)
    else:
        markup = types.InlineKeyboardMarkup()
        resend_btn = types.InlineKeyboardButton("🔄 إعادة إرسال", callback_data="resend_otp")
        markup.add(resend_btn)

        remaining_attempts = 3 - otp_data['attempts']
        msg = send_clean_message(
            chat_id, 
            f"⚠️ رمز التحقق غير صحيح\n\nلديك {remaining_attempts} محاولات متبقية",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, verify_otp)

    schedule_reminder(chat_id)

def show_payment_options(message):
    chat_id = message.chat.id

    # تطبيق الخصم إذا كان متوفراً
    discount = user_data.get(chat_id, {}).get('discount', 0)
    original_price = user_data.get(chat_id, {}).get('price', 0)

    if discount > 0:
        discounted_price = original_price - (original_price * discount / 100)
        user_data[chat_id]['final_price'] = discounted_price
    else:
        user_data[chat_id]['final_price'] = original_price

    markup = types.InlineKeyboardMarkup(row_width=1)

    options = [
        ("💳 الحوالة البنكية (🚧 قريباً)", "bank_transfer"),
        ("₿ Coinex (BSC - BEP20)", "coinex"),
        ("💎 شام كاش (🚧 قريباً)", "sham_cash"),
        ("📱 سيرياتيل كاش", "syriatel_cash"),
        ("🎁 بطاقات الهدايا", "gift_cards"),
        ("💵 Payoneer (🚧 قريباً)", "payoneer"),
        ("↩️ رجوع", "back_to_pubg")
    ]

    for text, callback in options:
        markup.add(types.InlineKeyboardButton(text, callback_data=callback))

    order_data = user_data.get(chat_id, {})

    price_msg = f"""
💰 اختر طريقة الدفع:

🔹 فئة UC: {order_data.get('uc_amount', '')}
"""

    if order_data.get('discount', 0) > 0:
        price_msg += f"""
💵 السعر الأصلي: {order_data.get('price', '')} ل.س
🎟️ الخصم: {order_data.get('discount')}%
💰 السعر النهائي: {int(order_data.get('final_price', 0))} ل.س
"""
    else:
        price_msg += f"💰 المبلغ المطلوب: {order_data.get('price', '')} ل.س"

    price_msg += "\nاختر طريقة الدفع المناسبة:"

    send_clean_message(chat_id, price_msg, reply_markup=markup)

    schedule_reminder(chat_id)

@bot.callback_query_handler(func=lambda call: call.data in [
    'bank_transfer', 'coinex', 'sham_cash', 
    'syriatel_cash', 'gift_cards', 'payoneer'
])
def handle_payment_method(call):
    chat_id = call.message.chat.id
    method = call.data

    if method == 'bank_transfer':
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_payment")
        markup.add(back_btn)

        send_clean_message(chat_id, "⚠️ الخدمة قيد التفعيل حالياً", reply_markup=markup)

    elif method == 'coinex':
        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton("✅ تأكيد التحويل", callback_data="confirm_coinex")
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_payment")
        markup.add(confirm_btn, back_btn)

        send_clean_message(chat_id, """
📌 للدفع عبر Coinex (BSC - BEP20):

🔹 عنوان المحفظة:
`0x694142b6a4c9dc077220ee037f1c42bd7b4d68b5`

الرجاء إرسال المبلغ المطلوب ثم الضغط على تأكيد التحويل
        """, reply_markup=markup, parse_mode="Markdown")

    elif method in ['sham_cash', 'payoneer']:
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_payment")
        markup.add(back_btn)

        send_clean_message(chat_id, "⏳ ستتوفر هذه الخدمة قريباً", reply_markup=markup)

    elif method == 'syriatel_cash':
        markup = types.InlineKeyboardMarkup()
        amount_btn = types.InlineKeyboardButton("💰 إدخال المبلغ", callback_data="enter_syriatel_amount")
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_payment")
        markup.add(amount_btn, back_btn)

        send_clean_message(chat_id, """
💳 للدفع عبر سيرياتيل كاش:

🔹 قم بتحويل المبلغ إلى أحد الرموز التالية:
74962454
78833277

ثم اضغط على زر "إدخال المبلغ"
        """, reply_markup=markup)

    elif method == 'gift_cards':
        markup = types.InlineKeyboardMarkup(row_width=1)
        telegram_btn = types.InlineKeyboardButton("📲 تواصل عبر تيليجرام", url=f"https://t.me/{SUPPORT_TELEGRAM[1:]}")
        whatsapp_btn = types.InlineKeyboardButton("📱 تواصل عبر واتساب", url=f"https://wa.me/{SUPPORT_WHATSAPP[1:]}")
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_payment")
        markup.add(telegram_btn, whatsapp_btn, back_btn)

        send_clean_message(chat_id, """
🎁 للدفع ببطاقات الهدايا:

يرجى التواصل مع إدارة المتجر لأتمام العملية
        """, reply_markup=markup)

    schedule_reminder(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == 'enter_syriatel_amount')
def ask_for_syriatel_amount(call):
    chat_id = call.message.chat.id
    msg = send_clean_message(chat_id, "💰 الرجاء إدخال المبلغ الذي تم تحويله:")
    bot.register_next_step_handler(msg, process_syriatel_amount)

    schedule_reminder(chat_id)

def process_syriatel_amount(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)

    try:
        amount = int(message.text)
        user_data[chat_id]['paid_amount'] = amount

        msg = send_clean_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل من تطبيق سيرياتيل كاش:")
        bot.register_next_step_handler(msg, process_syriatel_payment)
    except ValueError:
        send_clean_message(chat_id, "⚠️ الرجاء إدخال رقم صحيح")
        ask_for_syriatel_amount(message)

    schedule_reminder(chat_id)

def process_syriatel_payment(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)

    if not message.photo:
        send_clean_message(chat_id, "⚠️ يرجى إرسال صورة صحيحة")
        msg = send_clean_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل:")
        bot.register_next_step_handler(msg, process_syriatel_payment)
        return

    # حفظ بيانات المستخدم
    save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=user_data[chat_id].get('customer_name', ''),
        phone=user_data[chat_id].get('phone', ''),
        player_id=user_data[chat_id].get('player_id', '')
    )

    # إنشاء الطلب
    order_id = create_order(
        user_id=message.from_user.id,
        game_name="PUBG",
        uc_amount=user_data[chat_id].get('uc_amount', ''),
        player_id=user_data[chat_id].get('player_id', ''),
        price=user_data[chat_id].get('price', 0),
        paid_amount=user_data[chat_id].get('paid_amount', 0),
        payment_method="سيرياتيل كاش"
    )

    # إرسال تأكيد للعميل
    markup = types.InlineKeyboardMarkup(row_width=1)
    telegram_btn = types.InlineKeyboardButton("📲 تواصل عبر تيليجرام", url=f"https://t.me/{SUPPORT_TELEGRAM[1:]}")
    whatsapp_btn = types.InlineKeyboardButton("📱 تواصل عبر واتساب", url=f"https://wa.me/{SUPPORT_WHATSAPP[1:]}")
    dev_btn = types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEV_ACCOUNT[1:]}")
    channel_btn = types.InlineKeyboardButton("📢 قناة المتجر", url=NEWS_CHANNEL)
    markup.add(telegram_btn, whatsapp_btn, dev_btn, channel_btn)

    send_clean_message(chat_id, f"""
✨ شكراً لاستخدامك متجر ريما!

⏳ طلبك {format_order_id(order_id)} قيد المعالجة وسيتم تأكيده خلال 60 دقيقة.

لأي استفسار يمكنك التواصل عبر:
    """, reply_markup=markup)

    # إرسال الطلب إلى قناة الإدارة
    order_msg = f"""
🚨 طلب جديد {format_order_id(order_id)} (سيرياتيل كاش) 🚨

🎮 نوع الطلب: شحن {user_data[chat_id].get('uc_amount', '')} UC
💰 المبلغ المطلوب: {user_data[chat_id].get('price', '')} ل.س
💵 المبلغ المدفوع: {user_data[chat_id].get('paid_amount', '')} ل.س
🆔 ID اللاعب: {user_data[chat_id].get('player_id', '')}
👤 اسم العميل: {user_data[chat_id].get('customer_name', '')}
📱 الهاتف: {user_data[chat_id].get('phone', '')}
💳 طريقة الدفع: سيرياتيل كاش
👤 معرف الطلب: @{message.from_user.username if message.from_user.username else 'غير متوفر'}
    """

    markup_admin = types.InlineKeyboardMarkup()
    btn_complete = types.InlineKeyboardButton("✅ تم إتمام الطلب", callback_data=f"complete_{order_id}")
    btn_reject = types.InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{order_id}")
    markup_admin.add(btn_complete, btn_reject)

    bot.send_photo(
        ADMIN_CHANNEL, 
        message.photo[-1].file_id, 
        caption=order_msg,
        reply_markup=markup_admin
    )

    if chat_id in user_data:
        del user_data[chat_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith(('complete_', 'reject_')))
def handle_order_status(call):
    action, order_id = call.data.split('_')
    order_id = int(order_id)

    if action == 'complete':
        update_order_status(order_id, 'completed')

        conn = sqlite3.connect('rema_store.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM orders WHERE order_id = ?', (order_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id = result[0]

            markup = types.InlineKeyboardMarkup()
            channel_btn = types.InlineKeyboardButton("📢 قناة المتجر", url=NEWS_CHANNEL)
            markup.add(channel_btn)

            bot.send_message(user_id, f"""
🎉 تم إتمام طلبك {format_order_id(order_id)} بنجاح!

شكراً لثقتك بمتجر ريما. نتمنى لك تجربة ممتعة!

✨ لا تنسَ متابعة قناة المتجر للحصول على العروض والخصومات!
            """, reply_markup=markup)

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n✅ تم إتمام الطلب",
            reply_markup=None
        )

    elif action == 'reject':
        update_order_status(order_id, 'rejected')

        conn = sqlite3.connect('rema_store.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM orders WHERE order_id = ?', (order_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            user_id = result[0]
            markup = types.InlineKeyboardMarkup()
            support_btn = types.InlineKeyboardButton("📞 تواصل مع الدعم", url=f"https://t.me/{SUPPORT_TELEGRAM[1:]}")
            markup.add(support_btn)

            bot.send_message(user_id, f"""
⚠️ عذراً، تم رفض طلبك {format_order_id(order_id)}

للاستفسار عن سبب الرفض، يرجى التواصل مع الدعم الفني
            """, reply_markup=markup)

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n❌ تم رفض الطلب",
            reply_markup=None
        )

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_coinex')
def confirm_coinex(call):
    chat_id = call.message.chat.id
    msg = send_clean_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل:")
    bot.register_next_step_handler(msg, process_coinex_payment)

    schedule_reminder(chat_id)

def process_coinex_payment(message):
    chat_id = message.chat.id
    delete_user_message(chat_id, message.message_id)

    if not message.photo:
        send_clean_message(chat_id, "⚠️ يرجى إرسال صورة صحيحة")
        msg = send_clean_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل:")
        bot.register_next_step_handler(msg, process_coinex_payment)
        return

    save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=user_data[chat_id].get('customer_name', ''),
        phone=user_data[chat_id].get('phone', ''),
        player_id=user_data[chat_id].get('player_id', '')
    )

    order_id = create_order(
        user_id=message.from_user.id,
        game_name="PUBG",
        uc_amount=user_data[chat_id].get('uc_amount', ''),
        player_id=user_data[chat_id].get('player_id', ''),
        price=user_data[chat_id].get('price', 0),
        paid_amount=user_data[chat_id].get('price', 0),
        payment_method="Coinex (BSC - BEP20)"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    telegram_btn = types.InlineKeyboardButton("📲 تواصل عبر تيليجرام", url=f"https://t.me/{SUPPORT_TELEGRAM[1:]}")
    whatsapp_btn = types.InlineKeyboardButton("📱 تواصل عبر واتساب", url=f"https://wa.me/{SUPPORT_WHATSAPP[1:]}")
    dev_btn = types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEV_ACCOUNT[1:]}")
    channel_btn = types.InlineKeyboardButton("📢 قناة المتجر", url=NEWS_CHANNEL)
    markup.add(telegram_btn, whatsapp_btn, dev_btn, channel_btn)

    send_clean_message(chat_id, f"""
✨ شكراً لاستخدامك متجر ريما!

⏳ طلبك {format_order_id(order_id)} قيد المعالجة وسيتم تأكيده خلال 60 دقيقة.

لأي استفسار يمكنك التواصل عبر:
    """, reply_markup=markup)

    order_msg = f"""
🚨 طلب جديد {format_order_id(order_id)} (Coinex) 🚨

🎮 نوع الطلب: شحن {user_data[chat_id].get('uc_amount', '')} UC
💰 المبلغ: {user_data[chat_id].get('price', '')} ل.س
🆔 ID اللاعب: {user_data[chat_id].get('player_id', '')}
👤 اسم العميل: {user_data[chat_id].get('customer_name', '')}
📱 الهاتف: {user_data[chat_id].get('phone', '')}
💳 طريقة الدفع: Coinex (BSC - BEP20)
👤 معرف الطلب: @{message.from_user.username if message.from_user.username else 'غير متوفر'}
    """

    markup_admin = types.InlineKeyboardMarkup()
    btn_complete = types.InlineKeyboardButton("✅ تم إتمام الطلب", callback_data=f"complete_{order_id}")
    btn_reject = types.InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{order_id}")
    markup_admin.add(btn_complete, btn_reject)

    bot.send_photo(
        ADMIN_CHANNEL, 
        message.photo[-1].file_id, 
        caption=order_msg,
        reply_markup=markup_admin
    )

    if chat_id in user_data:
        del user_data[chat_id]

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_payment')
def back_to_payment(call):
    show_payment_options(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_pubg')
def back_to_pubg(call):
    pubg_charging(call)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_games')
def back_to_games(call):
    game_charging(call.message)

@bot.message_handler(func=lambda message: message.text == '📞 تواصل')
def contact_us(message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    telegram_btn = types.InlineKeyboardButton("📲 تيليجرام", url=f"https://t.me/{SUPPORT_TELEGRAM[1:]}")
    whatsapp_btn = types.InlineKeyboardButton("📱 واتساب", url=f"https://wa.me/{SUPPORT_WHATSAPP[1:]}")
    dev_btn = types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEV_ACCOUNT[1:]}")
    back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")

    markup.add(telegram_btn, whatsapp_btn, dev_btn, back_btn)

    send_clean_message(message.chat.id, """
📞 تواصل معنا:

يمكنك التواصل مع فريق الدعم عبر:
    """, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📢 قناة الأخبار')
def trust_channel(message):
    markup = types.InlineKeyboardMarkup()

    channel_btn = types.InlineKeyboardButton("📢 انضم للقناة", url=NEWS_CHANNEL)
    back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")

    markup.add(channel_btn, back_btn)

    send_clean_message(message.chat.id, """
📢 قناة الأخبار والعروض:

تابع آخر التحديثات والعروض على قناتنا الرسمية
    """, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main(call):
    send_welcome(call.message)

@bot.message_handler(func=lambda message: message.text == '👤 حسابي')
def my_account(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()

    # جلب معلومات المستخدم
    cursor.execute('''
    SELECT full_name, phone, player_id, registration_date 
    FROM users WHERE user_id = ?
    ''', (user_id,))
    user_info = cursor.fetchone()

    # جلب عدد الطلبات المكتملة
    cursor.execute('''
    SELECT COUNT(*) FROM orders 
    WHERE user_id = ? AND status = 'completed'
    ''', (user_id,))
    completed_orders = cursor.fetchone()[0]

    # جلب آخر طلب
    cursor.execute('''
    SELECT order_date, status FROM orders 
    WHERE user_id = ? ORDER BY order_date DESC LIMIT 1
    ''', (user_id,))
    last_order = cursor.fetchone()

    conn.close()

    damascus_tz = pytz.timezone('Asia/Damascus')
    current_time = datetime.now(damascus_tz).strftime("%Y-%m-%d %H:%M:%S")

    if user_info:
        markup = types.InlineKeyboardMarkup(row_width=1)
        edit_name_btn = types.InlineKeyboardButton("✏️ تعديل الاسم", callback_data="edit_name")
        edit_phone_btn = types.InlineKeyboardButton("✏️ تعديل رقم الهاتف", callback_data="edit_phone")
        edit_id_btn = types.InlineKeyboardButton("✏️ تعديل ID اللاعب", callback_data="edit_player_id")
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
        markup.add(edit_name_btn, edit_phone_btn, edit_id_btn, back_btn)

        account_msg = f"""
👤 معلومات حسابك:

الاسم: {user_info[0]}
رقم الهاتف: {user_info[1]}
ID اللاعب: {user_info[2]}
تاريخ التسجيل: {user_info[3]}

📊 إحصائيات:
عدد الطلبات المكتملة: {completed_orders}
"""
        if last_order:
            account_msg += f"""
آخر طلب:
التاريخ: {last_order[0]}
الحالة: {last_order[1]}
"""

        account_msg += f"\n⏰ الوقت الحالي: {current_time}"

        send_clean_message(chat_id, account_msg, reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("↩️ رجوع", callback_data="back_to_main")
        markup.add(back_btn)
        send_clean_message(chat_id, "⚠️ لم يتم العثور على معلومات الحساب. يرجى إجراء طلب أولاً.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['edit_name', 'edit_phone', 'edit_player_id'])
def handle_edit_profile(call):
    chat_id = call.message.chat.id
    edit_type = call.data.split('_')[1]

    if edit_type == 'name':
        msg = send_clean_message(chat_id, "👤 الرجاء إدخال الاسم الجديد:")
        bot.register_next_step_handler(msg, process_new_name)
    elif edit_type == 'phone':
        msg = send_clean_message(chat_id, "📱 الرجاء إدخال رقم الهاتف الجديد مع الرمز الدولي:")
        bot.register_next_step_handler(msg, process_new_phone)
    elif edit_type == 'player_id':
        msg = send_clean_message(chat_id, "🔢 الرجاء إدخال ID اللاعب الجديد:")
        bot.register_next_step_handler(msg, process_new_player_id)

def process_new_name(message):
    chat_id = message.chat.id
    new_name = message.text
    user_id = message.from_user.id

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET full_name = ? WHERE user_id = ?', (new_name, user_id))
    conn.commit()
    conn.close()

    send_clean_message(chat_id, "✅ تم تحديث الاسم بنجاح!")
    my_account(message)

def process_new_phone(message):
    chat_id = message.chat.id
    new_phone = message.text
    user_id = message.from_user.id

    if not new_phone.startswith('+') or len(new_phone) < 11 or len(new_phone) > 14:
        send_clean_message(chat_id, "⚠️ رقم الهاتف غير صحيح. يجب أن يبدأ بـ + ويتكون من 11-14 رقم.")
        return

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (new_phone, user_id))
    conn.commit()
    conn.close()

    send_clean_message(chat_id, "✅ تم تحديث رقم الهاتف بنجاح!")
    my_account(message)

@bot.message_handler(func=lambda message: message.text == '🔙 رجوع للقائمة الرئيسية')
def back_to_main_menu(message):
    send_welcome(message)

def process_new_player_id(message):
    chat_id = message.chat.id
    new_player_id = message.text
    user_id = message.from_user.id

    if not new_player_id.isdigit() or len(new_player_id) < 9:
        send_clean_message(chat_id, "⚠️ ID اللاعب غير صحيح. يجب أن يتكون من 9 أرقام على الأقل.")
        return

    conn = sqlite3.connect('rema_store.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET player_id = ? WHERE user_id = ?', (new_player_id, user_id))
    conn.commit()
    conn.close()

    send_clean_message(chat_id, "✅ تم تحديث ID اللاعب بنجاح!")
    my_account(message)

@bot.callback_query_handler(func=lambda call: call.data == 'coming_soon')
def coming_soon(call):
    bot.answer_callback_query(call.id, "⏳ هذه الخدمة ستتوفر قريباً!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'start_order')
def start_order(call):
    game_charging(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('complete_order_'))
def complete_order(call):
    order_id = int(call.data.split('_')[2])
    status = get_order_status(order_id)

    if status == 'completed':
        bot.answer_callback_query(call.id, "✅ هذا الطلب تم إتمامه بالفعل", show_alert=True)
    elif status == 'rejected':
        bot.answer_callback_query(call.id, "❌ هذا الطلب تم رفضه", show_alert=True)
    else:
        show_payment_options(call.message)

def schedule_backup():
    """جدولة النسخ الاحتياطي كل 6 ساعات"""
    backup_database()
    Timer(21600, schedule_backup).start()

if __name__ == '__main__':
    print("✅ Bot is running...")
    # بدء جدولة النسخ الاحتياطي
    schedule_backup()
    bot.infinity_polling()