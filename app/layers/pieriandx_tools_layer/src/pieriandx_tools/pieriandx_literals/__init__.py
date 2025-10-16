#!/usr/bin/env python

from typing import Literal, Dict

EthnicityType = Literal[
    "hispanic_or_latino",
    "not_hispanic_or_latino",
    "not_reported",
    "unknown",
]

GenderType = Literal[
  "unknown",
  "male",
  "female",
  "unspecified",
  "other",
  "ambiguous",
  "not_applicable",
]

RaceType = Literal[
    "american_indian_or_alaska_native",
    "asian",
    "black_or_african_american",
    "native_hawaiian_or_other_pacific_islander",
    "not_reported",
    "unknown",
    "white",
]

SampleType = Literal[
    'patientcare',
    'clinical_trial',
    'validation',
    'proficiency_testing',
]

SequencingSampleType = Literal[
    'DNA'
]

SequencingType = Literal[
    "pairedEnd",
    "singleEnd",
]

DataType = Literal[
    "microsatOutputUri",
    "geneCovReportUri",
    "exonCovReportUri",
    "tmbMetricsUri",
    "cnvVcfUri",
    "hardFilteredVcfUri",
    "fusionsUri",
    "metricsOutputUri",
    "samplesheetContents"
]

DataNameSuffixType = Literal[
    ".microsat_output.json",
    ".gene_cov_report.tsv",
    ".exon_cov_report.tsv",
    ".tmb.metrics.csv",
    ".cnv.vcf",
    ".hard-filtered.vcf",
    "_Fusions.csv",
    "_MetricsOutput.tsv",
]

DataNameSuffixByDataType: Dict[DataType, DataNameSuffixType] = {
    "microsatOutputUri": ".microsat_output.json",
    "geneCovReportUri": ".gene_cov_report.tsv",
    "exonCovReportUri": ".exon_cov_report.tsv",
    "tmbMetricsUri": ".tmb.metrics.csv",
    "cnvVcfUri": ".cnv.vcf",
    "hardFilteredVcfUri": ".hard-filtered.vcf",
    "fusionsUri": "_Fusions.csv",
    "metricsOutputUri": "_MetricsOutput.tsv",
}
