"""
pymdm.mdm - MDM provider abstraction layer.

Provides provider-specific implementations for script parameter parsing
and MDM-specific operations. Auto-detects or allows explicit selection
of the MDM provider (Jamf Pro, Intune, etc.).
"""

from ._base import GenericParamParser, MdmParamParser, get_provider
from .intune import IntuneParamParser
from .jamf import JamfParamParser

__all__ = [
    "GenericParamParser",
    "IntuneParamParser",
    "JamfParamParser",
    "MdmParamParser",
    "get_provider",
]
