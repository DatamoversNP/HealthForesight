# App Service Plan Quota Request - Step by Step

## On the Support Request Page

### Step 1: Problem Description Tab

1. **Issue type**: ✅ Already selected "Service and subscription limits (quotas)"

2. **Subscription**: ✅ Already selected "Azure subscription 1"

3. **Quota type**: 
   - Click the dropdown
   - Type "app" in the search box
   - **Select: "Function or Web App (Windows and Linux)"**
   - This is the correct option for App Service Plan quotas

4. Click **"Next"** to proceed to Step 2

### Step 2: Recommended Solution Tab

- Azure will show recommended solutions
- Click **"Next"** to continue

### Step 3: Additional Details Tab

Fill in:

**Severity**: 
- Select **"C - Minimal impact"** or **"D - Moderate impact"**

**Problem description**:
```
Request quota increase for App Service Plan Basic tier.

Subscription: Azure subscription 1
Region: East US
Current limit: 0 cores
Requested limit: 1 core for Basic B1 plan

Purpose: Deploying HealthForesight platform API backend (FastAPI/Python application).
Need Basic tier App Service Plan to host the API service.
```

**Additional details** (optional):
```
This is for a production healthcare analytics platform.
The application requires Basic tier (B1) with 1 core and 1.75 GB RAM.
Currently unable to create App Service Plan due to quota limit of 0.
```

**Contact method**: Select your preference (Email/Phone)

**Contact details**: Your email/phone

Click **"Next"**

### Step 4: Review + Create Tab

- Review all information
- Click **"Create"**

## After Submission

- You'll receive a confirmation email
- Support request will be created
- Usually approved within 24-48 hours
- Sometimes instant for small requests

## While Waiting

Upload your data to Azure File Storage (no quota needed):

```bash
./deploy-to-azure-free-tier.sh
```

This will upload all your data files while you wait for quota approval.


