// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IOracle {
    function verifyProof(bytes calldata proof) external view returns (bool);
}

contract MockOracle is IOracle {
    function verifyProof(bytes calldata) external pure returns (bool) {
        return true;
    }
}
