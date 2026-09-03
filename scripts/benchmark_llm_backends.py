"""Compare configured LLM backends on one fixed SkillRL-shaped prompt."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillstack.llm import LlmClient, load_backends, load_env_file


DEFAULT_BACKENDS = (
    "asu_glm_5_2",
    "asu_qwen3_235b_thinking_2507",
    "deepseek_v4_flash",
    "zhipu_glm_flashx",
)
BENCHMARK_PROMPT = """You update a reusable skill library from failed ALFWorld trajectories.

Task: Place two salt shakers in a drawer.
Failure trajectory summary:
- The agent opened a drawer and saw no salt shaker.
- It found one salt shaker and one pepper shaker on a countertop.
- It incorrectly picked up the pepper shaker.
- It continued searching and exhausted the step budget.

Existing skill: For two-object tasks, locate and collect both required objects before placement.

Identify the concrete failure cause and propose exactly two concise, non-duplicate reusable skills.
Return only valid JSON with this schema and no markdown:
{"skills":[{"title":"...","principle":"...","when_to_apply":"..."}]}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backends", nargs="+", default=list(DEFAULT_BACKENDS))
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=2048)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be at least 1")

    load_env_file()
    configured = load_backends()
    unknown = sorted(set(args.backends) - set(configured))
    if unknown:
        parser.error(f"unknown backend(s): {', '.join(unknown)}")

    with ThreadPoolExecutor(max_workers=len(args.backends)) as executor:
        futures = {
            executor.submit(
                _benchmark_backend,
                configured[name],
                args.repetitions,
                args.max_tokens,
            ): name
            for name in args.backends
        }
        backend_results = {}
        for future in as_completed(futures):
            name = futures[future]
            try:
                backend_results[name] = future.result()
            except Exception as error:  # retain per-provider failure evidence
                backend_results[name] = {
                    "backend": name,
                    "model": configured[name].model,
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "calls": [],
                }

    ordered = [backend_results[name] for name in args.backends]
    result = {
        "benchmark": "skillrl_shaped_backend_latency_v1",
        "prompt_sha256": hashlib.sha256(BENCHMARK_PROMPT.encode("utf-8")).hexdigest(),
        "temperature": 0,
        "max_tokens": args.max_tokens,
        "repetitions": args.repetitions,
        "cache_busting_repetition_id": True,
        "execution": "providers_concurrent; repetitions_sequential_within_provider",
        "results": ordered,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if all(item["status"] == "completed" for item in ordered) else 1


def _benchmark_backend(backend, repetitions: int, max_tokens: int):
    client = LlmClient(backend)
    calls = []
    for index in range(1, repetitions + 1):
        prompt = (
            f"{BENCHMARK_PROMPT}\nBenchmark repetition ID: {index}. "
            "This identifier does not change the task.\n"
        )
        started = time.monotonic()
        response = client.chat(
            [{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0,
        )
        end_to_end_latency = time.monotonic() - started
        content = response["content"]
        valid_json, valid_shape = _validate_content(content)
        usage = response["usage"]
        successful_attempt_latency = float(response["latency_seconds"])
        completion_tokens = int(usage.get("completion_tokens", 0))
        calls.append({
            "repetition": index,
            "latency_seconds": round(end_to_end_latency, 3),
            "successful_attempt_latency_seconds": successful_attempt_latency,
            "usage": usage,
            "completion_tokens_per_second": round(
                completion_tokens / end_to_end_latency, 3
            ) if end_to_end_latency else None,
            "estimated_personal_api_cost_usd": client.estimate_cost_usd(usage),
            "content_characters": len(content),
            "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "strict_json": valid_json,
            "expected_shape": valid_shape,
            "content_preview": content[:200],
        })

    latencies = [call["latency_seconds"] for call in calls]
    throughputs = [
        call["completion_tokens_per_second"]
        for call in calls
        if call["completion_tokens_per_second"] is not None
    ]
    return {
        "backend": backend.name,
        "model": backend.model,
        "status": "completed",
        "summary": {
            "median_latency_seconds": round(statistics.median(latencies), 3),
            "mean_latency_seconds": round(statistics.mean(latencies), 3),
            "min_latency_seconds": round(min(latencies), 3),
            "max_latency_seconds": round(max(latencies), 3),
            "mean_completion_tokens_per_second": round(statistics.mean(throughputs), 3),
            "strict_json_successes": sum(call["strict_json"] for call in calls),
            "expected_shape_successes": sum(call["expected_shape"] for call in calls),
            "total_estimated_personal_api_cost_usd": sum(
                call["estimated_personal_api_cost_usd"] for call in calls
            ),
        },
        "calls": calls,
    }


def _validate_content(content: str):
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return False, False
    skills = parsed.get("skills") if isinstance(parsed, dict) else None
    expected = (
        isinstance(skills, list)
        and len(skills) == 2
        and all(
            isinstance(skill, dict)
            and all(isinstance(skill.get(field), str) and skill[field].strip()
                    for field in ("title", "principle", "when_to_apply"))
            for skill in skills
        )
    )
    return True, expected


if __name__ == "__main__":
    raise SystemExit(main())
