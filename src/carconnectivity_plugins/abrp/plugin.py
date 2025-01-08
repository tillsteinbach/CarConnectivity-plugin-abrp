"""Module implements the plugin to connect with ABRP"""
from __future__ import annotations
from typing import TYPE_CHECKING

import threading
import logging
from datetime import timedelta

from requests import Response, Session, codes
from requests.structures import CaseInsensitiveDict
from requests.adapters import HTTPAdapter, Retry
from requests import RequestException

from carconnectivity.errors import ConfigurationError
from carconnectivity.util import config_remove_credentials
from carconnectivity.vehicle import GenericVehicle, ElectricVehicle
from carconnectivity.charging import Charging
from carconnectivity.drive import GenericDrive
from carconnectivity.attributes import BooleanAttribute, DurationAttribute
from carconnectivity_plugins.base.plugin import BasePlugin
from carconnectivity_plugins.abrp._version import __version__

if TYPE_CHECKING:
    from typing import Dict, Optional, Any
    from carconnectivity.carconnectivity import CarConnectivity

LOG: logging.Logger = logging.getLogger("carconnectivity.plugins.abrp")


API_BASE_URL = 'https://api.iternio.com/1/'
CARCONNECTIVITY_IDENTIFIER = '6225724a-65fb-4d4c-9ac5-d7dff2b78c1d'

HEADER = CaseInsensitiveDict({'accept': 'application/json',
                              'user-agent': f'CarConnectivity ({__version__})',
                              'accept-language': 'en-en',
                              'Authorization': f'APIKEY {CARCONNECTIVITY_IDENTIFIER}'})


