"""Module implements the plugin to connect with ABRP"""
from __future__ import annotations
from typing import TYPE_CHECKING

import threading
import logging

from requests import Session, codes
from requests.structures import CaseInsensitiveDict
from requests.adapters import HTTPAdapter, Retry
from requests import RequestException

from carconnectivity.observable import Observable
from carconnectivity.errors import ConfigurationError
from carconnectivity.util import config_remove_credentials
from carconnectivity.vehicle import GenericVehicle
from carconnectivity.drive import GenericDrive
from carconnectivity_plugins.base.plugin import BasePlugin
from carconnectivity_plugins.abrp._version import __version__

if TYPE_CHECKING:
    from typing import Dict, Optional
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

        self._background_connect_thread: Optional[threading.Thread] = None
        self._background_publish_topics_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.subscribed_vehicles: Dict[str, GenericVehicle] = {}

        self.subsequent_errors: int = 0
        self.__session: Session = Session()
        self.__session.headers = HEADER
        retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.__session.mount('https://api.iternio.com', HTTPAdapter(max_retries=retries))

        self.telemetry_data: Dict[str, Dict] = {}

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

    def startup(self) -> None:
        LOG.info("Starting ABRP plugin")
        self.__check_subscribe_vehicles()
        flag: Observable.ObserverEvent = Observable.ObserverEvent.ENABLED | Observable.ObserverEvent.DISABLED
        self.car_connectivity.garage.add_observer(self.__on_garage_enabled, flag=flag, priority=Observable.ObserverPriority.USER_LOW,
                                                  on_transaction_end=True)
        LOG.debug("Starting ABRP plugin done")

    def __check_subscribe_vehicles(self) -> None:
        for vin in self.tokens.keys():
            vehicle: GenericVehicle | None = self.car_connectivity.garage.get_vehicle(vin)
            if vehicle is not None and vehicle not in self.subscribed_vehicles.values():
                vehicle.add_observer(self.__on_vehicle_update, flag=Observable.ObserverEvent.UPDATED, priority=Observable.ObserverPriority.USER_LOW,
                                     on_transaction_end=True)
                self.subscribed_vehicles[vin] = vehicle
                LOG.debug("Subscribed to vehicle %s", vin)
                self._update_telemetry(vehicle)

    def __on_garage_enabled(self, element, flags) -> None:
        if isinstance(element, GenericVehicle):
            vin: Optional[str] = element.vin.value
            if vin is None:
                raise ValueError("Vehicle has no VIN")
            if flags & Observable.ObserverEvent.ENABLED:
                self.__check_subscribe_vehicles()
            elif flags & Observable.ObserverEvent.DISABLED:
                element.remove_observer(self.__on_vehicle_update)
                self.subscribed_vehicles.pop(vin)
                LOG.debug("Unsubscribed from vehicle %s", vin)

    def __on_vehicle_update(self, element, flags) -> None:
        if flags & Observable.ObserverEvent.UPDATED:
            LOG.debug("Vehicle %s updated", element)
            self._update_telemetry(element)
        if flags & Observable.ObserverEvent.DISABLED:
            LOG.debug("Vehicle %s disabled", element)
            element.remove_observer(self.__on_vehicle_update)
            self.subscribed_vehicles.pop(element.vin)

    def _update_telemetry(self, vehicle: GenericVehicle) -> None:
        """
        Publishes the data of the given vehicle to ABRP.
        Args:
            vehicle (GenericVehicle): The vehicle to publish data for.
        """
        vin = vehicle.vin.value
        if vin is None:
            raise ValueError("Vehicle has no VIN")
        LOG.debug("updating telemetry for vehicle %s", vehicle.vin)
        telemetry_data = {}
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
        self.telemetry_data[vin] = telemetry_data
        self._publish_telemetry(vehicle)

    def _publish_telemetry(self, vehicle: GenericVehicle):  # noqa: C901
        vin = vehicle.vin.value
        if vin is None:
            raise ValueError("Vehicle has no VIN")
        if vin in self.tokens and vin in self.telemetry_data:
            token = self.tokens[vin]
            params = {'token': token}
            data = {'tlm': self.telemetry_data[vin]}
            try:
                response = self.__session.post(API_BASE_URL + 'tlm/send', params=params, json=data)
                if response.status_code != codes['ok']:
                    LOG.error('ABRP send telemetry %s for vehicle vin failed with status code %d', str(data), response.status_code)
                else:
                    response_data = response.json()
                    if response_data is not None:
                        if 'status' in response_data:
                            if response_data['status'] != 'ok':
                                if self.subsequent_errors > 0:
                                    LOG.error('ABRP send telemetry %s for vehicle %s failed', str(data), vin)
                                else:
                                    LOG.warning('ABRP send telemetry %s for vehicle %s failed', str(data), vin)
                            else:
                                self.subsequent_errors = 0
                            if 'missing' in response_data:
                                LOG.info('ABRP send telemetry %s for vehicle %s: %s', str(data), vin, response_data["missing"])
                        else:
                            LOG.error('ABRP send telemetry %s for vehicle %s returned unexpected data %s', str(data), vin, str(response_data))
                    else:
                        LOG.error('ABRP send telemetry %s for vehicle %s for account returned empty data', str(data), vin)
            except RequestException as e:
                if self.subsequent_errors > 0:
                    LOG.error('ABRP send telemetry %s for vehicle %s failed: %s, will try again after next change', str(data), vin, e)
                else:
                    LOG.warning('ABRP send telemetry %s for vehicle %s failed: %s, will try again after next change', str(data), vin, e)

    def shutdown(self) -> None:
        """
        Shuts down the connector by persisting current state, closing the session,
        and cleaning up resources.

        This method performs the following actions:
        1. Persists the current state.
        2. Closes the session.
        3. Sets the session and manager to None.
        4. Calls the shutdown method of the base connector.
        """
        LOG.info("Shutting down ABRP plugin")
        for vehicle in self.subscribed_vehicles.values():
            vehicle.remove_observer(self.__on_vehicle_update)
        return super().shutdown()

    def get_version(self) -> str:
        return __version__
