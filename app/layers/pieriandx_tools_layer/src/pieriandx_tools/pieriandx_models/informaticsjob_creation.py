#!/usr/bin/env python3

# Standard imports
import typing
from typing import TypedDict, List, cast

# Local imports
from . import PierianDxBaseModel

# Output dicts
if typing.TYPE_CHECKING:
    from .specimen_sequencer_info import SequencerRunInfoJobDict


class InformaticsjobCreationInputDict(TypedDict):
    accessionNumber: str
    sequencerRunInfos: List['SequencerRunInfoJobDict']


class InformaticsjobCreationDict(TypedDict):
    input: List[InformaticsjobCreationInputDict]


class InformaticsjobCreation(PierianDxBaseModel):
    # Local imported attributes
    case_accession_number: str
    specimen_sequencer_run_info: 'SpecimenSequencerInfo'

    def to_dict(self, **kwargs) -> InformaticsjobCreationDict:
        # Get data from parent dump
        data = super().to_dict(**kwargs)

        # Initialise case dict
        return cast(
            InformaticsjobCreationDict,
            {
                "input": [
                    {
                        "accessionNumber": data['caseAccessionNumber'],
                        "sequencerRunInfos": [
                            self.specimen_sequencer_run_info.to_informaticsjob_dict()
                        ]
                    }
                ]
            }
        )


# Local model imports at the bottom to avoid circular imports
from .specimen_sequencer_info import SpecimenSequencerInfo
InformaticsjobCreation.model_rebuild()
