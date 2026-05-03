import { BigInt } from "@graphprotocol/graph-ts";

import {
  JobPosted as JobPostedEvent,
  BidAssigned as BidAssignedEvent,
  EscrowReleased as EscrowReleasedEvent,
} from "../generated/OrbittMarket/OrbittMarket";

import {
  MetadataUpdated as MetadataUpdatedEvent,
} from "../generated/OrbittRegistry/OrbittRegistry";

import {
  SubnameRegistered as SubnameRegisteredEvent,
  ReputationScoreUpdated as ReputationScoreUpdatedEvent,
} from "../generated/OrbittSubnameRegistrar/OrbittSubnameRegistrar";

import { Agent, Job, ReputationEvent } from "../generated/schema";

const STATUS_POSTED = "POSTED";
const STATUS_ASSIGNED = "ASSIGNED";
const STATUS_ESCROW_RELEASED = "ESCROW_RELEASED";

function getOrCreateAgent(id: string): Agent {
  let agent = Agent.load(id);
  if (agent == null) {
    agent = new Agent(id);
    agent.reputationScore = BigInt.fromI32(0);
    agent.jobsCompleted = BigInt.fromI32(0);
  }
  return agent as Agent;
}

function getOrCreateJob(id: string): Job {
  let job = Job.load(id);
  if (job == null) {
    job = new Job(id);
  }
  return job as Job;
}

export function handleJobPosted(event: JobPostedEvent): void {
  const jobId = event.params.jobId.toString();
  const job = new Job(jobId);

  job.poster = event.params.poster;
  job.paymentToken = event.params.paymentToken;
  job.escrowAmount = event.params.amount;
  job.specHash = event.params.specHash;
  job.deadline = event.params.deadline;
  job.status = STATUS_POSTED;

  job.save();
}

export function handleBidAccepted(event: BidAssignedEvent): void {
  const jobId = event.params.jobId.toString();
  const job = getOrCreateJob(jobId);

  job.agentTokenId = event.params.agentTokenId;
  job.status = STATUS_ASSIGNED;
  job.save();
}

export function handleEscrowReleased(event: EscrowReleasedEvent): void {
  const jobId = event.params.jobId.toString();
  const job = getOrCreateJob(jobId);

  job.status = STATUS_ESCROW_RELEASED;
  job.save();
}

export function handleMetadataUpdated(event: MetadataUpdatedEvent): void {
  const agentId = event.params.tokenId.toString();
  const agent = getOrCreateAgent(agentId);

  agent.inftTokenId = event.params.tokenId;
  agent.walletAddress = event.transaction.from;
  agent.save();
}

export function handleSubnameRegistered(event: SubnameRegisteredEvent): void {
  const agentId = event.params.agentTokenId.toString();
  const agent = getOrCreateAgent(agentId);

  agent.inftTokenId = event.params.agentTokenId;
  agent.walletAddress = event.params.requester;
  agent.ensName = event.params.label;
  agent.save();
}

export function handleReputationUpdated(event: ReputationScoreUpdatedEvent): void {
  const agentId = event.params.node.toHexString();
  const agent = getOrCreateAgent(agentId);

  const newScore = event.params.score;
  const delta = newScore;

  agent.reputationScore = newScore;
  agent.save();

  const repEvent = new ReputationEvent(
    event.transaction.hash.toHexString() + "-" + event.logIndex.toString()
  );
  repEvent.agent = agent.id;
  repEvent.delta = delta;
  repEvent.newScore = newScore;
  repEvent.reason = "reputation_score_updated";
  repEvent.timestamp = event.block.timestamp;
  repEvent.save();
}
