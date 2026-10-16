def to_dkk(amount, currency, day, rates):
    rate = rates.get((day.strftime("%Y-%m"), currency))
    if rate is None:
        return None
    return amount * rate