class Plugin(BasePlugin):
    """
    Plugin class for ABRP connectivity.
    Args:
        car_connectivity (CarConnectivity): An instance of CarConnectivity.
        config (Dict): Configuration dictionary containing connection details.
    """
    def __init__(self, plugin_id: str, car_connectivity: CarConnectivity, config: Dict) -> None:
        BasePlugin.__init__(self, plugin_id=plugin_id, car_connectivity=car_connectivity, config=config)

        self._background_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self.subsequent_errors: int = 0
        self.__session: Session = Session()
        self.__session.headers = HEADER  # pyright: ignore[reportAttributeAccessIssue]
        retries = Retry(total=3, connect=3, read=3, status=3, other=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.__session.mount('https://api.iternio.com', HTTPAdapter(max_retries=retries))

        self.connected: BooleanAttribute = BooleanAttribute(name="connected", parent=self, value=False)
        self.interval: DurationAttribute = DurationAttribute(name="interval", parent=self)

        # Configure logging
        if 'log_level' in config and config['log_level'] is not None:
            config['log_level'] = config['log_level'].upper()
            if config['log_level'] in logging.getLevelNamesMapping():
                LOG.setLevel(config['log_level'])
                self.log_level._set_value(config['log_level'])  # pylint: disable=protected-access
            else:
                raise ConfigurationError(f'Invalid log level: "{config["log_level"]}" not in {list(logging.getLevelNamesMapping().keys())}')
        LOG.info("Loading abrp plugin with config %s", config_remove_credentials(self.config))

        if 'tokens' not in self.config or not self.config['tokens']:
            raise ValueError('No ABRP Tokens specified in config ("tokens" missing)')
        self.tokens: Dict[str, str] = self.config['tokens']

        interval: int = 60
        if 'interval' in self.config:
            interval = self.config['interval']
            if interval < 10:
                raise ValueError('Intervall must be at least 10 seconds')
        self.interval._set_value(timedelta(seconds=interval))  # pylint: disable=protected-access

    def startup(self) -> None:
        LOG.info("Starting ABRP plugin")
        self._background_thread = threading.Thread(target=self._background_loop, daemon=False)
        self._background_thread.start()
        LOG.debug("Starting ABRP plugin done")

    def _background_loop(self) -> None:
        self._stop_event.clear()
        while not self._stop_event.is_set():
            for vin, token in self.tokens.items():
                self._update_and_publish_telemetry(vin, token)
            if self.interval.value is not None:
                self._stop_event.wait(self.interval.value.total_seconds())
            else:
                self._stop_event.wait(60)

    def shutdown(self) -> None:
        self._stop_event.set()
        if self._background_thread is not None:
            self._background_thread.join()
        self.connected._set_value(False)  # pylint: disable=protected-access
        return super().shutdown()

    def _update_and_publish_telemetry(self, vin: str, token: str) -> None:
        """
        Publishes the data of the given vehicle to ABRP.
        Args:
            vehicle (GenericVehicle): The vehicle to publish data for.
        """
        vehicle: Optional[GenericVehicle] = self.car_connectivity.garage.get_vehicle(vin)
        if vehicle is None:
            return
        LOG.debug("updating telemetry for vehicle %s", vehicle.vin)
        telemetry_data: Dict[str, Any] = {}
        if vehicle.drives.enabled:
            electric_drive: Optional[GenericDrive] = None
            if len(vehicle.drives.drives) == 1 and next(iter(vehicle.drives.drives.values())).enabled:
                electric_drive = next(iter(vehicle.drives.drives.values()))
            elif len(vehicle.drives.drives) > 1:
                for drive in vehicle.drives.drives.values():
                    if drive.enabled and drive.type.value == GenericDrive.Type.ELECTRIC:
                        electric_drive = drive
                        break
            if electric_drive is not None:
                if electric_drive.level.enabled and electric_drive.level.value is not None:
                    telemetry_data['soc'] = electric_drive.level.value
                    if electric_drive.level.last_updated is not None:
                        telemetry_data['utc'] = electric_drive.level.last_updated.timestamp()

                if electric_drive.range.enabled and electric_drive.range.value is not None:
                    telemetry_data['est_battery_range'] = electric_drive.range.value

        if vehicle.odometer.enabled and vehicle.odometer.value is not None:
            telemetry_data['odometer'] = vehicle.odometer.value

        if isinstance(vehicle, ElectricVehicle):
            if vehicle.charging is not None and vehicle.charging.enabled:
                if vehicle.charging.state.enabled and vehicle.charging.state.value is not None:
                    if vehicle.charging.state.value in [Charging.ChargingState.CHARGING,
                                                        Charging.ChargingState.CONSERVATION,
                                                        Charging.ChargingState.DISCHARGING]:
                        telemetry_data['is_charging'] = True
                    elif vehicle.charging.state.value in [Charging.ChargingState.OFF,
                                                          Charging.ChargingState.READY_FOR_CHARGING,
                                                          Charging.ChargingState.ERROR]:
                        telemetry_data['is_charging'] = False
                if vehicle.charging.type.enabled and vehicle.charging.type.value is not None:
                    if vehicle.charging.type.value == Charging.ChargingType.DC:
                        telemetry_data['is_dcfc'] = True
                    elif vehicle.charging.type.value == Charging.ChargingType.AC:
                        telemetry_data['is_dcfc'] = False
                if vehicle.charging.power.enabled and vehicle.charging.power.value is not None:
                    power: float = vehicle.charging.power.value * -1
                    if vehicle.charging.state.enabled and vehicle.charging.state.value is not None \
                            and vehicle.charging.state.value == Charging.ChargingState.DISCHARGING:
                        power = power * -1
                    telemetry_data['power'] = power

        if vehicle.position is not None and vehicle.position.enabled:
            if vehicle.position.position_type.enabled and vehicle.position.position_type.value is not None:
                if vehicle.position.position_type.value == vehicle.position.PositionType.PARKING:
                    telemetry_data['is_parked'] = True
                elif vehicle.position.position_type.value == vehicle.position.PositionType.DRIVING:
                    telemetry_data['is_parked'] = False
            if vehicle.position.latitude.enabled and vehicle.position.latitude.value is not None \
                    and vehicle.position.longitude.enabled and vehicle.position.longitude.value is not None:
                telemetry_data['lat'] = vehicle.position.latitude.value
                telemetry_data['lon'] = vehicle.position.longitude.value
        self._publish_telemetry(vin, telemetry_data, token)

    def _publish_telemetry(self, vin: str, telemetry_data: Dict, token: str):  # noqa: C901
        params: Dict[str, str] = {'token': token}
        data: Dict[str, Dict[str, Any]] = {'tlm': telemetry_data}
        try:
            response: Response = self.__session.post(API_BASE_URL + 'tlm/send', params=params, json=data)
            if response.status_code != codes['ok']:
                LOG.error('ABRP send telemetry %s for vehicle vin failed with status code %d', str(data), response.status_code)
            else:
                response_data = response.json()
                if response_data is not None:
                    if 'status' in response_data:
                        if response_data['status'] != 'ok':
                            if self.subsequent_errors > 0:
                                LOG.error('ABRP send telemetry %s for vehicle %s failed', str(data), vin)
                                self.connected._set_value(False)  # pylint: disable=protected-access
                            else:
                                LOG.warning('ABRP send telemetry %s for vehicle %s failed', str(data), vin)
                                self.connected._set_value(False)  # pylint: disable=protected-access
                        else:
                            self.subsequent_errors = 0
                            self.connected._set_value(True)  # pylint: disable=protected-access
                        if 'missing' in response_data:
                            LOG.info('ABRP send telemetry %s for vehicle %s: %s', str(data), vin, response_data["missing"])
                    else:
                        LOG.error('ABRP send telemetry %s for vehicle %s returned unexpected data %s', str(data), vin, str(response_data))
                        self.connected._set_value(False)  # pylint: disable=protected-access
                else:
                    LOG.error('ABRP send telemetry %s for vehicle %s for account returned empty data', str(data), vin)
                    self.connected._set_value(False)  # pylint: disable=protected-access
        except RequestException as e:
            if self.subsequent_errors > 0:
                LOG.error('ABRP send telemetry %s for vehicle %s failed: %s, will try again after next change', str(data), vin, e)
                self.connected._set_value(False)  # pylint: disable=protected-access
            else:
                LOG.warning('ABRP send telemetry %s for vehicle %s failed: %s, will try again after next change', str(data), vin, e)
                self.connected._set_value(False)  # pylint: disable=protected-access

    def get_version(self) -> str:
        return __version__
