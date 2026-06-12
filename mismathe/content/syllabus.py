"""Maharashtra HSC + MHT-CET Class 11 syllabus reference.

Used for test generation, schedule planning, and weak-area mapping.
The student will provide their actual chapter list — this is the canonical
fallback. Update via /update_syllabus once the student shares their list.
"""
from __future__ import annotations


CLASS_11_SYLLABUS: dict[str, list[str]] = {
    "Physics": [
        "Units and Measurements",
        "Mathematical Methods",
        "Motion in a Plane",
        "Laws of Motion",
        "Gravitation",
        "Mechanical Properties of Solids",
        "Thermal Properties of Matter",
        "Sound",
        "Optics",
        "Electrostatics",
        "Semiconductor Devices",
    ],
    "Chemistry": [
        "Some Basic Concepts of Chemistry",
        "Structure of Atom",
        "Chemical Bonding",
        "Redox Reactions",
        "Elements of Group 1 and 2",
        "States of Matter (Gases & Liquids)",
        "Adsorption and Colloids",
        "Hydrocarbons",
        "Basic Principles of Organic Chemistry",
        "Nature of Chemical Bond",
        "Modern Periodic Table",
    ],
    "Mathematics": [
        "Angle and its Measurement",
        "Trigonometry I",
        "Trigonometry II",
        "Determinants and Matrices",
        "Straight Line",
        "Circle",
        "Conic Sections",
        "Measures of Dispersion",
        "Probability",
        "Complex Numbers",
        "Sequences and Series",
        "Permutations and Combinations",
        "Sets and Relations",
        "Functions",
        "Limits",
        "Continuity",
        "Differentiation",
    ],
}


# High-weightage chapters for MHT-CET (smart-priority engine reference)
HIGH_PRIORITY_CHAPTERS: dict[str, list[str]] = {
    "Physics": [
        "Electrostatics",
        "Optics",
        "Laws of Motion",
        "Gravitation",
        "Sound",
    ],
    "Chemistry": [
        "Some Basic Concepts of Chemistry",
        "Structure of Atom",
        "Chemical Bonding",
        "Hydrocarbons",
        "Redox Reactions",
    ],
    "Mathematics": [
        "Trigonometry I",
        "Trigonometry II",
        "Straight Line",
        "Circle",
        "Differentiation",
        "Probability",
        "Complex Numbers",
    ],
}


def all_chapters() -> dict[str, list[str]]:
    return CLASS_11_SYLLABUS


def subjects() -> list[str]:
    return list(CLASS_11_SYLLABUS.keys())


def chapters_for(subject: str) -> list[str]:
    return CLASS_11_SYLLABUS.get(subject, [])
