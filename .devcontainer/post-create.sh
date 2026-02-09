#!/bin/bash
set -e

echo "🚗 Setting up AutoDrive Rental Car Agent Development Environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"

# Check Azure CLI
echo "☁️ Checking Azure CLI..."
if command -v az &> /dev/null; then
    echo "  ✓ Azure CLI is installed: $(az --version | head -n1)"
else
    echo "  ⚠ Azure CLI not found"
fi

# Verify Python environment
echo "🐍 Python environment:"
echo "  Python: $(python --version)"
echo "  Pip: $(pip --version)"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "  ✓ Created .env file - please update with your Azure credentials"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Update .env with your Azure AI Foundry credentials"
echo "  2. Run 'az login' to authenticate with Azure"
echo "  3. Run 'python main.py' to test the agent locally"
echo ""
