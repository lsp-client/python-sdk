from __future__ import annotations

"""
Example unit tests for Capability module.

This file demonstrates the expected test structure for testing
the capability-based protocol system.
"""


class TestCapabilityBuild:
    """Tests for capability building functions."""

    def test_build_client_capabilities_empty(self):
        """Test building client capabilities with no capabilities."""
        from lsp_client.capability.build import build_client_capabilities
        from lsp_client.client.abc import Client

        capabilities = build_client_capabilities(Client)
        assert capabilities is not None
        assert hasattr(capabilities, "workspace")
        assert hasattr(capabilities, "text_document")
        assert hasattr(capabilities, "window")
        assert hasattr(capabilities, "general")
        assert hasattr(capabilities, "notebook_document")

    def test_build_client_capabilities_with_mixins(self):
        """Test building client capabilities with capability mixins."""
        from lsp_client.capability.build import build_client_capabilities
        from lsp_client.capability.request.hover import WithRequestHover

        class HoverClient(WithRequestHover):
            pass

        capabilities = build_client_capabilities(HoverClient)
        assert capabilities is not None


class TestCapabilityProtocols:
    """Tests for capability protocol classes."""

    def test_text_document_capability_protocol(self):
        """Test TextDocumentCapabilityProtocol."""
        from lsp_client.protocol import TextDocumentCapabilityProtocol

        # Check that the protocol exists
        assert TextDocumentCapabilityProtocol is not None

    def test_workspace_capability_protocol(self):
        """Test WorkspaceCapabilityProtocol."""
        from lsp_client.protocol import WorkspaceCapabilityProtocol

        # Check that the protocol exists
        assert WorkspaceCapabilityProtocol is not None

    def test_window_capability_protocol(self):
        """Test WindowCapabilityProtocol."""
        from lsp_client.protocol import WindowCapabilityProtocol

        # Check that the protocol exists
        assert WindowCapabilityProtocol is not None

    def test_general_capability_protocol(self):
        """Test GeneralCapabilityProtocol."""
        from lsp_client.protocol import GeneralCapabilityProtocol

        # Check that the protocol exists
        assert GeneralCapabilityProtocol is not None


class TestServerRequestHooks:
    """Tests for server request hook system."""

    def test_server_request_hook_protocol_exists(self):
        """Test that ServerRequestHookProtocol exists."""
        from lsp_client.protocol import ServerRequestHookProtocol

        assert ServerRequestHookProtocol is not None

    def test_server_request_hook_registry_exists(self):
        """Test that ServerRequestHookRegistry exists."""
        from lsp_client.protocol import ServerRequestHookRegistry

        registry = ServerRequestHookRegistry()
        assert registry is not None

    def test_build_server_request_hooks_empty(self):
        """Test building server request hooks with no hooks."""
        from lsp_client.capability.build import build_server_request_hooks

        # Create a simple dict-like object without hooks
        class NoHooks:
            pass

        hooks = build_server_request_hooks(NoHooks())
        assert hooks is not None


class TestCapabilityMixins:
    """Tests for capability mixin classes."""

    def test_request_capabilities_exist(self):
        """Test that request capability mixins exist."""
        from lsp_client.capability.request import (
            WithRequestCompletion,
            WithRequestDefinition,
            WithRequestHover,
            WithRequestReferences,
        )

        assert WithRequestDefinition is not None
        assert WithRequestHover is not None
        assert WithRequestCompletion is not None
        assert WithRequestReferences is not None

    def test_notification_capabilities_exist(self):
        """Test that notification capability mixins exist."""
        from lsp_client.capability.notification import (
            WithNotifyDidChangeConfiguration,
            WithNotifyTextDocumentSynchronize,
        )

        assert WithNotifyDidChangeConfiguration is not None
        assert WithNotifyTextDocumentSynchronize is not None

    def test_server_notification_capabilities_exist(self):
        """Test that server notification capability mixins exist."""
        from lsp_client.capability.server_notification import (
            WithReceivePublishDiagnostics,
            WithReceiveShowMessage,
        )

        assert WithReceivePublishDiagnostics is not None
        assert WithReceiveShowMessage is not None

    def test_server_request_capabilities_exist(self):
        """Test that server request capability mixins exist."""
        from lsp_client.capability.server_request import (
            WithRespondApplyEdit,
            WithRespondConfigurationRequest,
            WithRespondWorkspaceFoldersRequest,
        )

        assert WithRespondApplyEdit is not None
        assert WithRespondConfigurationRequest is not None
        assert WithRespondWorkspaceFoldersRequest is not None


class TestWithRespondApplyEdit:
    """Tests for WithRespondApplyEdit capability."""

    def test_capability_imports(self):
        """Test that WithRespondApplyEdit can be imported."""
        from lsp_client.capability.server_request import WithRespondApplyEdit

        assert WithRespondApplyEdit is not None

    def test_capability_registers_workspace_capability(self):
        """Test that WithRespondApplyEdit registers workspace capabilities."""
        from lsp_client.capability.server_request import WithRespondApplyEdit
        from lsp_client.utils.types import lsp_type

        cap = lsp_type.WorkspaceClientCapabilities()
        WithRespondApplyEdit.register_workspace_capability(cap)

        # Check that applyEdit is enabled
        assert cap.apply_edit is True

        # Check that workspace_edit capabilities are set
        assert cap.workspace_edit is not None
        assert cap.workspace_edit.document_changes is True

        # Check that resource operations are advertised
        assert cap.workspace_edit.resource_operations is not None
        assert lsp_type.ResourceOperationKind.Create in cap.workspace_edit.resource_operations
        assert lsp_type.ResourceOperationKind.Rename in cap.workspace_edit.resource_operations
        assert lsp_type.ResourceOperationKind.Delete in cap.workspace_edit.resource_operations

        # Check failure handling
        assert cap.workspace_edit.failure_handling == lsp_type.FailureHandlingKind.Undo

    def test_capability_iterates_methods(self):
        """Test that WithRespondApplyEdit includes workspace/applyEdit in methods."""
        from lsp_client.capability.server_request import WithRespondApplyEdit
        from lsp_client.utils.types import lsp_type

        methods = list(WithRespondApplyEdit.iter_methods())
        assert lsp_type.WORKSPACE_APPLY_EDIT in methods

    def test_capability_is_protocol(self):
        """Test that WithRespondApplyEdit is a runtime checkable protocol."""
        from lsp_client.capability.server_request import WithRespondApplyEdit

        # Verify it's a runtime_checkable protocol
        assert hasattr(WithRespondApplyEdit, "__subclasshook__")
