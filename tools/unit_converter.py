from langchain_core.tools import tool

# Conversion tables: base unit → multiplier
_LENGTH = {
    "mm": 0.001, "cm": 0.01, "m": 1, "km": 1000,
    "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
    "ft": 0.3048, "feet": 0.3048, "foot": 0.3048,
    "yd": 0.9144, "yard": 0.9144, "yards": 0.9144,
    "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
}

_WEIGHT = {
    "mg": 0.001, "g": 1, "gram": 1, "grams": 1,
    "kg": 1000, "kilogram": 1000, "kilograms": 1000,
    "oz": 28.3495, "ounce": 28.3495, "ounces": 28.3495,
    "lb": 453.592, "lbs": 453.592, "pound": 453.592, "pounds": 453.592,
    "ton": 907185, "tons": 907185,
}

_VOLUME = {
    "ml": 0.001, "l": 1, "liter": 1, "liters": 1, "litre": 1, "litres": 1,
    "gal": 3.78541, "gallon": 3.78541, "gallons": 3.78541,
    "cup": 0.236588, "cups": 0.236588,
    "fl_oz": 0.0295735, "fluid_oz": 0.0295735,
    "pt": 0.473176, "pint": 0.473176, "pints": 0.473176,
    "qt": 0.946353, "quart": 0.946353, "quarts": 0.946353,
}

_CATEGORIES = {"length": _LENGTH, "weight": _WEIGHT, "volume": _VOLUME}


def _convert_temperature(value: float, from_u: str, to_u: str) -> float:
    # Normalize unit names
    aliases = {"c": "celsius", "f": "fahrenheit", "k": "kelvin"}
    from_u = aliases.get(from_u, from_u)
    to_u = aliases.get(to_u, to_u)

    # Convert to Celsius first
    if from_u == "fahrenheit":
        c = (value - 32) * 5 / 9
    elif from_u == "kelvin":
        c = value - 273.15
    else:
        c = value

    # Convert from Celsius to target
    if to_u == "fahrenheit":
        return c * 9 / 5 + 32
    elif to_u == "kelvin":
        return c + 273.15
    return c


@tool
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between units of measurement (length, weight, volume, temperature).

    Args:
        value: The numeric value to convert.
        from_unit: Source unit (e.g., "km", "lb", "celsius", "gallon").
        to_unit: Target unit (e.g., "miles", "kg", "fahrenheit", "liters").
    """
    from_u = from_unit.lower().strip()
    to_u = to_unit.lower().strip()

    # Temperature
    temp_units = {"c", "f", "k", "celsius", "fahrenheit", "kelvin"}
    if from_u in temp_units and to_u in temp_units:
        result = _convert_temperature(value, from_u, to_u)
        return f"{value} {from_unit} = {result:.2f} {to_unit}"

    # Find category
    for cat_name, table in _CATEGORIES.items():
        if from_u in table and to_u in table:
            # Convert: value * from_multiplier / to_multiplier
            result = value * table[from_u] / table[to_u]
            return f"{value} {from_unit} = {result:.4g} {to_unit}"

    return (
        f"Cannot convert '{from_unit}' to '{to_unit}'. "
        f"Supported: length (m, km, mi, ft, in), weight (g, kg, lb, oz), "
        f"volume (l, gal, cup, ml), temperature (C, F, K)."
    )
