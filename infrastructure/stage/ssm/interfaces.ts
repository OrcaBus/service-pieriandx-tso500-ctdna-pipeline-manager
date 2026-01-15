import { Dag, DagVersion, PanelId, PanelName, ProjectInfo, ProjectName } from '../interfaces';

export interface SsmParameterValues {
  // Payload defaults
  workflowName: string;
  payloadVersion: string;

  // PierianDx Client Configurations
  pierianDxUserEmail: string;
  pierianDxInstitution: string;
  pierianDxBaseUrl: string;

  // Sequencerrun Prefix
  sequencerrunRoot: string;

  // Dag
  dagNameByDagVersionMap: Record<DagVersion, Dag>;
  defaultDagVersion: string;

  // Panel
  panelIdByPanelName: Record<PanelName, PanelId>;
  defaultPanelName: PanelName;

  // Project Info configuration
  projectInfoConfigurationMap: Record<ProjectName, ProjectInfo>;
  defaultProjectInfoConfiguration: ProjectInfo;

  // S3 Lookup
  snomedSpecimenTypeS3Path: string;
  snomedCtDiseaseTreeS3Path: string;
}

export interface SsmParameterPaths {
  // Top level prefix
  ssmRootPrefix: string;

  // Payload
  workflowName: string;
  payloadVersion: string;

  // PierianDx Client Configurations
  pierianDxUserEmail: string;
  pierianDxInstitution: string;
  pierianDxBaseUrl: string;

  // Sequencerrun Prefix
  sequencerrunRoot: string;

  // Dag
  dagNameByDagVersionPrefix: string;
  defaultDagVersionPath: string;

  // Panel
  panelIdByPanelNamePrefix: string;
  defaultPanelNamePath: string;

  // Project Info
  projectInfoConfigurationMapPrefix: string;
  defaultProjectInfoConfigurationPath: string;

  // S3 Lookup
  snomedSpecimenTypeS3Path: string;
  snomedCtDiseaseTreeS3Path: string;
}

export interface BuildSsmParameterProps {
  ssmParameterValues: SsmParameterValues;
  ssmParameterPaths: SsmParameterPaths;
}
