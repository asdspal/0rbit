// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title OrbittRegistry
 * @dev ERC-7857-inspired registry for AI agent identity NFTs.
 */
contract OrbittRegistry is ERC721, ReentrancyGuard, Ownable {
    mapping(uint256 => bytes32) private _metadataHashes;
    mapping(uint256 => string) private _encryptedURIs;
    mapping(uint256 => uint256) public reputation;
    mapping(uint256 => uint256) public jobsCompleted;
    mapping(uint256 => string) public axlPeerId;
    mapping(uint256 => mapping(address => bytes)) private _usageAuthorizations;

    address public immutable phalaOracle;
    address public immutable ogStorage;
    address public keeper;

    uint256 private _nextTokenId = 1;

    event MetadataUpdated(uint256 indexed tokenId, bytes32 metadataHash, string encryptedURI);
    event UsageAuthorized(uint256 indexed tokenId, address indexed executor, bytes perms);

    constructor(
        string memory name,
        string memory symbol,
        address phalaOracleAddress,
        address ogStorageAddress
    ) ERC721(name, symbol) Ownable(msg.sender) {
        phalaOracle = phalaOracleAddress;
        ogStorage = ogStorageAddress;
        keeper = msg.sender;
    }

    modifier onlyKeeper() {
        require(msg.sender == keeper, "OrbittRegistry: keeper only");
        _;
    }

    function setKeeper(address newKeeper) external onlyOwner {
        require(newKeeper != address(0), "OrbittRegistry: zero keeper");
        keeper = newKeeper;
    }

    function mint(address to, string calldata encryptedURI, bytes32 metadataHash) external nonReentrant {
        require(to != address(0), "OrbittRegistry: mint to zero address");
        require(bytes(encryptedURI).length != 0, "OrbittRegistry: empty URI");
        require(metadataHash != bytes32(0), "OrbittRegistry: empty hash");

        uint256 tokenId = _nextTokenId++;
        _metadataHashes[tokenId] = metadataHash;
        _encryptedURIs[tokenId] = encryptedURI;

        _safeMint(to, tokenId);
        emit MetadataUpdated(tokenId, metadataHash, encryptedURI);
    }

    function transfer(
        address from,
        address to,
        uint256 tokenId,
        bytes calldata sealedKey,
        bytes calldata proof
    ) external nonReentrant {
        require(_isApprovedOrOwnerInternal(msg.sender, tokenId), "OrbittRegistry: not approved");
        require(to != address(0), "OrbittRegistry: transfer to zero address");
        require(sealedKey.length != 0, "OrbittRegistry: missing sealed key");
        require(proof.length != 0, "OrbittRegistry: missing proof");

        // GAP: integrate Phala TEE oracle re-encryption verification when spec is finalized.
        // Placeholder to avoid silently discarding ERC-7857 parameters.
        sealedKey;
        proof;

        _transfer(from, to, tokenId);
    }

    function updateReputation(uint256 tokenId, uint256 newScore) external onlyKeeper {
        require(_existsInternal(tokenId), "OrbittRegistry: token missing");
        require(newScore <= 1000, "OrbittRegistry: score too high");
        reputation[tokenId] = newScore;
    }

    function authorizeUsage(uint256 tokenId, address executor, bytes calldata perms) external {
        require(_isApprovedOrOwnerInternal(msg.sender, tokenId), "OrbittRegistry: not owner nor approved");
        require(executor != address(0), "OrbittRegistry: zero executor");
        require(perms.length != 0, "OrbittRegistry: empty perms");

        _usageAuthorizations[tokenId][executor] = perms;
        emit UsageAuthorized(tokenId, executor, perms);
    }

    function getAuthorization(uint256 tokenId, address executor) external view returns (bytes memory) {
        return _usageAuthorizations[tokenId][executor];
    }

    function _existsInternal(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }

    function _isApprovedOrOwnerInternal(address spender, uint256 tokenId) internal view returns (bool) {
        address owner = _ownerOf(tokenId);
        return (spender == owner || getApproved(tokenId) == spender || isApprovedForAll(owner, spender));
    }
}
