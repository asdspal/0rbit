// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MockENSRegistry {
    bytes32 public lastParent;
    bytes32 public lastLabel;
    address public lastOwner;
    address public lastResolver;
    uint64 public lastTtl;

    mapping(bytes32 => address) public owner;
    mapping(bytes32 => address) public resolver;

    function setSubnodeRecord(
        bytes32 node,
        bytes32 label,
        address owner_,
        address resolver_,
        uint64 ttl
    ) external {
        bytes32 subnode = keccak256(abi.encodePacked(node, label));
        owner[subnode] = owner_;
        resolver[subnode] = resolver_;
        lastParent = node;
        lastLabel = label;
        lastOwner = owner_;
        lastResolver = resolver_;
        lastTtl = ttl;
    }
}

contract MockTextResolver {
    mapping(bytes32 => mapping(string => string)) private _text;

    function setText(bytes32 node, string calldata key, string calldata value) external {
        _text[node][key] = value;
    }

    function text(bytes32 node, string calldata key) external view returns (string memory) {
        return _text[node][key];
    }
}

contract MockOrbittRegistry {
    mapping(uint256 => address) private _owners;
    mapping(uint256 => address) private _approved;
    mapping(address => mapping(address => bool)) private _operatorApproval;
    mapping(uint256 => string) private _axlPeerId;
    mapping(uint256 => uint256) private _reputation;

    function setOwner(uint256 tokenId, address owner_) external {
        _owners[tokenId] = owner_;
    }

    function setApproved(uint256 tokenId, address operator) external {
        _approved[tokenId] = operator;
    }

    function setApprovalForAll(address owner_, address operator, bool approved) external {
        _operatorApproval[owner_][operator] = approved;
    }

    function setAxlPeerId(uint256 tokenId, string calldata peerId) external {
        _axlPeerId[tokenId] = peerId;
    }

    function setReputation(uint256 tokenId, uint256 score) external {
        _reputation[tokenId] = score;
    }

    function ownerOf(uint256 tokenId) external view returns (address) {
        return _owners[tokenId];
    }

    function getApproved(uint256 tokenId) external view returns (address) {
        return _approved[tokenId];
    }

    function isApprovedForAll(address owner_, address operator) external view returns (bool) {
        return _operatorApproval[owner_][operator];
    }

    function axlPeerId(uint256 tokenId) external view returns (string memory) {
        return _axlPeerId[tokenId];
    }

    function reputation(uint256 tokenId) external view returns (uint256) {
        return _reputation[tokenId];
    }
}
