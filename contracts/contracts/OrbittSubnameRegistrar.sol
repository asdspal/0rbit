// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";

interface IENSRegistry {
    function owner(bytes32 node) external view returns (address);

    function setSubnodeRecord(bytes32 node, bytes32 label, address owner_, address resolver, uint64 ttl) external;
}

interface ITextResolver {
    function setText(bytes32 node, string calldata key, string calldata value) external;
}

interface IOrbittRegistry {
    function ownerOf(uint256 tokenId) external view returns (address);

    function getApproved(uint256 tokenId) external view returns (address);

    function isApprovedForAll(address owner, address operator) external view returns (bool);

    function axlPeerId(uint256 tokenId) external view returns (string memory);

    function reputation(uint256 tokenId) external view returns (uint256);
}

/**
 * @title OrbittSubnameRegistrar
 * @notice Issues ENS subnames under a fixed parent node and synchronizes agent metadata
 *         into resolver text records (capabilities, reputation_score, inft_token_id, axl_peer_id).
 */
contract OrbittSubnameRegistrar is Ownable {
    using Strings for uint256;

    string private constant KEY_CAPABILITIES = "capabilities";
    string private constant KEY_REPUTATION = "reputation_score";
    string private constant KEY_INFT_TOKEN_ID = "inft_token_id";
    string private constant KEY_AXL_PEER_ID = "axl_peer_id";

    IENSRegistry public immutable ens;
    IOrbittRegistry public immutable agentRegistry;
    bytes32 public immutable parentNode;

    ITextResolver public resolver;
    address public keeper;

    mapping(bytes32 => uint256) public nodeToTokenId;

    event SubnameRegistered(bytes32 indexed node, string label, uint256 agentTokenId, address indexed requester);
    event CapabilitiesUpdated(bytes32 indexed node, string label, string capabilitiesCSV);
    event ReputationScoreUpdated(bytes32 indexed node, string label, uint256 score);
    event ResolverUpdated(address indexed newResolver);
    event KeeperUpdated(address indexed newKeeper);

    modifier onlyKeeper() {
        require(msg.sender == keeper, "OrbittSubnameRegistrar: keeper only");
        _;
    }

    constructor(
        address ensRegistry,
        bytes32 parentNode_,
        address resolver_,
        address agentRegistry_,
        address keeper_
    ) Ownable(msg.sender) {
        require(ensRegistry != address(0), "OrbittSubnameRegistrar: zero ENS");
        require(parentNode_ != bytes32(0), "OrbittSubnameRegistrar: zero parent");
        require(resolver_ != address(0), "OrbittSubnameRegistrar: zero resolver");
        require(agentRegistry_ != address(0), "OrbittSubnameRegistrar: zero registry");

        ens = IENSRegistry(ensRegistry);
        parentNode = parentNode_;
        resolver = ITextResolver(resolver_);
        agentRegistry = IOrbittRegistry(agentRegistry_);
        keeper = keeper_ == address(0) ? msg.sender : keeper_;
    }

    function setResolver(address newResolver) external onlyOwner {
        require(newResolver != address(0), "OrbittSubnameRegistrar: zero resolver");
        resolver = ITextResolver(newResolver);
        emit ResolverUpdated(newResolver);
    }

    function setKeeper(address newKeeper) external onlyOwner {
        require(newKeeper != address(0), "OrbittSubnameRegistrar: zero keeper");
        keeper = newKeeper;
        emit KeeperUpdated(newKeeper);
    }

    function register(string calldata label, uint256 agentTokenId, string[] calldata capabilities) external {
        require(bytes(label).length != 0, "OrbittSubnameRegistrar: empty label");
        require(address(resolver) != address(0), "OrbittSubnameRegistrar: resolver unset");

        (bytes32 labelHash, bytes32 node) = _labelAndNode(label);
        require(nodeToTokenId[node] == 0, "OrbittSubnameRegistrar: label taken");

        address controller = _requireAgentController(agentTokenId);
        string memory peerId = agentRegistry.axlPeerId(agentTokenId);
        require(bytes(peerId).length != 0, "OrbittSubnameRegistrar: missing peer id");

        string memory capabilitiesCSV = _joinCapabilities(capabilities);
        uint256 currentRep = agentRegistry.reputation(agentTokenId);

        ens.setSubnodeRecord(parentNode, labelHash, address(this), address(resolver), 0);

        resolver.setText(node, KEY_CAPABILITIES, capabilitiesCSV);
        resolver.setText(node, KEY_REPUTATION, currentRep.toString());
        resolver.setText(node, KEY_INFT_TOKEN_ID, agentTokenId.toString());
        resolver.setText(node, KEY_AXL_PEER_ID, peerId);

        nodeToTokenId[node] = agentTokenId;
        emit SubnameRegistered(node, label, agentTokenId, controller);
    }

    function setCapabilities(string calldata label, string[] calldata capabilities) external onlyOwner {
        (, bytes32 node) = _labelAndNode(label);
        require(nodeToTokenId[node] != 0, "OrbittSubnameRegistrar: unregistered label");

        string memory capabilitiesCSV = _joinCapabilities(capabilities);
        resolver.setText(node, KEY_CAPABILITIES, capabilitiesCSV);
        emit CapabilitiesUpdated(node, label, capabilitiesCSV);
    }

    function setReputationScore(string calldata label, uint256 score) external onlyKeeper {
        require(score <= 1000, "OrbittSubnameRegistrar: score too high");
        (, bytes32 node) = _labelAndNode(label);
        require(nodeToTokenId[node] != 0, "OrbittSubnameRegistrar: unregistered label");

        resolver.setText(node, KEY_REPUTATION, score.toString());
        emit ReputationScoreUpdated(node, label, score);
    }

    function _labelAndNode(string calldata label) private view returns (bytes32 labelHash, bytes32 node) {
        labelHash = keccak256(abi.encodePacked(label));
        node = keccak256(abi.encodePacked(parentNode, labelHash));
    }

    function _joinCapabilities(string[] calldata capabilities) private pure returns (string memory) {
        if (capabilities.length == 0) {
            return "";
        }

        string memory csv = capabilities[0];
        for (uint256 i = 1; i < capabilities.length; i++) {
            csv = string.concat(csv, ",", capabilities[i]);
        }
        return csv;
    }

    function _requireAgentController(uint256 tokenId) private view returns (address owner_) {
        owner_ = agentRegistry.ownerOf(tokenId);
        require(owner_ != address(0), "OrbittSubnameRegistrar: invalid token");
        require(
            msg.sender == owner_ ||
                agentRegistry.getApproved(tokenId) == msg.sender ||
                agentRegistry.isApprovedForAll(owner_, msg.sender),
            "OrbittSubnameRegistrar: unauthorized"
        );
    }
}
