# Install Azure CLI on macOS

## Quick Installation

### Option 1: Using Homebrew (Recommended)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Azure CLI
brew install azure-cli

# Verify installation
az --version
```

### Option 2: Using Installer Script

```bash
# Download and run installer
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Or use the macOS installer
curl -L https://aka.ms/InstallAzureCLIMacOS | bash
```

### Option 3: Using pip (Python)

```bash
# Install via pip
pip3 install azure-cli

# Verify installation
az --version
```

## After Installation

1. **Login to Azure:**
   ```bash
   az login
   ```
   This will open a browser for authentication.

2. **Set your subscription (if you have multiple):**
   ```bash
   # List subscriptions
   az account list --output table
   
   # Set active subscription
   az account set --subscription "Your Subscription Name or ID"
   ```

3. **Verify you're logged in:**
   ```bash
   az account show
   ```

## Verify Installation

```bash
# Check version
az --version

# Should show something like:
# azure-cli                         2.xx.x
# core                              2.xx.x
# telemetry                          1.x.x
```

## Troubleshooting

### Issue: Command not found after installation

**Solution**: Add to PATH or restart terminal
```bash
# Add to PATH (if using Homebrew)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or restart your terminal
```

### Issue: Permission denied

**Solution**: Use sudo or install via Homebrew
```bash
# Homebrew doesn't need sudo
brew install azure-cli
```

### Issue: Python version conflicts

**Solution**: Use Homebrew which manages dependencies
```bash
brew install azure-cli
```

## Next Steps

Once Azure CLI is installed:

1. Run the deployment script:
   ```bash
   ./deploy-complete-to-azure.sh
   ```

2. Or follow the manual guide:
   ```bash
   # Read the guide
   cat AZURE_COMPLETE_DEPLOYMENT_GUIDE.md
   ```


