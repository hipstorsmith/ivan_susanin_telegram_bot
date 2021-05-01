# ivan_susanin_telegram_bot

## Description

This bot uses Google Maps Directions API to create paths between points

Link: https://t.me/ivan_susanin_pathfinder_bot

## Commands
<b>/start</b> - start bot

<b>/transport</b> - set default transport mode

<b>/go</b> - start navigating

<b>/help</b> - view help

<b>/options</b> - set advanced options

## Features
### Navigation
All geographical points can be set up as text or location data. You have to set origin and destination points and optionally you can add some additional waypoints.
At each step you can look at target step location by choosing image (if it is available on Google Street View) as seen from current step starting point

### Set transport type
Google Directions and this bot support four transport types: driving, walking, bicycling, transit. Walking and bicycling paths are not supported for some regions 
with corresponding routes.

### Options
This bot supports most of Google Maps functionality (see below)

## Advanced bot options
### Units
<b>metric</b> (default): meters and kilometers

<b>imperial</b>: feet and miles

### Avoidance
Set up features to avoid. Supports multiple selection

<b>tolls</b>: toll bridges and roads

<b>highways</b>: major highways

<b>ferries</b>: ferries

<b>indoor</b>: indoor steps

### Traffic model
Set up model to calculate time in traffic.

<b>best_guess</b> (default): estimates travel time based on historical data. Estimated time will be close to actual

<b>pessimistic</b>: estimates travel time based on historical data with bad traffic conditions. Estimated time will be longer than actual

<b>optimistic</b>: estimates travel time based on historical data with good traffic conditions. Estimated time will be shorter than actual

### Transit mode
Set up preferable transit modes (affects only transit routes). Supports multiple selection

<b>bus</b>: prefer travel by bus

<b>subway</b>: prefer travel by subway

<b>train</b>: prefer travel by train

<b>tram</b>: prefer travel by tram and light rail

<b>rail</b>: prefer travel by train, tram, light rail, and subway

### Transit routing preference

Set up transit routing preference (affects only transit routes)

<b>clear</b> (default): calculate routes as usual without bias to walking/transfer

<b>less_walking</b>: calculate routes with less walking

<b>fewer_transfers</b>: calculate routes with less transfers

## TBA
Departure and arrival time settings, favourite locations, alternative routes
