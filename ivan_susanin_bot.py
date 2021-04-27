# coding=utf-8

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.redis import RedisStorage2
import requests
import logging
import functools
import operator

import config
import messages
import keyboard
import parameters


redis_storage = RedisStorage2(host=config.redis_host,
                              port=config.redis_port,
                              db=0)

bot = Bot(token=config.TG_TOKEN)
dp = Dispatcher(bot, storage=redis_storage)
logging.basicConfig(level=logging.INFO)


class UserStates(StatesGroup):
    """
    List of all bot states
    """
    START, TRAVEL_MODE, OPTIONS, SET_UNITS, SET_AVOIDANCE, SET_TRAFFIC_MODEL, SET_TRANSIT_MODE, SET_TRANSIT_ROUTING, \
        SET_ORIGIN, SET_DESTINATION, SET_WAYPOINTS, CONFIRMATION, BUILDING, FINISH = \
        [State() for _ in range(14)]


def process_location(message: types.Message):
    """
    Extracts location from message
    :param message: incoming message as text or location
    :return: str: message text or geographical coordinates
    """
    try:
        # Processing location as geopoint
        location = '{},{}'.format(message.location.latitude, message.location.longitude)
    except AttributeError:
        # Processing location as text
        location = message.text

    return location


async def process_selection(message: types.Message,
                            state: FSMContext,
                            parameter_name):
    """
    Changing selection parameter (e.g. travel mode) processing
    :param message: incoming message
    :param state: current state context
    :param parameter_name: parameter name to be changed
    """
    content = config.DEFAULT_USER_DATA[parameter_name] if message.text == 'clear' else message.text
    if content != 'back':
        await state.update_data(**{parameter_name: content})
        await message.answer(messages.CHANGED_PARAMETER_MESSAGE.format(parameters.PARAMETER_NAMES[parameter_name],
                                                                       content),
                             parse_mode='HTML')


async def process_selection_back(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    await message.answer(messages.reply_current_options(user_data),
                         reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS['options'],
                                                               one_time_keyboard=False,
                                                               row_len=3),
                         parse_mode='HTML')
    await UserStates.OPTIONS.set()


async def process_multi_selection(message: types.Message,
                                  state: FSMContext,
                                  parameter_name):
    """
    Changing multiple selection (e.g. avoidance) parameter
    :param message: incoming message
    :param state: current state context
    :param parameter_name: parameter name to be changed
    """
    content = message.text
    user_data = await state.get_data()
    if content == 'back':
        await process_selection_back(message, state)
    else:
        user_data[parameter_name][content] = not user_data[parameter_name][content]
        await state.update_data(**{parameter_name: user_data[parameter_name]})

        selected = messages.multi_selection_setting_format(user_data, parameter_name)

        await message.answer(messages.CHANGED_PARAMETER_MESSAGE.format(parameters.PARAMETER_NAMES[parameter_name],
                                                                       ', '.join(selected)),
                             reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS[parameter_name],
                                                                   one_time_keyboard=False,
                                                                   row_len=3),
                             parse_mode='HTML')


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message, state: FSMContext):
    """
    Start command processing: set start state and send welcome message
    """
    await UserStates.START.set()
    await state.update_data(**config.DEFAULT_USER_DATA)
    await message.answer(messages.WELCOME_MESSAGE,
                         reply_markup=keyboard.create_keyboard(keyboard.COMMANDS, one_time_keyboard=False),
                         parse_mode='HTML')


@dp.message_handler(commands=['help'],
                    state='*')
async def process_help_command(message: types.Message):
    """
    Help command processing
    """
    await message.answer(messages.HELP_MESSAGE,
                         parse_mode='HTML')


@dp.message_handler(commands=['transport'],
                    state=UserStates.START)
async def process_transport_command(message: types.Message, state: FSMContext):
    """
    Setting travel mode command processing
    """
    user_data = await state.get_data()
    await message.answer(messages.TRAVEL_MODE_MESSAGE.format(user_data['mode']),
                         reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS['mode']),
                         parse_mode='HTML')
    await UserStates.TRAVEL_MODE.set()


