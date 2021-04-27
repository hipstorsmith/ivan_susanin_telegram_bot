import re
import math
import requests

import config
import parameters

# Welcoming messages
WELCOME_MESSAGE = 'Hi! I am Ivan Susanin and I can build step-by-step route from location to location.'
HELP_MESSAGE = 'Commands:\n' \
               '/transport - select default transport mode (default - driving)\n' \
               '/go - start building a route\n' \
               '/help - view this help message\n' \
               '/options - set advanced options (units, avoidance, traffic model, transit mode, transit routing)\n\n' \
               'Navigation:\n' \
               'This bot uses Google Maps Directions to build routes from point to point using given parameters. ' \
               'Set starting location, target location, waypoints (optional) and press start. Each location can be ' \
               'set as text or location\n' \
               'At each step you can look at target step location by choosing image (if it is available on ' \
               'Google Street View) as been seen from current step starting point'

# Options messages
OPTIONS_MESSAGE = 'Options: \n' \
                  '<b>Travel mode</b>: {}\n' \
                  '<b>Units</b>: {}\n' \
                  '<b>Avoid</b>: {}\n' \
                  '<b>Traffic model</b>: {}\n' \
                  '<b>Transit mode</b>: {}\n' \
                  '<b>Transit routing</b>: {}'

CHANGED_PARAMETER_MESSAGE = '<b>{}</b> changed to <b>{}</b>'

TRAVEL_MODE_MESSAGE = 'Choose your travel mode.\n' \
                      '<b>driving</b> (default): standard driving directions using road network\n' \
                      '<b>walking</b>: walking directions via pedestrian paths and sidewalks (if available)\n' \
                      '<b>bicycling</b>: bicycling directions via bicycle paths and preferred streets (if ' \
                      'available)\n' \
                      '<b>transit</b>: directions via public transit routes (if available)\n' \
                      'Current: <b>{}</b>\n'

UNITS_MESSAGE = 'Choose preferable units system\n' \
                'Current: <b>{}</b>'

AVOID_MESSAGE = 'Choose features to avoid\n' \
                '<b>tolls</b>: avoid toll roads/bridges\n' \
                '<b>highways</b>: avoid highways\n' \
                '<b>ferries</b>: avoid ferries\n' \
                '<b>indoor</b>: avoid indoor steps for walking and transit\n' \
                'Current: <b>{}</b>'

TRAFFIC_MODEL_MESSAGE = 'Choose model calculating time in traffic\n' \
                        '<b>best_guess</b>: estimates travel time based on historical data\n' \
                        '<b>pessimistic</b>: estimates travel time based on historical data with bad traffic ' \
                        'conditions\n' \
                        '<b>optimistic</b>: estimates travel time based on historical data with good traffic ' \
                        'conditions\n' \
                        'Current: <b>{}</b>'

TRANSIT_MODE_MESSAGE = 'Choose preferable transit modes (affects only transit routes)\n' \
                       '<b>bus</b>: prefer travel by bus\n' \
                       '<b>subway</b>: prefer travel by subway\n' \
                       '<b>train</b>: prefer travel by train\n' \
                       '<b>tram</b>: prefer travel by tram and light rail\n' \
                       '<b>rail</b>: prefer travel by train, tram, light rail, and subway\n' \
                       'Current: <b>{}</b>'

TRANSIT_ROUTING_MESSAGE = 'Choose transit routing preference (affects only transit routes)\n' \
                          '<b>less_walking</b>: calculate routes with less walking\n' \
                          '<b>fewer_transfers</b>: calculate routes with less transfers\n' \
                          '<b>clear</b>: calculate routes as usual\n' \
                          'Current: <b>{}</b>'

# Set navigation messages
ORIGIN_REQUEST_MESSAGE = 'Set origin point'
DESTINATION_REQUEST_MESSAGE = 'Set destination point'
WAYPOINT_REQUEST_MESSAGE = 'Set additional waypoint or press skip'
CONFIRMATION_MESSAGE = 'Building <b>{}</b> path from <b>{}</b> to <b>{}</b>{}. Continue?'

