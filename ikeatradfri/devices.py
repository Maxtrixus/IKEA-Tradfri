from pytradfri import Gateway, const, error
import json
import colorsys

from .exceptions import UnsupportedDeviceCommand


class ikea_device(object):
    _device = None

    def __init__(self, device, api):
        self._device = device
        self.api = api
        # self.deviceID = device.id
        # self.deviceName = device.name
        # self.modelNumber = device.device_info.model_number
        # self.lastState = device.light_control.lights[0].state
        # self.lastLevel = device.light_control.lights[0].dimmer
        # self.lastWB = device.light_control.lights[0].hex_color

    @property
    def id(self):
        return self._device.id

    @property
    def name(self):
        return self._device.name

    @property
    def model(self):
        return self._device.device_info.model_number

    @property
    def device_type(self):
        if self._device.has_light_control:
            return "Light"
        if self._device.has_socket_control:
            return "Outlet"
        if self._device.device_info.power_source == 3:
            return "Remote"

    @property
    def state(self):
        if self._device.has_light_control:
            return self._device.light_control.lights[0].state
        if self._device.has_socket_control:
            return self._device.socket_control.sockets[0].state

    @property
    def dimmable(self):
        if self._device.has_light_control:
            return self._device.light_control.can_set_dimmer
        else:
            return False

    @property
    def level(self):
        if not self.dimmable:
            return None

        return self._device.light_control.lights[0].dimmer

    @property
    def battery_level(self):
        return self._device.device_info.battery_level

    @property
    def colorspace(self):
        if "CWS" in self.model:
            return "CWS"
        if "WS" in self.model:
            return "WS"
        return "W"
    
    @property
    def has_hex(self):
        if self._device.has_light_control:
            return self._device.light_control.can_set_xy
        else:
            return False

    @property
    def hex(self):
        if self.has_hex:
            return self._device.light_control.lights[0].hex_color
        else:
            return None

    @property
    def description(self):
        descript = {
            "DeviceID": self.id,
            "Name": self.name,
            "State": self.state,
            "Level": self.level,
            "Type": self.device_type,
            "Dimmable": self.dimmable,
            "Colorspace": self.colorspace,
            "Hex": self.hex}

        if self._device.device_info.power_source == 3:
            descript["Battery_Level"] = self.battery_level

        return descript

    @property
    def raw(self):
        return self._device.raw

    # Functions
    async def set_state(self, state):
        if self._device.has_light_control:
            await self.api(self._device.light_control.set_state(state))
        elif self._device.has_socket_control:
            await self.api(self._device.socket_control.set_state(state))
        else:
            raise UnsupportedDeviceCommand
        await self.refresh()

    async def set_level(self, level, transition_time=10):
        if self.dimmable:
            await self.api(self._device.light_control.set_dimmer(
                int(level), transition_time=transition_time))
        else:
            raise UnsupportedDeviceCommand
        await self.refresh()

    async def set_hex(self, hex, transition_time=10):
        if self.has_hex:
            await self.api(self._device.light_control.set_hex_color(
                hex, transition_time=transition_time))
        else:
            raise UnsupportedDeviceCommand

        await self.refresh()

    async def set_hsb(self, hue, saturation, brightness=None,
                      transition_time=10):
        if brightness is not None:
            brightness = int(brightness)

        await self.api(
            self._device.
            light_control.set_hsb(int(hue),
                                  int(saturation), brightness,
                                  transition_time=transition_time))

    async def set_rgb(self, red, green, blue):
        h, s, b = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        print(h, s, b)
        await self.set_hsb(h * const.RANGE_HUE[1],
                           s * const.RANGE_SATURATION[1],
                           b * const.RANGE_BRIGHTNESS[1])

    async def refresh(self):
        gateway = Gateway()
        self.__init__(await self.api(gateway.get_device(
            int(self.id))), self.api)


class ikea_group(object):

    def __init__(self, group, api):
        self._group = group
        self._api = api

    @property
    def description(self):
        return {"DeviceID": self._group.id,
                "Name": self._group.name,
                "Type": "Group",
                "Dimmable": True,
                "State": self._group.state,
                "Level": self._group.dimmer,
                "Colorspace": self.colorspace,
                "Hex": self.hex}

    @property
    def colorspace(self):
        return "W"

    @property
    def hex(self):
        return None

    async def set_state(self, state):
        await self._api(self._group.set_state(state))
        await self.refresh()

    async def set_level(self, level, transition_time=10):
        await self._api(self._group.set_dimmer(level, transition_time))
        await self.refresh()

    async def set_hex(self, hex, transition_time=10):
        for aID in self._group.member_ids:
            dev = await get_device(self._api, Gateway(), aID)
            if dev.device_has_hex:
                await dev.set_hex(hex, transition_time=transition_time)

    async def refresh(self):
        gateway = Gateway()
        self.__init__(await self._api(
            gateway.get_group(int(self._group.id))), self._api)


async def get_device(api, gateway, id):
    try:
        targetDevice = await api(gateway.get_device(int(id)))
        return ikea_device(targetDevice, api)
    except (error.ClientError, json.decoder.JSONDecodeError):
        # Is it a group?
        targetGroup = await api(gateway.get_group(int(id)))
        return ikea_group(targetGroup, api)


async def get_devices(api, gateway):
    devices = await api(await api(gateway.get_devices()))

    lights = []
    outlets = []
    others = []
    groups = []

    for aDevice in sorted(devices, key=lambda device: device.id):
        if aDevice.has_light_control:
            lights.append(ikea_device(aDevice, api))
        elif aDevice.has_socket_control:
            outlets.append(ikea_device(aDevice, api))
        else:
            others.append(ikea_device(aDevice, api))

    all_groups = await api(await api(gateway.get_groups()))
    for group in all_groups:
        groups.append(ikea_group(group, api))
    return (lights, outlets, groups, others)

# async def setDeviceState(api, gateway, id, state):
#     device = await api(gateway.get_device(str(id)))

#     if device.has_light_control:
#         await api(device.light_control.set_state(state))
#     elif device.has_socket_control:
#         await api(device.socket_control.set_state(state))

# async def setDeviceLevel(api, gateway, id, value):
#     device = await api(gateway.get_device(str(id)))
#     await api(device.light_control.set_dimmer(int(value)))
