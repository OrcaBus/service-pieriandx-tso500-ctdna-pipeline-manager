#!/usr/bin/env python

# Standard imports
from typing import Optional, TypedDict, cast

from pydantic import model_validator, computed_field

# Data imports
from pieriandx_tools.pieriandx_literals import DataType, DataNameSuffixByDataType
from pieriandx_tools.pieriandx_models import PierianDxBaseModel

PATH_EXTENSION = "Data/Intensities/BaseCalls"


class DataFileDict(TypedDict):
    srcUri: str
    destUri: str
    needsDecompression: bool
    contents: str


class DataFile(PierianDxBaseModel):
    # Initialise the class variables
    sequencerrun_path_root: str
    file_type: DataType
    sample_id: str
    src_uri: Optional[str]
    contents: Optional[str]

    # Add model validator, confirm that either src_uri or contents is provided
    @model_validator(mode="after")
    def check_src_uri_or_contents(self):
        if self.src_uri is None and self.contents is None:
            raise ValueError("Either src_uri or contents must be provided")

    @computed_field
    def needs_decompression(self) -> bool:
        # Determine compression status by src uri file extension
        if self.src_uri is not None and self.src_uri.endswith(".gz"):
            return True
        else:
            return False

    @computed_field
    def dest_uri(self) -> str:
        if self.file_type == 'samplesheetContents':
            return self.sequencerrun_path_root.rstrip("/") + "/" + 'SampleSheet.csv'
        return (
            self.sequencerrun_path_root.rstrip("/") + "/" + PATH_EXTENSION + "/" +
            self.sample_id + DataNameSuffixByDataType[self.file_type]
        )

    def to_dict(self, **kwargs) -> DataFileDict:
        data = super().to_dict(**kwargs)

        return cast(
            DataFileDict,
            dict(filter(
                lambda kv_iter: kv_iter[0] in DataFileDict.__annotations__,
                data.items()
            ))
        )
