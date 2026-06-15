"""Class 11 PCM syllabus — your actual chapters with Maharashtra Board marks weightage.

Both columns from your textbook indexes are captured:
- "marks"             — base marks allotted in the paper
- "marks_with_option" — total marks counting questions WITH internal option

The priority engine sorts by "marks_with_option" — the higher the number,
the more weight that chapter carries and the more attention it deserves.

Updated 2026-06-13 from:
- Physics — 14 chapters
- Chemistry — 16 chapters
- Mathematics — 18 chapters (Part I: 9, Part II: 9)
"""
from __future__ import annotations

from typing import TypedDict


class Chapter(TypedDict):
    name: str
    marks: int
    marks_with_option: int


# Full chapter data — single source of truth.
CLASS_11_CHAPTERS: dict[str, list[Chapter]] = {
    "Physics": [
        {"name": "Units and Measurements", "marks": 5, "marks_with_option": 7},
        {"name": "Mathematical Methods", "marks": 5, "marks_with_option": 7},
        {"name": "Motion in a Plane", "marks": 6, "marks_with_option": 8},
        {"name": "Laws of Motion", "marks": 7, "marks_with_option": 10},
        {"name": "Gravitation", "marks": 5, "marks_with_option": 7},
        {"name": "Mechanical Properties of Solids", "marks": 4, "marks_with_option": 6},
        {"name": "Thermal Properties of Matter", "marks": 5, "marks_with_option": 7},
        {"name": "Sound", "marks": 5, "marks_with_option": 7},
        {"name": "Optics", "marks": 7, "marks_with_option": 10},
        {"name": "Electrostatics", "marks": 5, "marks_with_option": 7},
        {"name": "Electric Current Through Conductors", "marks": 4, "marks_with_option": 6},
        {"name": "Magnetism", "marks": 4, "marks_with_option": 6},
        {"name": "Electromagnetic Waves and Communication System", "marks": 4, "marks_with_option": 5},
        {"name": "Semiconductors", "marks": 4, "marks_with_option": 5},
    ],
    "Chemistry": [
        {"name": "Some Basic Concepts of Chemistry", "marks": 3, "marks_with_option": 5},
        {"name": "Introduction to Analytical Chemistry", "marks": 4, "marks_with_option": 6},
        {"name": "Basic Analytical Techniques", "marks": 2, "marks_with_option": 3},
        {"name": "Structure of Atom", "marks": 5, "marks_with_option": 7},
        {"name": "Chemical Bonding", "marks": 6, "marks_with_option": 8},
        {"name": "Redox Reaction", "marks": 3, "marks_with_option": 4},
        {"name": "Modern Periodic Table", "marks": 4, "marks_with_option": 6},
        {"name": "Elements of Group 1 and 2", "marks": 4, "marks_with_option": 6},
        {"name": "Elements of Group 13, 14 and 15", "marks": 6, "marks_with_option": 8},
        {"name": "States of Matter", "marks": 4, "marks_with_option": 6},
        {"name": "Adsorption and Colloids", "marks": 3, "marks_with_option": 4},
        {"name": "Chemical Equilibrium", "marks": 6, "marks_with_option": 8},
        {"name": "Nuclear Chemistry and Radioactivity", "marks": 3, "marks_with_option": 4},
        {"name": "Basic Principles of Organic Chemistry", "marks": 6, "marks_with_option": 8},
        {"name": "Hydrocarbons", "marks": 8, "marks_with_option": 11},
        {"name": "Chemistry in Everyday Life", "marks": 3, "marks_with_option": 4},
    ],
    "Mathematics": [
        # Part I
        {"name": "Angle and its Measurement", "marks": 3, "marks_with_option": 4},
        {"name": "Trigonometry - I", "marks": 4, "marks_with_option": 6},
        {"name": "Trigonometry - II", "marks": 6, "marks_with_option": 8},
        {"name": "Determinants and Matrices", "marks": 7, "marks_with_option": 10},
        {"name": "Straight Line", "marks": 4, "marks_with_option": 5},
        {"name": "Circle", "marks": 3, "marks_with_option": 4},
        {"name": "Conic Sections", "marks": 6, "marks_with_option": 8},
        {"name": "Measures of Dispersion", "marks": 4, "marks_with_option": 5},
        {"name": "Probability", "marks": 4, "marks_with_option": 6},
        # Part II
        {"name": "Complex Numbers", "marks": 4, "marks_with_option": 6},
        {"name": "Sequences and Series", "marks": 5, "marks_with_option": 7},
        {"name": "Permutations and Combinations", "marks": 6, "marks_with_option": 8},
        {"name": "Methods of Induction and Binomial Theorem", "marks": 5, "marks_with_option": 7},
        {"name": "Sets and Relations", "marks": 4, "marks_with_option": 6},
        {"name": "Functions", "marks": 4, "marks_with_option": 5},
        {"name": "Limits", "marks": 4, "marks_with_option": 6},
        {"name": "Continuity", "marks": 3, "marks_with_option": 5},
        {"name": "Differentiation", "marks": 4, "marks_with_option": 6},
    ],
}


# Backward-compatible name-only view used by older callers.
CLASS_11_SYLLABUS: dict[str, list[str]] = {
    subject: [c["name"] for c in chapters]
    for subject, chapters in CLASS_11_CHAPTERS.items()
}


def subjects() -> list[str]:
    return list(CLASS_11_CHAPTERS.keys())


def chapters_for(subject: str) -> list[str]:
    return [c["name"] for c in CLASS_11_CHAPTERS.get(subject, [])]


def chapter_marks(subject: str, chapter: str) -> Chapter | None:
    """Look up the marks weightage of a specific chapter."""
    for c in CLASS_11_CHAPTERS.get(subject, []):
        if c["name"].lower() == chapter.lower():
            return c
    return None


def top_priority(subject: str, n: int = 6) -> list[str]:
    """Top-N highest-marks chapters for a subject (priority engine)."""
    sorted_chapters = sorted(
        CLASS_11_CHAPTERS.get(subject, []),
        key=lambda c: c["marks_with_option"],
        reverse=True,
    )
    return [c["name"] for c in sorted_chapters[:n]]


# Pre-computed top-6 priority list per subject — what to focus on for max ROI.
HIGH_PRIORITY_CHAPTERS: dict[str, list[str]] = {
    subject: top_priority(subject, n=6) for subject in CLASS_11_CHAPTERS
}


def syllabus_text() -> str:
    """Render the full syllabus as a compact text block for the system prompt.

    Format:
      Physics — 14 chapters (marks / with-option):
        1. Units and Measurements  5/7
        ...
    """
    lines: list[str] = []
    for subject, chapters in CLASS_11_CHAPTERS.items():
        lines.append(f"{subject} — {len(chapters)} chapters (marks / with-option):")
        for i, c in enumerate(chapters, 1):
            lines.append(f"  {i:>2}. {c['name']}  {c['marks']}/{c['marks_with_option']}")
        lines.append("")
    return "\n".join(lines).strip()
