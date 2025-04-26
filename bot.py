import telebot
from telebot import types
import random
import pyotp
import time
from datetime import datetime

# إعدادات البوت
TOKEN = '7995774911:AAFi0STyX4w91O8IiZYYtfQRRoMRAMe4sdk'
ADMIN_CHANNEL = '@remabott'
SUPPORT_TELEGRAM = '@T_J3H'
SUPPORT_WHATSAPP = '+447405971105'
DEV_ACCOUNT = '@S_QlQ'
NEWS_CHANNEL = 'https://t.me/REMA_STORE0'

bot = telebot.TeleBot(TOKEN)

# هياكل البيانات
user_data = {}
otp_secrets = {}

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

# ------ نظام إدارة الرسائل الجديد ------
def update_message(chat_id, text, reply_markup=None, photo=None):
    """إرسال/تعديل الرسائل مع منع التراكم"""
    try:
        # حذف الرسائل القديمة أولاً
        if chat_id in user_data:
            for msg_id in user_data[chat_id].get('bot_message_ids', []):
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass

        # إرسال الرسالة الجديدة
        if photo:
            msg = bot.send_photo(chat_id, photo, caption=text, reply_markup=reply_markup)
        else:
            msg = bot.send_message(chat_id, text, reply_markup=reply_markup)

        # تحديث بيانات الرسائل
        user_data.setdefault(chat_id, {'bot_message_ids': [], 'user_message_ids': []})
        user_data[chat_id]['bot_message_ids'].append(msg.message_id)
        user_data[chat_id]['last_bot_message_id'] = msg.message_id
        
        return msg
    except Exception as e:
        print(f"Error in update_message: {e}")
        return None

def delete_user_message(message):
    """حذف رسالة المستخدم وإضافتها للسجل"""
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    chat_id = message.chat.id
    user_data.setdefault(chat_id, {'user_message_ids': []})
    user_data[chat_id]['user_message_ids'].append(message.message_id)

def clean_chat(chat_id):
    """تنظيف كل رسائل المحادثة"""
    if chat_id in user_data:
        # حذف رسائل البوت
        for msg_id in user_data[chat_id].get('bot_message_ids', []):
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass
        
        # حذف رسائل المستخدم
        for msg_id in user_data[chat_id].get('user_message_ids', []):
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass
        
        user_data[chat_id]['bot_message_ids'] = []
        user_data[chat_id]['user_message_ids'] = []

