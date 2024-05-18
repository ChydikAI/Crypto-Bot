from aiogram import Bot
import datetime

from aiogram.enums import ChatMemberStatus


async def check_channel_member(bot: Bot, channel_id: int, user_id: int) -> bool:
    try:
        if channel_id == 0:
            return True
        member = await bot.get_chat_member(channel_id, user_id)
        print(member.status)
        if str(member.status) == 'ChatMemberStatus.LEFT':
            return False
        else:
            return True
    except Exception:
        return False