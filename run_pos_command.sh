#!/bin/bash
# Wrapper script to run POS commands with Rosetta 2 (x86_64) to avoid ARM64/x86 DLL compatibility issues
#
# Usage:
#   ./run_pos_command.sh send_pos_payment 10000 --order-number "TEST-001"
#   ./run_pos_command.sh test_pos_connection
#   ./run_pos_command.sh debug_pos

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set Mono GAC prefix
export MONO_GAC_PREFIX="/opt/homebrew"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️  Warning: This script is designed for macOS. Running without Rosetta 2..."
    python manage.py "$@"
    exit $?
fi

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    echo "✅ Running with Rosetta 2 (x86_64) for ARM64/x86 DLL compatibility..."
    # Run command with Rosetta 2 (x86_64 architecture)
    arch -x86_64 python manage.py "$@"
else
    echo "✅ Running on $ARCH architecture..."
    # Run normally on x86_64
    python manage.py "$@"
fi