@dp.message_handler(lambda message: message.text in keyboard.OPTION_BUTTONS['mode'],
                    state=UserStates.TRAVEL_MODE)
async def process_transport_selection(message: types.Message, state: FSMContext):
    """
    Setting travel mode input processing
    """
    await process_selection(message=message,
                            state=state,
                            parameter_name='mode')
    await message.answer(messages.WAITING_MESSAGE,
                         reply_markup=keyboard.create_keyboard(keyboard.COMMANDS, one_time_keyboard=False, row_len=2),
                         parse_mode='HTML')
    await UserStates.START.set()


@dp.message_handler(commands=['options'],
                    state=UserStates.START)
async def process_options_command(message: types.Message, state: FSMContext):
    """
    Options command processing
    """
    user_data = await state.get_data()

    await message.answer(messages.reply_current_options(user_data),
                         reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS['options'], row_len=3),
                         parse_mode='HTML')
    await UserStates.OPTIONS.set()


@dp.message_handler(lambda message: message.text in keyboard.OPTION_BUTTONS['options'],
                    state=UserStates.OPTIONS)
async def process_options_selection(message: types.Message, state: FSMContext):
    """
    Options selection processing
    """
    content = message.text

    user_data = await state.get_data()
    
    if content == 'units':
        # Setting units
        await message.answer(messages.UNITS_MESSAGE.format(user_data['units']),
                             reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS['units'], row_len=3),
                             parse_mode='HTML')
        await UserStates.SET_UNITS.set()

    elif content == 'avoid':
        # Setting avoidance
        selected = messages.multi_selection_setting_format(user_data, 'avoid')
        await message.answer(messages.AVOID_MESSAGE.format(', '.join(selected)),
                             reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS['avoid'],
                                                                   one_time_keyboard=False,
                                                                   row_len=3),
                             parse_mode='HTML')
        await UserStates.SET_AVOIDANCE.set()

    elif content == 'traffic model':
        # Setting traffic model
        await message.answer(messages.TRAFFIC_MODEL_MESSAGE.format(user_data['traffic_model']),
                             reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS['traffic_model'], row_len=3),
                             parse_mode='HTML')
        await UserStates.SET_TRAFFIC_MODEL.set()

    elif content == 'transit mode':
        # Setting transit mode
        selected = messages.multi_selection_setting_format(user_data, 'transit_mode')
        await message.answer(messages.TRANSIT_MODE_MESSAGE.format(', '.join(selected)),
                             reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS['transit_mode'],
                                                                   one_time_keyboard=False,
                                                                   row_len=3),
                             parse_mode='HTML')
        await UserStates.SET_TRANSIT_MODE.set()

    elif content == 'transit routing preference':
        # Setting transit routing preference
        await message.answer(messages.TRANSIT_ROUTING_MESSAGE.format(user_data['transit_routing_preference']),
                             reply_markup=keyboard.create_keyboard(keyboard.OPTION_BUTTONS
                                                                   ['transit_routing_preference'], row_len=3),
                             parse_mode='HTML')
        await UserStates.SET_TRANSIT_ROUTING.set()

    elif content == 'back':
        # Return to main menu
        await message.answer(messages.WAITING_MESSAGE,
                             reply_markup=keyboard.create_keyboard(keyboard.COMMANDS, one_time_keyboard=False),
                             parse_mode='HTML')
        await UserStates.START.set()


@dp.message_handler(lambda message: message.text in keyboard.OPTION_BUTTONS['units'],
                    state=UserStates.SET_UNITS)
async def process_units_selection(message: types.Message, state: FSMContext):
    """
    Units selection processing
    """
    await process_selection(message=message,
                            state=state,
                            parameter_name='units')

    await process_selection_back(message, state)


@dp.message_handler(lambda message: message.text in keyboard.OPTION_BUTTONS['traffic_model'],
                    state=UserStates.SET_TRAFFIC_MODEL)
async def process_traffic_model_selection(message: types.Message, state: FSMContext):
    """
    Traffic model selection processing
    """

    await process_selection(message=message,
                            state=state,
                            parameter_name='traffic_model')

    await process_selection_back(message, state)


