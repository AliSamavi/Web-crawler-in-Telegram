from pyromod import listen
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from command import Control

API_ID = ???
API_HASH = "???"
BOT_TOKEN = "???"

app = Client("robot", API_ID, API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start") & filters.private)
async def START(client: Client, message: Message):
    text = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    if Control.check_exists(user_id):
        await message.reply("اگر برای اولین بار است که قصد دارید از این ربات استفاده کنید گزینه **اضافه کردن محصول** را بزنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("جستجوی محصول", "price search")], [InlineKeyboardButton("اضافه کردن محصول", "add product")]]))
    else:
        domain = await client.ask(chat_id, "دامنه خود را وارد کنید.")
        token = await client.ask(chat_id, "توکن وب سرویس خود را وارد کنید.")
        await message.reply(Control.save_domain_token(user_id, domain.text, token.text))


@app.on_callback_query()
async def BTN(client: Client, callback: CallbackQuery):
    data = callback.data
    if data.startswith("home"):
        await client.delete_messages(callback.message.chat.id, callback.message.id)
        await callback.message.reply("اگر برای اولین بار است که قصد دارید از این ربات استفاده کنید گزینه **اضافه کردن محصول** را بزنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("جستجوی محصول", "price search")], [InlineKeyboardButton("اضافه کردن محصول", "add product")]]))
    elif data.startswith("price search"):
        await callback.edit_message_text("اگر قصد دارید که قیمت ها را در سایت خودتان به روز کنم **اعمال ان در سایت** را بزنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("اعمال در سایت", "actions"), InlineKeyboardButton("html", "html")], [InlineKeyboardButton("برگشت", "home")]]))
    elif data.startswith("actions"):
        await callback.edit_message_text("لطفا یکی از سایت های زیر را انتخاب کنید تا قیمت محصولات ان را در سایت شما اعمال کنم.", reply_markup=InlineKeyboardMarkup(Control.btn_maker("a")))
    elif data.startswith("html"):
        await callback.edit_message_text("لطفا یکی از سایت های زیر را انتخاب کنید تا قیمت ان را جمع اوری و در فایل html ذخیره کنم.", reply_markup=InlineKeyboardMarkup(Control.btn_maker("h")))
    elif ".csv" in data:
        boolean = True
        while boolean:
            try:
                boolean = False
                ask = await client.ask(callback.message.chat.id, "مقدار تب ها را بین ۱ تا ۶ وارد کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("برگشت", "home")]]))
                if 1 <= int(ask.text) <= 6:
                    data = data + "@" + ask.text
                    await client.delete_messages(ask.chat.id, ask.id - 1)
                else:
                    ValueError
            except:
                boolean = True
                await client.delete_messages(ask.chat.id, ask.id - 1)

        await callback.edit_message_text("لطفا صبور باشید...\nوقتی به اتمام رسید به شما خبر خواهم داد.")
        Control().btn_action(data)
        if data[0] == "h":
            await client.delete_messages(callback.message.chat.id, callback.message.id)
            await client.send_document(callback.message.chat.id, "./app/cache/output.html", caption="جمع اوری قیمت به اتمام رسید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("برگشت", "home")]]))
        else:
            await callback.edit_message_text("فرایند به  روز رسانی محصولات به اتمام رسید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("برگشت", "home")]]))
    elif data.startswith("add product"):
        await client.delete_messages(callback.message.chat.id, callback.message.id)
        boolean = True
        while boolean:
            try:
                boolean = False
                file = await client.ask(callback.message.chat.id, "لطفا فایلی با پسوند csv برای من ارسال کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("برگشت", "home")]]))
                filename = file.document.file_name
                if ".csv" in filename:
                    await app.download_media(file.document, file_name=f"./data/{filename}")
                else:
                    raise ValueError
            except:
                boolean = True

app.run()
