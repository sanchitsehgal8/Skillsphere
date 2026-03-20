from typing import List

from pydantic import BaseModel

from app.models import JobDescription, JobRequirement


class RoleRequirementGraph(BaseModel):
    job: JobDescription
    core_requirements: List[JobRequirement]
    nice_to_have: List[JobRequirement]


class JobIntelligenceAgent:
   

    def build_role_graph(self, job_id: str, title: str, description: str) -> RoleRequirementGraph:
        text = f"{title}\n{description}".lower()

        
        core_keywords = [
            "python",
            "javascript",
            "typescript",
            "machine learning",
            "deep learning",
            "data engineering",
            "fastapi",
            "react",
            "llm",
        ]
        soft_keywords = [
            "communication",
            "ownership",
            "leadership",
            "mentorship",
            "collaboration",
        ]

        core: List[JobRequirement] = []
        nice: List[JobRequirement] = []

        for kw in core_keywords:
            if kw in text:
                core.append(JobRequirement(name=kw, weight=0.9, category="skill"))
        for kw in soft_keywords:
            if kw in text:
                nice.append(JobRequirement(name=kw, weight=0.6, category="soft-skill"))

        # Fallback: if nothing matched, create a generic requirement
        if not core:
            core.append(JobRequirement(name="problem solving", weight=0.8, category="soft-skill"))

        job = JobDescription(id=job_id, title=title, description=description, requirements=core + nice)
        return RoleRequirementGraph(job=job, core_requirements=core, nice_to_have=nice)
