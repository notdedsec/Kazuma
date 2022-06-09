START = "Yes, I'm Kazuma."
RESTART = "Re;Starting Bot in Another Instance from Zero."
GITPULL = "Re;Starting Bot in Another Instance from the Latest Commit."
NOT_SUDO = "This is a developer restricted command.\nYou do not have permissions to run this."

STEALING = "_STEAL!!_"
STEALING_PACK = "Stolen {} out of {} stickers."

NEW_PACK = "_STEAL!!_\nCreating a new steal pack."
NEW_PACK_CREATED = "New steal pack created! [Get it here](t.me/addstickers/{})."

REPLY_NOT_STICKER = "This skill works only when replied to stickers."
REPLY_NOT_MY_STICKER = "This skill only works on stickers of packs that I have stolen."
REPLY_NOT_STICKER_IMAGE = "This skill only works on stickers, images and videos."
REPLY_VID_DURATION_ERROR = "The video is too long ({}s)!\nMax duration is 3 seconds"
REPLY_VID_SIZE_ERROR = "The video is too big ({}KB)!\nMax size is 256KB"

STEAL_ERROR = "I couldn't steal that sticker. Blame Aqua for being so useless."
STEAL_NOT_REPLY = "Reply to an image or a sticker to steal."
STEAL_SUCESSFUL = "Steal sucessful! Here's your [steal pack](t.me/addstickers/{})."
STEAL_SKIPPED = "Steal sucessful but some stickers might've been skipped. Here's your [steal pack](t.me/addstickers/{})."
STEALPACK_NO_ARGS = "Specify a packname to steal stickers into. Like this:\n/stealpack _<pack-name>_"
STEALPACK_NOT_REPLY = "Reply to a sticker and send:\n/stealpack _<pack-name>_"

NEWPACK_ERROR = "I was unable to create that sticker pack. Must be the Demon King's magic."
RESIZE_ERROR = "Unable to resize image to the correct dimensions."
INVALID_EMOJI = "Some of the emojis you specified are not supported."
INVALID_PACKNAME = "The pack name or emojis you specified contain unsupported characters."
INVALID_PEER_ID = "Freshly isekai-d? Click the button to join my guild!"
PACK_DOESNT_EXIST = "What you're trying to steal doesn't exist.\n( ͡° ͜ʖ ͡°)"
PACK_LIMIT_EXCEEDED = "This pack has reached maximum capacity. You can /switch to a different pack or make a new one."
PACK_ALREADY_EXISTS = "I think you're looking for [this pack](t.me/addstickers/{})."
NO_STOLEN_PACKS = "You haven't stolen any packs yet newb."
UNANIMATED_IN_ANIMATED = "You can't add normal stickers in an animated sticker pack. Try stealing it in a normal pack."
ANIMATED_IN_UNANIMATED = "You can't add animated stickers in a normal sticker pack. Try stealing it in an animated pack."
NOT_YOUR_PACK = "Hah! Nice try but you can't mess with others' stickers."

DELETE_PACK = "This is beyond my powers. Use @stickers to delete sticker packs."
DELETE_ERROR = "I couldn't delete that sticker. Looks like those Arch-Devils are at it again."
DELETE_SUCESSFUL = "Poof! The sticker is gone."
DELETE_NOT_REPLY = "This skill only works on stickers of packs that I have stolen."

SETPOSITION_INVALID_INPUT = "That's not how this skill works. Reply to a sticker and try:\n/setposition _<position-number>_"
SETPOSITION_NOT_REPLY = "Reply to the sticker whose position you wanna change."
SETPOSITION_ERROR = "I couldn't change sticker positions. Maybe the undead are interfering with my magic."

SWITCH_INVALID_INPUT =  "Specify the pack you want to be set as default by:\n/switch _<pack-name>_\n/switch _<pack-index-number>_"
SWITCH_PACK_DOESNT_EXIST = "I don't think this pack exists. Use /mypacks to get a list of packs that you've stolen."
SWITCH_ALREADY_DEFAULT = "*{}* is already set as your default pack."
SWITCH_CHANGED_DEFAULT = "*{}* is now set as your default pack."
SWITCH_INDEX_ERROR = "I couldn't switch default packs. Maybe those Axis Cult members are interfering with my magic."
SWITCH_PACKNAME_ERROR = "I couldn't switch default packs. Maybe those Eris Cult members are interfering with my magic."

HELP = """
Hi, I'm Kazuma.
Here's a list of skills that I can use:

/steal - Steal a sticker
/stealpack - Steal the whole pack
/mypacks - List your steal packs
/switch - Change your default pack
/delsticker - Delete sticker from pack
/setposition - Change sticker postiton
"""
STATS = "Stealers: {}\nStolen Packs: {}"
GIST = "https://gist.github.com/notdedsec/2c4aa0359aef072b0e3025d55eaba858"