# ------ الأوامر الرئيسية ------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    delete_user_message(message)
    clean_chat(chat_id)
    
    # إعادة تعيين بيانات المستخدم
    user_data[chat_id] = {
        'bot_message_ids': [],
        'user_message_ids': [],
        'data': {}
    }
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton('🎮 شحن ألعاب'),
        types.KeyboardButton('📞 تواصل معنا'),
        types.KeyboardButton('📢 قناة الثقة والأخبار')
    ]
    markup.add(*buttons)
    
    welcome_msg = """
    أهلاً وسهلاً بكم في بوت متجر ريما 🛍️✨
    شريكك الدائم في الفوز والترفيه! 🎮🏆
    
    ✅ شحن سريع وآمن ⚡
    ✅ ثقة وضمان 100% 🔐
    ✅ أفضل الأسعار 💰
    ✅ دعم فني 24/7 🕒
    """
    
    update_message(chat_id, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🎮 شحن ألعاب')
def game_charging(message):
    chat_id = message.chat.id
    delete_user_message(message)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(f"{k.split('_')[0]} UC - {v:,} ل.س", callback_data=k)
        for k, v in UC_PRICES.items()
    ]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("💰 فئة مخصصة", callback_data="custom_amount"))
    
    update_message(chat_id, "اختر فئة الشحن المناسبة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.endswith('_UC') or call.data == 'custom_amount')
def handle_uc_selection(call):
    chat_id = call.message.chat.id
    delete_user_message(call.message)
    
    if call.data == 'custom_amount':
        update_message(chat_id, "⌨️ الرجاء إدخال المبلغ المطلوب (بالليرة السورية):")
        bot.register_next_step_handler(call.message, process_custom_amount)
    else:
        user_data[chat_id]['data'] = {
            'uc_amount': call.data.split('_')[0],
            'price': UC_PRICES[call.data]
        }
        update_message(chat_id, "🔢 الرجاء إدخال ID اللاعب (يجب أن لا يقل عن 9 خانات):")
        bot.register_next_step_handler(call.message, process_player_id)

def process_custom_amount(message):
    chat_id = message.chat.id
    delete_user_message(message)
    
    try:
        price = int(message.text)
        user_data[chat_id]['data'] = {
            'uc_amount': 'مخصص',
            'price': price
        }
        update_message(chat_id, "🔢 الرجاء إدخال ID اللاعب (يجب أن لا يقل عن 9 خانات):")
        bot.register_next_step_handler(message, process_player_id)
    except ValueError:
        error_msg = update_message(chat_id, "⚠️ الرجاء إدخال رقم صحيح")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        game_charging(message)

def process_player_id(message):
    chat_id = message.chat.id
    delete_user_message(message)
    player_id = message.text
    
    if len(player_id) < 9:
        error_msg = update_message(chat_id, "⚠️ ID اللاعب يجب أن لا يقل عن 9 خانات")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        
        update_message(chat_id, "🔢 الرجاء إدخال ID اللاعب (يجب أن لا يقل عن 9 خانات):")
        bot.register_next_step_handler(message, process_player_id)
        return
    
    user_data[chat_id]['data']['player_id'] = player_id
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_player_id"),
        types.InlineKeyboardButton("✏️ تعديل", callback_data="edit_player_id")
    )
    update_message(chat_id, f"🆔 ID اللاعب: {player_id}\nهل هذا صحيح؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['confirm_player_id', 'edit_player_id'])
def handle_player_id_confirmation(call):
    chat_id = call.message.chat.id
    delete_user_message(call.message)
    
    if call.data == 'edit_player_id':
        update_message(chat_id, "🔢 الرجاء إدخال ID اللاعب مرة أخرى:")
        bot.register_next_step_handler(call.message, process_player_id)
        return
    
    update_message(chat_id, "👤 الرجاء إدخال اسمك الكامل:")
    bot.register_next_step_handler(call.message, process_customer_name)

def process_customer_name(message):
    chat_id = message.chat.id
    delete_user_message(message)
    user_data[chat_id]['data']['customer_name'] = message.text
    
    update_message(chat_id, "📱 الرجاء إدخال رقم الهاتف مع الرمز الدولي (مثال: +963987654321):")
    bot.register_next_step_handler(message, process_phone_number)

def process_phone_number(message):
    chat_id = message.chat.id
    delete_user_message(message)
    phone = message.text
    
    if not phone.startswith('+'):
        error_msg = update_message(chat_id, "⚠️ الرجاء إدخال الرقم مع الرمز الدولي (مثال: +963987654321)")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        
        update_message(chat_id, "📱 الرجاء إدخال رقم الهاتف مع الرمز الدولي (مثال: +963987654321):")
        bot.register_next_step_handler(message, process_phone_number)
        return
    
    user_data[chat_id]['data']['phone'] = phone
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد", callback_data="confirm_phone"),
        types.InlineKeyboardButton("✏️ تعديل", callback_data="edit_phone")
    )
    update_message(chat_id, f"📱 رقم الهاتف: {phone}\nهل هذا صحيح؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['confirm_phone', 'edit_phone'])
def handle_phone_confirmation(call):
    chat_id = call.message.chat.id
    delete_user_message(call.message)
    
    if call.data == 'edit_phone':
        update_message(chat_id, "📱 الرجاء إدخال رقم الهاتف مع الرمز الدولي مرة أخرى:")
        bot.register_next_step_handler(call.message, process_phone_number)
        return
    
    send_otp(chat_id)

def send_otp(chat_id):
    secret = pyotp.random_base32()
    otp_secrets[chat_id] = {
        'secret': secret,
        'timestamp': time.time(),
        'attempts': 0
    }
    
    totp = pyotp.TOTP(secret, digits=6, interval=180)
    otp_code = totp.now()
    
    update_message(chat_id, f"🔐 رمز التحقق: {otp_code}\n(هذا للاختبار فقط، في الإنتاج سيتم إرساله لرقمك)")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 إعادة إرسال الرمز", callback_data="resend_otp"))
    
    update_message(chat_id, "⌨️ الرجاء إدخال رمز التحقق (صالح لمدة 3 دقائق):", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, verify_otp)

@bot.callback_query_handler(func=lambda call: call.data == 'resend_otp')
def resend_otp(call):
    chat_id = call.message.chat.id
    delete_user_message(call.message)
    send_otp(chat_id)

def verify_otp(message):
    chat_id = message.chat.id
    delete_user_message(message)
    user_otp = message.text.strip()
    
    otp_data = otp_secrets.get(chat_id)
    if not otp_data:
        error_msg = update_message(chat_id, "⚠️ انتهت صلاحية الجلسة، يرجى البدء من جديد")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        return
    
    otp_data['attempts'] += 1
    otp_secrets[chat_id] = otp_data
    
    if otp_data['attempts'] > 3:
        error_msg = update_message(chat_id, "⚠️ تجاوزت عدد المحاولات المسموح بها، يرجى البدء من جديد")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        del otp_secrets[chat_id]
        return
    
    totp = pyotp.TOTP(otp_data['secret'], digits=6, interval=180)
    
    if totp.verify(user_otp):
        update_message(chat_id, "✅ تم التحقق بنجاح!")
        show_payment_options(message)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 إعادة إرسال الرمز", callback_data="resend_otp"))
        
        remaining_attempts = 3 - otp_data['attempts']
        update_message(chat_id, f"⚠️ رمز التحقق غير صحيح. لديك {remaining_attempts} محاولات متبقية", reply_markup=markup)
        bot.register_next_step_handler(message, verify_otp)

def show_payment_options(message):
    chat_id = message.chat.id
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    options = [
        ("💳 الحوالة البنكية", "bank_transfer"),
        ("₿ Coinex (BSC - BEP20)", "coinex"),
        ("💎 شام كاش", "sham_cash"),
        ("🌐 بوابة دفع إلكترونية", "electronic_payment"),
        ("📱 سيرياتيل كاش", "syriatel_cash"),
        ("🎁 بطاقات الهدايا", "gift_cards"),
        ("💵 Payoneer", "payoneer")
    ]
    
    for text, callback in options:
        markup.add(types.InlineKeyboardButton(text, callback_data=callback))
    
    update_message(chat_id, "💰 اختر طريقة الدفع المناسبة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in [
    'bank_transfer', 'coinex', 'sham_cash', 
    'electronic_payment', 'syriatel_cash', 
    'gift_cards', 'payoneer'
])
def handle_payment_method(call):
    chat_id = call.message.chat.id
    delete_user_message(call.message)
    method = call.data
    
    if method == 'bank_transfer':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_payment"))
        update_message(chat_id, "⚠️ الخدمة قيد التفعيل حالياً", reply_markup=markup)
    
    elif method == 'coinex':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تأكيد التحويل", callback_data="confirm_coinex"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_payment")
        )
        update_message(chat_id, """
        📌 للدفع عبر Coinex (BSC - BEP20):
        
        عنوان المحفظة:
        `0x694142b6a4c9dc077220ee037f1c42bd7b4d68b5`
        
        الرجاء إرسال المبلغ المطلوب ثم الضغط على تأكيد التحويل
        """, reply_markup=markup, parse_mode="Markdown")
    
    elif method in ['sham_cash', 'electronic_payment', 'payoneer']:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_payment"))
        update_message(chat_id, "⏳ ستتوفر هذه الخدمة قريباً", reply_markup=markup)
    
    elif method == 'syriatel_cash':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("💰 إدخال المبلغ", callback_data="enter_syriatel_amount"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_payment")
        )
        update_message(chat_id, """
        💳 للدفع عبر سيرياتيل كاش:
        
        قم بتحويل المبلغ إلى أحد الرموز التالية:
        
        74962454
        78833277
        
        ثم اضغط على زر "إدخال المبلغ"
        """, reply_markup=markup)
    
    elif method == 'gift_cards':
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📲 تواصل عبر تيليجرام", url=f"https://t.me/{SUPPORT_TELEGRAM[1:]}"),
            types.InlineKeyboardButton("📱 تواصل عبر واتساب", url=f"https://wa.me/{SUPPORT_WHATSAPP[1:]}"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_payment")
        )
        update_message(chat_id, """
        🎁 للدفع ببطاقات الهدايا:
        
        يرجى التواصل مع إدارة المتجر لأتمام العملية
        """, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'enter_syriatel_amount')
