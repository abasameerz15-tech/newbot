import telebot
from telebot import types
import random
import time

# التوكن الخاص بك
API_TOKEN = '8441369377:AAHfbkLp-Dze0CBd79plIE1wQ3OEzMdLnd8'
bot = telebot.TeleBot(API_TOKEN)

user_data = {}

def check_sub(user_id, channels):
    """التحقق من الاشتراك الإجباري في القنوات"""
    if not channels: return True
    for ch in channels:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ['left', 'kicked']:
                return False
        except:
            # في حال كان اليوزر خطأ أو البوت ليس مشرفاً
            return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    """بداية تشغيل البوت وتصفير البيانات"""
    user_data[message.chat.id] = {
        'step': 'get_content', 
        'channels': [], 
        'participants': [], 
        'winners_count': 0,
        'caption': '',
        'photo': None
    }
    bot.reply_to(message, "👋 هلا عباس! أرسل الآن المحتوى (صورة مع الكليشة) اللي تبي تظهر في الروليت:")

@bot.message_handler(content_types=['text', 'photo'], func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'get_content')
def get_content(message):
    """استلام الصورة والكليشة"""
    uid = message.chat.id
    if message.content_type == 'photo':
        user_data[uid]['photo'] = message.photo[-1].file_id
        user_data[uid]['caption'] = message.caption if message.caption else "لا توجد كليشة"
    else:
        user_data[uid]['caption'] = message.text
        user_data[uid]['photo'] = None
    
    user_data[uid]['step'] = 'get_winners'
    bot.reply_to(message, "✅ تم حفظ المحتوى. الحين كم عدد الفائزين المطلوب؟")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'get_winners')
def get_winners(message):
    """تحديد عدد الفائزين"""
    if message.text.isdigit():
        user_data[message.chat.id]['winners_count'] = int(message.text)
        user_data[message.chat.id]['step'] = 'get_channels'
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تخطي الاشتراك ⏭️", callback_data="skip_ch"))
        bot.reply_to(message, "أرسل يوزر القناة الأولى للاشتراك الإجباري (مثال: @YourChannel):", reply_markup=markup)
    else:
        bot.reply_to(message, "الرجاء إرسال رقم فقط.")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'get_channels')
def get_channels(message):
    """إضافة قنوات الاشتراك الإجباري"""
    channel = message.text if message.text.startswith('@') else '@' + message.text
    user_data[message.chat.id]['channels'].append(channel)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إضافة قناة أخرى ➕", callback_data="add_more"))
    markup.add(types.InlineKeyboardButton("اكتفيت ✅", callback_data="done_ch"))
    bot.reply_to(message, f"تمت إضافة القناة {channel}. هل تريد إضافة غيرها؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_more")
def add_more(call):
    user_data[call.message.chat.id]['step'] = 'get_channels'
    bot.edit_message_text("أرسل يوزر القناة التالية:", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "done_ch")
def done_ch(call):
    user_data[call.message.chat.id]['step'] = 'get_target'
    bot.edit_message_text("تمام. أرسل الآن يوزر القناة اللي تبي أنشر فيها الروليت:", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "skip_ch")
def skip_ch(call):
    user_data[call.message.chat.id]['step'] = 'get_target'
    bot.edit_message_text("تم التخطي. أرسل يوزر القناة المستهدفة للنشر:", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get('step') == 'get_target')
def get_target(message):
    """تحديد قناة النشر والجاهزية"""
    target = message.text if message.text.startswith('@') else '@' + message.text
    user_data[message.chat.id]['target'] = target
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("انشر الروليت الآن 🚀", callback_data="publish"))
    bot.reply_to(message, f"سيتم النشر في القناة: {target}\nهل أنت جاهز؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "publish")
def publish(call):
    """عملية النشر النهائية"""
    uid = call.message.chat.id
    data = user_data[uid]
    
    # تنسيق رسالة الروليت
    sub_info = ""
    if data['channels']:
        sub_info = "\n『 **شروط المشاركة** 』\n"
        for i, ch in enumerate(data['channels'], 1):
            sub_info += f"{i} ⤶ [اضغط للاشتراك]({f'https://t.me/{ch.replace("@","")}'})\n"
        sub_info += "━━━━━━━━━━━━━━\n"

    msg_body = f"{data['caption']}\n{sub_info}🏆 عدد الفائزين: {data['winners_count']}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"المشاركة في السحب [0]", callback_data=f"join_{uid}"))
    markup.add(types.InlineKeyboardButton("إنهـاء الروليت 🛑", callback_data=f"end_{uid}"))
    
    try:
        if data['photo']:
            bot.send_photo(data['target'], data['photo'], caption=msg_body, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(data['target'], msg_body, reply_markup=markup, parse_mode="Markdown", disable_web_page_preview=True)
        bot.answer_callback_query(call.id, "تم النشر بنجاح!")
    except Exception as e:
        bot.answer_callback_query(call.id, "خطأ! تأكد أن البوت مشرف في القناة.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def join(call):
    """زر الانضمام للسحب"""
    owner_id = int(call.data.split('_')[1])
    data = user_data.get(owner_id)
    if not data: return

    if check_sub(call.from_user.id, data['channels']):
        if call.from_user.id not in [p['id'] for p in data['participants']]:
            data['participants'].append({'id': call.from_user.id, 'name': call.from_user.first_name})
            bot.answer_callback_query(call.id, "تم دخولك السحب بنجاح! ✅", show_alert=True)
            
            # تحديث عدد المشاركين على الزر
            count = len(data['participants'])
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"المشاركة في السحب [{count}]", callback_data=f"join_{owner_id}"))
            markup.add(types.InlineKeyboardButton("إنهـاء الروليت 🛑", callback_data=f"end_{owner_id}"))
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
            except: pass
        else:
            bot.answer_callback_query(call.id, "أنت مشارك بالفعل! 😎", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "اشترك في القنوات أولاً لتتمكن من المشاركة! ❌", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("end_"))
def end(call):
    """زر إنهاء الروليت وإعلان الفائزين"""
    owner_id = int(call.data.split('_')[1])
    if call.from_user.id == owner_id:
        data = user_data[owner_id]
        parts = data['participants']
        
        if not parts:
            final_text = "🏁 انتهى الروليت.. للأسف لا يوجد مشاركين!"
        else:
            winners = random.sample(parts, min(len(parts), data['winners_count']))
            winners_text = "\n".join([f"{i+1}- [{w['name']}](tg://user?id={w['id']})" for i, w in enumerate(winners)])
            final_text = f"🎊 **الفائزين في الروليت** 🎊\n\n{winners_text}\n\nألف مبروك وحظ أوفر للبقية!"

        # تحديث الرسالة لإعلان النتائج
        if data['photo']:
            bot.edit_message_caption(final_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(final_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "هذا الزر للمنظم فقط! ⚠️", show_alert=True)

if __name__ == '__main__':
    print("البوت شغال يا عباس..")
    bot.infinity_polling()
