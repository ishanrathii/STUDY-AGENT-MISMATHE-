"""Brain teasers, logic puzzles, mental math — daily mind training."""
from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Puzzle:
    question: str
    answer: str
    hint: str | None = None


PUZZLES: list[Puzzle] = [
    Puzzle(
        "I am an odd number. Take away one letter and I become even. What number am I?",
        "Seven — remove 's' and you get 'even'.",
        "Think wordplay, not math.",
    ),
    Puzzle(
        "A bat and a ball together cost ₹110. The bat costs ₹100 more than the ball. How much does the ball cost?",
        "₹5. (Ball ₹5, bat ₹105 — difference ₹100.)",
        "Most people answer ₹10 — wrong. Set it up algebraically.",
    ),
    Puzzle(
        "If 5 machines take 5 minutes to make 5 widgets, how long do 100 machines take to make 100 widgets?",
        "5 minutes. Each machine makes 1 widget in 5 minutes — scaling doesn't change per-machine time.",
        None,
    ),
    Puzzle(
        "A lily pad doubles in size each day. On day 48 it covers the whole pond. On what day does it cover half?",
        "Day 47. Exponential growth — final doubling matters most.",
        "Think backwards.",
    ),
    Puzzle(
        "Calculate mentally: 25 × 17 × 4",
        "1700. Reorder: (25 × 4) × 17 = 100 × 17.",
        "Always look for hidden 100s.",
    ),
    Puzzle(
        "Which is bigger: 3^4 or 4^3?",
        "3^4 = 81, 4^3 = 64. So 3^4 wins.",
        None,
    ),
    Puzzle(
        "A man is twice as old as his son. Twenty years ago he was thrice as old. How old are they now?",
        "Father 80, son 40. (Solve: F = 2S and F-20 = 3(S-20).)",
        "Linear system in two variables.",
    ),
    Puzzle(
        "What's the smallest positive integer n such that 1 + 2 + ... + n > 1000?",
        "n = 45. (Sum = 45×46/2 = 1035.)",
        "Use n(n+1)/2.",
    ),
    Puzzle(
        "How many trailing zeros does 100! have?",
        "24. Count factors of 5: ⌊100/5⌋ + ⌊100/25⌋ = 20 + 4.",
        "Trailing zeros come from 10 = 2×5; 5s are the bottleneck.",
    ),
    Puzzle(
        "You have 8 coins, one is fake (lighter). With a balance scale, find it in 2 weighings.",
        "Split 3-3-2. Weigh the two 3s. If equal → fake is in the 2; if unequal → in the lighter 3. Then 1 more weighing.",
        "Classic 3-way split.",
    ),
]


def random_puzzle() -> Puzzle:
    return random.choice(PUZZLES)
