#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

WEIGHTS = {
    0: 2, 1: 1, 2: 1, 3: 1, 4: 21, 5: 21, 6: 1, 7: 3, 8: 3, 9: 1,
    10: 1, 11: 1, 12: 8, 13: 8, 14: 2, 15: 1, 16: 34, 17: 21, 18: 1,
}
REQUIRED = {6, 8, 10}


def split_by_count(partitions):
    result = []
    for ptn in partitions:
        if len(ptn) <= 1:
            continue
        mid = (len(ptn) + 1) // 2
        result.extend([ptn[:mid], ptn[mid:]])
    return result


def split_by_weight(partitions, weights):
    """Paper Algorithm 1 weightedPartition: split each partition near half total weight."""
    result = []
    for ptn in partitions:
        if len(ptn) <= 1:
            continue
        target = sum(weights[x] for x in ptn) / 2.0
        prefix_weight = 0
        best_index = 1
        best_distance = float("inf")
        for index in range(1, len(ptn)):
            prefix_weight += weights[ptn[index - 1]]
            distance = abs(prefix_weight - target)
            if distance < best_distance:
                best_distance = distance
                best_index = index
        result.extend([ptn[:best_index], ptn[best_index:]])
    return result


def ensure_one_minimal(candidate, property_test, queries):
    """Paper Algorithm 1 final deletion pass."""
    changed = True
    while changed:
        changed = False
        for element in list(candidate):
            complement = candidate.copy()
            complement.remove(element)
            queries[0] += 1
            if property_test(complement):
                candidate = complement
                changed = True
                break
    return candidate


def minimize(elements, property_test, *, weighted, weights=None):
    """Small faithful model of Algorithm 1 and its unweighted ddmin-shaped baseline."""
    queries = [0]

    def recurse(partitions, current):
        while partitions:
            for ptn in partitions:
                queries[0] += 1
                if property_test(ptn):
                    next_partitions = (
                        split_by_weight([ptn], weights) if weighted else split_by_count([ptn])
                    )
                    return recurse(next_partitions, ptn.copy())

            for index, ptn in enumerate(partitions):
                complement = current.copy()
                for element in ptn:
                    if element in complement:
                        complement.remove(element)
                queries[0] += 1
                if property_test(complement):
                    remaining = partitions[:index] + partitions[index + 1 :]
                    return recurse(remaining, complement)

            partitions = (
                split_by_weight(partitions, weights) if weighted else split_by_count(partitions)
            )
        return current

    result = recurse([elements.copy()], elements.copy())
    if weighted:
        result = ensure_one_minimal(result, property_test, queries)
    return result, queries[0]


def paper_claim_audit():
    """Arithmetic/metadata audit only. It is L0, not L1."""
    claims = {
        "benchmarks": 62,
        "languages": ["C", "XML"],
        "wddmin_hdd_smaller_percent": 9.12,
        "wddmin_hdd_less_time_percent": 51.31,
        "wddmin_perses_smaller_percent": 0.96,
        "wddmin_perses_less_time_percent": 7.47,
        "wprobdd_hdd_smaller_percent": 13.40,
        "wprobdd_hdd_less_time_percent": 11.98,
        "wprobdd_perses_smaller_percent": 2.20,
        "wprobdd_perses_less_time_percent": 9.72,
        "probdd_repetitions": 5,
    }
    assert claims["benchmarks"] == 32 + 30
    assert claims["probdd_repetitions"] == 5
    return claims


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    elements = list(range(19))
    property_test = lambda xs: REQUIRED.issubset(set(xs))

    ddmin_result, ddmin_queries = minimize(elements, property_test, weighted=False)
    wdd_result, wdd_queries = minimize(elements, property_test, weighted=True, weights=WEIGHTS)
    uniform_result, uniform_queries = minimize(
        elements, property_test, weighted=True, weights={x: 1 for x in elements}
    )
    inverted_result, inverted_queries = minimize(
        elements,
        property_test,
        weighted=True,
        weights={x: max(WEIGHTS.values()) + 1 - WEIGHTS[x] for x in elements},
    )

    assert ddmin_result == sorted(REQUIRED)
    assert wdd_result == sorted(REQUIRED)
    assert uniform_result == sorted(REQUIRED)
    assert inverted_result == sorted(REQUIRED)
    assert wdd_queries < ddmin_queries

    summary = {
        "reproduction_level": "scoped L2 mechanism + L0 claim/artifact audit",
        "synthetic_case": {
            "elements": len(elements),
            "required_elements": sorted(REQUIRED),
            "total_weight": sum(WEIGHTS.values()),
            "ddmin": {"queries": ddmin_queries, "result": ddmin_result},
            "wddmin": {"queries": wdd_queries, "result": wdd_result},
            "wddmin_query_reduction_percent": round(
                100.0 * (ddmin_queries - wdd_queries) / ddmin_queries, 2
            ),
            "weight_ablation": {
                "true_weights_queries": wdd_queries,
                "uniform_weights_queries": uniform_queries,
                "inverted_weights_queries": inverted_queries,
            },
        },
        "paper_claims": paper_claim_audit(),
        "official_artifact": {
            "zenodo_doi": "10.5281/zenodo.14301983",
            "archive_md5": "2de412c8ba298e7ff861b2e293e11d11",
            "archive_size_mb": 320.4,
            "docker_image": "wddartifact/wdd:latest",
            "paper_scale_blocker": "full 62-case evaluation is explicitly documented as very long; ProbDD lanes require 5 repetitions",
        },
    }

    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
