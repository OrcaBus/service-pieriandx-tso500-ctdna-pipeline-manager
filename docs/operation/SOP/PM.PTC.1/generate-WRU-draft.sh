#!/usr/bin/env bash

# Set to fail
set -euo pipefail

# Globals
LAMBDA_FUNCTION_NAME="WruDraftValidator"

# CLI Defaults
FORCE=false  # Use --force to set to true

# Workflow constants
WORKFLOW_NAME="pieriandx-tso500"
WORKFLOW_VERSION="2.6.0"
PAYLOAD_VERSION="2025.09.25"

# Library ID array
LIBRARY_ID_ARRAY=()

# Functions
echo_stderr(){
  echo "$(date -Iseconds)" "$@" >&2
}

print_usage(){
  echo "
generate-WRU-draft.sh [-h | --help]
generate-WRU-draft.sh (library_id)...
                  [-f | --force]
                  [--workflow-version <workflow_version>]

Description:
Run this script to generate a draft WorkflowRunUpdate event for the specified library IDs.

Positional arguments:
  library_id:   One or more library IDs to link to the WorkflowRunUpdate event.

Keyword arguments:
  -h | --help:               Print this help message and exit.
  -f | --force:              Don't confirm before pushing the event to EventBridge.
  --workflow-version:        (Optional) The workflow version to use, defaults to ${WORKFLOW_VERSION},

Environment:
  AWS_PROFILE:  (Optional) The AWS CLI profile to use for authentication.
  AWS_REGION:   (Optional) The AWS region to use for AWS CLI commands.

Example usage:
bash generate-WRU-draft.sh library_id
"
}

get_hostname_from_ssm(){
  aws ssm get-parameter \
    --name "/hosted_zone/umccr/name" \
    --output json | \
  jq --raw-output \
    '.Parameter.Value'
}

get_orcabus_token(){
  aws secretsmanager get-secret-value \
    --secret-id orcabus/token-service-jwt \
    --output json \
    --query SecretString | \
  jq --raw-output \
    'fromjson | .id_token'
}

get_library_obj_from_library_id(){
  local library_id="$1"
  curl --silent --fail --show-error --location \
    --header "Authorization: Bearer $(get_orcabus_token)" \
    --url "https://metadata.$(get_hostname_from_ssm)/api/v1/library?libraryId=${library_id}" | \
  jq --raw-output \
    '
      .results[0] |
      {
        "libraryId": .libraryId,
        "orcabusId": .orcabusId
      }
    '
}

generate_portal_run_id(){
  echo "$(date -u +'%Y%m%d')$(openssl rand -hex 4)"
}

get_linked_libraries(){
  for library_id in "${LIBRARY_ID_ARRAY[@]}"; do
    get_library_obj_from_library_id "${library_id}"
  done | \
  jq --slurp --raw-output --compact-output
}

get_lambda_function_name(){
  aws lambda list-functions \
    --output json \
    --query "Functions" | \
  jq --raw-output --compact-output \
    --arg functionName "${LAMBDA_FUNCTION_NAME}" \
    '
      map(select(.FunctionName | contains($functionName))) |
      .[0].FunctionName
    '
}

get_workflow(){
  local workflow_name="$1"
  local workflow_version="$2"
  curl --silent --fail --show-error --location \
    --request GET \
    --get \
    --header "Authorization: Bearer $(get_orcabus_token)" \
    --url "https://workflow.$(get_hostname_from_ssm)/api/v1/workflow" \
    --data "$( \
      jq \
        --null-input --compact-output --raw-output \
        --arg workflowName "$workflow_name" \
        --arg workflowVersion "$workflow_version" \
        '
          {
            "name": $workflowName,
            "version": $workflowVersion,
          } |
          to_entries |
          map(
            "\(.key)=\(.value)"
          ) |
          join("&")
        ' \
    )" | \
  jq --compact-output --raw-output \
    '
      .results[0]
    '
}

get_workflow_run(){
  local portal_run_id="$1"

  curl --silent --fail --show-error --location \
    --request GET \
    --get \
    --header "Authorization: Bearer $(get_orcabus_token)" \
    --url "https://workflow.$(get_hostname_from_ssm)/api/v1/workflowrun?portalRunId=${portal_run_id}" | \
  jq --compact-output --raw-output \
    '
      if (.results | length) > 0 then
        .results[0]
      else
        empty
      end
    '
}

