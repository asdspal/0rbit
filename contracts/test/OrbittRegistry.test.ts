import { expect } from "chai";
import { network } from "hardhat";

const { ethers, networkHelpers } = await network.create();
const { loadFixture } = networkHelpers;

describe("OrbittRegistry", function () {
  async function deployRegistryFixture() {
    const [deployer, agent, keeperCandidate, executor] = await ethers.getSigners();
    const phalaOracle = ethers.Wallet.createRandom().address;
    const ogStorage = ethers.Wallet.createRandom().address;

    const registry = await ethers.deployContract("OrbittRegistry", [
      "0rbit Agent Registry",
      "ORBT",
      phalaOracle,
      ogStorage,
    ]);

    await registry.waitForDeployment();

    return { registry, deployer, agent, keeperCandidate, executor, phalaOracle, ogStorage };
  }

  describe("constructor", function () {
    it("initializes immutable addresses and metadata", async function () {
      const { registry, deployer, phalaOracle, ogStorage } = await loadFixture(deployRegistryFixture);

      expect(await registry.name()).to.equal("0rbit Agent Registry");
      expect(await registry.symbol()).to.equal("ORBT");
      expect(await registry.phalaOracle()).to.equal(phalaOracle);
      expect(await registry.ogStorage()).to.equal(ogStorage);
      expect(await registry.keeper()).to.equal(deployer.address);
    });
  });

  describe("mint", function () {
    it("mints a token and records metadata details", async function () {
      const { registry, agent } = await loadFixture(deployRegistryFixture);
      const metadataHash = ethers.keccak256(ethers.toUtf8Bytes("agent-metadata"));
      const encryptedURI = "phala://ciphertext";

      await expect(registry.mint(agent.address, encryptedURI, metadataHash))
        .to.emit(registry, "MetadataUpdated")
        .withArgs(1n, metadataHash, encryptedURI);

      expect(await registry.balanceOf(agent.address)).to.equal(1n);
      expect(await registry.ownerOf(1n)).to.equal(agent.address);
    });
  });

  describe("updateReputation", function () {
    it("enforces onlyKeeper modifier and updates score", async function () {
      const { registry, agent } = await loadFixture(deployRegistryFixture);
      const metadataHash = ethers.keccak256(ethers.toUtf8Bytes("agent-metadata"));
      await registry.mint(agent.address, "phala://ciphertext", metadataHash);

      await expect(registry.connect(agent).updateReputation(1n, 600)).to.be.revertedWith(
        "OrbittRegistry: keeper only",
      );

      await registry.updateReputation(1n, 725);
      expect(await registry.reputation(1n)).to.equal(725n);
    });
  });

  describe("authorizeUsage", function () {
    it("stores executor permissions and emits UsageAuthorized", async function () {
      const { registry, agent, executor } = await loadFixture(deployRegistryFixture);
      const metadataHash = ethers.keccak256(ethers.toUtf8Bytes("agent-metadata"));
      await registry.mint(agent.address, "phala://ciphertext", metadataHash);

      const perms = ethers.hexlify(ethers.toUtf8Bytes("run:inference"));

      await expect(registry.connect(agent).authorizeUsage(1n, executor.address, perms))
        .to.emit(registry, "UsageAuthorized")
        .withArgs(1n, executor.address, perms);

      expect(await registry.getAuthorization(1n, executor.address)).to.equal(perms);
    });
  });
});
