#!/usr/bin/env bash
# ==============================================================================
# AegisTrace (SIH26237) — Unified Build Script for Render / Cloud Native Runtimes
# ==============================================================================
set -o errexit

echo "==> Step 1: Building React Web SPA frontend..."
cd apps/web
npm ci --silent
npm run build
cd ../..

echo "==> Step 2: Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install opencv-python-headless

echo "==> Step 3: Preparing runtime data directories..."
mkdir -p data/artifacts data/demo_fixtures artifacts/deployment

echo "==> AegisTrace build complete and ready for deployment!"
