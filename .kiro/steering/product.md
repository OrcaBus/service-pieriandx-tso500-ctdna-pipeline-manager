# Product: PierianDx TSO500 ctDNA Pipeline Manager

## Summary

This is an OrcaBus microservice that manages the lifecycle of the **PierianDx TSO500 ctDNA pipeline** — a clinical reporting pipeline that submits TSO500 ctDNA analysis results to Velsera's (formerly PierianDx) Clinical Genomics Workspace (CGW) for variant interpretation and clinical report generation.

Unlike other OrcaBus pipeline managers that orchestrate CWL workflows on ICAv2, this service directly interacts with the PierianDx CGW API to create cases, upload sequencing data, launch informatics jobs, and monitor their completion. It follows the standard Pipeline Manager event model (DRAFT → READY → RUNNING → SUCCEEDED/FAILED) but uses the CGW API as its execution backend rather than ICAv2 WES.

This is a downstream service — it depends on the successful completion of the Dragen TSO500 ctDNA pipeline (via a glue state machine) to obtain analysis outputs as inputs.

## Core Responsibilities

- Accept `WorkflowRunStateChange` DRAFT events and validate/populate them into READY events
- React to upstream Dragen TSO500 ctDNA SUCCEEDED events and update existing DRAFT runs with new upstream data (glue pattern)
- Pull metadata from RedCap and the OrcaBus Metadata Service to construct case metadata
- Upload sample data files to PierianDx's S3 transfer bucket
- Create cases, sequencer runs, and informatics jobs in the CGW API
- Monitor active PierianDx informatics jobs on a schedule and emit `WorkflowRunStateChange` events on completion
- Validate draft schemas against a registered JSON schema before promotion
- Provide links to CGW case reports and VCF outputs in workflow run payloads

## Event Flow

```
DRAFT event (WorkflowRunStateChange)
  → populate draft data (Step Functions)
  → validate draft schema
  → emit READY event
  → generate PierianDx objects (case, sequencer run, informatics job)
  → upload sample data to PierianDx S3
  → create case + launch informatics job via CGW API
  → scheduled monitor checks job status
  → emit WorkflowRunStateChange events (SUCCEEDED/FAILED)

Upstream SUCCEEDED event (dragen-tso500-ctdna)
  → glue state machine
  → find matching DRAFT runs
  → merge upstream outputs into DRAFT payload
  → emit WorkflowRunUpdate DRAFT event (if changed)
```

## Upstream / Downstream

- **Upstream**: Dragen TSO500 ctDNA (provides analysis outputs via glue state machine)
- **Downstream**: None (terminal pipeline — delivers clinical reports via PierianDx CGW)
- **Key dependencies**: PierianDx CGW API, Workflow Manager, RedCap API, File Manager

## Environments

Deploys to `beta`, `gamma`, and `prod` via AWS CodePipeline. The toolchain account hosts the CodePipeline; application stacks deploy cross-account. Beta/Gamma use the PierianDx UAT environment; Prod uses the production CGW endpoint.
