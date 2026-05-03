import { network } from "hardhat";
import { readFile } from "node:fs/promises";

const ENS_REGISTRY_ADDRESS = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e";
const PARENT_NAME = "0rbit.eth";

async function main() {
  await loadEnv();
  const { ethers } = await network.create();
  const [deployer] = await ethers.getSigners();

  const resolverAddress = process.env.ENS_RESOLVER_ADDRESS;
  const registryAddress = process.env.ORBITT_REGISTRY_ADDRESS;
  const keeperEnv = process.env.ENS_KEEPER_ADDRESS;
  const keeperAddress = keeperEnv && ethers.isAddress(keeperEnv) ? keeperEnv : deployer.address;

  if (!resolverAddress) {
    throw new Error("Missing ENS_RESOLVER_ADDRESS in contracts/.env");
  }
  if (!registryAddress) {
    throw new Error("Missing ORBITT_REGISTRY_ADDRESS in contracts/.env");
  }
  if (!ethers.isAddress(resolverAddress)) {
    throw new Error(`Invalid ENS_RESOLVER_ADDRESS: ${resolverAddress}`);
  }
  if (!ethers.isAddress(registryAddress)) {
    throw new Error(`Invalid ORBITT_REGISTRY_ADDRESS: ${registryAddress}`);
  }

  const parentNode = ethers.namehash(PARENT_NAME);

  console.log("Deployer:", deployer.address);
  console.log("ENS Registry:", ENS_REGISTRY_ADDRESS);
  console.log("ENS Resolver:", resolverAddress);
  console.log("OrbittRegistry:", registryAddress);
  console.log("Keeper:", keeperAddress);
  console.log("Parent node:", parentNode);

  const RegistrarFactory = await ethers.getContractFactory("OrbittSubnameRegistrar");
  const registrar = await RegistrarFactory.deploy(
    ENS_REGISTRY_ADDRESS,
    parentNode,
    resolverAddress,
    registryAddress,
    keeperAddress,
  );
  await registrar.waitForDeployment();

  console.log("OrbittSubnameRegistrar:", await registrar.getAddress());
}

async function loadEnv() {
  try {
    const envText = await readFile(".env", "utf8");
    for (const line of envText.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const [key, ...rest] = trimmed.split("=");
      if (!key) continue;
      const value = rest.join("=").trim();
      if (value && !process.env[key]) {
        process.env[key] = value;
      }
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.warn("Warning: could not load .env:", message);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
