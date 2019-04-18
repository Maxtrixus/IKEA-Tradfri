import asyncio
import json
import logging
import signal


from . import config, devices as Devices, exceptions
from .server_commands import return_object

from pytradfri import error as Error


class tcp_server():
    _api = None
    _gateway = None
    _api_factory = None

    _server = None

    _transition_time = 10

    def __init__(self):
        pass

    async def handle_echo(self, reader, writer):
        while True:

            data = await reader.readline()
            if data:

                message = data.decode("utf-8")
                addr = writer.get_extra_info('peername')

                logging.info("Received {} from {}".format(message, addr))

                command = json.loads(message)

                if command["action"] == "initGateway":
                    returnData = await self.init_gateway(command)

                elif command['action'] == "getDevices":
                    returnData = await self.send_devices_list(command)

                elif command["action"] == "setState":
                    returnData = await self.set_state(command)

                elif command["action"] == "setLevel":
                    returnData = await self.set_level(command)

                elif command["action"] == "setHex":
                    returnData = await self.set_hex(command)

                else:
                    returnData = return_object(
                        action=command['action'],
                        status="Error",
                        result="Unknown command")

                logging.info("Sending: {0}".format(returnData.json))
                writer.write(returnData.json)
                await writer.drain()

            else:
                logging.info("Closing connection")
                writer.close()
                return

    async def init_gateway(self, command):
        self._api, self._gateway, self._api_factory = \
            await config.connectToGateway()
        return return_object("initGateway", status="Ok")

    async def send_devices_list(self, command):
        try:
            lights, sockets, groups, others = await Devices.get_devices(
                self._api, self._gateway)

            devices = []

            for aDevice in lights:
                devices.append(aDevice.description)

            for aDevice in sockets:
                devices.append(aDevice.description)

            for aGroup in groups:
                devices.append(aGroup.description)

            for aDevice in others:
                devices.append(aDevice.description)

            return return_object(
                action="getDevices",
                status="Ok",
                result=devices)

        except Error.ServerError:
            return return_object(
                "getDevices",
                status="Error",
                result="Server error")

    async def set_state(self, command):
        device = await Devices.get_device(
            self._api, self._gateway, command["deviceID"])
        if command["state"] == "On":
            await device.set_state(True)
        elif command["state"] == "Off":
            await device.set_state(False)

        await device.refresh()

        devices = []
        devices.append(device.description)
        return return_object(action="setState", status="Ok", result=devices)

    async def set_level(self, command):
        device = await Devices.get_device(
            self._api, self._gateway, command["deviceID"])

        await device.set_level(command["level"],
                               transition_time=self._transition_time)
        await device.refresh()

        devices = []
        devices.append(device.description)
        return return_object(action="setLevel", status="Ok", result=devices)

    async def set_hex(self, command):
        device = await Devices.get_device(self._api, self._gateway,
                                          command["deviceID"])
        await device.set_hex(command["hex"],
                             transition_time=self._transition_time)
        await device.refresh()

        devices = []
        devices.append(device.description)
        return return_object(action="setHex", status="Ok", result=devices)


    def start_tcp_server(self):
        loop = asyncio.get_event_loop()

        loop.create_task(config.getConfig())
        loop.create_task(self.handle_signals(loop))
        coro = asyncio.start_server(
            self.handle_echo, '127.0.0.1', 1234, loop=loop)

        try:
            self._server = loop.run_until_complete(coro)
        except exceptions.ConfigNotFound:
            logging.error("SgiteConfig-file not found")

        # Serve requests until Ctrl+C is pressed
        logging.info('Starting IKEA-Tradfri TCP server on {}'.format(self._server.sockets[0].getsockname()))
        loop.run_forever()
        
        
        # Close the server
        #self._server.close()
        #loop.run_until_complete(self._server.wait_closed())
        #loop.close()

    async def main(self):
        loop = asyncio.get_event_loop()
        
        await config.getConfig()

        self._server = await asyncio.start_server(
            self.handle_echo, '127.0.0.1', 1234)

        addr = self._server.sockets[0].getsockname()
        logging.info('Starting IKEA-Tradfri TCP server on {}'.format(addr))

        # loop.run_until_complete(self._server)
