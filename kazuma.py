import os
import sys
import math
import json
import logging
import hashlib
from PIL import Image
from io import BytesIO
from emoji import demojize, UNICODE_EMOJI
from telegram.utils.helpers import escape_markdown
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
        msg.reply_text(s.STEAL_NOT_REPLY)
        return

    emoji = "🤔"
    emojimode = True

    defpack = sql.get_default_pack(user.id)
    if defpack: packname = defpack[0][3]
    else: packname = user.first_name[:35] + "\'s Stolen Pack"

    if args:
        for x in args[-1]:
            if demojize(x) == x and '\\xf0\\x9f\\x8f\\' not in str(demojize(x).encode('utf-8')):
                emojimode = False
        if emojimode:
            if len(args) > 1: packname = ' '.join(args[:-1])
            emoji = args[-1]
        else: 
            packname = ' '.join(args)

    useridhash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packnamehash = hashlib.sha1(bytearray(packname.encode('utf-8'))).hexdigest()
    packid = f'K{packnamehash[:10]}{useridhash[:10]}_by_{bot.username}'

    try:
        if msg.reply_to_message.sticker: 
            file_id = msg.reply_to_message.sticker.file_id
            
        elif msg.reply_to_message.photo: 
            file_id = msg.reply_to_message.photo[-1].file_id
        
        elif msg.reply_to_message.document: 
            file_id = msg.reply_to_message.document.file_id
        
        bot.get_file(file_id).download(tempsticker)

    except: 
        msg.reply_text(s.REPLY_NOT_STICKER_IMAGE)
        return

    reply = msg.reply_text(s.STEALING, parse_mode=ParseMode.MARKDOWN)

    try:
        im = processimage(tempsticker)
        if not msg.reply_to_message.sticker: im.save(tempsticker, "PNG")
        bot.addStickerToSet(user_id=user.id, name=packid, png_sticker=open(tempsticker, 'rb'), emojis=emoji, timeout=99999)
        reply.edit_text(s.STEAL_SUCESSFUL.format(packid), parse_mode=ParseMode.MARKDOWN)

    except OSError as e:
        reply.edit_text(s.OS_ERROR)

    except TelegramError as e:

        if e.message == "Stickerset_invalid": 
            newpack(msg, user, open(tempsticker, 'rb'), emoji, packname, packid, True, reply, bot)

        elif e.message == "Invalid sticker emojis": 
            reply.edit_text(s.INVALID_EMOJI)

        elif e.message == "Sticker set name invalid":
            reply.edit_text(s.INVALID_PACKNAME)

        elif e.message == "Stickers_too_much": 
            reply.edit_text(s.PACK_LIMIT_EXCEEDED)

        elif e.message == "Internal Server Error: sticker set not found (500)":
            reply.edit_text(s.STEAL_SUCESSFUL.format(packid), parse_mode=ParseMode.MARKDOWN)

        else: 
            reply.edit_text(s.STEAL_ERROR)
            print(e.message)

    finally: im.close()


