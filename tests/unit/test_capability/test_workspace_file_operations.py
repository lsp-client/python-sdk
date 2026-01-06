from __future__ import annotations

from lsp_client.capability.build import build_client_capabilities
from lsp_client.capability.notification.did_create_files import WithNotifyDidCreateFiles
from lsp_client.capability.notification.did_delete_files import WithNotifyDidDeleteFiles
from lsp_client.capability.notification.did_rename_files import WithNotifyDidRenameFiles
from lsp_client.capability.request.will_create_files import WithRequestWillCreateFiles
from lsp_client.capability.request.will_delete_files import WithRequestWillDeleteFiles
from lsp_client.capability.request.will_rename_files import WithRequestWillRenameFiles


def test_mixin_did_create_files():
    class Client(WithNotifyDidCreateFiles):
        pass

    capabilities = build_client_capabilities(Client)
    assert capabilities.workspace is not None
    assert capabilities.workspace.file_operations is not None
    assert capabilities.workspace.file_operations.did_create is True


def test_mixin_did_rename_files():
    class Client(WithNotifyDidRenameFiles):
        pass

    capabilities = build_client_capabilities(Client)
    assert capabilities.workspace is not None
    assert capabilities.workspace.file_operations is not None
    assert capabilities.workspace.file_operations.did_rename is True


def test_mixin_did_delete_files():
    class Client(WithNotifyDidDeleteFiles):
        pass

    capabilities = build_client_capabilities(Client)
    assert capabilities.workspace is not None
    assert capabilities.workspace.file_operations is not None
    assert capabilities.workspace.file_operations.did_delete is True


def test_mixin_will_create_files():
    class Client(WithRequestWillCreateFiles):
        pass

    capabilities = build_client_capabilities(Client)
    assert capabilities.workspace is not None
    assert capabilities.workspace.file_operations is not None
    assert capabilities.workspace.file_operations.will_create is True


def test_mixin_will_rename_files():
    class Client(WithRequestWillRenameFiles):
        pass

    capabilities = build_client_capabilities(Client)
    assert capabilities.workspace is not None
    assert capabilities.workspace.file_operations is not None
    assert capabilities.workspace.file_operations.will_rename is True


def test_mixin_will_delete_files():
    class Client(WithRequestWillDeleteFiles):
        pass

    capabilities = build_client_capabilities(Client)
    assert capabilities.workspace is not None
    assert capabilities.workspace.file_operations is not None
    assert capabilities.workspace.file_operations.will_delete is True