# Get args
while [[ $# -gt 0 ]]; do
  case "$1" in
    # Help
    -h|--help)
      print_usage
      exit 0
      ;;
    # Force boolean
    -f|--force)
      FORCE=true
      shift
      ;;
    # Workflow version
    --workflow-version)
      WORKFLOW_VERSION="$2"
      shift 2
      ;;
    --workflow-version=*)
      WORKFLOW_VERSION="${1#*=}"
      shift
      ;;
    # Positional arguments (library IDs)
    *)
      LIBRARY_ID_ARRAY+=("$1")
      shift
      ;;
  esac
done

# Ensure at least one library ID was provided
if [ ${#LIBRARY_ID_ARRAY[@]} -eq 0 ]; then
  echo_stderr "Error: At least one library ID must be provided."
  print_usage
  exit 1
fi

# Generate the portal run id
portal_run_id="$(generate_portal_run_id)"
echo_stderr "Generated Portal Run ID: ${portal_run_id}"

# Get the workflow object
workflow="$( \
  get_workflow \
    "${WORKFLOW_NAME}" "${WORKFLOW_VERSION}" \
)"
echo_stderr "Using workflow: $(jq --raw-output '.orcabusId' <<< "${workflow}")"

# Generate the event
lambda_payload="$( \
  jq --null-input --raw-output \
    --argjson workflow "${workflow}" \
    --arg payloadVersion "${PAYLOAD_VERSION}" \
    --arg portalRunId "${portal_run_id}" \
    --argjson libraries "$(get_linked_libraries)" \
    '
      {
        "status": "DRAFT",
        "timestamp": (now | todateiso8601),
        "workflow": $workflow,
        "workflowRunName": ("umccr--manual--" + $workflow["name"] + "--" + ($workflow["version"] | gsub("\\."; "-")) + "--" + $portalRunId),
        "portalRunId": $portalRunId,
        "libraries": $libraries
      }
    ' \
)"

# Confirm before pushing the event
if [[ "${FORCE}" == "false" ]]; then
  echo_stderr "Send the following payload to the lambda object:"
  jq --raw-output <<< "${lambda_payload}" 1>&2

  read -r -p 'Confirm to push this event to EventBridge? (y/n): ' confirm_push
  if [[ ! "${confirm_push}" =~ ^[Yy]$ ]]; then
    echo_stderr "Aborting event push."
    exit 1
  fi
fi

# Push the event to EventBridge
mkfifo lambda_data_pipe
errors_json="$(mktemp "errors.XXXXXX.json")"
echo_stderr "Pushing the draft event for portalRunId ${portal_run_id} via WRU Validation Lambda Function"
aws lambda invoke \
  --function-name "$(get_lambda_function_name)" \
  --payload "$(jq --compact-output <<< "${lambda_payload}")" \
  --cli-binary-format raw-in-base64-out \
  --no-cli-pager \
  --invocation-type 'RequestResponse' \
  lambda_data_pipe 1>/dev/null & \
jq --raw-output \
  '
    if .statusCode != 200 then
      .body | fromjson
    else
      empty
    end
  ' \
  < lambda_data_pipe \
  > "${errors_json}" & \
wait
rm lambda_data_pipe

if [[ -s "${errors_json}" ]]; then
  echo_stderr "Error pushing event to Lambda Function:"
  jq --raw-output '.' < "${errors_json}" 1>&2
  rm "${errors_json}"
  exit 1
else
  rm "${errors_json}"
fi

echo_stderr "Waiting for the workflow run to be registered by the workflow manager"

while :; do
  workflow_run_object="$( \
    get_workflow_run "${portal_run_id}"
  )"

  # Check with the workflow manager for the workflow run object
  if [[ -n "${workflow_run_object}" ]]; then
    workflow_run_orcabus_id="$(jq --raw-output '.orcabusId' <<< "${workflow_run_object}")"
    echo_stderr "Workflow run registered with ID: ${workflow_run_orcabus_id}"
    break
  else
    echo_stderr "Workflow run not yet registered, waiting 10 seconds..."
    sleep 10
  fi

done

echo_stderr "Workflow Run Creation Event complete!"
echo_stderr "Please head to 'https://orcaui.$(get_hostname_from_ssm)/runs/workflow/${workflow_run_orcabus_id}' to track the status of the workflow run"
