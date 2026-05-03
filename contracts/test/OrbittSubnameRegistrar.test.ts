import { expect } from "chai";
import { network } from "hardhat";

const { ethers, networkHelpers } = await network.create();
const { loadFixture } = networkHelpers;

describe("OrbittSubnameRegistrar", function () {
  async function deployRegistrarFixture() {
    const [owner, agentOwner, keeper, other] = await ethers.getSigners();
    const parentNode = ethers.keccak256(ethers.toUtf8Bytes("orbitt.eth"));

    const ens = (await ethers.deployContract("MockENSRegistry")) as any;
    await ens.waitForDeployment();

    const resolver = (await ethers.deployContract("MockTextResolver")) as any;
    await resolver.waitForDeployment();

    const registry = (await ethers.deployContract("MockOrbittRegistry")) as any;
    await registry.waitForDeployment();

    const registrar = (await ethers.deployContract("OrbittSubnameRegistrar", [
      await ens.getAddress(),
      parentNode,
      await resolver.getAddress(),
      await registry.getAddress(),
      keeper.address,
    ])) as any;
    await registrar.waitForDeployment();

    const tokenId = 42n;
    await registry.setOwner(tokenId, agentOwner.address);
    await registry.setAxlPeerId(tokenId, "axl-peer-123");
    await registry.setReputation(tokenId, 880);

    return {
      owner,
      agentOwner,
      keeper,
      other,
      parentNode,
      ens,
      resolver,
      registry,
      registrar,
      tokenId,
    };
  }

  describe("register", function () {
    it("creates the subnode and sets text records", async function () {
      const { registrar, resolver, parentNode, agentOwner, tokenId } = await loadFixture(
        deployRegistrarFixture,
      );

      await registrar.connect(agentOwner).register("atlas", tokenId, ["code", "audit"]);

      const labelHash = ethers.keccak256(ethers.toUtf8Bytes("atlas"));
      const node = ethers.keccak256(ethers.solidityPacked(["bytes32", "bytes32"], [parentNode, labelHash]));

      expect(await resolver.text(node, "capabilities")).to.equal("code,audit");
      expect(await resolver.text(node, "reputation_score")).to.equal("880");
      expect(await resolver.text(node, "inft_token_id")).to.equal("42");
      expect(await resolver.text(node, "axl_peer_id")).to.equal("axl-peer-123");
    });
  });

  describe("setCapabilities", function () {
    it("restricts to owner and updates capabilities", async function () {
      const { registrar, resolver, parentNode, agentOwner, other, tokenId } = await loadFixture(
        deployRegistrarFixture,
      );

      await registrar.connect(agentOwner).register("atlas", tokenId, ["code"]);

      await expect(registrar.connect(other).setCapabilities("atlas", ["audit"]))
        .to.be.revertedWithCustomError(registrar, "OwnableUnauthorizedAccount")
        .withArgs(other.address);

      await registrar.setCapabilities("atlas", ["code", "audit"]);

      const labelHash = ethers.keccak256(ethers.toUtf8Bytes("atlas"));
      const node = ethers.keccak256(ethers.solidityPacked(["bytes32", "bytes32"], [parentNode, labelHash]));
      expect(await resolver.text(node, "capabilities")).to.equal("code,audit");
    });
  });

  describe("setReputationScore", function () {
    it("restricts to keeper and updates reputation", async function () {
      const { registrar, resolver, parentNode, agentOwner, other, tokenId, keeper } =
        await loadFixture(deployRegistrarFixture);

      await registrar.connect(agentOwner).register("atlas", tokenId, ["code"]);

      await expect(registrar.connect(other).setReputationScore("atlas", 777)).to.be.revertedWith(
        "OrbittSubnameRegistrar: keeper only",
      );

      await registrar.connect(keeper).setReputationScore("atlas", 777);

      const labelHash = ethers.keccak256(ethers.toUtf8Bytes("atlas"));
      const node = ethers.keccak256(ethers.solidityPacked(["bytes32", "bytes32"], [parentNode, labelHash]));
      expect(await resolver.text(node, "reputation_score")).to.equal("777");
    });
  });
});
