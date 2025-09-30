import { StageName } from '@orcabus/platform-cdk-constructs/shared-config/accounts';
import { EVENT_BUS_NAME } from '@orcabus/platform-cdk-constructs/shared-config/event-bridge';
import {
  BASE_URL,
  DAG_MAP,
  DEFAULT_DAG_VERSION,
  DEFAULT_PANEL_NAME,
  DEFAULT_PAYLOAD_VERSION,
  INSTITUTION,
  NEW_WORKFLOW_MANAGER_IS_DEPLOYED,
  PANEL_MAP,
  PROJECT_INFO_DEFAULT,
  PROJECT_INFO_MAP,
  REDCAP_LAMBDA_FUNCTION_NAME,
  S3_PIERIANDX_LOOKUP_BUCKET,
  S3_SEQUENCERRUN_ROOT,
  SNOMED_CT_DISEASE_TREE_S3_PATH,
  SNOMED_CT_SPECIMEN_TYPE_S3_PATH,
  SSM_PARAMETER_PATH_DEFAULT_DAG_VERSION,
  SSM_PARAMETER_PATH_DEFAULT_PANEL_NAME,
  SSM_PARAMETER_PATH_DEFAULT_PROJECT_INFO,
  SSM_PARAMETER_PATH_PANEL_BY_PANEL_NAME_PREFIX,
  SSM_PARAMETER_PATH_PAYLOAD_VERSION,
  SSM_PARAMETER_PATH_PIERIANDX_BASE_URL,
  SSM_PARAMETER_PATH_PIERIANDX_INSTITUTION,
  SSM_PARAMETER_PATH_PIERIANDX_USER_EMAIL,
  SSM_PARAMETER_PATH_PREFIX,
  SSM_PARAMETER_PATH_PREFIX_DAG_NAME_BY_DAG_VERSION_PREFIX,
  SSM_PARAMETER_PATH_PROJECT_INFO_BY_PROJECT_TYPE_PREFIX,
  SSM_PARAMETER_PATH_S3_DISEASE_TREE,
  SSM_PARAMETER_PATH_S3_SPECIMEN_TYPE_MAP,
  SSM_PARAMETER_PATH_SEQUENCER_ROOT,
  SSM_PARAMETER_PATH_WORKFLOW_NAME,
  USER_EMAIL,
  WORKFLOW_NAME,
} from './constants';
import { StatefulApplicationStackConfig, StatelessApplicationStackConfig } from './interfaces';
import { SsmParameterPaths, SsmParameterValues } from './ssm/interfaces';

export const getSsmParameterValues = (stage: StageName): SsmParameterValues => {
  return {
    // Payload defaults
    workflowName: WORKFLOW_NAME,
    payloadVersion: DEFAULT_PAYLOAD_VERSION,

    // PierianDx Credentials
    pierianDxUserEmail: USER_EMAIL,
    pierianDxInstitution: INSTITUTION[stage],
    pierianDxBaseUrl: BASE_URL[stage],

    // Sequencerrun Prefix
    sequencerrunRoot: S3_SEQUENCERRUN_ROOT[stage],

    // Dag
    dagNameByDagVersionMap: DAG_MAP,
    defaultDagVersion: DEFAULT_DAG_VERSION,

    // Panel
    panelIdByPanelName: PANEL_MAP,
    defaultPanelName: DEFAULT_PANEL_NAME,

    // Project Info
    projectInfoConfigurationMap: PROJECT_INFO_MAP,
    defaultProjectInfoConfiguration: PROJECT_INFO_DEFAULT,

    // S3 Lookup
    snomedSpecimenTypeS3Path: SNOMED_CT_SPECIMEN_TYPE_S3_PATH[stage],
    snomedCtDiseaseTreeS3Path: SNOMED_CT_DISEASE_TREE_S3_PATH[stage],
  };
};

export const getSsmParameterPaths = (): SsmParameterPaths => {
  return {
    // Top level prefix
    ssmRootPrefix: SSM_PARAMETER_PATH_PREFIX,

    // Payload
    workflowName: SSM_PARAMETER_PATH_WORKFLOW_NAME,
    payloadVersion: SSM_PARAMETER_PATH_PAYLOAD_VERSION,

    // PierianDxCredentials
    pierianDxUserEmail: SSM_PARAMETER_PATH_PIERIANDX_USER_EMAIL,
    pierianDxInstitution: SSM_PARAMETER_PATH_PIERIANDX_INSTITUTION,
    pierianDxBaseUrl: SSM_PARAMETER_PATH_PIERIANDX_BASE_URL,

    // Sequencerrun Prefix
    sequencerrunRoot: SSM_PARAMETER_PATH_SEQUENCER_ROOT,

    // Dag
    dagNameByDagVersionPrefix: SSM_PARAMETER_PATH_PREFIX_DAG_NAME_BY_DAG_VERSION_PREFIX,
    defaultDagVersionPath: SSM_PARAMETER_PATH_DEFAULT_DAG_VERSION,

    // Panel
    panelIdByPanelNamePrefix: SSM_PARAMETER_PATH_PANEL_BY_PANEL_NAME_PREFIX,
    defaultPanelNamePath: SSM_PARAMETER_PATH_DEFAULT_PANEL_NAME,

    // Project Info
    projectInfoConfigurationMapPrefix: SSM_PARAMETER_PATH_PROJECT_INFO_BY_PROJECT_TYPE_PREFIX,
    defaultProjectInfoConfigurationPath: SSM_PARAMETER_PATH_DEFAULT_PROJECT_INFO,

    // S3 Lookup
    snomedSpecimenTypeS3Path: SSM_PARAMETER_PATH_S3_SPECIMEN_TYPE_MAP,
    snomedCtDiseaseTreeS3Path: SSM_PARAMETER_PATH_S3_DISEASE_TREE,
  };
};

export const getStatefulStackProps = (stage: StageName): StatefulApplicationStackConfig => {
  // Get stateful application stack props
  return {
    // SSM Stuff
    ssmParameterValues: getSsmParameterValues(stage),
    ssmParameterPaths: getSsmParameterPaths(),

    // Bucket Stuff
    lookupBucketName: S3_PIERIANDX_LOOKUP_BUCKET[stage],
  };
};

export const getStatelessStackProps = (stage: StageName): StatelessApplicationStackConfig => {
  // Get stateless application stack props
  return {
    // Event bus object
    eventBusName: EVENT_BUS_NAME,

    // Workflow manager configuration
    isNewWorkflowManagerDeployed: NEW_WORKFLOW_MANAGER_IS_DEPLOYED[stage],

    // SSM Parameter paths
    ssmParameterPaths: getSsmParameterPaths(),

    // Redcap lambda name
    redcapLambdaName: REDCAP_LAMBDA_FUNCTION_NAME[stage],

    // S3 bucket
    lookupBucketName: S3_PIERIANDX_LOOKUP_BUCKET[stage],
  };
};
