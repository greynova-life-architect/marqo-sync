#!/usr/bin/env python3
"""Install missing dependencies for the Marqo Sync service."""

import subprocess
import sys
import os

def install_package(package):
    """Install a Python package using pip."""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """Install required dependencies."""
    print("🔧 Installing dependencies for Marqo Sync service...")
    print("=" * 50)
    
    # Required packages
    packages = [
        "psutil>=5.9.0",  # System resource monitoring
        "tiktoken>=0.5.0",  # Token counting for enhanced chunking
        "langdetect>=1.0.9",  # Language detection
        "pygments>=2.15.0",  # Syntax highlighting
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for package in packages:
        if install_package(package):
            success_count += 1
        print()  # Add spacing between packages
    
    print("=" * 50)
    print(f"Installation complete: {success_count}/{total_count} packages installed successfully")
    
    if success_count == total_count:
        print("✅ All dependencies installed successfully!")
        print("You can now run the sync service with full resource monitoring capabilities.")
    else:
        print("⚠️  Some dependencies failed to install.")
        print("The sync service will still work with fallback functionality.")
    
    print("\nTo install manually, run:")
    for package in packages:
        print(f"  pip install {package}")

if __name__ == "__main__":
    main()


