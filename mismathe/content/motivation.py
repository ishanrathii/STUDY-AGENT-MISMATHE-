"""Motivational content — movies, documentaries, founders, lessons."""
from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Recommendation:
    title: str
    kind: str  # movie | doc | book | series
    why: str


CATALOG: list[Recommendation] = [
    Recommendation("3 Idiots", "movie", "Studying for love of learning vs studying for fear — what's your why?"),
    Recommendation("Super 30", "movie", "Anand Kumar — proof that no resource is too small if your conviction is huge."),
    Recommendation("The Pursuit of Happyness", "movie", "Discipline under crushing pressure. Watch when you want to quit."),
    Recommendation("Whiplash", "movie", "Obsession with excellence. Will you settle for 'good'?"),
    Recommendation("Soul", "movie", "Purpose isn't a thing to find — it's lived daily. Useful when overwhelmed."),
    Recommendation("Free Solo", "doc", "Alex Honnold prepares for years for a 4-hour climb. That's preparation."),
    Recommendation("The Last Dance", "doc", "MJ's obsession with the basics. Greatness = repetition + standards."),
    Recommendation("Steve Jobs (2015)", "movie", "Obsession + standards + identity. Becoming someone, not just doing something."),
    Recommendation("Atomic Habits — James Clear", "book", "Identity > goals. 'I am the type of person who studies daily.'"),
    Recommendation("Deep Work — Cal Newport", "book", "Concentration is the new IQ. Practice it like a muscle."),
    Recommendation("Can't Hurt Me — David Goggins", "book", "When the brain says quit at 40% — that's when the real work starts."),
    Recommendation("Make Time — Knapp & Zeratsky", "book", "Daily highlight + laser + reflect. Simple. Powerful."),
    Recommendation("The Social Dilemma", "doc", "Why your attention is the product. Build your dopamine immunity."),
]


def random_recommendation() -> Recommendation:
    return random.choice(CATALOG)


def by_kind(kind: str) -> list[Recommendation]:
    return [r for r in CATALOG if r.kind == kind]
