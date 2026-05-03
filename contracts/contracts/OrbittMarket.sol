// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IOrbittRegistry {
    function ownerOf(uint256 tokenId) external view returns (address);
}

/**
 * @title OrbittMarket
 * @dev Job escrow contract per blueprint Section 6.2.
 */
contract OrbittMarket is Ownable, ReentrancyGuard {
    enum JobStatus {
        Posted,
        Assigned,
        InProgress,
        Complete,
        Disputed
    }

    struct Job {
        uint256 id;
        address poster;
        uint256 agentTokenId;
        address paymentToken;
        uint256 escrowAmount;
        bytes32 jobSpecHash;
        bytes32 outputHash;
        JobStatus status;
        uint256 deadline;
    }

    mapping(uint256 => Job) public jobs;
    uint256 public jobCount;
    IOrbittRegistry public registry;
    address public keeper;

    event JobPosted(
        uint256 indexed jobId,
        address indexed poster,
        address indexed paymentToken,
        uint256 amount,
        bytes32 specHash,
        uint256 deadline
    );
    event BidAssigned(uint256 indexed jobId, uint256 indexed agentTokenId);
    event OutputSubmitted(uint256 indexed jobId, bytes32 outputHash, bytes computeProof);
    event EscrowReleased(uint256 indexed jobId, address indexed recipient, uint256 amount);
    event JobDisputed(uint256 indexed jobId, address indexed caller);
    event KeeperUpdated(address indexed newKeeper);
    event RegistryUpdated(address indexed newRegistry);

    modifier onlyKeeper() {
        require(msg.sender == keeper, "OrbittMarket: keeper only");
        _;
    }

    constructor() Ownable(msg.sender) {
        keeper = msg.sender;
    }

    function setKeeper(address newKeeper) external onlyOwner {
        require(newKeeper != address(0), "OrbittMarket: zero keeper");
        keeper = newKeeper;
        emit KeeperUpdated(newKeeper);
    }

    function setRegistry(address newRegistry) external onlyOwner {
        require(newRegistry != address(0), "OrbittMarket: zero registry");
        registry = IOrbittRegistry(newRegistry);
        emit RegistryUpdated(newRegistry);
    }

    function postJob(
        address paymentToken,
        uint256 amount,
        bytes32 specHash,
        uint256 deadline
    ) external nonReentrant returns (uint256 jobId) {
        require(paymentToken != address(0), "OrbittMarket: zero token");
        require(amount > 0, "OrbittMarket: zero escrow");
        require(specHash != bytes32(0), "OrbittMarket: empty spec");
        require(deadline > block.timestamp, "OrbittMarket: deadline in past");

        jobId = ++jobCount;
        Job storage job = jobs[jobId];
        job.id = jobId;
        job.poster = msg.sender;
        job.paymentToken = paymentToken;
        job.escrowAmount = amount;
        job.jobSpecHash = specHash;
        job.status = JobStatus.Posted;
        job.deadline = deadline;

        require(
            IERC20(paymentToken).transferFrom(msg.sender, address(this), amount),
            "OrbittMarket: escrow transfer failed"
        );

        emit JobPosted(jobId, msg.sender, paymentToken, amount, specHash, deadline);
    }

    function assignBid(uint256 jobId, uint256 agentTokenId) external {
        require(agentTokenId != 0, "OrbittMarket: zero agent token");
        Job storage job = _requireJob(jobId);
        require(msg.sender == job.poster, "OrbittMarket: poster only");
        require(job.status == JobStatus.Posted, "OrbittMarket: invalid status");

        job.agentTokenId = agentTokenId;
        job.status = JobStatus.Assigned;

        emit BidAssigned(jobId, agentTokenId);
    }

    function submitOutput(
        uint256 jobId,
        bytes32 outputHash,
        bytes calldata computeProof
    ) external {
        Job storage job = _requireJob(jobId);
        require(job.status == JobStatus.Assigned, "OrbittMarket: not assigned");
        require(job.agentTokenId != 0, "OrbittMarket: no agent");
        require(outputHash != bytes32(0), "OrbittMarket: empty output");

        address agentOwner = _requireAgentOwner(job.agentTokenId);
        require(msg.sender == agentOwner, "OrbittMarket: agent only");

        job.outputHash = outputHash;
        job.status = JobStatus.Complete;

        emit OutputSubmitted(jobId, outputHash, computeProof);
    }

    function releaseEscrow(uint256 jobId) external onlyKeeper nonReentrant {
        Job storage job = _requireJob(jobId);
        require(job.status == JobStatus.Complete, "OrbittMarket: not complete");
        require(job.escrowAmount > 0, "OrbittMarket: no escrow");
        require(job.paymentToken != address(0), "OrbittMarket: token missing");

        address agentOwner = _requireAgentOwner(job.agentTokenId);
        uint256 amount = job.escrowAmount;
        job.escrowAmount = 0;

        require(
            IERC20(job.paymentToken).transfer(agentOwner, amount),
            "OrbittMarket: release failed"
        );

        emit EscrowReleased(jobId, agentOwner, amount);
    }

    function disputeJob(uint256 jobId) external {
        Job storage job = _requireJob(jobId);
        require(
            msg.sender == job.poster || msg.sender == keeper,
            "OrbittMarket: unauthorized dispute"
        );
        require(job.status != JobStatus.Disputed, "OrbittMarket: already disputed");

        job.status = JobStatus.Disputed;
        emit JobDisputed(jobId, msg.sender);
    }

    function _requireJob(uint256 jobId) internal view returns (Job storage job) {
        require(jobId != 0, "OrbittMarket: invalid id");
        job = jobs[jobId];
        require(job.id != 0, "OrbittMarket: job missing");
    }

    function _requireAgentOwner(uint256 agentTokenId) internal view returns (address) {
        require(agentTokenId != 0, "OrbittMarket: zero agent token");
        require(address(registry) != address(0), "OrbittMarket: registry unset");
        address agentOwner = registry.ownerOf(agentTokenId);
        require(agentOwner != address(0), "OrbittMarket: agent owner missing");
        return agentOwner;
    }

    // Reserved storage gap for future variables when proxying is introduced in later steps.
    uint256[47] private __gap;
}
