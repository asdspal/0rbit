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

    address public immutable phalaOracle;
    address public immutable ogStorage;

    constructor(
        string memory name,
        string memory symbol,
        address phalaOracleAddress,
        address ogStorageAddress
    ) ERC721(name, symbol) Ownable(msg.sender) {
        phalaOracle = phalaOracleAddress;
        ogStorage = ogStorageAddress;
    }
}
