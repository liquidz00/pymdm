"""
Backward-compatible facade for MDM script parameter parsing.

Preserves the original ParamParser static-method API while delegating
to the Jamf-specific implementation in ``pymdm.mdm.jamf``. For Intune
or other providers, use ``pymdm.mdm.IntuneParamProvider`` directly or
``pymdm.mdm.get_provider()``.
"""

from .mdm.jamf import JamfParamParser

# Shared instance used by the static facade
_jamf_parser = JamfParamParser()


class ParamParser:
    """Helper class for parsing MDM script parameters.

    This class preserves full backward compatibility with the original
    Jamf-specific ParamParser. All static methods delegate to
    ``JamfParamParser`` internally.

    For cross-platform / multi-provider usage, prefer:
    - ``from pymdm.mdm import get_provider`` for auto-detection
    - ``from pymdm.mdm import JamfParamParser`` for explicit Jamf usage
    - ``from pymdm.mdm import IntuneParamProvider`` for explicit Intune usage
    """

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
        JamfParamParser._validate_index(index)

    @staticmethod
    def get(index: int) -> str | None:
        """Safely retrieve Jamf parameter by index."""
        return _jamf_parser.get(index)

    @staticmethod
    def get_bool(index: int) -> bool:
        """Get a Jamf parameter and convert to boolean."""
        return _jamf_parser.get_bool(index)

    @staticmethod
    def get_int(index: int, default: int = 0) -> int:
        """Get a Jamf parameter and convert to integer."""
        return _jamf_parser.get_int(index, default=default)
