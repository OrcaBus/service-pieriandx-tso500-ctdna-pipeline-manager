import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { BuildSsmParameterProps } from './interfaces';

import * as path from 'path';

export function buildSsmParameters(scope: Construct, props: BuildSsmParameterProps) {
  /**
   * SSM Stack here
   *
   * */

  /**
   * Detail Level SSM Parameters
   */
  // Workflow name
  new ssm.StringParameter(scope, 'workflow-name', {
    parameterName: props.ssmParameterPaths.workflowName,
    stringValue: props.ssmParameterValues.workflowName,
  });

  /**
   * Payload level SSM Parameters
   */
  // Payload version
  new ssm.StringParameter(scope, 'payload-version', {
    parameterName: props.ssmParameterPaths.payloadVersion,
    stringValue: props.ssmParameterValues.payloadVersion,
  });

  /**
   * PierianDx Client Configurations
   */
  // User Email
  new ssm.StringParameter(scope, 'user-email', {
    parameterName: props.ssmParameterPaths.pierianDxUserEmail,
    stringValue: props.ssmParameterValues.pierianDxUserEmail,
  });
  // Institution
  new ssm.StringParameter(scope, 'institution', {
    parameterName: props.ssmParameterPaths.pierianDxInstitution,
    stringValue: props.ssmParameterValues.pierianDxInstitution,
  });
  // Base URL
  new ssm.StringParameter(scope, 'base-url', {
    parameterName: props.ssmParameterPaths.pierianDxBaseUrl,
    stringValue: props.ssmParameterValues.pierianDxBaseUrl,
  });

  /**
   * Sequencerrun prefix
   */
  // Sequencerrun prefix
  new ssm.StringParameter(scope, 'sequencerrun-prefix', {
    parameterName: props.ssmParameterPaths.sequencerrunRoot,
    stringValue: props.ssmParameterValues.sequencerrunRoot,
  });

  /**
   * Dag stuff
   */
  // Dag configuration map
  for (const [key, value] of Object.entries(props.ssmParameterValues.dagNameByDagVersionMap)) {
    new ssm.StringParameter(scope, `dag-${key}`, {
      parameterName: path.join(props.ssmParameterPaths.dagNameByDagVersionPrefix, key),
      stringValue: JSON.stringify(value),
    });
  }

  // Dag default version
  new ssm.StringParameter(scope, 'dag-default-version', {
    parameterName: props.ssmParameterPaths.defaultDagVersionPath,
    stringValue: props.ssmParameterValues.defaultDagVersion,
  });

  /**
   * Panel
   */
  // Panel configuration map
  for (const [key, value] of Object.entries(props.ssmParameterValues.panelIdByPanelName)) {
    new ssm.StringParameter(scope, `panel-${key}`, {
      parameterName: path.join(props.ssmParameterPaths.panelIdByPanelNamePrefix, key),
      stringValue: value,
    });
  }

  // Panel default version
  new ssm.StringParameter(scope, 'panel-default-version', {
    parameterName: props.ssmParameterPaths.defaultPanelNamePath,
    stringValue: props.ssmParameterValues.defaultPanelName,
  });

  /**
   * Project Info
   */
  // Project Info configuration map
  for (const [key, value] of Object.entries(props.ssmParameterValues.projectInfoConfigurationMap)) {
    new ssm.StringParameter(scope, `project-info-${key}`, {
      parameterName: path.join(props.ssmParameterPaths.projectInfoConfigurationMapPrefix, key),
      stringValue: JSON.stringify(value),
    });
  }

  // Default Project Info
  new ssm.StringParameter(scope, 'default-project-info', {
    parameterName: props.ssmParameterPaths.defaultProjectInfoConfigurationPath,
    stringValue: JSON.stringify(props.ssmParameterValues.defaultProjectInfoConfiguration),
  });

  /**
   * S3 Lookup
   */
  new ssm.StringParameter(scope, 'snomed-specimen-type-s3-path', {
    parameterName: props.ssmParameterPaths.snomedSpecimenTypeS3Path,
    stringValue: props.ssmParameterValues.snomedSpecimenTypeS3Path,
  });
  new ssm.StringParameter(scope, 'snomed-ct-disease-tree-s3-path', {
    parameterName: props.ssmParameterPaths.snomedCtDiseaseTreeS3Path,
    stringValue: props.ssmParameterValues.snomedCtDiseaseTreeS3Path,
  });
}