def ask_for_syriatel_amount(call):
    chat_id = call.message.chat.id
    delete_user_message(call.message)
    update_message(chat_id, "💰 الرجاء إدخال المبلغ الذي تم تحويله:")
    bot.register_next_step_handler(call.message, process_syriatel_amount)

def process_syriatel_amount(message):
    chat_id = message.chat.id
    delete_user_message(message)
    
    try:
        amount = int(message.text)
        user_data[chat_id]['data']['paid_amount'] = amount
        
        update_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل من تطبيق سيرياتيل كاش:")
        bot.register_next_step_handler(message, process_syriatel_payment)
    except ValueError:
        error_msg = update_message(chat_id, "⚠️ الرجاء إدخال رقم صحيح")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        ask_for_syriatel_amount(message)

def process_syriatel_payment(message):
    chat_id = message.chat.id
    delete_user_message(message)
    
    if not message.photo:
        error_msg = update_message(chat_id, "⚠️ يرجى إرسال صورة صحيحة")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        
        update_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل:")
        bot.register_next_step_handler(message, process_syriatel_payment)
        return
    
    # إرسال تأكيد للعميل
    order_data = user_data[chat_id]['data']
    update_message(chat_id, f"""
    🎉 شكراً لثقتك بنا!
    
    تم استلام طلبك بنجاح:
    - المبلغ المدفوع: {order_data.get('paid_amount', '')} ل.س
    - عبر سيرياتيل كاش
    
    سيتم معالجة طلبك خلال وقت قصير ⏳
    
    للاستفسار يمكنك التواصل معنا:
    📲 تيليجرام: @T_J3H
    👨‍💻 حساب المطور: @S_QlQ
    """)
    
    # إرسال الطلب للإدارة
    order_msg = f"""
    🚨 طلب جديد (سيرياتيل كاش) 🚨
    
    🎮 نوع الطلب: شحن {order_data.get('uc_amount', '')} UC
    💰 المبلغ المطلوب: {order_data.get('price', '')} ل.س
    💵 المبلغ المدفوع: {order_data.get('paid_amount', '')} ل.س
    🆔 ID اللاعب: {order_data.get('player_id', '')}
    👤 اسم العميل: {order_data.get('customer_name', '')}
    📱 الهاتف: {order_data.get('phone', '')}
    💳 طريقة الدفع: سيرياتيل كاش
    👤 معرف الطلب: @{message.from_user.username if message.from_user.username else 'غير متوفر'}
    """
    bot.send_photo(ADMIN_CHANNEL, message.photo[-1].file_id, caption=order_msg)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_coinex')
