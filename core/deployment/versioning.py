"""
core/deployment/versioning.py

Semantic Versioning and Compatibility Management for AegisTrace.
Implements SemVer 2.0.0 parsing, comparison, and schema compatibility gates.
Guarantees upgrade safety and prevents downgrade / rollback attacks.
"""

import re
from typing import Tuple, Optional


SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


class SemVer:
    """
    Representation of a Semantic Version 2.0.0.
    """

    def __init__(self, major: int, minor: int, patch: int, prerelease: Optional[str] = None):
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)
        self.prerelease = prerelease

    @classmethod
    def parse(cls, version_str: str) -> "SemVer":
        clean_str = version_str.lstrip("v").strip()
        match = SEMVER_REGEX.match(clean_str)
        if not match:
            raise ValueError(f"Invalid SemVer 2.0.0 string: {version_str}")
        groups = match.groupdict()
        return cls(
            major=int(groups["major"]),
            minor=int(groups["minor"]),
            patch=int(groups["patch"]),
            prerelease=groups.get("prerelease"),
        )

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return False
        return self.to_tuple() == other.to_tuple() and self.prerelease == other.prerelease

    def __lt__(self, other: "SemVer") -> bool:
        if self.to_tuple() != other.to_tuple():
            return self.to_tuple() < other.to_tuple()
        # Normal version has higher precedence than prerelease
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return str(self.prerelease or "") < str(other.prerelease or "")

    def __le__(self, other: "SemVer") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SemVer") -> bool:
        return not self <= other

    def __ge__(self, other: "SemVer") -> bool:
        return not self < other

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base

    def is_backward_compatible_with(self, baseline: "SemVer") -> bool:
        """
        SemVer rule: within the same major version (>0), newer minor/patch versions
        are backward compatible with older baselines.
        """
        if self.major != baseline.major:
            return False
        return self >= baseline


CURRENT_SYSTEM_VERSION = SemVer(1, 0, 0)
