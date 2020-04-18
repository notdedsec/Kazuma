#!env/scripts/python
import os
import sys
import math
import json
import time
import logging
import hashlib
from PIL import Image
from telegram.ext import Updater, CommandHandler, run_async
from telegram import Bot, TelegramError, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

import strings as s
import database as sql

@run_async
def steal(bot, update, args):
    msg = update.effective_message
    user = update.effective_user
    tempsticker = f"{str(user.id)}.png"
    if not msg.reply_to_message:
        reply(msg, s.STEAL_NOT_REPLY)
        return

    emoji = "🤔"
    defpack = sql.get_default_pack(user.id)
    if defpack: packname = defpack[0][3]
    else: packname = user.first_name[:35] + "\'s Stolen Pack"
    if args:
        if len(args[-1][-1].encode('utf-8')) == 1:
            packname = ' '.join(args)
            if msg.reply_to_message.sticker: 
                emoji = msg.reply_to_message.sticker.emoji
        else:
            emoji = str(args[-1])
            if len(args) > 1:
                packname = ' '.join(args[:-1])

    useridhash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packnamehash = hashlib.sha1(bytearray(packname.lower().encode('utf-8'))).hexdigest()
    packid = f'K{packnamehash[:10]}{useridhash[:10]}_by_{bot.username}'
    replymsg = msg.reply_text(s.STEALING, parse_mode=ParseMode.MARKDOWN)

    try:
        if msg.reply_to_message.sticker: 
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo: 
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document: 
            file_id = msg.reply_to_message.document.file_id
        bot.get_file(file_id).download(tempsticker)
        processimage(tempsticker)
        pngsticker = open(tempsticker, 'rb')
        bot.addStickerToSet(user_id=user.id, name=packid, png_sticker=pngsticker, emojis=emoji)
        replymsg.edit_text(s.STEAL_SUCESSFUL.format(packid), parse_mode=ParseMode.MARKDOWN)
    except OSError as e:
        replymsg.edit_text(s.REPLY_NOT_STICKER_IMAGE)
    except TelegramError as e:
        if e.message == "Stickerset_invalid": 
            newpack(msg, user, tempsticker, emoji, packname, packid, True, replymsg, bot)
        elif e.message == "Invalid sticker emojis": 
            replymsg.edit_text(s.INVALID_EMOJI)
        elif e.message == "Sticker set name invalid":
            replymsg.edit_text(s.INVALID_PACKNAME)
        elif e.message == "Stickers_too_much": 
            replymsg.edit_text(s.PACK_LIMIT_EXCEEDED)
        elif e.message == "Internal Server Error: sticker set not found (500)":
            replymsg.edit_text(s.STEAL_SUCESSFUL.format(packid), parse_mode=ParseMode.MARKDOWN)
        else: 
            replymsg.edit_text(s.STEAL_ERROR)
            print(e.message)
    finally: 
        pngsticker.close()
        os.system('del '+tempsticker)
        reply(msg, None, replymsg)

@run_async
def stealpack(bot, update, args):
    msg = update.effective_message
    user = update.effective_user
    if not args:
        reply(msg, s.STEALPACK_NO_ARGS, parse_mode=ParseMode.MARKDOWN)
        return
    if not msg.reply_to_message:
        reply(msg, s.STEALPACK_NOT_REPLY)
        return
    try: 
        sticker = msg.reply_to_message.sticker
    except: 
        reply(msg, s.REPLY_NOT_STICKER_IMAGE)
        return
    packname = ' '.join(args)
    replymsg = msg.reply_text(s.STEALING, parse_mode=ParseMode.MARKDOWN)
    try: 
        oldpack = bot.getStickerSet(sticker.set_name)
    except TelegramError as e:
        if e.message == "Stickerset_invalid": 
            replymsg.edit_text(s.PACK_DOESNT_EXIST, parse_mode=ParseMode.MARKDOWN)
            reply(msg, None, replymsg)
            return

    useridhash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packnamehash = hashlib.sha1(bytearray(packname.lower().encode('utf-8'))).hexdigest()
    packid = f'K{packnamehash[:10]}{useridhash[:10]}_by_{bot.username}'

    skipped = False
    for sticker in oldpack.stickers:
        try:
            tempsticker = f"{str(sticker.file_id) + str(user.id)}.png"
            bot.get_file(sticker.file_id).download(tempsticker)
            processimage(tempsticker)
            pngsticker = open(tempsticker, 'rb')
            bot.addStickerToSet(user_id=user.id, name=packid, png_sticker=pngsticker, emojis=sticker.emoji)
        except OSError as e:
            replymsg.edit_text(s.REPLY_NOT_STICKER_IMAGE)
        except Exception as e:
            if e.message == "Stickerset_invalid":
                newpack(msg, user, tempsticker, sticker.emoji, packname, packid, False, replymsg, bot)
            else:
                skipped = True
                pass
        finally: 
            pngsticker.close()
            os.system('del '+tempsticker)
        try: 
            replymsg.edit_text(s.STEALING_PACK.format(oldpack.stickers.index(sticker), len(oldpack.stickers)), parse_mode=ParseMode.MARKDOWN)
        except: 
            pass
    if skipped: 
        replymsg.edit_text(s.STEAL_SKIPPED.format(packid), parse_mode=ParseMode.MARKDOWN)
    else: 
        replymsg.edit_text(s.STEAL_SUCESSFUL.format(packid), parse_mode=ParseMode.MARKDOWN)
    reply(msg, None, replymsg)

