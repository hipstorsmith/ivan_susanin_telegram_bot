# coding=utf-8

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Commands
COMMANDS = ['/go', '/transport', '/options', '/help']

# Options
OPTION_BUTTONS = {'options': ['units', 'avoid', 'traffic model', 'transit mode', 'transit routing preference', 'back'],
                  'mode': ['driving', 'walking', 'bicycling', 'transit', 'back'],
                  'units': ['metric', 'imperial', 'back'],
                  'traffic_model': ['best_guess', 'optimistic', 'pessimistic', 'back'],
                  'transit_routing_preference': ['less_walking', 'fewer_transfers', 'clear', 'back'],
                  'avoid': ['tolls', 'highways', 'ferries', 'indoor', 'back'],
                  'transit_mode': ['bus', 'subway', 'train', 'tram', 'rail', 'back']}

# Navigation
PATHFINDER_BUTTONS = {'start': ['start', 'cancel'],
                      'navigation': ['next', 'previous', 'cancel', 'target location image'],
                      'finish': ['restart', 'finish'],
                      'waypoint': ['skip', 'cancel'],
                      'cancel': ['cancel']}


def create_keyboard(functions, one_time_keyboard=True, row_len=2):
    """
    Creates reply keyboard with required button names
    :param functions: iterable object. Consists of required button names
    :param one_time_keyboard: boolean. True if keyboard is hidden after single choice
    :param row_len: integer. Length of row of buttons
    :return: keyboard with button names
    """

    buttons = [KeyboardButton(function) for function in functions]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=one_time_keyboard)
    for i in range(0, len(buttons), row_len):
        keyboard = keyboard.row(*buttons[i:i + row_len if row_len + i <= len(buttons) else len(buttons)])

    return keyboard
