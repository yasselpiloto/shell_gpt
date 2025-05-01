import os
import shlex
from pathlib import Path
from typing import Dict, List, Any

from sgpt.config import SHELL_GPT_CONFIG_FOLDER

# Path to the command safety configuration file
COMMAND_SAFETY_CONFIG_PATH = SHELL_GPT_CONFIG_FOLDER / "command_safety.yaml"

# Default safety configuration
DEFAULT_SAFETY_CONFIG = {
    "always-confirm": [
        "rm", "sudo", "chmod", "chown", "mv", "mkfs", "dd", 
        ">", "|", "wget", "curl", "apt", "apt-get",
        "yum", "brew", "pip", "npm", "yarn", 
        "shutdown", "reboot", "eval"
    ],
    "always-approve": [
        "ls", "cd", "echo", "pwd", "cat", "grep"
    ]
}


def load_safety_config() -> Dict[str, List[str]]:
    """
    Load command safety configuration from YAML file.
    If the file doesn't exist, create it with default values.
    
    Returns:
        Dict containing 'always-confirm' and 'always-approve' lists
    """
    try:
        import yaml
    except ImportError:
        print("PyYAML is not installed. Using default safety configuration.")
        return DEFAULT_SAFETY_CONFIG
    
    if not COMMAND_SAFETY_CONFIG_PATH.exists():
        create_default_safety_config()
    
    try:
        with open(COMMAND_SAFETY_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            # Ensure both keys exist
            if "always-confirm" not in config:
                config["always-confirm"] = DEFAULT_SAFETY_CONFIG["always-confirm"]
            if "always-approve" not in config:
                config["always-approve"] = DEFAULT_SAFETY_CONFIG["always-approve"]
            return config
    except Exception as e:
        print(f"Error loading safety config: {e}. Using default configuration.")
        return DEFAULT_SAFETY_CONFIG


def create_default_safety_config() -> None:
    """
    Create default safety configuration file
    """
    try:
        import yaml
    except ImportError:
        print("PyYAML is not installed. Cannot create safety configuration file.")
        return
    
    SHELL_GPT_CONFIG_FOLDER.mkdir(exist_ok=True, parents=True)
    with open(COMMAND_SAFETY_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_SAFETY_CONFIG, f, default_flow_style=False)


def save_safety_config(config: Dict[str, List[str]]) -> None:
    """
    Save command safety configuration to YAML file
    
    Args:
        config: Dictionary containing 'always-confirm' and 'always-approve' lists
    """
    try:
        import yaml
    except ImportError:
        print("PyYAML is not installed. Cannot save safety configuration.")
        return
    
    SHELL_GPT_CONFIG_FOLDER.mkdir(exist_ok=True, parents=True)
    with open(COMMAND_SAFETY_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)


def is_safe_to_auto_execute(command: str, auto_approve: bool) -> bool:
    """
    Determines if a command is safe to auto-execute based on configuration
    
    Args:
        command: The shell command to check
        auto_approve: Whether auto-approve is enabled
    
    Returns:
        True if the command is safe to auto-execute, False otherwise
    """
    if not auto_approve:
        return False
    
    # Empty command is safe
    if not command.strip():
        return True
    
    # Load safety configuration
    safety_config = load_safety_config()
    
    try:
        # Parse first word/command from the input
        cmd_parts = shlex.split(command)
        if not cmd_parts:
            return True  # Empty command
        
        base_cmd = cmd_parts[0]
        
        # Check if command is in always-approve list (bypass safety checks)
        if base_cmd in safety_config.get("always-approve", []):
            return True
            
        # Check if command is in always-confirm list
        if base_cmd in safety_config.get("always-confirm", []):
            return False
            
        # Check if any pattern in always-confirm appears in the full command
        for pattern in safety_config.get("always-confirm", []):
            if pattern in command:
                return False
    except Exception:
        # If there's any error in parsing, err on the side of caution
        return False
                
    # If we've gotten here and auto_approve is True, we can proceed
    return True


def add_to_approve_list(commands: List[str]) -> None:
    """
    Add commands to the always-approve list
    
    Args:
        commands: List of commands to add
    """
    config = load_safety_config()
    for cmd in commands:
        if cmd not in config["always-approve"]:
            config["always-approve"].append(cmd)
    save_safety_config(config)


def add_to_confirm_list(commands: List[str]) -> None:
    """
    Add commands to the always-confirm list
    
    Args:
        commands: List of commands to add
    """
    config = load_safety_config()
    for cmd in commands:
        if cmd not in config["always-confirm"]:
            config["always-confirm"].append(cmd)
    save_safety_config(config)


def remove_from_approve_list(commands: List[str]) -> None:
    """
    Remove commands from the always-approve list
    
    Args:
        commands: List of commands to remove
    """
    config = load_safety_config()
    config["always-approve"] = [cmd for cmd in config["always-approve"] if cmd not in commands]
    save_safety_config(config)


def remove_from_confirm_list(commands: List[str]) -> None:
    """
    Remove commands from the always-confirm list
    
    Args:
        commands: List of commands to remove
    """
    config = load_safety_config()
    config["always-confirm"] = [cmd for cmd in config["always-confirm"] if cmd not in commands]
    save_safety_config(config)


def get_safety_config_display() -> str:
    """
    Get a formatted string representation of the safety configuration
    
    Returns:
        Formatted string showing the current safety configuration
    """
    config = load_safety_config()
    
    result = "Command Safety Configuration:\n\n"
    
    result += "Always Confirm (commands that require explicit approval):\n"
    for cmd in sorted(config["always-confirm"]):
        result += f"  - {cmd}\n"
    
    result += "\nAlways Approve (commands that bypass safety checks):\n"
    for cmd in sorted(config["always-approve"]):
        result += f"  - {cmd}\n"
    
    return result