def newpack(msg, user, tempsticker, emoji, packname, packid, sendreply, replymsg, bot):
    try:
        pngsticker = open(tempsticker, 'rb')
        replymsg.edit_text(s.NEW_PACK, parse_mode=ParseMode.MARKDOWN)
        bot.createNewStickerSet(user.id, packid, packname, png_sticker=pngsticker, emojis=emoji, timeout=99999)
        default = 0 if sql.get_default_pack(user.id) else 1
        sql.new_pack(packid, user.id, default, packname)
        pngsticker.close()
    except TelegramError as e:
        if e.message == "Sticker set name is already occupied": 
            replymsg.edit_text(s.PACK_ALREADY_EXISTS.format(packid), parse_mode=ParseMode.MARKDOWN)
        if e.message == "Internal Server Error: created sticker set not found (500)": # it throws this error but the pack gets created anyway. idk.
            replymsg.edit_text(s.NEW_PACK_CREATED.format(packid), parse_mode=ParseMode.MARKDOWN)
            default = 0 if sql.get_default_pack(user.id) else 1
            sql.new_pack(packid, user.id, default, packname)
        elif e.message == "Sticker set name invalid" and sendreply: 
            replymsg.edit_text(s.INVALID_PACKNAME)
        elif e.message == "Peer_id_invalid": 
            replymsg.edit_text(s.INVALID_PEER_ID, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Start", url=f"t.me/{bot.username}")]]))
        else: 
            replymsg.edit_text(s.NEWPACK_ERROR)
            print(e)
    else:
        if sendreply: 
            replymsg.edit_text(s.NEW_PACK_CREATED.format(packid), parse_mode=ParseMode.MARKDOWN)    
    finally:
        reply(msg, None, replymsg)

def reply(msg, text=None, replymsg=None):
    if text:
        replymsg = msg.reply_markdown(text)
    if msg.chat.type == msg.chat.PRIVATE:
        return
    time.sleep(15)
    try:
        replymsg.delete()
        msg.delete()
    except: pass

def processimage(tempsticker):
    maxsize = (512, 512)
    im = Image.open(tempsticker)
    if (im.width and im.height) < 512:
        size1 = im.width
        size2 = im.height
        if im.width > im.height:
            scale = 512/size1
            size1new = 512
            size2new = size2 * scale
        else:
            scale = 512/size2
            size1new = size1 * scale
            size2new = 512
        size1new = math.floor(size1new)
        size2new = math.floor(size2new)
        sizenew = (size1new, size2new)
        im = im.resize(sizenew)
    else: 
        im.thumbnail(maxsize)
    im.save(tempsticker, "PNG")
    im.close()

def delsticker(bot, update):
    msg = update.effective_message
    if not msg.reply_to_message.sticker:
        reply(msg, s.DELETE_NOT_REPLY)
        return
    if not msg.reply_to_message.sticker.set_name in str(sql.list_packs(update.effective_user.id)):
        reply(msg, s.DELETE_NOT_YOUR_PACK)
        return
    try: 
        bot.delete_sticker_from_set(msg.reply_to_message.sticker.file_id)
    except: 
        replymsg = msg.reply_text(s.DELETE_ERROR)
    else: 
        replymsg = msg.reply_text(s.DELETE_SUCESSFUL)
    reply(msg, None, replymsg)

def delpack(bot, update):
    msg = update.effective_message
    replymsg = msg.reply_text(s.DELETE_PACK)
    reply(msg, None, replymsg)
    
def setposition(bot, update, args):
    msg = update.effective_message
    try: 
        position = int(args[-1])
    except:
        replymsg = msg.reply_markdown(s.SETPOSITION_INVALID_INPUT)
        return
    if not msg.reply_to_message: 
        replymsg = msg.reply_text(s.STEAL_NOT_REPLY)
        return
    if msg.reply_to_message.sticker:
        try: 
            bot.set_sticker_position_in_set(msg.reply_to_message.sticker.file_id, position)
            replymsg = msg.reply_text("Sticker position changed.")
        except: 
            replymsg = msg.reply_markdown(s.SETPOSITION_ERROR)
    else: 
        replymsg = msg.reply_text(s.REPLY_NOT_MY_STICKER)
    reply(msg, None, replymsg)

def checkpacks(bot, packs):
    response = False
    for pack in packs:
        try: bot.getStickerSet(pack[0])
        except TelegramError as e:
            if e.message == "Stickerset_invalid": 
                sql.delete_pack(pack[0])
                response = True
                continue
    return(response)
    # checks if the pack actually exists or has been deleted
    # if a pack is deleted via @stickers, its packid will be deleted forever even if you try to re-create it with the same packname

@run_async
def mypacks(bot, update):
    msg = update.effective_message
    user = update.effective_user
    packs = sql.list_packs(user.id)
    defpack = sql.get_default_pack(user.id)
    packlist = f"{user.first_name}'s steal pack list :\n"
    if checkpacks(bot, packs): 
        packs = sql.list_packs(user.id)
    blank = packlist
    count = 0
    for pack in packs:
        count += 1
        if pack == defpack[0]:
            packlist += f"\n*{count}.* [{pack[3]}](t.me/addstickers/{pack[0]}) ✓"
        else:
            packlist += f"\n*{count}.* [{pack[3]}](t.me/addstickers/{pack[0]})"
    if packlist == blank:
        replymsg = msg.reply_text(s.NO_STOLEN_PACKS)
    else:
        replymsg = msg.reply_markdown(packlist)
    reply(msg, None, replymsg)

def switch(bot, update, args):
    user = update.effective_user
    msg = update.effective_message
    if not args:
        reply(msg, s.SWITCH_INVALID_INPUT)
        return    
    packs = sql.list_packs(user.id)
    if not packs:
        reply(msg, s.NO_STOLEN_PACKS)
        return
    if checkpacks(bot, packs): 
        packs = sql.list_packs(user.id)
    if args[-1].isdigit():
        try: 
            newdefpack = packs[int(args[-1])-1]
            defpack = sql.get_default_pack(user.id)
        except:
            reply(msg, s.SWITCH_PACK_DOESNT_EXIST)
            return
        if defpack == newdefpack:
            reply(msg, s.SWITCH_ALREADY_DEFAULT.format(newdefpack[3]))
        else:
            try:
                sql.remove_default(user.id)
                sql.set_default_by_id(newdefpack[0])
                reply(msg, s.SWITCH_CHANGED_DEFAULT.format(newdefpack[3]))
            except: 
                reply(msg, s.SWITCH_INDEX_ERROR)
    else:
        arg = ' '.join(args)
        if not sql.get_pack_by_name(arg.lower(), user.id):
            reply(msg, s.SWITCH_PACK_DOESNT_EXIST)
            return
        try:
            sql.remove_default(user.id)
            sql.set_default_by_name(arg.lower(), user.id)
            reply(msg, s.SWITCH_CHANGED_DEFAULT.format(arg))
        except: 
            reply(msg, s.SWITCH_PACKNAME_ERROR)

def kstats(bot, update):
    if update.message.from_user.id not in sudoList: 
        reply(update.effective_message, s.NOT_SUDO)
        return
    ulist = []
    db = sql.get_all()
    for i in db:
        if i[1] not in ulist:
            ulist.append(i[1])
    ucount = len(ulist)
    pcount = len(db)
    update.effective_message.reply_text(s.STATS.format(ucount, pcount))

def restart(bot, update):
    if update.message.from_user.id not in sudoList: 
        reply(update.effective_message, s.NOT_SUDO)
        return
    print('\n---------\nRESTARTED\n---------')
    update.effective_message.reply_text(s.RESTART)
    os.execv('launch.bat', sys.argv)

def gitpull(bot, update):
    if update.message.from_user.id not in sudoList: 
        reply(update.effective_message, s.NOT_SUDO)
        return
    print('\n---------\nGITPULLED\n---------')
    reply(update.effective_message, s.GITPULL)
    os.system('git pull')
    os.execv('launch.bat', sys.argv)

def start(bot, update):
    update.effective_message.reply_text(s.START)

def help(bot, update):
    button = [InlineKeyboardButton(text="More Information", url=s.GIST)]
    update.effective_message.reply_text(s.HELP, reply_markup=InlineKeyboardMarkup([button]))

if __name__ == "__main__":
    try:
        with open('config.json', 'r') as f: config = json.load(f)
        sudoList = config['sudoList']
        botToken = config['botToken']
    except:
        config ={"database": "database-name.db", "botToken": "bot-token-here", "sudoList": [12345678, 87654321]}
        with open('config.json', 'w') as f: json.dump(config, f, indent=4)
        print('Edit the config.json and add all necessary information.')

    updater = Updater(botToken)
    os.system("title " + Bot(botToken).first_name)
    logging.basicConfig(format='\n\n%(levelname)s\n%(asctime)s\n%(name)s\n%(message)s', level=logging.ERROR)

    updater.dispatcher.add_handler(CommandHandler('steal', steal, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('stealpack', stealpack, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('delsticker', delsticker))
    updater.dispatcher.add_handler(CommandHandler('delpack', delpack))
    updater.dispatcher.add_handler(CommandHandler('setposition', setposition, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('switch', switch, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('mypacks', mypacks))
    updater.dispatcher.add_handler(CommandHandler('restart', restart))
    updater.dispatcher.add_handler(CommandHandler('gitpull', gitpull))
    updater.dispatcher.add_handler(CommandHandler('kstats', kstats))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help))

    logging.info('Bot Started.')
    updater.start_polling()
    updater.idle()
