"""Toy coffee subscription (Stage S dry-run fixture). Not a real product."""
from dataclasses import dataclass
from datetime import date, timedelta

CYCLE_DAYS = 28            # one box every 4 weeks


@dataclass
class Subscription:
    id: int
    customer_email: str
    status: str            # "active" | "cancelled"
    next_ship: date
    next_charge: date      # charged 2 days before ship
    gift: bool = False     # bought for someone else, prepaid for N boxes
    boxes_left: int = 0    # only for gifts


def cancel(sub: Subscription) -> Subscription:
    sub.status = "cancelled"
    return sub


def advance(sub: Subscription) -> Subscription:
    """Called by the nightly job after a box ships."""
    sub.next_ship = sub.next_ship + timedelta(days=CYCLE_DAYS)
    sub.next_charge = sub.next_ship - timedelta(days=2)
    if sub.gift:
        sub.boxes_left -= 1
    return sub
