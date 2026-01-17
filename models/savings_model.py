from dataclasses import dataclass

@dataclass
class SavingsGoal:
    id: str           # Document ID in Firestore
    name: str
    target_amount: float
    current_amount: float
