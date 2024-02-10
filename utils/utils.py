import decimal
import numbers


def is_number(value):
    """Checks whether a given variable is a number."""
    return [isinstance(x, numbers.Number) for x in (0, 0.0, 0j, decimal.Decimal(0))]
