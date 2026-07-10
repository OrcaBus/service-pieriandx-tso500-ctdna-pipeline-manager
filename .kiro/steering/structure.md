# Project Structure

## Top-Level Layout

```
├── app/                        # Application logic (lambdas, layers, step functions, schemas)
├── bin/deploy.ts               # CDK entry point — initialises stateless + stateful root stacks
├── infrastructure/             # CDK infrastructure code
│   ├── stage/                  # Per-environment application stacks
│   └── toolchain/              # CodePipeline stacks (deploy to beta/gamma/prod)
├── test/                       # CDK/cdk-nag compliance tests
├── docs/                       # Draw.io exports, SOPs, workflow studio exports
├── .kiro/steering/             # AI steering documents
├── cdk.json                    # CDK app config (entry: `pnpx ts-node bin/deploy.ts`)
├── package.json / pnpm-workspace.yaml
└── Makefile                    # Common developer commands
```

## `app/` — Application Logic

```
app/
├── event-schemas/              # JSON schemas for event validation
│   └── complete-data-draft-schema.json
├── lambdas/                    # Python Lambda functions
│   ├── compare_payload_py/
│   ├── find_latest_workflow_py/
│   ├── generate_case_metadata_py/
│   ├── generate_case_py/
│   ├── generate_informaticsjob_py/
│   ├── generate_output_data_payload_py/
│   ├── generate_pieriandx_objects_py/
│   ├── generate_sequencerrun_py/
│   ├── generate_wru_event_object_with_merged_data_py/
│   ├── get_case_metadata_from_redcap_py/
│   ├── get_data_files_from_tso500_workflow_run_py/
│   ├── get_fastq_id_list_from_rgid_list_py/
│   ├── get_fastq_rgids_from_library_id_py/
│   ├── get_informaticsjob_and_report_status_py/
│   ├── get_libraries_py/
│   ├── get_metadata_tags_py/
│   ├── get_payload_py/
│   ├── get_redcap_tags_for_library_id_py/
│   ├── get_workflow_run_object_py/
│   ├── list_active_workflow_runs_py/
│   ├── upload_pieriandx_sample_data_to_s3_py/
│   └── validate_draft_data_complete_schema_py/
├── layers/                     # Lambda layers
│   └── pieriandx_tools_layer/  # Shared PierianDx client utilities (pyriandx SDK, helpers)
└── step-functions-templates/   # ASL JSON Step Functions definitions
    ├── glue_succeeded_events_to_draft_update_sfn_template.asl.json
    ├── launch_pieriandx_from_ready_event_sfn_template.asl.json
    ├── monitor_pdx_runs_sfn_template.asl.json
    ├── populate_draft_data_sfn_template.asl.json
    └── validate_draft_data_and_put_ready_event_sfn_template.asl.json
```

### Lambda Naming Convention

Lambda directories use `snake_case` with a `_py` suffix (e.g. `get_libraries_py`). The CDK infrastructure converts camelCase names to snake_case automatically via `camelCaseToSnakeCase()`.

### Lambda Pattern

- Single file per Lambda, named `<function_name>.py`
- Must export `handler(event, context) -> Dict[str, Any]`
- Extensive docstrings describing input/output event shapes
- Business logic only — no AWS SDK calls for infrastructure wiring (IAM, SSM lookups are CDK-managed)
- Commented-out `if __name__ == "__main__"` blocks for local testing
- PierianDx-specific lambdas use the shared `pieriandx_tools_layer` for CGW API access

## `infrastructure/` — CDK Code

```
infrastructure/
├── stage/
│   ├── config.ts               # Environment configs (beta, gamma, prod)
│   ├── constants.ts            # All app constants (SSM paths, event names, DAG versions, panel maps, S3 refs)
│   ├── interfaces.ts           # Shared TypeScript interfaces for the stack
│   ├── stateless-application-stack.ts
│   ├── stateful-application-stack.ts
│   ├── lambda/                 # Lambda construct builders
│   │   ├── index.ts            # buildAllLambdas() — iterates lambdaNameList
│   │   └── interfaces.ts       # Lambda name list + requirements map
│   ├── layers/                 # Lambda layer construct builders (PierianDx tools)
│   ├── step-functions/         # Step Function construct builders
│   ├── event-rules/            # EventBridge rule builders
│   ├── event-targets/          # EventBridge target builders
│   ├── event-schemas/          # Schema registry construct builders
│   ├── s3/                     # S3 bucket construct builders (lookup bucket)
│   ├── ssm/                    # SSM parameter construct builders
│   └── utils/                  # Shared utilities (camelCase ↔ kebab/snake conversions)
└── toolchain/
    ├── constants.ts            # Toolchain-specific constants
    ├── stateless-stack.ts      # CodePipeline for stateless deployments
    └── stateful-stack.ts       # CodePipeline for stateful deployments
```

### Infrastructure Patterns

- Each resource type (lambda, step-functions, event-rules, etc.) has its own `index.ts` (builder) and `interfaces.ts` (types)
- All constants (SSM paths, event names, DAG versions, panel maps, project info maps, S3 bucket names) live in `infrastructure/stage/constants.ts` — do not hardcode these elsewhere
- Lambdas are built with `PythonUvFunction` from `@orcabus/platform-cdk-constructs`
- PierianDx-specific lambdas receive the `pieriandx_tools_layer` Lambda layer for CGW API access
- IAM permissions are granted inline in `infrastructure/stage/lambda/index.ts` based on per-Lambda requirement flags in `interfaces.ts`
- `NagSuppressions` are added inline with justification comments wherever `cdk-nag` rules are suppressed

## Key Conventions

- **Event source**: `orcabus.pieriandxtso500ctdna`
- **Event bus**: `OrcaBusMain`
- **SSM prefix**: `/orcabus/workflows/pieriandx-tso500-ctdna/`
- **Stack prefix**: `orca-pdx`
- **Workflow name**: `pieriandx-tso500-ctdna`
- **Lambda runtime**: Python 3.14 on ARM64
- **Upstream workflow name**: `dragen-tso500-ctdna` (glue pattern dependency)
- When adding a new Lambda: add the directory under `app/lambdas/<name>_py/`, register it in `infrastructure/stage/lambda/interfaces.ts`, and declare its IAM requirement flags there
- When adding a new DAG version: update `DAG_MAP` and `DEFAULT_DAG_VERSION` in `constants.ts`
- When adding a new panel: update `PANEL_MAP` in `constants.ts`
- When adding a new project type: update `PROJECT_INFO_MAP` in `constants.ts`