def confirm_coinex(call):
    chat_id = call.message.chat.id
    delete_user_message(call.message)
    update_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل:")
    bot.register_next_step_handler(call.message, process_coinex_payment)

def process_coinex_payment(message):
    chat_id = message.chat.id
    delete_user_message(message)
    
    if not message.photo:
        error_msg = update_message(chat_id, "⚠️ يرجى إرسال صورة صحيحة")
        time.sleep(2)
        try:
            bot.delete_message(chat_id, error_msg.message_id)
        except:
            pass
        
        update_message(chat_id, "📤 الرجاء إرسال صورة إثبات التحويل:")
        bot.register_next_step_handler(message, process_coinex_payment)
        return
    
    # إرسال تأكيد للعميل
    update_message(chat_id, """
    🎉 شكراً لثقتك بنا!
    
    سيتم معالجة طلبك خلال وقت قصير ⏳
    
    للاستفسار يمكنك التواصل معنا:
    📲 تيليجرام: @T_J3H
    👨‍💻 حساب المطور: @S_QlQ
    """)
    
    # إرسال الطلب للإدارة
    order_data = user_data[chat_id]['data']
    order_msg = f"""
    🚨 طلب جديد 🚨
    
    🎮 نوع الطلب: شحن {order_data.get('uc_amount', '')} UC
    💰 المبلغ: {order_data.get('price', '')} ل.س
    🆔 ID اللاعب: {order_data.get('player_id', '')}
    👤 اسم العميل: {order_data.get('customer_name', '')}
    📱 الهاتف: {order_data.get('phone', '')}
    💳 طريقة الدفع: Coinex (BSC - BEP20)
    👤 معرف الطلب: @{message.from_user.username if message.from_user.username else 'غير متوفر'}
    """
    bot.send_photo(ADMIN_CHANNEL, message.photo[-1].file_id, caption=order_msg)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_payment')
def back_to_payment(call):
    delete_user_message(call.message)
    show_payment_options(call.message)

@bot.message_handler(func=lambda m: m.text == '📞 تواصل معنا')
def contact_us(message):
    chat_id = message.chat.id
    delete_user_message(message)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📲 تيليجرام", url=f"https://t.me/{SUPPORT_TELEGRAM[1:]}"),
        types.InlineKeyboardButton("📱 واتساب", url=f"https://wa.me/{SUPPORT_WHATSAPP[1:]}"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
    )
    update_message(chat_id, """
    📞 تواصل معنا:
    
    يمكنك التواصل مع فريق الدعم عبر:
    """, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '📢 قناة الثقة والأخبار')
def trust_channel(message):
    chat_id = message.chat.id
    delete_user_message(message)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📢 انضم للقناة", url=NEWS_CHANNEL),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
    )
    update_message(chat_id, """
    📢 قناة الثقة والأخبار:
    
    تابع آخر التحديثات والعروض على قناتنا الرسمية
    """, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main(call):
    delete_user_message(call.message)
    send_welcome(call.message)

if __name__ == '__main__':
    print("✅ البوت يعمل الآن...")
    bot.in