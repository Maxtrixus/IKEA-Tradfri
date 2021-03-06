import argparse, sys
from . import __version__


def get_version():
    return __version__


def check_level(value):
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid level value")
    if 0 <= value <= 254:
        return value
    else:
        raise argparse.ArgumentTypeError("Invalid level value")


def getArgs():
    parser = argparse.ArgumentParser()

    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-v", "--verbose", action="count")
    parser.add_argument("--version", action="store_true")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = False

    parser_config = subparsers.add_parser("config")
    parser_config_subparsers = parser_config.add_subparsers(dest="config")

    parser_config_gateway = parser_config_subparsers.add_parser("gateway")
    parser_config_gateway.add_argument("IP")
    parser_config_gateway.add_argument("KEY")

    parser_config_subparsers.add_parser("server-type").add_argument(
        "value", choices=["tcp", "http", "both"]
    )
    parser_config_subparsers.add_parser("server-ip").add_argument("value")
    parser_config_subparsers.add_parser("tcp-port").add_argument("value")
    parser_config_subparsers.add_parser("http-port").add_argument("value")
    parser_config_subparsers.add_parser("transition-time").add_argument("value")

    parser_service = subparsers.add_parser("service").add_subparsers(
        dest="service_command"
    )
    # parser_service.required = True
    parser_service_create = parser_service.add_parser("create")
    parser_service_create.add_argument("--user")
    parser_service_create.add_argument("--group")

    subparsers.add_parser("on").add_argument("ID")
    subparsers.add_parser("off").add_argument("ID")

    name_parser = subparsers.add_parser("name")
    name_parser.add_argument("ID")
    name_parser.add_argument("NAME")

    server_parser = subparsers.add_parser("server")
    server_parser.add_argument("--tcp", action="store_true")
    server_parser.add_argument("--server-type", choices=["tcp", "http", "both"])
    server_parser.add_argument("--host", dest="server_host")
    server_parser.add_argument("--http-port", dest="http_port")
    server_parser.add_argument("--tcp-port", dest="tcp_port")

    parser_list = subparsers.add_parser("list")
    parser_list.add_argument("--expand-groups", action="store_true")
    subparsers.add_parser("test")

    # subparsers.add_parser("pair")

    parser_level = subparsers.add_parser("level")
    parser_level.add_argument("ID")
    parser_level.add_argument("value", type=check_level)
    parser_level.add_argument(
        "--transition-time", nargs="?", default=10, type=int, dest="transition_time"
    )

    parser_colortemp = subparsers.add_parser("wb")
    parser_colortemp.add_argument("ID")
    parser_colortemp.add_argument("value", choices=["cold", "normal", "warm"])
    parser_colortemp.add_argument(
        "--transition-time", nargs="?", default=10, type=int, dest="transition_time"
    )

    parser_hex = subparsers.add_parser("hex")
    parser_hex.add_argument("ID")
    parser_hex.add_argument("value", nargs="?", default="show")
    parser_hex.add_argument("--list", action="store_true")
    parser_hex.add_argument(
        "--transition-time", nargs="?", default=10, type=int, dest="transition_time"
    )

    parser_hsb = subparsers.add_parser("hsb")
    parser_hsb.add_argument("ID")
    parser_hsb.add_argument("hue")
    parser_hsb.add_argument("saturation")
    parser_hsb.add_argument("brightness", nargs="?")

    parser_rgb = subparsers.add_parser("rgb")
    parser_rgb.add_argument("ID")
    parser_rgb.add_argument("red", type=int)
    parser_rgb.add_argument("green", type=int)
    parser_rgb.add_argument("blue", type=int)

    subparsers.add_parser("raw").add_argument("ID")

    subparsers.add_parser("observe")

    parser_color = subparsers.add_parser("color")
    subparser_color = parser_color.add_subparsers(dest="color_command")
    subparser_color.add_parser("list").add_argument("ID")

    parser_set_color = subparser_color.add_parser("set")
    parser_set_color.add_argument("ID")
    parser_set_color.add_argument("color")

    args = parser.parse_args()
    return args, parser
