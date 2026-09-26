#!/usr/bin/env bash
set -e

echo "=== SIH26237 Environment Check ==="
echo "OS: $(uname -s 2>/dev/null || echo 'Unknown')"
echo "Kernel: $(uname -r 2>/dev/null || echo 'Unknown')"
echo "Python: $(python3 --version 2>/dev/null || python --version 2>/dev/null || echo 'Not found')"
echo "Pip: $(pip3 --version 2>/dev/null || pip --version 2>/dev/null || echo 'Not found')"
echo "Node.js: $(node --version 2>/dev/null || echo 'Not found')"
echo "npm: $(npm --version 2>/dev/null || echo 'Not found')"
echo "Git: $(git --version 2>/dev/null || echo 'Not found')"
echo "CMake: $(cmake --version 2>/dev/null | head -n 1 || echo 'Not found')"
echo "Compiler: $(gcc --version 2>/dev/null | head -n 1 || clang --version 2>/dev/null | head -n 1 || echo 'Not found')"
echo "OpenSSL: $(openssl version 2>/dev/null || echo 'Not found in PATH')"
echo "Docker: $(docker --version 2>/dev/null || echo 'Not found / Optional for v0.1')"
echo "==================================="
