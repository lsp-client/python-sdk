from __future__ import annotations

from attrs import frozen

from .container import ContainerServer
from .local import LocalServer


@frozen
class DefaultServers:
    local: LocalServer
    container: ContainerServer
