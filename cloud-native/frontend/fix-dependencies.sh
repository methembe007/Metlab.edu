#!/bin/bash

# Quick fix for TanStack dependency issues

echo "🔧 Fixing TanStack dependencies..."
echo ""

# Remove node_modules and lock file
echo "🧹 Cleaning..."
rm -rf node_modules package-lock.json

# Reinstall with correct versions
echo "📦 Reinstalling dependencies..."
npm install --legacy-peer-deps

echo ""
echo "✅ Dependencies fixed!"
echo ""
echo "Now run: npm run dev"