# Info messages
UNKNOWN_COMMAND_MESSAGE = 'Unknown command. Please try again'
WAITING_MESSAGE = 'Waiting for your commands'
CANCEL_MESSAGE = 'Navigation cancelled'
NOT_FOUND_MESSAGE = 'Path not found'
REACH_MESSAGE = 'You have reached your destination'
FINISH_MESSAGE = 'Navigation finished'
RESTART_MESSAGE = 'Starting path from beginning'


def reply_message(user_data):
    """
    Creates reply message about current navigation step
    :param: user data dictionary
    :return: message
    """

    current_step = user_data['directions'][user_data['step']]

    message = '{}\nDistance: <b>{}</b>\nDuration: <b>{}</b>'.format(process_instructions(current_step),
                                                                    current_step["distance"]["text"],
                                                                    current_step["duration"]["text"])

    # For transit routes walking steps includes a list of sub-steps. This condition processes them
    if 'steps' in current_step:
        step_details = '\n'.join(['{} (<b>{}</b>)'.format(process_instructions(step),
                                                          step["distance"]["text"])
                                  for step in current_step['steps']])
        message += '\n' + step_details

    # Add transit details to message
    if 'transit_details' in current_step:
        transit_details_all = current_step['transit_details']
        transit_details = 'From: <b>{}</b>\nTo: <b>{}</b>\nBus: <b>{}</b>'.\
            format(transit_details_all['departure_stop']['name'],
                   transit_details_all['arrival_stop']['name'],
                   transit_details_all['line']['short_name'])
        message += '\n' + transit_details

    return message


def reply_image(user_data):
    """
    Requests panorama image of target location on current step from Google StreetView API
    :param: user data dictionary
    :return: image (as byte string)
    """

    start_coords = {key: float(value) for key, value in
                    user_data["directions"][user_data["step"]]["start_location"].items()}
    end_coords = {key: float(value) for key, value in
                  user_data["directions"][user_data["step"]]["end_location"].items()}

    # Calculate panorama angle as being seen from starting point to ending point
    bearing = (math.atan2(math.sin(end_coords['lng'] - start_coords['lng']) * math.cos(end_coords['lat']),
                          math.cos(start_coords['lat']) * math.sin(end_coords['lat']) -
                          math.sin(start_coords['lat']) * math.cos(end_coords['lat']) *
                          math.cos(end_coords['lng'] - start_coords['lng'])
                          ) * 180 / math.pi + 360) % 360

    payload_view = {
        'location': '{},{}'.format(end_coords['lat'], end_coords['lng']),
        'size': '600x400',
        'heading': str(bearing),
        'key': config.GMAPS_TOKEN
    }
    street_view = requests.get(config.GMAPS_IMAGE_URL, params=payload_view)
    return street_view.content


def multi_selection_setting_format(user_data, option):
    """
    Getting only selected options from multiselected property
    :param user_data: dictionary of current user data
    :param option: option name
    :return: list of selected options
    """
    return [value for value in user_data[option] if user_data[option][value]]


def reply_current_options(user_data):
    """
    Getting current options message
    :param user_data: dictionary of current user data
    :return: options message
    """
    return OPTIONS_MESSAGE.format(*[', '.join(multi_selection_setting_format(user_data, opt))
                                    if isinstance(user_data[opt], dict) and multi_selection_setting_format(user_data,
                                                                                                           opt)
                                    else user_data[opt] if user_data[opt] and not isinstance(user_data[opt], dict)
                                    else '<i>not specified</i>'
                                    for opt in parameters.PARAMETER_NAMES.keys()])


def process_instructions(current_step):
    """
    Remove unsupported tags from path instructions
    :param current_step: current step instructions
    :return: str, processed instructions
    """
    # Replace unsupported div tag with <b> tag
    div_tag_regexp = '<div.*?>'  # Regular expression to filter out unsupported div tag
    instructions = re.sub(div_tag_regexp, '. <b>', current_step.get("html_instructions", 'Go').replace('/div', '/b'))

    # Replace unsupported span tag with <i> tag
    span_tag_regexp = '<span.*?>'  # Regular expression to filter out unsupported span tag
    instructions = re.sub(span_tag_regexp, '<i>', instructions.replace('/span', '/i'))

    return instructions
