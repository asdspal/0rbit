import { network } from "hardhat";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

async function main() {
  await loadEnv();
  const ogStorageAddress = process.env.OG_STORAGE_ADDRESS;

  if (!ogStorageAddress) {
    throw new Error("Missing OG_STORAGE_ADDRESS in contracts/.env");
  }

  const { ethers } = await network.create();
  const [deployer] = await ethers.getSigners();
  console.log("Deployer:", deployer.address);

  const OracleFactory = await ethers.getContractFactory("MockOracle");
  const oracle = await OracleFactory.deploy();
  await oracle.waitForDeployment();

  const RegistryFactory = await ethers.getContractFactory("OrbittRegistry");
  const registry = await RegistryFactory.deploy(
    "0rbit Agent Registry",
    "ORBT",
    await oracle.getAddress(),
    ogStorageAddress
  );
  await registry.waitForDeployment();

  const MarketFactory = await ethers.getContractFactory("OrbittMarket");
  const market = await MarketFactory.deploy();
  await market.waitForDeployment();

  await (await (market as any).setRegistry(await registry.getAddress())).wait();

  const oracleAddress = await oracle.getAddress();
  const registryAddress = await registry.getAddress();
  const marketAddress = await market.getAddress();

  console.log("MockOracle:", oracleAddress);
  console.log("OrbittRegistry:", registryAddress);
  console.log("OrbittMarket:", marketAddress);

  const deploymentsDir = join("deployments");
  await mkdir(deploymentsDir, { recursive: true });
  await writeFile(
    join(deploymentsDir, "0g-testnet.json"),
    JSON.stringify(
      {
        network: "0gTestnet",
        chainId: 16602,
        mockOracle: oracleAddress,
        orbittRegistry: registryAddress,
        orbittMarket: marketAddress,
      },
      null,
      2
    )
  );
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
