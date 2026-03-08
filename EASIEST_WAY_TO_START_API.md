# Easiest Way to Start API - Use Virtual Environment

## The Problem

Your system uses an "externally managed" Python environment (macOS with Homebrew Python), which prevents installing packages directly.

## The Solution

Use a virtual environment! I've created a script that does everything automatically.

## One Command to Start Everything

Just run this:

```bash
cd "/Users/nilesh.patil/Downloads/Utilization Elastisity and Policy Impact Solution"
./setup-venv-and-start-api.sh
```

## What It Does

1. ✅ Creates a virtual environment (`.venv` folder) - only once
2. ✅ Installs all Python packages in the virtual environment
3. ✅ Starts the API server
4. ✅ Everything is isolated and clean

## First Time

The first time you run it:
- Takes 2-3 minutes (installing packages)
- Creates `.venv` folder
- Then starts the API

## After That

Every time after:
- Just runs in seconds
- Uses the existing virtual environment
- Starts the API immediately

## To Stop API

```bash
./stop-api.sh
```

## To Restart API

```bash
./setup-venv-and-start-api.sh
```

## That's It!

One script, everything automated. The virtual environment keeps everything clean and isolated.
