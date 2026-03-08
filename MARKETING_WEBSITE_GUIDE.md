# HealthForesight Marketing Website

## Overview

The HealthForesight marketing website is an enterprise-grade public-facing site designed for payer executives. It runs independently from the main application on port **3052**.

## Features

- **Enterprise Healthcare Design**: Authoritative, data-driven, strategic partner tone
- **Complete Information Architecture**: All pages from the blueprint
- **Responsive Layout**: Works on desktop and mobile
- **Sticky Navigation**: Professional header that stays visible while scrolling
- **Executive-Focused Content**: Designed for quick scanning and decision-making

## Pages

1. **Home Page** (`/`) - Executive landing with hero, market reality, missing intelligence, four pillars, and who it's for sections
2. **Platform** (`/platform`) - Detailed platform capabilities
3. **Solutions** (`/solutions`) - Buyer-oriented solution modules
4. **How It Works** (`/how-it-works`) - Functional flow visualization
5. **Who It's For** (`/who-its-for`) - Enterprise buyer personas
6. **Insights** (`/insights`) - Thought leadership content
7. **Company** (`/company`) - About, values, and trust signals
8. **Request Demo** (`/request-demo`) - Executive-friendly demo request form

## Running the Marketing Site

### Development

**Important**: The marketing site is completely separate from the main app. Make sure you're running it with the correct command:

```bash
cd apps/web
npm run dev:marketing
```

The site will be available at `http://localhost:3052`

**Note**: The Vite config automatically uses `index-marketing.html` instead of `index.html` when running the marketing site. If you see the main app instead of the marketing site, make sure:
1. You're using `npm run dev:marketing` (not `npm run dev`)
2. The port is 3052 (not 3050)
3. Check the browser console to see which entry point is loading

### Build

```bash
cd apps/web
npm run build:marketing
```

The built files will be in `apps/web/dist-marketing/`

## Design System

### Colors
- **Primary**: Deep Indigo/Navy (#3B2F8F) - Trust, governance, stability
- **Secondary**: Teal/Muted Cyan (#2EC4C6) - Intelligence, foresight, healthcare
- **Accent**: Soft Amber (#E6A23C) - Insight, warnings, risk signals
- **Neutrals**: Cool grays, off-white backgrounds

### Typography
- **Headlines**: IBM Plex Sans (bold, spaced, confident)
- **Body**: Inter (high readability)
- **Numbers**: Tabular numerals enabled

### Visual Language
- Abstract intelligence diagrams
- Policy → Impact → Learning loops
- Minimal icons, consistent stroke
- No stock photos of doctors
- Executive skimmability

## Architecture

- **Entry Point**: `src/main-marketing.tsx`
- **App Component**: `src/AppMarketing.tsx`
- **Layout**: `src/components/marketing/MarketingLayout.tsx`
- **Pages**: `src/pages/marketing/*`
- **Vite Config**: `vite.marketing.config.ts`
- **HTML**: `index-marketing.html`

## Notes

- The marketing site is completely separate from the main application
- It uses the same theme system but is optimized for public-facing content
- All navigation paths are relative to root (`/`) not `/marketing`
- The site runs on port 3052 to avoid conflicts with the main app (port 3050)