@dp.message_handler(lambda message: message.text in keyboard.OPTION_BUTTONS['transit_routing_preference'],
                    state=UserStates.SET_TRANSIT_ROUTING)
async def process_transit_routing_selection(message: types.Message, state: FSMContext):
    """
    Transit routing selection processing
    """
    await process_selection(message=message,
                            state=state,
                            parameter_name='transit_routing_preference')

    await process_selection_back(message, state)


@dp.message_handler(lambda message: message.text in keyboard.OPTION_BUTTONS['avoid'],
                    state=UserStates.SET_AVOIDANCE)
async def process_avoid_selection(message: types.Message, state: FSMContext):
    await process_multi_selection(message, state, 'avoid')


@dp.message_handler(lambda message: message.text in keyboard.OPTION_BUTTONS['transit_mode'],
                    state=UserStates.SET_TRANSIT_MODE)
async def process_transit_mode_selection(message: types.Message, state: FSMContext):
    await process_multi_selection(message, state, 'transit_mode')


@dp.message_handler(lambda message: message.text == 'cancel',
                    state='*')
async def process_cancel(message: types.Message, state: FSMContext):
    await state.update_data(**config.DEFAULT_GEO_DATA)
    await message.answer(messages.CANCEL_MESSAGE,
                         reply_markup=keyboard.create_keyboard(keyboard.COMMANDS, one_time_keyboard=False),
                         parse_mode='HTML')
    await UserStates.START.set()


@dp.message_handler(commands=['go'],
                    state=UserStates.START)
async def process_go_command(message: types.Message):
    """
    Go command processing
    """
    await message.answer(messages.ORIGIN_REQUEST_MESSAGE,
                         reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['cancel'],
                                                               one_time_keyboard=False),
                         parse_mode='HTML')
    await UserStates.SET_ORIGIN.set()


@dp.message_handler(state=UserStates.SET_ORIGIN,
                    content_types=[types.ContentType.TEXT, types.ContentType.LOCATION])
async def process_origin(message: types.Message, state: FSMContext):
    """
    Setting origin point processing
    """

    await state.update_data(origin=process_location(message))

    await message.answer(messages.DESTINATION_REQUEST_MESSAGE,
                         reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['cancel'],
                                                               one_time_keyboard=False),
                         parse_mode='HTML')

    await UserStates.SET_DESTINATION.set()


@dp.message_handler(state=UserStates.SET_DESTINATION,
                    content_types=[types.ContentType.TEXT, types.ContentType.LOCATION])
async def process_destination(message: types.Message, state: FSMContext):
    """
    Setting destination point processing
    """

    await state.update_data(destination=process_location(message))

    await message.answer(messages.WAYPOINT_REQUEST_MESSAGE,
                         reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['waypoint'], row_len=1),
                         parse_mode='HTML')
    await UserStates.SET_WAYPOINTS.set()


@dp.message_handler(state=UserStates.SET_WAYPOINTS,
                    content_types=[types.ContentType.TEXT, types.ContentType.LOCATION])
async def process_waypoints(message: types.Message, state: FSMContext):
    content = message.text
    user_data = await state.get_data()

    if content == 'skip':
        # Finishing adding waypoints
        waypoints_str = ' through <b>{}</b>'.format(", ".join(user_data['waypoints'])) if user_data['waypoints'] else ''

        await message.answer(messages.CONFIRMATION_MESSAGE.format(user_data['mode'],
                                                                  user_data['origin'],
                                                                  user_data['destination'],
                                                                  waypoints_str),
                             reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['start']),
                             parse_mode='HTML')

        await UserStates.CONFIRMATION.set()

    else:
        # Adding waypoint
        user_data['waypoints'].append(process_location(message))
        await state.update_data(waypoints=user_data['waypoints'])
        await message.answer(messages.WAYPOINT_REQUEST_MESSAGE,
                             reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['waypoint'], row_len=2),
                             parse_mode='HTML')


