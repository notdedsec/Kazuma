import os
import cv2
import math
import json
import time
import logging
import hashlib
import datetime
from PIL import Image
from pyffmpeg import FFmpeg, FFprobe
from telegram.ext import Updater, CommandHandler
from telegram import Bot, TelegramError, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

import strings as s
import database as sql

def steal(update, context):
    msg = update.effective_message
    user = update.effective_user
    tempsticker = f"{str(user.id)}.png"
    if not msg.reply_to_message:
        reply(msg, s.STEAL_NOT_REPLY)
        return

    emoji = "🤔"
    defpack = sql.get_default_pack(user.id)
    if defpack: packname = defpack[0][3]
    else: packname = user.first_name[:35]+"'s Stolen Pack"
    if context.args:
        if len(context.args[-1][-1].encode('utf-8')) == 1:
            packname = ' '.join(context.args)
            if msg.reply_to_message.sticker: 
                emoji = msg.reply_to_message.sticker.emoji
        else:
            emoji = str(context.args[-1])
            if len(context.args) > 1:
                packname = ' '.join(context.args[:-1])

    useridhash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packnamehash = hashlib.sha1(bytearray(packname.lower().encode('utf-8'))).hexdigest()
    packid = f'K{packnamehash[:10]}{useridhash[:10]}_by_{context.bot.username}'
    replymsg = msg.reply_text(s.STEALING, parse_mode=ParseMode.MARKDOWN)

    try:
        if msg.reply_to_message.sticker: 
            if msg.reply_to_message.sticker.is_animated:
                tempsticker = tempsticker[:-3]+'tgs'
            if msg.reply_to_message.sticker.is_video:
                tempsticker = tempsticker[:-3] + 'webm'
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo: 
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.animation:
            extension = msg.reply_to_message.animation.mime_type.split('/')[1]
            tempsticker = tempsticker[:-3] + extension
            file_id = msg.reply_to_message.animation.file_id
        elif msg.reply_to_message.video:
            extension = msg.reply_to_message.video.mime_type.split('/')[1]
            tempsticker = tempsticker[:-3] + extension
            file_id = msg.reply_to_message.video.file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        context.bot.get_file(file_id).download(tempsticker)
        
        if not tempsticker.endswith(('webm', 'tgs')):
            if not process_file(replymsg, tempsticker):
                return 

        # Renaming tempsticker to the processed webm file
        if tempsticker.endswith('mp4'):
            os.remove(tempsticker)
            tempsticker = tempsticker[:-3] + 'webm'
        
        stickerfile = open(tempsticker, 'rb')

        if tempsticker.endswith('png'):
            context.bot.addStickerToSet(user_id=user.id, name=packid, png_sticker=stickerfile, emojis=emoji)
        elif tempsticker.endswith('webm'):
            context.bot.addStickerToSet(user_id=user.id, name=packid, webm_sticker=stickerfile, emojis=emoji)
        else:
            context.bot.addStickerToSet(user_id=user.id, name=packid, tgs_sticker=stickerfile, emojis=emoji)
        replymsg.edit_text(s.STEAL_SUCESSFUL.format(packid), parse_mode=ParseMode.MARKDOWN)
    except OSError as e:
        replymsg.edit_text(s.REPLY_NOT_STICKER_IMAGE)
    except TelegramError as e:
        if e.message == "Stickerset_invalid": 
            newpack(msg, user, tempsticker, emoji, packname, packid, True, replymsg, context.bot)
        elif e.message == "Sticker_tgs_notgs": 
            replymsg.edit_text(s.UNANIMATED_IN_ANIMATED)
        elif e.message == "Sticker_png_nopng": 
            replymsg.edit_text(s.ANIMATED_IN_UNANIMATED)
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
        try:
            stickerfile.close()
        except UnboundLocalError: # to deal with undefined stickerfile variable
            pass
        os.system('del '+tempsticker)
        reply(msg, None, replymsg)

