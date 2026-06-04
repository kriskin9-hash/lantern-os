#!/usr/bin/env python3
"""
Lantern Startup and LLM Integration Tests

Tests the actual startup flow, LLM service detection, and provider configuration.
"""

import json
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock


class TestLLMPortDetection(unittest.TestCase):
    """Test LLM service port detection logic."""

    @staticmethod
    def port_is_open(port: int, timeout: float = 0.5) -> bool:
        """Check if a port is responding."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0

    def test_lm_studio_detection(self):
        """Test LM Studio port detection."""
        is_open = self.port_is_open(1234)
        if is_open:
            print("[OK] LM Studio detected on port 1234")
        else:
            print("[INFO] LM Studio not running - expected if not installed")
        # Don't fail, just report status

    def test_ollama_detection(self):
        """Test Ollama port detection."""
        is_open = self.port_is_open(11434)
        if is_open:
            print("[OK] Ollama detected on port 11434")
        else:
            print("[INFO] Ollama not running - expected if not installed")
        # Don't fail, just report status

    def test_cloud_api_endpoints(self):
        """Test that cloud API endpoints are configured."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        endpoints = {
            'claude': 'https://api.anthropic.com/v1/messages',
            'gemini': 'https://generativelanguage.googleapis.com/v1beta/models/',
            'deepseek': 'https://api.deepseek.com/v1/chat/completions',
            'lm_studio': 'http://127.0.0.1:1234/v1/chat/completions',
            'ollama': 'http://127.0.0.1:11434/api/chat'
        }

        for provider_id, expected_endpoint in endpoints.items():
            provider = data['llm_providers'].get(provider_id)
            self.assertIsNotNone(provider, f"Provider {provider_id} not configured")
            actual_endpoint = provider.get('endpoint')
            self.assertEqual(actual_endpoint, expected_endpoint,
                           f"Endpoint mismatch for {provider_id}")


class TestProviderConfiguration(unittest.TestCase):
    """Test provider configuration and defaults."""

    def test_primary_provider_set(self):
        """Test that primary provider is configured."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        primary = data.get('primary_provider')
        self.assertIsNotNone(primary, "No primary provider set")
        self.assertIn(primary, data['llm_providers'],
                     f"Primary provider '{primary}' not in providers")

    def test_fallback_provider_set(self):
        """Test that fallback provider is configured."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        fallback = data.get('fallback_provider')
        self.assertIsNotNone(fallback, "No fallback provider set")
        self.assertIn(fallback, data['llm_providers'],
                     f"Fallback provider '{fallback}' not in providers")

    def test_family_bindings_valid(self):
        """Test that family bindings point to real providers."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        family_bindings = data.get('family_bindings', {})
        available_providers = set(data['llm_providers'].keys())

        for family_id, bindings in family_bindings.items():
            primary = bindings.get('primary')
            fallback = bindings.get('fallback')

            self.assertIn(primary, available_providers,
                         f"Family {family_id} primary '{primary}' not found")
            self.assertIn(fallback, available_providers,
                         f"Family {family_id} fallback '{fallback}' not found")


class TestConfigConsistency(unittest.TestCase):
    """Test configuration file consistency."""

    def test_all_providers_have_status(self):
        """Test that all providers have a status field."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        for provider_id, provider in data['llm_providers'].items():
            self.assertIn('status', provider,
                         f"Provider {provider_id} missing status field")
            # Status should be one of these values
            valid_statuses = ['READY_TO_CONFIGURE', 'OFFLINE_READY', 'CONFIGURED', 'ERROR']
            self.assertIn(provider['status'], valid_statuses,
                         f"Invalid status '{provider['status']}' for {provider_id}")

    def test_provider_config_fields_present(self):
        """Test that provider config sections are valid."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        for provider_id, provider in data['llm_providers'].items():
            config = provider.get('config')
            self.assertIsNotNone(config,
                               f"Provider {provider_id} missing config section")
            self.assertIn('model', config,
                         f"Provider {provider_id} config missing model field")


class TestScriptAvailability(unittest.TestCase):
    """Test that all required startup scripts exist."""

    def test_startup_scripts_present(self):
        """Test that all startup scripts are present."""
        scripts_dir = Path(__file__).parent.parent / "scripts"

        required_scripts = [
            "lantern-desktop-auth-ui.py",
            "start-local-llms.ps1",
            "start-lantern-with-llms.bat"
        ]

        for script in required_scripts:
            script_path = scripts_dir / script
            self.assertTrue(script_path.exists(),
                          f"Required script not found: {script}")

    def test_startup_script_not_empty(self):
        """Test that startup scripts have content."""
        scripts_dir = Path(__file__).parent.parent / "scripts"

        scripts = {
            "lantern-desktop-auth-ui.py": "def start_local_llms",
            "start-local-llms.ps1": "Write-Host",
            "start-lantern-with-llms.bat": "@echo off"
        }

        for script_name, expected_content in scripts.items():
            script_path = scripts_dir / script_name
            with open(script_path, encoding='utf-8') as f:
                content = f.read()
            self.assertIn(expected_content, content,
                         f"Script {script_name} missing expected content: {expected_content}")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLLMPortDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestProviderConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestScriptAvailability))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