@dp.message_handler(lambda message: message.text in keyboard.PATHFINDER_BUTTONS['start'],
                    state=UserStates.CONFIRMATION)
async def process_confirmation(message: types.Message, state: FSMContext):
    """
    Confirmation processing
    """
    user_data = await state.get_data()

    payload_maps = {
        'origin': user_data['origin'],
        'destination': user_data['destination'],
        'mode': user_data['mode'],
        'waypoints': '|'.join(user_data['waypoints']),
        'units': user_data['units'],
        'avoid': '|'.join(messages.multi_selection_setting_format(user_data, 'avoid')),
        'traffic_model': user_data['traffic_model'],
        'transit_mode': '|'.join(messages.multi_selection_setting_format(user_data, 'transit_mode')),
        'departure_time': user_data['departure_time'],
        'transit_routing_preference': user_data['transit_routing_preference'],
        'key': config.GMAPS_TOKEN
    }
    # Getting google maps data
    gmaps_data = requests.get('https://maps.googleapis.com/maps/api/directions/json?', params=payload_maps).json()

    if gmaps_data['status'] != 'OK':
        # Path not found
        await message.answer(messages.NOT_FOUND_MESSAGE,
                             reply_markup=keyboard.create_keyboard(keyboard.COMMANDS, one_time_keyboard=False),
                             parse_mode='HTML')
        await UserStates.START.set()

    else:
        # Path found
        await state.update_data(directions=functools.reduce(operator.iconcat, [leg["steps"] for leg in
                                                                               gmaps_data["routes"][0]["legs"]], []))
        await message.answer(messages.reply_message(await state.get_data()),
                             reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['navigation']),
                             parse_mode='HTML')
        await UserStates.BUILDING.set()


@dp.message_handler(lambda message: message.text in keyboard.PATHFINDER_BUTTONS['navigation'],
                    state=UserStates.BUILDING)
async def process_path(message: types.Message, state: FSMContext):
    """
    Path processing
    """
    content = message.text
    user_data = await state.get_data()
    steps_number = len(user_data['directions'])

    if content == 'target location image':
        # Getting target location image
        await message.answer_photo(messages.reply_image(await state.get_data()),
                                   reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['navigation']),
                                   parse_mode='HTML')
    else:
        if content == 'next':
            # Next step
            await state.update_data(step=user_data['step'] + 1)
        elif content == 'previous' and user_data['step'] > 0:
            # Previous step
            await state.update_data(step=user_data['step'] - 1)

        user_data = await state.get_data()

        if user_data['step'] >= steps_number:
            # Destination reached
            await message.answer(messages.REACH_MESSAGE,
                                 reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['finish']),
                                 parse_mode='HTML')
            await UserStates.FINISH.set()

        else:
            # Still going
            await message.answer(messages.reply_message(await state.get_data()),
                                 reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['navigation']),
                                 parse_mode='HTML')


@dp.message_handler(lambda message: message.text in keyboard.PATHFINDER_BUTTONS['finish'],
                    state=UserStates.FINISH)
async def process_restart(message: types.Message, state: FSMContext):
    """
    Finish navigation processing
    """
    content = message.text

    if content == 'finish':
        # Finish pathfinder and go to main
        await state.update_data(**config.DEFAULT_GEO_DATA)
        await message.answer(messages.FINISH_MESSAGE,
                             reply_markup=keyboard.create_keyboard(keyboard.COMMANDS, one_time_keyboard=False),
                             parse_mode='HTML')
        await UserStates.START.set()

    elif content == 'restart':
        # Start pathfinder from beginning
        await message.answer(messages.RESTART_MESSAGE,
                             parse_mode='HTML')
        await state.update_data(step=0)

        await message.answer(messages.reply_message(await state.get_data()),
                             reply_markup=keyboard.create_keyboard(keyboard.PATHFINDER_BUTTONS['navigation']),
                             parse_mode='HTML')
        await UserStates.BUILDING.set()


@dp.message_handler(state='*')
async def process_unknown(message: types.Message):
    await message.answer(messages.UNKNOWN_COMMAND_MESSAGE,
                         parse_mode='HTML')


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
