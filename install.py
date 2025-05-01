#!/usr/bin/env python3
import os
import platform
import subprocess
import sys
import shutil
import argparse
from pathlib import Path


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ShellGPT Installation Script",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--skip-checks", 
        action="store_true",
        help="Skip prerequisite checks and proceed directly to installation"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Show detailed output during installation"
    )
    parser.add_argument(
        "--no-venv-in-project", 
        action="store_true",
        help="Don't configure Poetry to create virtualenvs in the project directory"
    )
    parser.add_argument(
        "--global", 
        action="store_true",
        dest="global_install",
        help="Install ShellGPT globally (makes 'sgpt' available as a direct command)"
    )
    return parser.parse_args()


def check_python_version():
    """Verify Python version meets requirements (>=3.10)."""
    min_version = (3, 10)
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        print(f"Error: Python {min_version[0]}.{min_version[1]} or higher is required.")
        print(f"Current Python version is {current_version[0]}.{current_version[1]}")
        sys.exit(1)
    
    print(f"✓ Python version {current_version[0]}.{current_version[1]} meets requirements.")


def check_poetry_installation():
    """Check if Poetry is installed, install if not."""
    if shutil.which("poetry") is None:
        print("Poetry not found. Installing Poetry...")
        
        # Poetry installation differs by platform
        if platform.system() == "Windows":
            # Windows installation
            try:
                subprocess.run(
                    ["powershell", "-Command", 
                     "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -"],
                    check=True
                )
                # Add to PATH for this session
                poetry_path = str(Path.home() / "AppData" / "Roaming" / "Python" / "Scripts")
                os.environ["PATH"] += os.pathsep + poetry_path
            except subprocess.CalledProcessError:
                print("Error: Failed to install Poetry on Windows.")
                sys.exit(1)
        else:
            # Unix-based installation (macOS, Linux)
            try:
                # Using subprocess.run with shell=True for pipe operation
                subprocess.run(
                    "curl -sSL https://install.python-poetry.org | python3 -",
                    check=True, shell=True
                )
                # Add to PATH for this session
                poetry_path = str(Path.home() / ".local" / "bin")
                os.environ["PATH"] += os.pathsep + poetry_path
            except subprocess.CalledProcessError:
                print("Error: Failed to install Poetry.")
                sys.exit(1)
        
        print("✓ Poetry has been installed.")
    else:
        print("✓ Poetry is already installed.")


def check_system_dependencies():
    """Check for necessary system dependencies based on platform."""
    system = platform.system()
    
    if system == "Linux":
        # Check for common build dependencies on Linux
        dependencies = ["gcc", "python3-dev"]
        missing_deps = []
        
        for dep in dependencies:
            print(f"Checking for {dep}...")
            if subprocess.run(["which", dep], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
                missing_deps.append(dep)
        
        if missing_deps:
            print("Warning: The following dependencies were not found:")
            for dep in missing_deps:
                print(f"  - {dep}")
            print("These might be needed for some dependencies.")
            print("Consider installing them with your package manager.")
    
    elif system == "Darwin":  # macOS
        # Check for Xcode command line tools
        if subprocess.run(["xcode-select", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
            print("Warning: Xcode Command Line Tools not found.")
            print("Consider installing them with: xcode-select --install")
    
    # Add Windows-specific checks if needed
    elif system == "Windows":
        # Check for Visual C++ Build Tools
        print("Note: On Windows, you might need Microsoft Visual C++ Build Tools")
        print("      if you encounter issues with native extensions.")
        print("      You can download them from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")


def install_shellgpt(verbose=False):
    """Install ShellGPT using Poetry."""
    print("\nInstalling ShellGPT with Poetry...")
    
    # Run poetry install in the current directory
    cmd = ["poetry", "install"]
    if verbose:
        # Show verbose output
        result = subprocess.run(cmd)
    else:
        # Capture output to keep it clean
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print("Error: Poetry installation failed.")
        if not verbose:
            print("Try running with --verbose for more information.")
        sys.exit(1)
    
    # If we get here, installation succeeded
    print("✓ ShellGPT has been successfully installed!")


def setup_virtual_environment():
    """Configure the virtual environment if needed."""
    # Ensure poetry is creating virtualenvs in the project directory
    subprocess.run(["poetry", "config", "virtualenvs.in-project", "true"], check=True)
    print("✓ Poetry configured to create virtual environments in the project directory.")


def display_usage_instructions():
    """Show instructions on how to use the installed package."""
    print("\n=== How to Use ShellGPT ===")
    print("Option 1: Run directly with Poetry:")
    print("  poetry run sgpt \"Your prompt here\"")
    print("\nOption 2: Activate the virtual environment and run:")
    print("  poetry shell")
    print("  sgpt \"Your prompt here\"")
    print("\nOption 3: Install ShellGPT globally:")
    print("  poetry build")
    print("  pip install dist/*.whl")


def install_globally(verbose=False):
    """Install ShellGPT globally."""
    print("\nInstalling ShellGPT globally...")
    
    # Build the package
    print("Building package...")
    build_cmd = ["poetry", "build"]
    if verbose:
        result = subprocess.run(build_cmd)
    else:
        result = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print("Error: Failed to build package.")
        if not verbose:
            print("Try running with --verbose for more information.")
        sys.exit(1)
    
    # Install the package globally
    print("Installing package globally...")
    # Find the wheel file
    dist_dir = Path("dist")
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("Error: No wheel file found in dist directory.")
        sys.exit(1)
    
    # Use the latest wheel file (in case there are multiple)
    wheel_file = str(sorted(wheel_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
    
    install_cmd = [sys.executable, "-m", "pip", "install", wheel_file]
    if verbose:
        result = subprocess.run(install_cmd)
    else:
        result = subprocess.run(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print("Error: Failed to install package globally.")
        if not verbose:
            print("Try running with --verbose for more information.")
        sys.exit(1)
    
    print("✓ ShellGPT has been successfully installed globally!")
    print("  You can now run 'sgpt' directly from anywhere.")


def main():
    """Main installation process."""
    args = parse_arguments()
    
    print("=== ShellGPT Installation Script ===\n")
    
    if not args.skip_checks:
        # Step 1: Check Python version
        check_python_version()
        
        # Step 2: Check and install Poetry if needed
        check_poetry_installation()
        
        # Step 3: Check system dependencies
        check_system_dependencies()
    else:
        print("Skipping prerequisite checks as requested.")
    
    # Step 4: Configure Poetry
    if not args.no_venv_in_project:
        setup_virtual_environment()
    
    # Step 5: Install ShellGPT
    install_shellgpt(verbose=args.verbose)
    
    # Step 6: Install globally if requested
    if args.global_install:
        install_globally(verbose=args.verbose)
    
    # Step 7: Show usage instructions
    if not args.global_install:
        display_usage_instructions()
    
    print("\nInstallation complete!")


if __name__ == "__main__":
    main()
