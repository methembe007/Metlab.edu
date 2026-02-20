#!/bin/bash

# Frontend Setup Script for WSL/Linux
# This script sets up the frontend development environment

set -e

echo "========================================="
echo "Metlab.edu Frontend Setup"
echo "========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"
echo ""

# Clean existing installation if it exists
if [ -d "node_modules" ]; then
    echo "🧹 Cleaning existing node_modules..."
    rm -rf node_modules
fi

if [ -f "package-lock.json" ]; then
    echo "🧹 Removing package-lock.json..."
    rm -f package-lock.json
fi

# Clean npm cache
echo "🧹 Cleaning npm cache..."
npm cache clean --force

echo ""
echo "📦 Installing dependencies..."
npm install --legacy-peer-deps

echo ""
echo "🔧 Installing missing peer dependencies..."
npm install @tanstack/router-generator@^1.87.0 --legacy-peer-deps

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "To start the development server, run:"
echo "  npm run dev"
echo ""
echo "The app will be available at http://localhost:3000"
echo ""