def stealpack(update, context):
    msg = update.effective_message
    user = update.effective_user
    if not context.args:
        reply(msg, s.STEALPACK_NO_context.args, parse_mode=ParseMode.MARKDOWN)
        return
    if not msg.reply_to_message:
        reply(msg, s.STEALPACK_NOT_REPLY)
        return
    try: 
        sticker = msg.reply_to_message.sticker
    except: 
        reply(msg, s.REPLY_NOT_STICKER_IMAGE)
        return
    packname = ' '.join(context.args)
    replymsg = msg.reply_text(s.STEALING, parse_mode=ParseMode.MARKDOWN)
    try: 
        oldpack = context.bot.getStickerSet(sticker.set_name)
    except TelegramError as e:
        if e.message == "Stickerset_invalid": 
            replymsg.edit_text(s.PACK_DOESNT_EXIST, parse_mode=ParseMode.MARKDOWN)
            reply(msg, None, replymsg)
            return

    useridhash = hashlib.sha1(bytearray(user.id)).hexdigest()
    packnamehash = hashlib.sha1(bytearray(packname.lower().encode('utf-8'))).hexdigest()
    packid = f'K{packnamehash[:10]}{useridhash[:10]}_by_{context.bot.username}'
    
    if msg.reply_to_message.sticker.is_animated:
        ext = 'tgs'
    elif msg.reply_to_message.sticker.is_video:
        ext = 'webm'
    else:
        ext = 'png'

    skipped = False
    for sticker in oldpack.stickers:
        try:
            tempsticker = f"{str(sticker.file_id) + str(user.id)}.{ext}"
            context.bot.get_file(sticker.file_id).download(tempsticker)
            if not tempsticker.endswith(('webm', 'tgs')):
                if not process_file(replymsg, tempsticker):
                    return
            stickerfile = open(tempsticker, 'rb')
            if tempsticker.endswith('png'):
                context.bot.addStickerToSet(user_id=user.id, name=packid, png_sticker=stickerfile, emojis=sticker.emoji)
            elif tempsticker.endswith('webm'):
                context.bot.addStickerToSet(user_id=user.id, name=packid, webm_sticker=stickerfile, emojis=sticker.emoji)
            else:
                context.bot.addStickerToSet(user_id=user.id, name=packid, tgs_sticker=stickerfile, emojis=sticker.emoji)
        except OSError as e:
            replymsg.edit_text(s.REPLY_NOT_STICKER_IMAGE)
        except Exception as e:
            if e.message == "Stickerset_invalid":
                newpack(msg, user, tempsticker, sticker.emoji, packname, packid, False, replymsg, context.bot)
            else:
                skipped = True
                pass
        finally: 
            stickerfile.close()
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
        stickerfile = open(tempsticker, 'rb')
        replymsg.edit_text(s.NEW_PACK, parse_mode=ParseMode.MARKDOWN)
        if tempsticker.endswith('png'):
            bot.createNewStickerSet(user.id, packid, packname, png_sticker=stickerfile, emojis=emoji, timeout=9999)
        elif tempsticker.endswith('webm'):
            bot.createNewStickerSet(user.id, packid, packname, webm_sticker=stickerfile, emojis=emoji, timeout=9999)
        else:
            bot.createNewStickerSet(user.id, packid, packname, tgs_sticker=stickerfile, emojis=emoji, timeout=9999)
        default = 0 if sql.get_default_pack(user.id) else 1
        sql.new_pack(packid, user.id, default, packname)
        stickerfile.close()
    except TelegramError as e:
        if e.message == "Sticker set name is already occupied": 
            replymsg.edit_text(s.PACK_ALREADY_EXISTS.format(packid), parse_mode=ParseMode.MARKDOWN)
        if e.message == "Internal Server Error: created sticker set not found (500)": # throws this error but pack gets created anyway. idk.
            replymsg.edit_text(s.NEW_PACK_CREATED.format(packid), parse_mode=ParseMode.MARKDOWN)
            default = 0 if sql.get_default_pack(user.id) else 1
            sql.new_pack(packid, user.id, default, packname)
        elif e.message == "Sticker set name invalid" and sendreply: 
            replymsg.edit_text(s.INVALID_PACKNAME)
        elif e.message == "Peer_id_invalid": 
            kb = [[InlineKeyboardButton(text="Start", url=f"t.me/{bot.username}")]]
            replymsg.edit_text(s.INVALID_PEER_ID, reply_markup=InlineKeyboardMarkup(kb))
        else: 
            replymsg.edit_text(s.NEWPACK_ERROR)
            print(e)
    else:
        if sendreply: 
            replymsg.edit_text(s.NEW_PACK_CREATED.format(packid), parse_mode=ParseMode.MARKDOWN)    
    finally:
        reply(msg, None, replymsg)

def reply(msg, text=None, replymsg=None, delete=True):
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
    size = (512, 512)
    im = Image.open(tempsticker)
    if (im.width and im.height) < size[0]:
        if im.width > im.height:
            wnew = size[0]
            hnew = size[0]/im.width*im.height
        else:
            wnew = size[0]/im.height*im.width
            hnew = size[0]
        im = im.resize((math.floor(wnew), math.floor(hnew)))
    else: 
        im.thumbnail(size)
    im.save(tempsticker, "PNG")
    im.close()

def process_vid(frame_rate, tempsticker):
    """Change file to webm format with proper dimensions (atleast one side 512px)"""

    ff = FFmpeg()
    vid = cv2.VideoCapture(tempsticker)

    if tempsticker.endswith('webm'):
        webm_tempsticker = tempsticker
    else:
        webm_tempsticker = os.path.splitext(tempsticker)[0] + '.webm'

    h = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
    w = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

    if h >= w:
        h = 512
        w = -1
    else:
        w = 512
        h = -1

    frame_rate_option = "-r 30" if frame_rate > 30 else " "

    ff.options(f"-i {tempsticker} -filter:v scale={w}:{h} -c:a copy -an {frame_rate_option}{webm_tempsticker}")
    
