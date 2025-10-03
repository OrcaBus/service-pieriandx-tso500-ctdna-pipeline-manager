#!/usr/bin/env python3

# Standard library imports
import typing
from typing import Optional, List, TypedDict, NotRequired, Union

# Local imported attributes
from .dag import Dag
from .disease import Disease

# Literal imports
from ..pieriandx_literals import SampleType

# Local imports
from . import PierianDxBaseModel

# TypedDicts (for outputs)
if typing.TYPE_CHECKING:
    from .specimen import SpecimenDict
    from .disease import DiseaseDict
    from .physician import PhysicianDict
    from .specimen import IdentifiedSpecimenDict, DeIdentifiedSpecimenDict


class CaseCreationDict(TypedDict):
    # Local class imports
    dagName: str
    dagDescription: str
    disease: 'DiseaseDict'
    identified: bool
    indication: NotRequired[str]
    panelName: str
    sampleType: SampleType
    specimens: List['SpecimenDict']


class IdentifiedCaseCreationDict(CaseCreationDict):
    # Local class imports
    physicians: List['PhysicianDict']  # List of PhysicianDict
    specimens: List['IdentifiedSpecimenDict']  # SpecimenDict from IdentifiedSpecimen


class DeIdentifiedCaseCreationDict(CaseCreationDict):
    # Local class imports
    specimens: List['DeIdentifiedSpecimenDict']  # SpecimenDict from DeIdentifiedSpec


CaseCreationDictType = Union[IdentifiedCaseCreationDict, DeIdentifiedCaseCreationDict]


class CaseCreation(PierianDxBaseModel):
    # Attributes
    dag: Dag
    disease: Disease
    is_identified: bool
    indication: Optional[str] = None
    panel_name: str
    sample_type: SampleType
    specimen: 'Specimen'

    def to_dict(self, **kwargs) -> CaseCreationDict:
        data = super().to_dict(**kwargs)

        # Fix dag
        dag = data.pop('dag')
        data['dagName'] = dag['name']
        data['dagDescription'] = dag['description']

        # Fix identified
        data['identified'] = data.pop('isIdentified')

        # Fix specimens
        _ = data.pop('specimen')
        data['specimens'] = [self.specimen.to_dict()]

        # Fix disease
        data['disease'] = self.disease.to_dict()

        return data


class IdentifiedCaseCreation(CaseCreation):
    # Imports
    requesting_physician: 'Physician'
    specimen: 'IdentifiedSpecimen'
    is_identified: bool = True

    def to_dict(self, **kwargs) -> IdentifiedCaseCreationDict:
        # Initialise dict
        data: Union[CaseCreationDict, IdentifiedCaseCreationDict] = super().to_dict(**kwargs)

        # Fix physicians
        _ = data.pop('requestingPhysician')
        data['physicians'] = [self.requesting_physician.to_dict(**kwargs)]

        # Return data
        return data


class DeIdentifiedCaseCreation(CaseCreation):
    # Local class imports
    specimen: 'DeIdentifiedSpecimen'
    is_identified: bool = False

    if typing.TYPE_CHECKING:
        def to_dict(self, **kwargs) -> DeIdentifiedCaseCreationDict:
            pass


# Local model imports at the bottom
# Local class imports
from .specimen import Specimen
from .physician import Physician
from .specimen import IdentifiedSpecimen
from .specimen import DeIdentifiedSpecimen

# Then rebuild each model
CaseCreation.model_rebuild()
IdentifiedCaseCreation.model_rebuild()
DeIdentifiedCaseCreation.model_rebuild()

CaseCreationType = Union[IdentifiedCaseCreation, DeIdentifiedCaseCreation]
