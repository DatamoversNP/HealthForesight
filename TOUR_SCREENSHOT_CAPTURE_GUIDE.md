# Automated Screenshot Capture Guide

## 🎯 Overview

I've created an **automated screenshot capture system** that uses Playwright to programmatically take screenshots of all tour targets. No manual screenshot taking required!

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd apps/web
npm install playwright
npx playwright install chromium
```

### Step 2: Start Frontend Server

Make sure your frontend is running:

```bash
npm run dev
```

The frontend should be accessible at `http://localhost:3050`

### Step 3: Capture Screenshots

Run the automated capture script:

```bash
npm run capture-screenshots
```

Or use the shell script:

```bash
./scripts/capture-screenshots-simple.sh
```

## 📋 What Gets Captured

The script automatically captures screenshots for:

### Dashboard Tour (6 screenshots)
- Dashboard overview
- Key metrics cards
- Decision recommendations
- Cost trend forecast
- Risk register
- Policy performance

### Policy Catalog Tour (4 screenshots)
- Policy catalog overview
- Search and filters
- Policy list
- Create policy options

### Policy Builder Tour (4 screenshots)
- Policy builder header
- Builder steps navigation
- Scope configuration
- Levers configuration

### Policy Workspace Tour (4 screenshots)
- Workspace tabs
- Assumptions manager
- Guardrails manager
- Version control

### Analysis Workspace Tour (4 screenshots)
- Analysis overview
- Analysis tabs
- Impact results
- Trust panel

### What-If Analysis Tour (3 screenshots)
- What-if overview
- Scenario builder
- Scenario comparison

### Data Ingestion Tour (3 screenshots)
- Ingestion dashboard
- Upload interface
- Ingestion history

**Total: 28 screenshots** automatically captured!

## 🔧 How It Works

1. **Launches Browser**: Uses Playwright to launch Chromium
2. **Navigates Pages**: Automatically navigates to each page
3. **Finds Elements**: Locates tour target elements by CSS selector
4. **Captures Screenshots**: Takes element-specific screenshots with padding
5. **Saves Files**: Saves to `public/screenshots/tours/`

## 📁 Output Location

All screenshots are saved to:
```
apps/web/public/screenshots/tours/
```

## ✅ Verification

After capturing, verify all targets work:

```bash
npm run test-tour-targeting
# or
./scripts/test-tour-targeting.sh
```

This script checks that all tour target class names exist in the codebase.

## 🎨 Screenshot Specifications

- **Format**: PNG
- **Resolution**: Element-specific (with 20px padding)
- **Viewport**: 1920x1080
- **Quality**: High (Playwright default)

## 🔍 Troubleshooting

### Element Not Found

If an element is not found:
1. Check that the page is fully loaded
2. Verify the class name exists in the component
3. Check browser console for errors
4. Ensure you're logged in (if required)

### Login Required

The script attempts automatic login. If login fails:
1. Check login page selectors
2. Update login credentials in the script
3. Manually log in before running the script

### Screenshots Are Empty

If screenshots are captured but appear empty:
1. Check element visibility (may be hidden)
2. Verify element has content
3. Check viewport size
4. Ensure element is in viewport

## 🎯 Customization

### Adjust Screenshot Settings

Edit `scripts/capture-tour-screenshots-playwright.js`:

```javascript
// Change viewport size
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
})

// Change padding
const padding = 20 // Adjust as needed

// Change wait times
wait: 2000 // Milliseconds to wait after page load
```

### Add New Targets

Add to `TOUR_TARGETS` object:

```javascript
'my-new-tour': [
  { 
    target: '.my-element', 
    name: 'my-screenshot.png', 
    route: '/my-page', 
    wait: 2000 
  },
]
```

## 📊 Feedback System

After completing a tour, users are prompted for feedback:
- **Rating**: 1-5 stars
- **Helpfulness**: Yes/No
- **Category**: Content, Clarity, Completeness, etc.
- **Comments**: Free-form text

Feedback is saved to localStorage and can be exported for analysis.

## 🎬 Demo Workflow

1. **Capture Screenshots**: Run `npm run capture-screenshots`
2. **Review Screenshots**: Check `public/screenshots/tours/`
3. **Optimize if Needed**: Compress or resize images
4. **Test Tours**: Start tours and verify screenshots appear
5. **Gather Feedback**: Use feedback system to improve tours

## 💡 Tips

- **Run during development**: Capture screenshots as you build features
- **Update regularly**: Re-capture when UI changes
- **Version control**: Commit screenshots to track UI evolution
- **Optimize images**: Use tools like ImageOptim to reduce file size
- **Test targeting**: Run verification script after UI changes

## 🚀 Advanced Usage

### Headless Mode

Edit the script to run in headless mode:

```javascript
const browser = await chromium.launch({
  headless: true, // Change to true
})
```

### Batch Processing

Run for multiple environments:

```bash
# Development
BASE_URL=http://localhost:3050 npm run capture-screenshots

# Staging
BASE_URL=https://staging.example.com npm run capture-screenshots

# Production
BASE_URL=https://app.example.com npm run capture-screenshots
```

## 📝 Next Steps

1. ✅ **Install Playwright**: `npm install playwright && npx playwright install chromium`
2. ✅ **Start Frontend**: `npm run dev`
3. ✅ **Capture Screenshots**: `npm run capture-screenshots`
4. ✅ **Verify Targeting**: `npm run test-tour-targeting`
5. ✅ **Test Tours**: Start tours and verify screenshots appear correctly

The automated system handles everything - just run the script and all screenshots will be captured automatically!

