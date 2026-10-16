PERILS = ["fire", "flood", "hail", "storm", "subsidence"]
COUNTED_STATUSES = ("settled", "open")


def incurred(status, paid, reserve):
    # A settled claim can still show a reserve. We ignore it.
    if status == "settled":
        return paid
    if status == "open":
        return paid + reserve
    return 0.0
