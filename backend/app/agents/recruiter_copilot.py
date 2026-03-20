from typing import List

from app.models import JobDescription, CandidateProfile, SkillGraph, MatchScore, AuditLogEntry


class RecruiterCopilotAgent:
    """Natural language-ish interface surfacing insights.

    We don't call an LLM here to keep the system dependency-free;
    instead we generate structured explanations that read cleanly.
    """

    def summarize_candidate(
        self,
        candidate: CandidateProfile,
        graph: SkillGraph,
        match: MatchScore | None,
        audit: AuditLogEntry | None,
    ) -> str:
        lines: List[str] = []
        lines.append(f"Candidate: {candidate.name} ({candidate.id})")
        if candidate.headline:
            lines.append(f"Headline: {candidate.headline}")
        if candidate.summary:
            lines.append(f"Summary: {candidate.summary}")

        top_skills = sorted(graph.skills, key=lambda s: s.score, reverse=True)[:5]
        skills_str = ", ".join(f"{s.name} ({s.score:.2f})" for s in top_skills)
        lines.append(f"Top skills: {skills_str}")
        lines.append(f"Learning velocity: {graph.learning_velocity:.2f}")

        if match is not None:
            lines.append(f"Match score for job {match.job_id}: {match.score:.2f}")
            lines.append(f"Match rationale: {match.explanation}")
            if (
                match.time_to_productivity_pomodoros is not None
                and match.time_to_productivity_hours is not None
                and match.time_to_productivity_sprints is not None
            ):
                lines.append(
                    "Time-to-productivity (TTP) = focused effort before independent role-level output. "
                    f"Estimate: {match.time_to_productivity_pomodoros:.1f} pomodoros "
                    f"(~{match.time_to_productivity_hours:.1f} hours, "
                    f"~{match.time_to_productivity_sprints:.2f} sprints).",
                )
            if match.direct_matches:
                lines.append(
                    "Directly satisfied requirements: "
                    + ", ".join(sorted(set(match.direct_matches)))
                    + ".",
                )
            if match.adjacent_support:
                lines.append(
                    "Adjacency-based potential: "
                    + "; ".join(match.adjacent_support)
                    + ".",
                )

        if audit is not None and audit.bias_flags:
            reasons = "; ".join(f.reason for f in audit.bias_flags)
            lines.append(f"Bias audit flags: {reasons}")
        elif audit is not None:
            lines.append("Bias audit: no fairness concerns raised for this candidate.")

        return "\n".join(lines)

    def summarize_shortlist(
        self,
        job: JobDescription,
        candidates: List[CandidateProfile],
        graphs: List[SkillGraph],
        matches: List[MatchScore],
        audits: List[AuditLogEntry],
    ):
        by_id_candidate = {c.id: c for c in candidates}
        by_id_graph = {g.candidate_id: g for g in graphs}
        by_id_audit = {a.candidate_id: a for a in audits}

        lines: List[str] = []
        lines.append(f"Shortlist for role: {job.title} ({job.id})")
        lines.append("---")

        for rank, match in enumerate(matches, start=1):
            cand = by_id_candidate.get(match.candidate_id)
            graph = by_id_graph.get(match.candidate_id)
            audit = by_id_audit.get(match.candidate_id)
            if not cand or not graph:
                continue
            lines.append(f"Rank {rank}: {cand.name} - score {match.score:.2f}")
            lines.append(f"  Learning velocity: {graph.learning_velocity:.2f}")
            if (
                match.time_to_productivity_pomodoros is not None
                and match.time_to_productivity_hours is not None
                and match.time_to_productivity_sprints is not None
            ):
                lines.append(
                    "  TTP: "
                    f"{match.time_to_productivity_pomodoros:.1f} pomodoros "
                    f"(~{match.time_to_productivity_hours:.1f}h, "
                    f"~{match.time_to_productivity_sprints:.2f} sprints)",
                )
            if match.direct_matches:
                lines.append(
                    "  Direct: " + ", ".join(sorted(set(match.direct_matches))) + ".",
                )
            if match.adjacent_support:
                lines.append(
                    "  Adjacent support: " + "; ".join(match.adjacent_support) + ".",
                )
            if audit and audit.bias_flags:
                lines.append("  Bias flags present (see audit log).")
            lines.append("")

        return "\n".join(lines)
