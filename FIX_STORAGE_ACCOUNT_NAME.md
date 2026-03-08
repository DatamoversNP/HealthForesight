# Fix: Storage Account Name Validation

## Issue

Azure Storage Account names must:
- Be between **3 and 24 characters** in length
- Contain **only lowercase letters and numbers**
- Be **globally unique**

The previous script generated names like `healthforesight1768728542` which is **29 characters** - too long!

## Solution

I've updated the deployment scripts to generate shorter, valid names:

### Storage Account Name Format
- **Format**: `hf` + last 8 digits of timestamp
- **Example**: `hf12345678` (10 characters)
- **Max length**: 24 characters

### Example Generated Names
- Storage Account: `hf12345678` (10 chars)
- API App: `hf-api12345678` (13 chars)
- Web App: `hf-web12345678` (14 chars)

## Updated Scripts

✅ **DEPLOY_TO_AZURE.sh** - Fixed with validation
✅ **scripts/azure/deploy-app-service.sh** - Fixed name generation
✅ **AZURE_DEPLOYMENT_STEP_BY_STEP.md** - Updated example

## How to Use

### Option 1: Let Script Generate Names (Recommended)

The script will now automatically generate valid names:

```bash
./DEPLOY_TO_AZURE.sh
```

When prompted, just press Enter to use the generated names, or provide your own (must be valid).

### Option 2: Provide Your Own Names

When running the script, you can provide your own names, but they must meet Azure requirements:

**Storage Account Name:**
- 3-24 characters
- Only lowercase letters (a-z) and numbers (0-9)
- No hyphens, underscores, or special characters
- Example: `hfstorage123` ✅
- Example: `HealthForesight` ❌ (uppercase)
- Example: `hf-storage` ❌ (hyphen)

**App Service Names:**
- Can contain hyphens and lowercase letters
- Example: `hf-api-123` ✅

## Validation

The script now validates storage account names and will:
1. Check if the name is valid (3-24 chars, lowercase+numbers only)
2. Use the generated name if your input is invalid
3. Show an error message explaining the requirements

## Example Output

```
Storage Account Name (must be globally unique, 3-24 chars, lowercase+numbers only) [hf12345678]: 
```

Just press Enter to use `hf12345678`, or type your own valid name.

## Testing

You can test the name generation:

```bash
# Generate a test name
TIMESTAMP=$(date +%s | tail -c 8)
echo "hf${TIMESTAMP}"

# Output: hf12345678 (10 characters)
```

## Summary

✅ **Fixed**: Scripts now generate valid storage account names
✅ **Validation**: Input validation added
✅ **Documentation**: Updated guides with correct examples
✅ **Ready**: You can now deploy without name validation errors

Run `./DEPLOY_TO_AZURE.sh` again - it should work now!
