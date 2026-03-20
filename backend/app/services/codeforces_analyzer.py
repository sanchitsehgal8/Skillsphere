from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev
from typing import Any

import requests


CODEFORCES_API = "https://codeforces.com/api"


def _api(path: str, params: dict[str, Any]) -> Any:
    response = requests.get(f"{CODEFORCES_API}/{path}", params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "OK":
        raise ValueError(data.get("comment") or "Codeforces API request failed")
    return data.get("result")


def _bucket_label(rating: int) -> str:
    if rating < 1200:
        return "800-1199"
    if rating < 1600:
        return "1200-1599"
    if rating < 2000:
        return "1600-1999"
    if rating < 2400:
        return "2000-2399"
    if rating < 2800:
        return "2400-2799"
    return "2800+"


def analyze_codeforces_handle(handle: str) -> dict[str, Any]:
    info = _api("user.info", {"handles": handle})[0]
    submissions = _api("user.status", {"handle": handle, "from": 1, "count": 5000})
    rating_history = _api("user.rating", {"handle": handle})

    current_rating = int(info.get("rating") or 0)
    max_rating = int(info.get("maxRating") or current_rating)
    rank_title = (info.get("rank") or "unrated").replace("_", " ").title()

    submission_count = len(submissions)
    accepted = [s for s in submissions if s.get("verdict") == "OK"]
    accepted_count = len(accepted)
    acceptance_rate = (accepted_count / submission_count * 100.0) if submission_count else 0.0

    solved_set = {
        (
            s.get("problem", {}).get("contestId"),
            s.get("problem", {}).get("index"),
            s.get("problem", {}).get("name"),
        )
        for s in accepted
    }
    total_solved = len(solved_set)

    # Contest stats
    contest_count = len(rating_history)
    ranks = [int(c.get("rank") or 0) for c in rating_history if c.get("rank")]

    # Proxy percentile: relative to the user's own contest history (honest approximation)
    if ranks:
        rank_percentiles = [sum(1 for r2 in ranks if r2 >= r) / len(ranks) * 100.0 for r in ranks]
        avg_rank_percentile = mean(rank_percentiles)
    else:
        avg_rank_percentile = 0.0

    # Difficulty + tags
    attempted_by_bucket: Counter[str] = Counter()
    accepted_by_bucket: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()

    for s in submissions:
        p = s.get("problem", {})
        rating = p.get("rating")
        if isinstance(rating, int):
            bucket = _bucket_label(rating)
            attempted_by_bucket[bucket] += 1
            if s.get("verdict") == "OK":
                accepted_by_bucket[bucket] += 1

    for s in accepted:
        tags = s.get("problem", {}).get("tags") or []
        for t in tags:
            tag_counter[t] += 1

    comfort_zone = "unknown"
    if accepted_by_bucket:
        comfort_zone = accepted_by_bucket.most_common(1)[0][0]

    struggle_zone = "unknown"
    weakest = []
    for bucket, attempted in attempted_by_bucket.items():
        if attempted < 5:
            continue
        acc = accepted_by_bucket.get(bucket, 0)
        weak_score = acc / attempted if attempted else 0.0
        weakest.append((weak_score, bucket))
    if weakest:
        weakest.sort(key=lambda x: x[0])
        struggle_zone = weakest[0][1]

    top_tags = [t for t, _ in tag_counter.most_common(8)]

    canonical_tags = [
        "dp",
        "graphs",
        "greedy",
        "math",
        "binary search",
        "implementation",
        "data structures",
        "number theory",
        "strings",
        "constructive algorithms",
    ]
    attempted_tags = set(tag_counter.keys())
    tag_gaps = [t for t in canonical_tags if t not in attempted_tags][:5]

    # Contest trajectory + volatility
    deltas = [int(c.get("newRating", 0)) - int(c.get("oldRating", 0)) for c in rating_history]
    best_delta = max(deltas) if deltas else 0
    worst_delta = min(deltas) if deltas else 0

    if len(rating_history) >= 8:
        first_avg = mean(int(x.get("newRating") or 0) for x in rating_history[:5])
        last_avg = mean(int(x.get("newRating") or 0) for x in rating_history[-5:])
        drift = last_avg - first_avg
        if drift > 40:
            trajectory = "rising"
        elif drift < -40:
            trajectory = "declining"
        else:
            trajectory = "plateauing"
    elif len(rating_history) >= 2:
        drift = int(rating_history[-1].get("newRating") or 0) - int(rating_history[0].get("oldRating") or 0)
        trajectory = "rising" if drift > 0 else "declining" if drift < 0 else "plateauing"
    else:
        trajectory = "insufficient-data"

    volatility = pstdev(deltas) if len(deltas) >= 2 else 0.0
    consistency_score = max(0.0, min(100.0, 100.0 - volatility * 1.5))
    if consistency_score >= 75:
        stability_label = "stable"
    elif consistency_score >= 45:
        stability_label = "moderately-volatile"
    else:
        stability_label = "volatile"

    # Honest mentor-style verdict
    strongest = top_tags[:3] if top_tags else ["implementation"]
    blockers = []
    if tag_gaps:
        blockers.append(f"tag gaps in {', '.join(tag_gaps[:3])}")
    if struggle_zone != "unknown":
        blockers.append(f"low conversion in {struggle_zone}")
    if contest_count < 10:
        blockers.append("limited contest volume")

    habit_signal = "improvement-focused"
    if trajectory in {"plateauing", "declining"} and comfort_zone in {"800-1199", "1200-1599"}:
        habit_signal = "comfort-zone stuck"

    rating_vs_habits = (
        f"Rating suggests {rank_title.lower()} level, while solve patterns center around {comfort_zone}."
        ""
    )

    return {
        "handle": handle,
        "stats_overview": {
            "current_rating": current_rating,
            "max_rating": max_rating,
            "rank_title": rank_title,
            "total_problems_solved": total_solved,
            "submission_count": submission_count,
            "acceptance_rate": round(acceptance_rate, 2),
            "contest_participation_count": contest_count,
            "average_rank_percentile": round(avg_rank_percentile, 2),
            "average_rank_percentile_note": "Percentile is a self-history percentile proxy due public API limits.",
        },
        "problem_solving_profile": {
            "difficulty_distribution": {
                "attempted": dict(attempted_by_bucket),
                "accepted": dict(accepted_by_bucket),
            },
            "most_practiced_tags": top_tags,
            "comfort_zone": comfort_zone,
            "struggle_zone": struggle_zone,
            "tag_gaps": tag_gaps,
        },
        "contest_performance": {
            "rating_trajectory": trajectory,
            "best_contest_delta": best_delta,
            "worst_contest_delta": worst_delta,
            "consistency_score": round(consistency_score, 2),
            "stability": stability_label,
        },
        "honest_skill_verdict": {
            "genuinely_good_at": strongest,
            "holding_back": blockers or ["needs broader high-difficulty exposure"],
            "rating_vs_habits": rating_vs_habits,
            "improvement_signal": habit_signal,
            "mentor_summary": (
                f"Strongest in {', '.join(strongest)}. "
                f"Main blockers: {', '.join(blockers) if blockers else 'broaden high-difficulty practice'}. "
                f"Current trajectory is {trajectory} with {stability_label} contest consistency."
            ),
        },
    }
