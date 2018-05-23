import logging
import voluptuous as vol
from . import melview_api

from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA, SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE, SUPPORT_OPERATION_MODE, SUPPORT_SWING_MODE, ATTR_TEMPERATURE, STATE_HEAT
    ,STATE_DRY, STATE_COOL, STATE_FAN_ONLY, STATE_AUTO, STATE_OFF, SUPPORT_ON_OFF)
from homeassistant.const import (TEMP_CELSIUS, CONF_USERNAME, CONF_PASSWORD)
from homeassistant.helpers.entity import (Entity)
import homeassistant.helpers.config_validation as cv

log = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""

    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]

    hass.data["DATA_MELVIEW"] = {}

    if discovery_info is not None:
        log.warn("Discovered a Mitsubishi Heatpump")
    else:
        devices = []

        units = config['units']

        for unit in units:
            log.warn("Adding unit: " + str(unit))
            device = MitsubishiHeatpump(unit['name'], unit['unitid'], username, password, hass)
            devices.append(device)

    #token = melview_api.login(username, password)
    #if token:
    #    log.warn("Login Successful")
    #    for room in melview_api.list_rooms(token):
    #        log.warn("Found room " + room.room)
    #        device = MitsubishiHeatpump(room.room, room.unitid)
    #        devices.append(device)
    #    
    #    melview_api.logout()

    #for device in devices:
    #    print(device.name)
    #    device.update()

    if add_devices is not None:
        add_devices(devices)


class MitsubishiHeatpump(ClimateDevice):
    """Representation of a Sensor."""

    def __init__(self, name, unitid, username, password, hass):
        """Initialize the sensor."""
        self._status = None
        self._state = None
        self._name = name
        self._unitid = unitid
        self._username = username
        self._password = password
        self._hass = hass

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self._status:
            if self._status.setmode == melview_api.MODE_HEAT:
                return STATE_HEAT
            elif self._status.setmode == melview_api.MODE_DRY:
                return STATE_DRY
            elif self._status.setmode == melview_api.MODE_COOL:
                return STATE_COOL
            elif self._status.setmode == melview_api.MODE_FAN:
                return STATE_FAN_ONLY
            elif self._status.setmode == melview_api.MODE_AUTO:
                return STATE_AUTO
            else:
                return STATE_OFF
        return None

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return [STATE_HEAT, STATE_DRY, STATE_COOL, STATE_FAN_ONLY, STATE_AUTO]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._status:
            return int(self._status.roomtemp)
        return None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._status:
            return int(self._status.settemp)
        return None

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return None

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return None

    @property
    def is_on(self):
        """Return true if on."""
        if self._status and self._status.power == 1:
            return True
        return False

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        if self._status:
            return self._status.setfan
        return None

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return [1, 2, 3, 4, 5]

    @property
    def current_swing_mode(self):
        """Return the fan setting."""
        if self._status:
            return self._status.airdir
        return None

    @property
    def swing_list(self):
        """Return the list of available swing modes."""
        return [1, 2, 3, 4, 5]

    def set_temperature(self, **kwargs):
        """Set new target temperature."""

        temp = kwargs.get(ATTR_TEMPERATURE)

        token = self.login()
        if token:
            print('send_set_temp: {}'.format(temp))
            melview_api.send_set_temp(token, self._unitid, temp)
            print('send_set_temp finished')

    def set_humidity(self, humidity):
        """Set new target humidity."""
        raise NotImplementedError()

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        token = self.login()
        if token:
            print('send_set_fan: {}'.format(fan_mode))
            melview_api.send_set_fan(token, self._unitid, fan_mode)
            print('send_set_fan finished')

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        mode = None
        if operation_mode == STATE_HEAT:
            mode = melview_api.MODE_HEAT
        elif operation_mode == STATE_DRY:
            mode = melview_api.MODE_DRY
        elif operation_mode == STATE_COOL:
            mode = melview_api.MODE_COOL
        elif operation_mode == STATE_FAN_ONLY or operation_mode == STATE_OFF:
            mode = melview_api.MODE_FAN
        elif operation_mode == STATE_AUTO:
            mode = melview_api.MODE_AUTO

        if mode:
            token = self.login()
            if token:
                print('send_set_mode: {}'.format(operation_mode))
                melview_api.send_set_mode(token, self._unitid, mode)
                print('send_set_mode finished')
        else:
            print('not setting mode as {} is not supported by melview'.format(operation_mode))

    def set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        raise NotImplementedError()
        #token = self.login()
        #if token:
        #    melview_api.

    def turn_on(self):
        """Turn device on."""
        self.set_power(1)

    def turn_off(self):
        """Turn device off."""
        self.set_power(0)

    def set_power(self, power):
        token = self.login()
        if token:
            print('send_set_power: {}'.format(power))
            melview_api.send_set_power(token, self._unitid, power)
            print('finished send_set_power')

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_OPERATION_MODE | SUPPORT_SWING_MODE | SUPPORT_ON_OFF

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """

        token = self.login()
        
        if token:
            self._status = melview_api.get_unit_status(token, self._unitid)
            if self._status:
                print(self._status)

    def login(self):
        token = self._hass.data["DATA_MELVIEW"].get("cookie", None)
        if token is not None:
            log.warn("Found token from cache")
            return token
        token = melview_api.login(self._username, self._password)
        if token is not None:
            self._hass.data["DATA_MELVIEW"]["cookie"] = token
            log.warn("Login successful, got token")
            return token
        log.warn("Login unsuccessful")
        return None
