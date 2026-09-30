from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

import langfuse

from app import tracing


class TracingAdapterTests(unittest.TestCase):
    def test_adapter_uses_the_installed_langfuse_v4_api(self) -> None:
        self.assertEqual(tracing.observe.__module__, langfuse.observe.__module__)
        client = tracing.get_langfuse_client()
        self.assertTrue(callable(client.update_current_span))
        self.assertTrue(callable(client.update_current_generation))
        self.assertTrue(callable(client.start_as_current_observation))

    def test_tracing_is_disabled_without_both_keys(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(tracing.tracing_enabled())
        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-only"}, clear=True):
            self.assertFalse(tracing.tracing_enabled())

    def test_flush_langfuse_flushes_the_current_client(self) -> None:
        client = Mock()
        with patch.object(tracing, "get_langfuse_client", return_value=client):
            tracing.flush_langfuse()
        client.flush.assert_called_once_with()

    def test_observation_context_is_noop_when_client_has_no_observation_api(self) -> None:
        with tracing.observation_context(object(), name="optional-child") as observation:
            observation.update(output={"safe": True})


if __name__ == "__main__":
    unittest.main()
