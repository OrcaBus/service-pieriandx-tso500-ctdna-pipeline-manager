#!/usr/bin/env python3

# Standard imports
import typing
from typing import Dict, TypedDict

# Local imports
from . import PierianDxBaseModel

# Output models
class DagDict(TypedDict):
    dagDescription: str
    dagName: str


class Dag(PierianDxBaseModel):
    # Attributes
    name: str
    description: str

    def to_dict(self, **kwargs) -> DagDict:
        data = super().to_dict(**kwargs)

        return {
            "dagName": data['name'],
            "dagDescription": data['description']
        }
