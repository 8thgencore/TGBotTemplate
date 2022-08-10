from datetime import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tgbot.config import Config
from tgbot.models.user_tg import UserTG
from tgbot.states import PingState


async def ping(message: types.Message, state: FSMContext, user: UserTG, config: Config) -> None:
    delta = get_time_delta(message.date)
    aim = 10
    results = [delta]

    args = message.text.split()[1:]
    if args and args[0].isdigit():
        aim = int(args[0])
        if aim < 1:
            await user.send_message("<b>Минимальное количество раз:</b> 1")
            return

    text = get_request_text(config.tg_bot.commands.ping.command, aim, len(results) - 1)
    base_message = await user.send_message(text)

    await PingState.waiting_for_ping.set()
    await state.update_data(aim=aim,
                            results=results,
                            base_message_id=base_message.message_id)


async def get_ping_data(message: types.Message, state: FSMContext, user: UserTG, config: Config) -> None:
    delta = get_time_delta(message.date)

    await message.delete()

    data = await state.get_data()
    aim: int = data.get("aim")
    results: list[float] = data.get("results")
    base_message_id: int = data.get("base_message_id")

    if results and len(results) < aim:
        results.append(delta)
        await state.update_data(results=results)
        text = get_request_text(config.tg_bot.commands.ping.command, aim, len(results) - 1)
        await user.edit_message_text(text, base_message_id)
    else:
        await user.delete_message(base_message_id)
        average_ping = round(sum(results) / len(results) * 1000)
        circle = get_color_circle(average_ping)
        await user.send_message(f"{circle} <b>Средний пинг:</b> <code>{average_ping}</code> ms")
        await state.finish()


def get_request_text(commend: str, aim: int, results_len: int) -> str:
    return f"Отправьте /{commend} еще {aim - results_len} раз"


def get_time_delta(receive_time: datetime) -> float:
    return (datetime.now() - receive_time).total_seconds()


def get_color_circle(average_ping: int) -> str:
    if average_ping <= 1200:
        return "🟢"
    elif average_ping <= 2000:
        return "🟡"
    else:
        return "🔴"


def register_ping_handlers(dp: Dispatcher) -> None:
    config: Config = dp.bot.get("config")
    dp.register_message_handler(ping,
                                command=config.tg_bot.commands.ping,
                                is_admin=True)
    dp.register_message_handler(get_ping_data,
                                command=config.tg_bot.commands.ping,
                                is_admin=True,
                                state=PingState.waiting_for_ping)
