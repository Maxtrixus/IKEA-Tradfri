#!/usr/bin/env python3

import sys
from pytradfri import Gateway
from pytradfri.api.libcoap_api import api_factory

import argparse
import configparser
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

iniFile = "{0}/tradfri.ini".format(dir_path)

print (iniFile)

def SaveConfig(args):
    config["Gateway"] = {"ip": args.gateway, "key": args.key}

    with open (iniFile, "w") as configfile:
        config.write(configfile)


def change_listener(device):
  print(device.name + " is now " + str(device.light_control.lights[0].state))

config = configparser.ConfigParser()

config["Gateway"] = {"ip": "UNDEF", "key": "UNDEF"}

if os.path.exists(iniFile):
    config.read(iniFile)

whiteTemps = {"cold":"f5faf6", "normal":"f1e0b5", "warm":"efd275"}

parser = argparse.ArgumentParser()
parser.add_argument("--gateway", "-g")
parser.add_argument("--key")
parser.add_argument("id", nargs='?', default=0)

subparsers = parser.add_subparsers(dest="command")
subparsers.required = True

subparsers.add_parser("on")
subparsers.add_parser("off")
subparsers.add_parser("list")
subparsers.add_parser("test")

parser_level = subparsers.add_parser("level")
parser_level.add_argument("value")

parser_colortemp = subparsers.add_parser("whitetemp")
parser_colortemp.add_argument("value", choices=['cold', 'normal', 'warm'])

args = parser.parse_args()

if args.gateway != None:
    config["Gateway"]["ip"] = args.gateway
    SaveConfig(args)

if args.key != None:
    config["Gateway"]["key"] = args.key
    SaveConfig(args)

if config["Gateway"]["ip"]=="UNDEF":
    print("Gateway not set. Use --gateway to specify")
    quit()

if config["Gateway"]["key"]=="UNDEF":
    print("Key not set. Use --key to specify")
    quit()

api = api_factory(config["Gateway"]["ip"], config["Gateway"]["key"])
gateway = Gateway()

device = api(gateway.get_device(args.id))

if args.command == "on":
    api(device.light_control.set_state(True))

if args.command == "off":
    api(device.light_control.set_state(False))

if args.command == "level":
    api(device.light_control.set_dimmer(int(args.value)))

if args.command == "whitetemp":
    api(device.light_control.set_hex_color(whiteTemps[args.value]))

if args.command == "list":
    devices = api(*api(gateway.get_devices()))

    for aDevice in devices:
        print(aDevice)

if args.command == "test":
    devices = gateway.get_devices()
    lights = [dev for dev in devices if dev.has_light_control]

    lights[0].observe(change_listener)
