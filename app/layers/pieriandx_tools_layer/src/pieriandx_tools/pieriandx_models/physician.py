#!/usr/bin/env python3

# Standard Library Imports
import typing
from typing import TypedDict

# Local Imports
from . import PierianDxBaseModel


class PhysicianDict(TypedDict):
    firstName: str
    lastName: str


class Physician(PierianDxBaseModel):
    # Attributes
    first_name: str
    last_name: str

    if typing.TYPE_CHECKING:
        def to_dict(self, **kwargs) -> PierianDxBaseModel:
            pass
