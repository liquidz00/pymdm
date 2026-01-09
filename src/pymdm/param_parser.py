import sys


class ParamParser:
    """Helper class for parsing MDM script parameters."""

    # Jamf reserves parameters 0-3
    # $0 = Script name
    # $1 = Mount point of the target drive
    # $2 = Computer name
    # $3 = Username of logged in user
    _RESERVED_PARAMS = (0, 1, 2, 3)
    _MIN_USABLE_PARAM = 4
    _MAX_USABLE_PARAM = 11

    @staticmethod
    def _validate_index(index: int) -> None:
        """Validates the parameter index is usable."""
        if index in ParamParser._RESERVED_PARAMS:
            raise ValueError(
                f"Parameter ${index} is reserved by Jamf Pro and should not be used. "
                f"Use parameters ${ParamParser._MIN_USABLE_PARAM} - ${ParamParser._MAX_USABLE_PARAM} instead."
            )
        if index < ParamParser._MIN_USABLE_PARAM or index > ParamParser._MAX_USABLE_PARAM:
            raise ValueError(
                f"Parameter ${index} is out of usable range. "
                f"Use parameters ${ParamParser._MIN_USABLE_PARAM}-${ParamParser._MAX_USABLE_PARAM}."
            )

    @staticmethod
    def get(index: int) -> str | None:
        """Safely retrieve Jamf parameter by index."""
        ParamParser._validate_index(index)
        return sys.argv[index] if len(sys.argv) > index else None

    @staticmethod
    def get_bool(index: int) -> bool:
        """Get a Jamf parameter and convert to boolean."""
        ParamParser._validate_index(index)
        value = ParamParser.get(index)
        if not value:
            return False
        return value.strip().lower() in ("true", "1", "yes", "y")

    @staticmethod
    def get_int(index: int, default: int = 0) -> int:
        """Get a Jamf parameter and convert to integer."""
        ParamParser._validate_index(index)
        value = ParamParser.get(index)
        if not value:
            return default
        try:
            return int(value.strip())
        except ValueError:
            return default
