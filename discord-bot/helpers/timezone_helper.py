import pycountry
from pytz import country_timezones


def get_timezones(string: str) -> list | None:
    try:
        country_obj = pycountry.countries.lookup(string)
    except LookupError:
        return None

    country_code = country_obj.alpha_2
    return country_timezones.get(country_code)


def country_to_timezone(string: str) -> str | None:
    try:
        country_obj = pycountry.countries.lookup(string)
    except LookupError:
        return None

    country_code = country_obj.alpha_2
    timezones = country_timezones.get(country_code)
    return timezones[0] if timezones else None
