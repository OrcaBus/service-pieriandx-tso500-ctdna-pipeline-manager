import { EventPattern, IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import { Duration } from 'aws-cdk-lib';

/**
 * EventBridge Rules Interfaces
 */
export type EventBridgeRuleName =
  // Dragen Succeeded
  | 'upstreamSucceededEventLegacy'
  | 'upstreamSucceededEvent'
  // Draft events
  | 'wrscDraftLegacy'
  | 'wrscDraft'
  // Pre-ready
  | 'wrscReadyLegacy'
  | 'wrscReady'
  // Monitor runs
  | 'monitorPdxRunsSchedule';

export const eventBridgeRuleNameList: EventBridgeRuleName[] = [
  // Dragen Succeeded event
  'upstreamSucceededEventLegacy',
  'upstreamSucceededEvent',
  // Draft events
  'wrscDraftLegacy',
  'wrscDraft',
  // Pre-ready
  'wrscReadyLegacy',
  'wrscReady',
  // Monitor runs
  'monitorPdxRunsSchedule',
];

export interface EventBridgeRuleProps {
  ruleName: EventBridgeRuleName;
  eventBus: IEventBus;
  eventPattern: EventPattern;
}

export interface EventBridgeRulesProps {
  eventBus: IEventBus;
}

export interface EventBridgeRuleObject {
  ruleName: EventBridgeRuleName;
  ruleObject: Rule;
}

export interface ScheduledEventBridgeRuleProps extends Omit<
  EventBridgeRuleProps,
  'eventBus' | 'eventPattern'
> {
  scheduleDuration?: Duration;
}

export type BuildDraftRuleProps = Omit<EventBridgeRuleProps, 'eventPattern'>;
export type BuildReadyRuleProps = Omit<EventBridgeRuleProps, 'eventPattern'>;
