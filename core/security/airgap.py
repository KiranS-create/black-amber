"""
core/security/airgap.py

Network Egress Guard and Air-Gap Enforcement for AegisTrace.
Guarantees that when running in air-gapped / isolated mode, zero outbound
network connections can be established to external hosts.
Intercepts low-level socket connections and DNS resolution to ensure fail-closed
isolation, while permitting essential local inter-process loopback (127.0.0.1 / localhost).
"""

import os
import socket
from contextlib import contextmanager
from typing import Optional, Set, Tuple, Any, Callable


class AirgapViolationError(RuntimeError):
    """Raised when an outbound network connection is attempted in air-gap mode."""
    pass


# Allowed loopback destinations
LOOPBACK_HOSTS: Set[str] = {
    "127.0.0.1",
    "::1",
    "localhost",
    "0.0.0.0",
    "::",
}


def is_loopback(host: str) -> bool:
    """Check if host is an allowed local loopback or local binding address."""
    if not host:
        return True
    host_clean = host.strip().lower()
    if host_clean in LOOPBACK_HOSTS:
        return True
    if host_clean.startswith("127."):
        return True
    return False


class NetworkEgressGuard:
    """
    Enforces air-gap network policy by intercepting socket operations.
    """

    _original_connect: Optional[Callable] = None
    _original_create_connection: Optional[Callable] = None
    _original_getaddrinfo: Optional[Callable] = None
    _installed: bool = False

    @classmethod
    def is_installed(cls) -> bool:
        return cls._installed

    @classmethod
    def install(cls) -> None:
        """Install socket hooks blocking external egress."""
        if cls._installed:
            return

        cls._original_connect = socket.socket.connect
        cls._original_create_connection = socket.create_connection
        cls._original_getaddrinfo = socket.getaddrinfo

        orig_connect = cls._original_connect
        orig_create_conn = cls._original_create_connection
        orig_getaddrinfo = cls._original_getaddrinfo

        def hooked_connect(sock_self, address, *args, **kwargs):
            host = None
            port = None
            if isinstance(address, tuple) and len(address) >= 2:
                host = str(address[0])
                port = address[1]
            elif isinstance(address, str):
                # Unix socket or path
                return orig_connect(sock_self, address, *args, **kwargs)

            if host and not is_loopback(host):
                raise AirgapViolationError(
                    f"Egress blocked in air-gap mode: attempt to connect to external host '{host}:{port}'"
                )
            return orig_connect(sock_self, address, *args, **kwargs)

        def hooked_create_connection(address, *args, **kwargs):
            host = str(address[0]) if isinstance(address, tuple) else str(address)
            if not is_loopback(host):
                raise AirgapViolationError(
                    f"Egress blocked in air-gap mode: attempt to create connection to external host '{host}'"
                )
            return orig_create_conn(address, *args, **kwargs)

        def hooked_getaddrinfo(host, port, *args, **kwargs):
            if host and not is_loopback(str(host)):
                raise AirgapViolationError(
                    f"DNS/Resolution blocked in air-gap mode: attempt to resolve external host '{host}'"
                )
            return orig_getaddrinfo(host, port, *args, **kwargs)

        socket.socket.connect = hooked_connect
        socket.create_connection = hooked_create_connection
        socket.getaddrinfo = hooked_getaddrinfo
        cls._installed = True

    @classmethod
    def uninstall(cls) -> None:
        """Restore original socket functions."""
        if not cls._installed:
            return

        if cls._original_connect:
            socket.socket.connect = cls._original_connect
        if cls._original_create_connection:
            socket.create_connection = cls._original_create_connection
        if cls._original_getaddrinfo:
            socket.getaddrinfo = cls._original_getaddrinfo

        cls._installed = False


@contextmanager
def enforce_airgap():
    """
    Context manager to enforce airgap mode during code execution.
    """
    already_installed = NetworkEgressGuard.is_installed()
    if not already_installed:
        NetworkEgressGuard.install()
    try:
        yield
    finally:
        if not already_installed:
            NetworkEgressGuard.uninstall()


# Automatically activate if environment variable is set
if os.environ.get("AEGISTRACE_AIRGAP_MODE", "").strip().lower() in ("1", "true", "yes") or \
   os.environ.get("AEGISTRACE_ENFORCE_AIRGAP", "").strip().lower() in ("1", "true", "yes"):
    NetworkEgressGuard.install()
