"""
Module for information about the vehicle and Route in ABRP
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from carconnectivity.objects import GenericObject
from carconnectivity.attributes import LevelAttribute

if TYPE_CHECKING:
    from carconnectivity.vehicle import GenericVehicle


class ABRP(GenericObject):
    """
    Represents the vehicle in ABRP
    """
    def __init__(self, vehicle: GenericVehicle) -> None:
        super().__init__(object_id='abrp', parent=vehicle)
        self.next_charge_level = LevelAttribute('next_charge_level', parent=self, tags={'plugin_custom'})

    def __str__(self) -> str:
        return_string: str = ''
        if self.next_charge_level.enabled:
            return_string += f'\t{self.next_charge_level}\n'
        return return_string
