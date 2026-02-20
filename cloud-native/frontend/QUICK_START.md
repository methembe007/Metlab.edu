# Quick Start Guide

## ⚠️ Important: WSL/Windows Path Issue

You're currently trying to run commands from Windows CMD/PowerShell on a WSL path (`\\wsl.localhost\Ubuntu\...`). This won't work properly.

## ✅ Solution: Run from WSL

### Step 1: Open WSL Terminal

Open a WSL (Ubuntu) terminal. You can do this by:
- Opening Windows Terminal and selecting "Ubuntu" profile
- Or running `wsl` from Windows CMD/PowerShell
- Or searching for "Ubuntu" in Windows Start menu

### Step 2: Navigate to the Project

```bash
cd /home/metrix/git/Metlab.edu/cloud-native/frontend
```

### Step 3: Run the Setup Script

```bash
# Make the script executable
chmod +x setup.sh

# Run the setup
./setup.sh
```

Or manually run the commands:

```bash
# Clean existing installation
rm -rf node_modules package-lock.json

# Clean npm cache
npm cache clean --force

# Install dependencies
npm install --legacy-peer-deps
```

### Step 4: Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Alternative: Use Docker

If you prefer to avoid WSL/Windows path issues entirely, you can use Docker:

```bash
# From WSL terminal
cd /home/metrix/git/Metlab.edu/cloud-native/frontend

# Build the Docker image
docker build -t metlab-frontend .

# Run the container
docker run -p 3000:3000 metlab-frontend
```

## Why This Happens

Windows CMD/PowerShell cannot directly execute commands in WSL paths. The error messages you're seeing:

- `UNC paths are not supported` - Windows CMD doesn't support `\\wsl.localhost\...` paths
- `'vinxi' is not recognized` - The npm packages are not accessible from Windows context

**Solution**: Always run npm commands from within the WSL terminal when working with WSL-based projects.

## Verification

After successful installation, verify everything works:

```bash
# Check installed packages
npm list --depth=0

# Start dev server
npm run dev
```

You should see:
```
vinxi v0.5.11
➜ Local:   http://localhost:3000/
```

## Next Steps

Once the dev server is running:

1. Open `http://localhost:3000` in your browser
2. You should see the Metlab.edu home page
3. TanStack Router Devtools will appear in the bottom-right
4. TanStack Query Devtools will appear in the bottom-left

## Troubleshooting

### "The requested module does not provide an export named 'CONSTANTS'"

This is a TanStack package version mismatch. Run the fix script:

```bash
# From WSL terminal
cd /home/metrix/git/Metlab.edu/cloud-native/frontend
chmod +x fix-dependencies.sh
./fix-dependencies.sh
npm run dev
```

Or manually:
```bash
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm run dev
```

### "Cannot find module" errors

Run from WSL terminal:
```bash
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Port 3000 already in use

```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9

# Or use a different port by setting environment variable
PORT=3001 npm run dev
```

### Permission errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER /home/metrix/git/Metlab.edu/cloud-native/frontend
```

## Summary

✅ **Always use WSL terminal** for npm commands in WSL projects
✅ **Run `./setup.sh`** for automated setup
✅ **Access via `http://localhost:3000`** from any browser (Windows or WSL)