@run_async
def stealpack(bot, update, args):

    msg = update.effective_message
    user = update.effective_user

    if not msg.reply_to_message.sticker:
        msg.reply_markdown(s.STEALPACK_NOT_REPLY)
        return

    if not args:
        msg.reply_markdown(s.STEALPACK_NO_ARGS)
        return

    packname = ' '.join(args)
    reply = msg.reply_text(s.STEALING, parse_mode=ParseMode.MARKDOWN)

    try: oldpack = bot.getStickerSet(msg.reply_to_message.sticker.set_name)
    except TelegramError as e:
        if e.message == "Stickerset_invalid": 
            reply.edit_text(s.PACK_DOESNT_EXIST, parse_mode=ParseMode.MARKDOWN)
            return

    useridhash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packnamehash = hashlib.sha1(bytearray(packname.encode('utf-8'))).hexdigest()
    packid = f'K{packnamehash[:10]}{useridhash[:10]}_by_{bot.username}'

    count = 0
    skipped = False
    total = len(oldpack.stickers)
    for sticker in oldpack.stickers:

        try:
            tempsticker = f"{str(sticker.file_id) + str(user.id)}.png"
            bot.get_file(sticker.file_id).download(tempsticker)
            im = processimage(tempsticker)
            im.save(tempsticker, "PNG")
            bot.addStickerToSet(user_id=user.id, name=packid, png_sticker=open(tempsticker, 'rb'), emojis=sticker.emoji)

        except (OSError, PermissionError) as e:
            skipped = True
            pass

        except TelegramError as e: 

            if e.message == "Stickers_too_much":
                skipped = True
                pass
            
            elif e.message == "Sticker_png_dimensions": 
                reply.edit_text(s.RESIZE_ERROR)
                return
            
            elif e.message == "Stickerset_invalid": 
                newpack(msg, user, open(tempsticker, 'rb'), sticker.emoji, packname, packid, False, reply, bot)
            
            print(e.message)

        finally: im.close()

        count += 1
        os.remove(tempsticker)
        reply.edit_text(s.STEALING_PACK.format(count, total), parse_mode=ParseMode.MARKDOWN, timeout=9999)

    if skipped: reply.edit_text(s.STEAL_SKIPPED.format(packid), parse_mode=ParseMode.MARKDOWN)
    else: reply.edit_text(s.STEAL_SUCESSFUL.format(packid), parse_mode=ParseMode.MARKDOWN)


