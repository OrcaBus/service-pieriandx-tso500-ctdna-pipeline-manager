# Running Workflow Validations

- Version: 1.0
- Contact: Alexis Lucattini, [alexisl@unimelb.edu.au](mailto:alexisl@unimelb.edu.au)

This SOP describes how to validate the PierianDx TSO500 ctDNA pipeline after infrastructure changes, DAG version updates, or panel configuration changes.

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Validation Procedure](#validation-procedure)
  - [Step 1: Submit a test case](#step-1-submit-a-test-case)
  - [Step 2: Monitor pipeline execution](#step-2-monitor-pipeline-execution)
  - [Step 3: Verify CGW results](#step-3-verify-cgw-results)
  - [Step 4: Verify OrcaBus events](#step-4-verify-orcabus-events)
- [Expected Outcomes](#expected-outcomes)
- [Troubleshooting](#troubleshooting)

## Overview

Unlike ICAv2-based pipelines where validation involves comparing VCF outputs against truth sets, PierianDx pipeline validation focuses on:

1. Successful data transfer to PierianDx S3
2. Successful case creation in the CGW
3. Informatics job completion without errors
4. Correct report generation and output data capture

## Prerequisites

- AWS credentials for the beta environment
- Access to PierianDx CGW UAT portal
- A known-good test library (e.g. a previously validated TSO500 ctDNA library)
- Portal token set in the environment (`PORTAL_TOKEN`)

## Validation Procedure

### Step 1: Submit a test case

Follow the [Manual Pipeline Execution SOP](../PM.PTC.1/PM.PTC.1-ManualPipelineExecution.md) to submit a DRAFT event using a previously validated test library.

```bash
bash docs/operation/SOP/PM.PTC.1/generate-WRU-draft.sh \
  --comment "Workflow validation test" \
  <test_library_id>
```

### Step 2: Monitor pipeline execution

Monitor the pipeline through its stages:

1. **DRAFT → populated DRAFT**: Check the `orca-pdx--populateDraftData` state machine in the [Step Functions console](https://ap-southeast-2.console.aws.amazon.com/states/home?region=ap-southeast-2#/statemachines)
2. **DRAFT → READY**: Check `orca-pdx--validateDraftDataAndPutReadyEvent`
3. **READY → RUNNING**: Check `orca-pdx--launchPieriandxFromReadyEvent`
4. **RUNNING → SUCCEEDED**: Wait for the monitor state machine to detect completion

### Step 3: Verify CGW results

1. Log into the PierianDx CGW UAT portal
2. Locate the case by the workflow run name or library ID
3. Verify:
   - Case was created with correct metadata (patient, specimen, disease)
   - Sequencer run data was uploaded correctly
   - Informatics job completed successfully
   - Report is available and contains expected variant annotations

### Step 4: Verify OrcaBus events

Confirm the correct events were emitted:

1. Check the workflow run in the [OrcaBus Portal](https://portal.umccr.org/)
2. Verify the state transitions: DRAFT → READY → RUNNING → SUCCEEDED
3. Verify the output payload contains report links and VCF URIs

## Expected Outcomes

| Check                    | Expected                            |
| ------------------------ | ----------------------------------- |
| State machine executions | All complete without errors         |
| CGW case creation        | Case visible in UAT portal          |
| Informatics job          | Completed with PASS status          |
| Report                   | Available with variant annotations  |
| Output payload           | Contains `reportUrl` and `vcfUri`   |
| Event transitions        | DRAFT → READY → RUNNING → SUCCEEDED |

## Troubleshooting

If validation fails, consult the [Troubleshooting SOP](../PM.PTC.5/PM.PTC.5-Troubleshooting.md) for common issues and their resolution.
