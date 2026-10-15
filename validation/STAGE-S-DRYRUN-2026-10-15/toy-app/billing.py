"""Toy billing (Stage S dry-run fixture)."""
from datetime import date


def charge_due(subs, today: date):
    """Nightly: every active sub whose next_charge is today gets charged via the card on file."""
    return [s for s in subs if s.status == "active" and s.next_charge == today]


def on_card_declined(sub):
    """Three retries, one per day, then the sub is cancelled and an email goes out."""
    ...