def check_vid(replymsg, tempsticker):
    """Check if the file fulfill the requirements specified in https://core.telegram.org/stickers#video-stickers"""

    fp = FFprobe(tempsticker)
    
    # Convert duration to seconds. 00:01:02.120 -> 62.12s
    dur, milliseconds = fp.duration.split('.')
    x = time.strptime(dur,'%H:%M:%S')
    duration = datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec, milliseconds=int(milliseconds)).total_seconds()

    frame_rate = float(fp.fps)
    size = os.path.getsize(tempsticker)

    # Duration max 3s
    if duration > 3:
        replymsg.edit_text(s.REPLY_VID_DURATION_ERROR.format(duration))
        return False

    # Size max 256KB
    if size > 256000:
        replymsg.edit_text(s.REPLY_VID_SIZE_ERROR.format(size/1000))
        return False
    
    process_vid(frame_rate, tempsticker)
    return True
    

def process_file(replymsg, tempsticker):
    if tempsticker.endswith(('.mp4', '.webm')):
        if not check_vid(replymsg, tempsticker):
            return False
    else:
        processimage(tempsticker)
    return True

def delsticker(update, context):
    msg = update.effective_message
    if not msg.reply_to_message.sticker:
        reply(msg, s.DELETE_NOT_REPLY)
        return
    if not msg.reply_to_message.sticker.set_name in str(sql.list_packs(update.effective_user.id)):
        reply(msg, s.NOT_YOUR_PACK)
        return
    try: 
        context.bot.delete_sticker_from_set(msg.reply_to_message.sticker.file_id)
    except: 
        replymsg = msg.reply_text(s.DELETE_ERROR)
    else: 
        replymsg = msg.reply_text(s.DELETE_SUCESSFUL)
    reply(msg, None, replymsg)

def delpack(update, context):
    msg = update.effective_message
    replymsg = msg.reply_text(s.DELETE_PACK)
    reply(msg, None, replymsg)
    
def setposition(update, context):
    msg = update.effective_message
    if not msg.reply_to_message.sticker.set_name in str(sql.list_packs(update.effective_user.id)):
        reply(msg, s.NOT_YOUR_PACK)
        return
    try: 
        position = int(context.args[-1])
    except:
        replymsg = msg.reply_markdown(s.SETPOSITION_INVALID_INPUT)
        return
    if not msg.reply_to_message: 
        replymsg = msg.reply_text(s.STEAL_NOT_REPLY)
        return
    if msg.reply_to_message.sticker:
        try: 
            context.bot.set_sticker_position_in_set(msg.reply_to_message.sticker.file_id, position)
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

def mypacks(update, context):
    msg = update.effective_message
    user = update.effective_user
    packs = sql.list_packs(user.id)
    defpack = sql.get_default_pack(user.id)
    packlist = f"{user.first_name}'s steal pack list :\n"
    if checkpacks(context.bot, packs): 
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

def switch(update, context):
    user = update.effective_user
    msg = update.effective_message
    if not context.args:
        reply(msg, s.SWITCH_INVALID_INPUT)
        return    
    packs = sql.list_packs(user.id)
    if not packs:
        reply(msg, s.NO_STOLEN_PACKS)
        return
    if checkpacks(context.bot, packs): 
        packs = sql.list_packs(user.id)
    if context.args[-1].isdigit():
        try: 
            newdefpack = packs[int(context.args[-1])-1]
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
        arg = ' '.join(context.args)
        if not sql.get_pack_by_name(arg.lower(), user.id):
            reply(msg, s.SWITCH_PACK_DOESNT_EXIST)
            return
        try:
            sql.remove_default(user.id)
            sql.set_default_by_name(arg.lower(), user.id)
            reply(msg, s.SWITCH_CHANGED_DEFAULT.format(arg))
        except: 
            reply(msg, s.SWITCH_PACKNAME_ERROR)

def kstats(update, context):
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

def start(update, context):
    update.effective_message.reply_text(s.START)

def help(update, context):
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

    updater = Updater(botToken, use_context=True)
    os.system("title "+ Bot(botToken).first_name)
    logging.basicConfig(format='\n\n%(levelname)s\n%(asctime)s\n%(name)s\n%(message)s', level=logging.ERROR)

    updater.dispatcher.add_handler(CommandHandler('steal', steal, pass_args=True, run_async=True))
    updater.dispatcher.add_handler(CommandHandler('stealpack', stealpack, pass_args=True, run_async=True))
    updater.dispatcher.add_handler(CommandHandler('delsticker', delsticker))
    updater.dispatcher.add_handler(CommandHandler('delpack', delpack))
    updater.dispatcher.add_handler(CommandHandler('setposition', setposition, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('switch', switch, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler('mypacks', mypacks, run_async=True))
    updater.dispatcher.add_handler(CommandHandler('kstats', kstats))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help))

    logging.info('Bot Started.')
    updater.start_polling()
    updater.idle()
