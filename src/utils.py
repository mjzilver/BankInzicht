from constants import Zakelijkheid


def format_month(period_str):
    year, month = period_str.split("-")
    dutch_months = [
        "Alle maanden",
        "januari",
        "februari",
        "maart",
        "april",
        "mei",
        "juni",
        "juli",
        "augustus",
        "september",
        "oktober",
        "november",
        "december",
    ]
    return f"{dutch_months[int(month)]} {year}"


def format_zakelijk(zakelijk):
    if zakelijk is True or zakelijk == 1:
        return Zakelijkheid.BUSINESS.value
    elif zakelijk is False or zakelijk == 0:
        return Zakelijkheid.NON_BUSINESS.value