def newpack(msg, user, png_sticker, emoji, packname, packid, sendreply, reply, bot):
    
    try:
        reply.edit_text(s.NEW_PACK, parse_mode=ParseMode.MARKDOWN)
        bot.createNewStickerSet(user.id, packid, packname, png_sticker=png_sticker, emojis=emoji, timeout=99999)
        default = 0 if sql.get_default_pack(user.id) else 1
        sql.new_pack(packid, user.id, default, packname)
    
    except TelegramError as e:

        if e.message == "Sticker set name is already occupied": 
            reply.edit_text(s.PACK_ALREADY_EXISTS.format(packid), parse_mode=ParseMode.MARKDOWN)

        # it throws this error but the pack gets created anyway. idk.
        if e.message == "Internal Server Error: created sticker set not found (500)": 
            reply.edit_text(s.NEW_PACK_CREATED.format(packid), parse_mode=ParseMode.MARKDOWN)
            default = 0 if sql.get_default_pack(user.id) else 1
            sql.new_pack(packid, user.id, default, packname)

        elif e.message == "Sticker set name invalid" and sendreply: 
            reply.edit_text(s.INVALID_PACKNAME)

        elif e.message == "Peer_id_invalid": 
            reply.edit_text(s.INVALID_PEER_ID, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Start", url=f"t.me/{bot.username}")]]))

        else: 
            reply.edit_text(s.NEWPACK_ERROR)
            print(e)

    else:
        if sendreply: 
            reply.edit_text(s.NEW_PACK_CREATED.format(packid), parse_mode=ParseMode.MARKDOWN)


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

    else: im.thumbnail(maxsize)
    return(im)


def delsticker(bot, update):

    msg = update.effective_message
    if msg.reply_to_message.sticker:

        try:
            bot.delete_sticker_from_set(msg.reply_to_message.sticker.file_id)
            msg.reply_text(s.DELETE_SUCESSFUL)

        except: msg.reply_text(s.DELETE_ERROR)

    else: msg.reply_text(s.DELETE_NOT_REPLY)


def delpack(bot, update):
    update.effective_message.reply_text(s.DELETE_PACK)


def setposition(bot, update, args):

    msg = update.effective_message
    try: position = int(args[-1])
    except:
        msg.reply_markdown(s.SETPOSITION_INVALID_INPUT)
        return

    if not msg.reply_to_message: 
        msg.reply_text(s.STEAL_NOT_REPLY)
        return

    if msg.reply_to_message.sticker:
        try: 
            bot.set_sticker_position_in_set(msg.reply_to_message.sticker.file_id, position)
            msg.reply_text("Sticker position changed.")

        except: msg.reply_markdown(s.SETPOSITION_ERROR)

    else: msg.reply_text(s.REPLY_NOT_MY_STICKER)


def checkpacks(bot, packs):

    r = False
    for pack in packs:
        try: bot.getStickerSet(pack[0])
        except TelegramError as e:
            if e.message == "Stickerset_invalid": 
                sql.delete_pack(pack[0])
                r = True
                continue
    return(r)

    # code to check if the pack in database actually exists or has been deleted
    # warning: if a packid is deleted via @stickers, it will forever be deleted 
    # from the database even if you attempt to re create one with the same name


def mypacks(bot, update):

    user = update.effective_user
    msg = update.effective_message
    packs = sql.list_packs(user.id)
    defpack = sql.get_default_pack(user.id)

    if checkpacks(bot, packs): 
        packs = sql.list_packs(user.id)

    reply = f"{user.first_name}'s steal pack list :\n"
    blank = reply

    count = 0
    for pack in packs:
        count += 1

        if pack == defpack[0]:
            reply += f"\n*{count}.* [{pack[3]}](t.me/addstickers/{pack[0]}) ✓"
        else:
            reply += f"\n*{count}.* [{pack[3]}](t.me/addstickers/{pack[0]})"

    if reply == blank:
        msg.reply_text(s.NO_STOLEN_PACKS)
    else:
        msg.reply_markdown(reply)


def switch(bot, update, args):
    
    user = update.effective_user
    msg = update.effective_message
    packs = sql.list_packs(user.id)

    if not packs:
        msg.reply_text(s.NO_STOLEN_PACKS)
        return

    if not args:
        msg.reply_markdown(s.SWITCH_INVALID_INPUT)
        return

    if checkpacks(bot, packs): 
        packs = sql.list_packs(user.id)

    try: index = int(args[-1]) - 1
    except: indexmode = False
    else: indexmode = True

    if indexmode:
        try: 
            newdefpack = packs[index]
            defpack = sql.get_default_pack(user.id)

        except:
            msg.reply_text(s.SWITCH_PACK_DOESNT_EXIST)
            return

        if defpack == newdefpack:
            msg.reply_markdown(s.SWITCH_ALREADY_DEFAULT.format(newdefpack[3]))

        else:
            try:
                sql.remove_default(user.id)
                sql.set_default_by_id(newdefpack[0])
                msg.reply_markdown(s.SWITCH_CHANGED_DEFAULT.format(newdefpack[3]))

            except: msg.reply_markdown(s.SWITCH_INDEX_ERROR)

    else:
        arg = ' '.join(args)
        if not sql.get_pack_by_name(arg.lower(), user.id):
            msg.reply_text(s.SWITCH_PACK_DOESNT_EXIST)
            return

        try:
            sql.remove_default(user.id)
            sql.set_default_by_name(arg.lower(), user.id)
            msg.reply_markdown(s.SWITCH_CHANGED_DEFAULT.format(arg))

        except: msg.reply_markdown(s.SWITCH_PACKNAME_ERROR)


def restart(bot, update):

    if update.message.from_user.id not in sudoList: 
        update.effective_message.reply_text(s.NOT_SUDO)
        return

    update.effective_message.reply_text(s.RESTART)
    os.execv('launch.bat', sys.argv)


def gitpull(bot, update):

    if update.message.from_user.id not in sudoList: 
        update.effective_message.reply_text(s.NOT_SUDO)
        return

    update.effective_message.reply_text(s.GITPULL)
    os.system('git pull')
    os.execv('launch.bat', sys.argv)


def start(bot, update):
    update.effective_message.reply_text(s.START)


def help(bot, update):
    update.effective_message.reply_text(s.HELP)


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
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help))

    logging.info('Bot Started.')
    updater.start_polling()
    updater.idle()
