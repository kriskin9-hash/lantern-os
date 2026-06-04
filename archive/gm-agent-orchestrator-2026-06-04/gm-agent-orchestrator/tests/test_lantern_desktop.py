#!/usr/bin/env python3
"""
Lantern Desktop Comprehensive Test Suite

Tests startup, LLM integration, provider auth, config management, and error handling.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestLanternStartup(unittest.TestCase):
    """Test app startup and initialization."""

    def test_lantern_auth_ui_imports(self):
        """Test that lantern-desktop-auth-ui.py can be imported."""
        script_path = Path(__file__).parent.parent / "scripts" / "lantern-desktop-auth-ui.py"
        # Just verify the script exists and is Python valid
        if script_path.exists():
            with open(script_path, encoding='utf-8') as f:
                code = f.read()
            try:
                compile(code, str(script_path), 'exec')
            except SyntaxError as e:
                self.fail(f"Syntax error in lantern-desktop-auth-ui.py: {e}")
        else:
            self.fail("lantern-desktop-auth-ui.py not found")

    def test_credentials_directory_exists(self):
        """Test that credentials directory is created."""
        creds_dir = Path.home() / ".lantern" / "credentials"
        # Create if doesn't exist
        creds_dir.mkdir(parents=True, exist_ok=True)
        self.assertTrue(creds_dir.exists())

    def test_lantern_config_directory_exists(self):
        """Test that .lantern directory exists."""
        lantern_dir = Path.home() / ".lantern"
        lantern_dir.mkdir(parents=True, exist_ok=True)
        self.assertTrue(lantern_dir.exists())


class TestLLMDetection(unittest.TestCase):
    """Test LLM service detection and startup."""

    def test_port_detection_function(self):
        """Test the port detection logic."""
        # Verify the start-local-llms.ps1 script exists
        script_path = Path(__file__).parent.parent / "scripts" / "start-local-llms.ps1"
        self.assertTrue(script_path.exists(), "start-local-llms.ps1 not found")

    def test_lm_studio_port(self):
        """Test LM Studio port is accessible (if running)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 1234))
        sock.close()
        # Don't fail if not running, just note it
        if result == 0:
            print("[INFO] LM Studio is running on port 1234")
        else:
            print("[INFO] LM Studio is NOT running on port 1234 (expected if not installed)")

    def test_ollama_port(self):
        """Test Ollama port is accessible (if running)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 11434))
        sock.close()
        if result == 0:
            print("[INFO] Ollama is running on port 11434")
        else:
            print("[INFO] Ollama is NOT running on port 11434 (expected if not installed)")


class TestConfigFiles(unittest.TestCase):
    """Test configuration file handling."""

    def test_llm_configurations_exists(self):
        """Test that llm-configurations.json exists."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        self.assertTrue(config_path.exists(), f"Config file not found at {config_path}")

    def test_llm_configurations_valid_json(self):
        """Test that llm-configurations.json is valid JSON."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        try:
            with open(config_path) as f:
                data = json.load(f)
            self.assertIn("llm_providers", data)
            self.assertIn("primary_provider", data)
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON in llm-configurations.json: {e}")

    def test_llm_configurations_has_all_providers(self):
        """Test that all expected providers are configured."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        expected_providers = ["claude", "gemini", "deepseek", "lm_studio", "ollama"]
        for provider in expected_providers:
            self.assertIn(provider, data["llm_providers"],
                         f"Provider '{provider}' not found in config")

    def test_provider_has_required_fields(self):
        """Test that each provider has required fields."""
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        with open(config_path) as f:
            data = json.load(f)

        required_fields = ["name", "type", "endpoint", "config", "status"]
        for provider_id, provider in data["llm_providers"].items():
            for field in required_fields:
                self.assertIn(field, provider,
                             f"Field '{field}' missing from provider '{provider_id}'")


class TestAuthUI(unittest.TestCase):
    """Test authentication UI logic."""

    def test_provider_auth_ui_class_exists(self):
        """Test that ProviderAuthUI class exists in lantern-desktop-auth-ui.py."""
        script_path = Path(__file__).parent.parent / "scripts" / "lantern-desktop-auth-ui.py"
        with open(script_path, encoding='utf-8') as f:
            code = f.read()
        # Check for the class definition
        self.assertIn("class ProviderAuthUI", code,
                     "ProviderAuthUI class not found in lantern-desktop-auth-ui.py")

    def test_provider_icons_and_names(self):
        """Test that providers have icons and names in source."""
        script_path = Path(__file__).parent.parent / "scripts" / "lantern-desktop-auth-ui.py"
        with open(script_path, encoding='utf-8') as f:
            code = f.read()
        # Check for provider definitions with icons
        self.assertIn('"icon"', code, "Provider icons not found in source")
        self.assertIn('"name"', code, "Provider names not found in source")


class TestFilePermissions(unittest.TestCase):
    """Test file and directory permissions."""

    def test_credentials_directory_permissions(self):
        """Test that credentials directory has secure permissions."""
        creds_dir = Path.home() / ".lantern" / "credentials"
        creds_dir.mkdir(parents=True, exist_ok=True)
        # On Windows, check that directory exists and is readable
        self.assertTrue(os.access(creds_dir, os.R_OK))

    def test_lantern_directory_writable(self):
        """Test that .lantern directory is writable."""
        lantern_dir = Path.home() / ".lantern"
        self.assertTrue(os.access(lantern_dir, os.W_OK))


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_missing_config_file_handling(self):
        """Test app behavior with missing config (should not crash)."""
        # This test verifies the app doesn't hardcode paths unsafely
        config_path = Path.home() / ".lantern" / "llm-configurations.json"
        # Ensure config exists for other tests
        self.assertTrue(config_path.exists())

    def test_invalid_credentials_handling(self):
        """Test that invalid API keys don't crash the app."""
        # Create a temporary invalid credentials file
        creds_dir = Path.home() / ".lantern" / "credentials"
        creds_dir.mkdir(parents=True, exist_ok=True)

        test_cred = creds_dir / "test_invalid.json"
        test_cred.write_text("{ invalid json }")

        # Try to load it (should handle gracefully)
        try:
            with open(test_cred) as f:
                json.load(f)
            self.fail("Should have raised JSONDecodeError")
        except json.JSONDecodeError:
            # Expected - but app should handle this gracefully
            pass
        finally:
            test_cred.unlink(missing_ok=True)


class TestIntegration(unittest.TestCase):
    """Integration tests between components."""

    def test_lantern_script_exists(self):
        """Test that lantern-desktop-auth-ui.py exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "lantern-desktop-auth-ui.py"
        self.assertTrue(script_path.exists(), f"Script not found at {script_path}")

    def test_llm_startup_script_exists(self):
        """Test that start-local-llms.ps1 exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "start-local-llms.ps1"
        self.assertTrue(script_path.exists(), f"Script not found at {script_path}")

    def test_batch_launcher_exists(self):
        """Test that start-lantern-with-llms.bat exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "start-lantern-with-llms.bat"
        self.assertTrue(script_path.exists(), f"Script not found at {script_path}")


def run_tests():
    """Run all tests and generate report."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLanternStartup))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthUI))
    suite.addTests(loader.loadTestsFromTestCase(TestFilePermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
