"""CLI entrypoint for OrbitAgent per Section 14 Phase 4 Item 6."""

from __future__ import annotations

import argparse
import asyncio

from agents.plugins.orbit.agent import OrbitAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the 0rbit agent listener")
    parser.add_argument("--ens", required=True, help="Agent ENS name (e.g., worker.orbit.eth)")
    parser.add_argument("--peer-id", required=True, help="AXL peer id for this agent")
    parser.add_argument(
        "--capabilities",
        nargs="+",
        required=True,
        help="Capability slugs declared in the blueprint (e.g., code research design)",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="Backend API base URL for job discovery",
    )
    return parser.parse_args()


async def run_agent(args: argparse.Namespace) -> None:
    agent = OrbitAgent(args.ens, args.peer_id, args.capabilities, args.api_base)
    try:
        await agent.start()
    except asyncio.CancelledError:  # pragma: no cover - signal path
        raise
    except KeyboardInterrupt:
        await agent.stop()
    finally:
        await agent.stop()


def main() -> None:
    args = parse_args()
    asyncio.run(run_agent(args))


if __name__ == "__main__":
    main()
