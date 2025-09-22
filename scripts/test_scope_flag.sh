#!/bin/bash
# Test script for the --scope/-s flag functionality

set -e

echo "=== Testing gac --scope flag ==="
echo

# Create a temporary test directory
TEST_DIR="/tmp/gac-scope-test-$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize git repo
git init
git config user.email "test@example.com"
git config user.name "Test User"

# Create initial commit
echo "Initial content" > test.py
git add test.py
git commit -m "Initial commit"

echo "1. Testing --scope flag (infer scope)"
echo "   Creating a new authentication file..."
cat > auth.py << 'EOF'
def login(username, password):
    """Handle user login."""
    return True
EOF
git add auth.py

echo "   Running: gac preview --scope"
gac preview --scope || echo "Note: Preview may fail if AI providers aren't configured"
echo

echo "2. Testing without --scope flag"
echo "   Adding a README file..."
cat > README.md << 'EOF'
# Test Project
This is a test project for gac scope testing.
EOF
git add README.md

echo "   Running: gac preview"
gac preview || echo "Note: Preview may fail if AI providers aren't configured"
echo

echo "3. Testing --scope with other flags"
echo "   Modifying auth.py with hint..."
echo "def logout(): pass" >> auth.py
git add auth.py

echo "   Running: gac preview --scope --one-liner --hint 'Add logout functionality'"
gac preview --scope --one-liner --hint "Add logout functionality" || echo "Note: Preview may fail if AI providers aren't configured"
echo

# Cleanup
cd /
rm -rf "$TEST_DIR"

echo "=== Test script completed ==="
echo
echo "Note: This script demonstrates the --scope flag usage."
echo "Actual commit message generation requires AI provider configuration."
echo "Run 'pytest tests/test_scope_flag.py' for comprehensive unit tests."
