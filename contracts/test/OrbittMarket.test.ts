import { expect } from "chai";
import { network } from "hardhat";

const { ethers, networkHelpers } = await network.create();
const { loadFixture } = networkHelpers;

describe("OrbittMarket", function () {
  async function deployMarketFixture() {
    const [deployer, poster, agent, other] = await ethers.getSigners();
    const phalaOracle = ethers.Wallet.createRandom().address;
    const ogStorage = ethers.Wallet.createRandom().address;

    const registry = (await ethers.deployContract("OrbittRegistry", [
      "0rbit Agent Registry",
      "ORBT",
      phalaOracle,
      ogStorage,
    ])) as any;
    await registry.waitForDeployment();

    const market = (await ethers.deployContract("OrbittMarket")) as any;
    await market.waitForDeployment();
    await market.setRegistry(await registry.getAddress());

    const usdc = (await ethers.deployContract("MockUSDC", ["USD Coin", "USDC", 6])) as any;
    await usdc.waitForDeployment();

    return { deployer, poster, agent, other, registry, market, usdc };
  }

  async function postJobFixture() {
    const { deployer, poster, agent, other, registry, market, usdc } =
      await loadFixture(deployMarketFixture);

    const specHash = ethers.keccak256(ethers.toUtf8Bytes("job-spec"));
    const amount = 1_000_000n;
    const block = await ethers.provider.getBlock("latest");
    const deadline = BigInt((block?.timestamp ?? 0) + 3600);

    await usdc.mint(poster.address, amount);
    await usdc.connect(poster).approve(await market.getAddress(), amount);

    await market
      .connect(poster)
      .postJob(await usdc.getAddress(), amount, specHash, deadline);

    return {
      deployer,
      poster,
      agent,
      other,
      registry,
      market,
      usdc,
      specHash,
      amount,
      deadline,
    };
  }

  describe("postJob", function () {
    it("creates a job and escrows USDC", async function () {
      const { poster, market, usdc, amount, specHash, deadline } = await loadFixture(postJobFixture);

      expect(await market.jobCount()).to.equal(1n);

      const job = await market.jobs(1n);
      expect(job.id).to.equal(1n);
      expect(job.poster).to.equal(poster.address);
      expect(job.paymentToken).to.equal(await usdc.getAddress());
      expect(job.escrowAmount).to.equal(amount);
      expect(job.jobSpecHash).to.equal(specHash);
      expect(job.status).to.equal(0n);
      expect(job.deadline).to.equal(deadline);

      expect(await usdc.balanceOf(await market.getAddress())).to.equal(amount);
    });
  });

  describe("assignBid", function () {
    it("records the agent token and updates status", async function () {
      const { poster, market } = await loadFixture(postJobFixture);
      const agentTokenId = 1n;

      await market.connect(poster).assignBid(1n, agentTokenId);

      const job = await market.jobs(1n);
      expect(job.agentTokenId).to.equal(agentTokenId);
      expect(job.status).to.equal(1n);
    });
  });

  describe("submitOutput", function () {
    it("stores the output hash and marks complete", async function () {
      const { poster, agent, registry, market } = await loadFixture(postJobFixture);
      const metadataHash = ethers.keccak256(ethers.toUtf8Bytes("agent-metadata"));

      await registry.mint(agent.address, "phala://ciphertext", metadataHash);
      await market.connect(poster).assignBid(1n, 1n);

      const outputHash = ethers.keccak256(ethers.toUtf8Bytes("output"));
      const computeProof = ethers.hexlify(ethers.toUtf8Bytes("proof"));

      await market.connect(agent).submitOutput(1n, outputHash, computeProof);

      const job = await market.jobs(1n);
      expect(job.outputHash).to.equal(outputHash);
      expect(job.status).to.equal(3n);
    });
  });

  describe("releaseEscrow", function () {
    it("transfers USDC to the agent", async function () {
      const { deployer, poster, agent, registry, market, usdc, amount } = await loadFixture(
        postJobFixture,
      );

      const metadataHash = ethers.keccak256(ethers.toUtf8Bytes("agent-metadata"));
      await registry.mint(agent.address, "phala://ciphertext", metadataHash);
      await market.connect(poster).assignBid(1n, 1n);

      const outputHash = ethers.keccak256(ethers.toUtf8Bytes("output"));
      const computeProof = ethers.hexlify(ethers.toUtf8Bytes("proof"));
      await market.connect(agent).submitOutput(1n, outputHash, computeProof);

      const agentBalanceBefore = await usdc.balanceOf(agent.address);
      const marketBalanceBefore = await usdc.balanceOf(await market.getAddress());

      await market.connect(deployer).releaseEscrow(1n);

      const agentBalanceAfter = await usdc.balanceOf(agent.address);
      const marketBalanceAfter = await usdc.balanceOf(await market.getAddress());

      expect(agentBalanceAfter - agentBalanceBefore).to.equal(amount);
      expect(marketBalanceBefore - marketBalanceAfter).to.equal(amount);
      expect(marketBalanceAfter).to.equal(0n);
    });
  });

  describe("disputeJob", function () {
    it("moves job to disputed status", async function () {
      const { poster, market } = await loadFixture(postJobFixture);

      await market.connect(poster).disputeJob(1n);

      const job = await market.jobs(1n);
      expect(job.status).to.equal(4n);
    });
  });
});
