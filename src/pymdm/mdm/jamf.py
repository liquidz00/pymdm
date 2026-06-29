"""
Jamf Pro MDM provider implementation.

Handles Jamf Pro-specific script parameter parsing. Jamf Pro passes
script parameters via sys.argv with parameters 0-3 reserved and
parameters 4-11 available for user-defined values.
"""

from __future__ import annotations

from ._base import GenericParamParser


class JamfParamParser(GenericParamParser):
    """
    Jamf Pro parameter parser.

    Jamf Pro reserves parameters 0-3:
    - $0 = Script name
    - $1 = Mount point of the target drive
    - $2 = Computer name
    - $3 = Username of logged in user

    User-defined parameters are $4 through $11 (indices 4-11 in sys.argv).

    Extends GenericParamParser with Jamf's reserved-index validation.
    """

    _RESERVED_PARAMS = (0, 1, 2, 3)
    _MIN_USABLE_PARAM = 4
    _MAX_USABLE_PARAM = 11

    @staticmethod
    def _validate_index(index: int) -> None:
        """
        Validates the parameter index is usable.

        :param index: Parameter index to validate
        :type index: int
        :raises ValueError: If index is reserved (0-3) or out of range
        """
        if index in JamfParamParser._RESERVED_PARAMS:
            raise ValueError(
                f"Parameter ${index} is reserved by Jamf Pro and should not be used. "
                f"Use parameters ${JamfParamParser._MIN_USABLE_PARAM} - ${JamfParamParser._MAX_USABLE_PARAM} instead."
            )
        if index < JamfParamParser._MIN_USABLE_PARAM or index > JamfParamParser._MAX_USABLE_PARAM:
            raise ValueError(
                f"Parameter ${index} is out of usable range. "
                f"Use parameters ${JamfParamParser._MIN_USABLE_PARAM}-${JamfParamParser._MAX_USABLE_PARAM}."
            )

    def get(self, key: int | str) -> str | None:
        """
        Safely retrieve Jamf parameter by index.

        :param key: Parameter index (must be int in range 4-11)
        :type key: int | str
        :return: Parameter value, or None if not provided
        :rtype: str | None
        :raises TypeError: If key is not an integer
        """
        if not isinstance(key, int):
            raise TypeError(
                f"Jamf parameter keys must be integers (got {type(key).__name__}). "
                f"Use an integer index between {self._MIN_USABLE_PARAM} and {self._MAX_USABLE_PARAM}."
            )
        self._validate_index(key)
        return super().get(key)
