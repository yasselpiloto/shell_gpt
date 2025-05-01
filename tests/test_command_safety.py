import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from sgpt.command_safety import (
    DEFAULT_SAFETY_CONFIG,
    add_to_approve_list,
    add_to_confirm_list,
    create_default_safety_config,
    get_safety_config_display,
    is_safe_to_auto_execute,
    load_safety_config,
    remove_from_approve_list,
    remove_from_confirm_list,
    save_safety_config,
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config_path(temp_config_dir, monkeypatch):
    """Mock the config path to use a temporary directory."""
    config_path = Path(temp_config_dir) / "command_safety.yaml"
    monkeypatch.setattr("sgpt.command_safety.COMMAND_SAFETY_CONFIG_PATH", config_path)
    monkeypatch.setattr("sgpt.command_safety.SHELL_GPT_CONFIG_FOLDER", Path(temp_config_dir))
    return config_path


def test_create_default_safety_config(mock_config_path):
    """Test creating the default safety configuration file."""
    create_default_safety_config()
    assert mock_config_path.exists()
    
    with open(mock_config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    assert "always-confirm" in config
    assert "always-approve" in config
    assert "rm" in config["always-confirm"]
    assert "ls" in config["always-approve"]


def test_load_safety_config_creates_default_if_not_exists(mock_config_path):
    """Test that load_safety_config creates a default config if none exists."""
    config = load_safety_config()
    
    assert mock_config_path.exists()
    assert "always-confirm" in config
    assert "always-approve" in config
    assert config == DEFAULT_SAFETY_CONFIG


def test_load_safety_config_loads_existing_config(mock_config_path):
    """Test loading an existing safety configuration."""
    test_config = {
        "always-confirm": ["test-cmd1", "test-cmd2"],
        "always-approve": ["test-cmd3", "test-cmd4"],
    }
    
    os.makedirs(os.path.dirname(mock_config_path), exist_ok=True)
    with open(mock_config_path, "w", encoding="utf-8") as f:
        yaml.dump(test_config, f)
    
    config = load_safety_config()
    
    assert config == test_config
    assert "test-cmd1" in config["always-confirm"]
    assert "test-cmd3" in config["always-approve"]


def test_save_safety_config(mock_config_path):
    """Test saving a safety configuration."""
    test_config = {
        "always-confirm": ["test-cmd1", "test-cmd2"],
        "always-approve": ["test-cmd3", "test-cmd4"],
    }
    
    save_safety_config(test_config)
    
    with open(mock_config_path, "r", encoding="utf-8") as f:
        loaded_config = yaml.safe_load(f)
    
    assert loaded_config == test_config


def test_is_safe_to_auto_execute():
    """Test the is_safe_to_auto_execute function."""
    # Mock the load_safety_config function to return a test configuration
    test_config = {
        "always-confirm": ["rm", "sudo", "mv"],
        "always-approve": ["ls", "echo", "pwd"],
    }
    
    with mock.patch("sgpt.command_safety.load_safety_config", return_value=test_config):
        # Test with auto_approve=False
        assert not is_safe_to_auto_execute("ls -la", False)
        
        # Test with auto_approve=True
        # Safe commands (in always-approve list)
        assert is_safe_to_auto_execute("ls -la", True)
        assert is_safe_to_auto_execute("echo hello", True)
        
        # Unsafe commands (in always-confirm list)
        assert not is_safe_to_auto_execute("rm -rf /", True)
        assert not is_safe_to_auto_execute("sudo apt update", True)
        
        # Commands not in either list
        assert is_safe_to_auto_execute("cat file.txt", True)
        
        # Commands containing unsafe patterns
        assert not is_safe_to_auto_execute("cat file.txt | sudo tee /etc/hosts", True)
        
        # Empty command
        assert is_safe_to_auto_execute("", True)
        assert is_safe_to_auto_execute("   ", True)


def test_add_to_approve_list(mock_config_path):
    """Test adding commands to the always-approve list."""
    # Create a default config
    create_default_safety_config()
    
    # Add commands to the always-approve list
    add_to_approve_list(["test-cmd1", "test-cmd2"])
    
    # Load the config and check if the commands were added
    config = load_safety_config()
    assert "test-cmd1" in config["always-approve"]
    assert "test-cmd2" in config["always-approve"]


def test_add_to_confirm_list(mock_config_path):
    """Test adding commands to the always-confirm list."""
    # Create a default config
    create_default_safety_config()
    
    # Add commands to the always-confirm list
    add_to_confirm_list(["test-cmd1", "test-cmd2"])
    
    # Load the config and check if the commands were added
    config = load_safety_config()
    assert "test-cmd1" in config["always-confirm"]
    assert "test-cmd2" in config["always-confirm"]


def test_remove_from_approve_list(mock_config_path):
    """Test removing commands from the always-approve list."""
    # Create a config with test commands
    test_config = {
        "always-confirm": ["cmd1", "cmd2"],
        "always-approve": ["cmd3", "cmd4", "cmd5"],
    }
    save_safety_config(test_config)
    
    # Remove commands from the always-approve list
    remove_from_approve_list(["cmd3", "cmd5"])
    
    # Load the config and check if the commands were removed
    config = load_safety_config()
    assert "cmd3" not in config["always-approve"]
    assert "cmd4" in config["always-approve"]
    assert "cmd5" not in config["always-approve"]


def test_remove_from_confirm_list(mock_config_path):
    """Test removing commands from the always-confirm list."""
    # Create a config with test commands
    test_config = {
        "always-confirm": ["cmd1", "cmd2", "cmd3"],
        "always-approve": ["cmd4", "cmd5"],
    }
    save_safety_config(test_config)
    
    # Remove commands from the always-confirm list
    remove_from_confirm_list(["cmd1", "cmd3"])
    
    # Load the config and check if the commands were removed
    config = load_safety_config()
    assert "cmd1" not in config["always-confirm"]
    assert "cmd2" in config["always-confirm"]
    assert "cmd3" not in config["always-confirm"]


def test_get_safety_config_display(mock_config_path):
    """Test getting a formatted display of the safety configuration."""
    # Create a config with test commands
    test_config = {
        "always-confirm": ["cmd1", "cmd2"],
        "always-approve": ["cmd3", "cmd4"],
    }
    save_safety_config(test_config)
    
    # Get the display
    display = get_safety_config_display()
    
    # Check if the display contains the expected information
    assert "Command Safety Configuration" in display
    assert "Always Confirm" in display
    assert "Always Approve" in display
    assert "cmd1" in display
    assert "cmd2" in display
    assert "cmd3" in display
    assert "cmd4" in display
