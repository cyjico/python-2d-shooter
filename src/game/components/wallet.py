from dataclasses import dataclass


@dataclass(slots=True)
class Wallet:
    """Currency an entity carries."""

    balance: int = 800
    total_earned: int = 0
    """Everything earned so far, not counting the starting balance or spending."""

    def can_afford(self, amount: int):
        return self.balance >= amount

    def earn(self, amount: int):
        if amount < 0:
            raise ValueError(f"Cannot earn a negative amount ({amount})")
        self.balance += amount
        self.total_earned += amount

    def spend(self, amount: int):
        if not self.can_afford(amount):
            raise ValueError(f"Cannot afford {amount} with {self.balance}")
        self.balance -= amount
