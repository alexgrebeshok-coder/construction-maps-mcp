"""Validators for cadastral numbers, coordinates, etc."""

import re
from typing import Tuple


def validate_cadastral_number(cadastral_number: str) -> bool:
    """
    Validate Russian cadastral number format.

    Format: XX:XX:XXXXXXX:XXXX (Region:District:Quarter:Parcel)

    Args:
        cadastral_number: Cadastral number string

    Returns:
        True if valid format, False otherwise
    """
    # Pattern: 2 digits : 2 digits : 7 digits : 1+ digits
    pattern = r"^\d{2}:\d{2}:\d{7}:\d+$"
    return bool(re.match(pattern, cadastral_number))


def validate_coordinates(lon: float, lat: float) -> bool:
    """
    Validate geographic coordinates.

    Args:
        lon: Longitude
        lat: Latitude

    Returns:
        True if coordinates are valid
    """
    return -180 <= lon <= 180 and -90 <= lat <= 90


def normalize_cadastral_number(cadastral_number: str) -> str:
    """
    Normalize cadastral number by removing extra spaces and converting to standard format.

    Args:
        cadastral_number: Raw cadastral number

    Returns:
        Normalized cadastral number
    """
    # Remove all spaces
    normalized = cadastral_number.replace(" ", "").replace("\t", "")

    # Replace various separators with colon
    for sep in ["-", "/", ".", ","]:
        normalized = normalized.replace(sep, ":")

    return normalized


def parse_cadastral_parts(cadastral_number: str) -> Tuple[int, int, int, int]:
    """
    Parse cadastral number into its components.

    Args:
        cadastral_number: Cadastral number in format XX:XX:XXXXXXX:XXXX

    Returns:
        Tuple of (region, district, quarter, parcel)

    Raises:
        ValueError: If cadastral number format is invalid
    """
    if not validate_cadastral_number(cadastral_number):
        raise ValueError(f"Invalid cadastral number format: {cadastral_number}")

    parts = cadastral_number.split(":")
    return int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])


def format_cadastral_number(region: int, district: int, quarter: int, parcel: int) -> str:
    """
    Format cadastral number components into standard string.

    Args:
        region: Region code (2 digits)
        district: District code (2 digits)
        quarter: Quarter code (7 digits)
        parcel: Parcel code (variable length)

    Returns:
        Formatted cadastral number
    """
    return f"{region:02d}:{district:02d}:{quarter:07d}:{parcel}"
