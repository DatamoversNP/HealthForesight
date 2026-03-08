# Documentation Portal Guide

## Overview

The HealthForesight Documentation Portal provides comprehensive documentation covering:
- Product Overview & Core Principles
- System Architecture
- Data Flow (End-to-End)
- Data Models (All Models)
- Source Data Specifications
- Technical Documentation (API Endpoints, Implementation Details)

## Accessing the Documentation Portal

### Option 1: Via Main Application (Port 3050)
The documentation portal is accessible via the main application:

1. Start the main web server (if not already running):
   ```bash
   cd apps/web
   npm run dev
   ```

2. Navigate to: `http://localhost:3050/documentation`

3. Or click "Documentation" in the navigation menu

### Option 2: Dedicated Documentation Server (Port 3051)
To run the documentation portal on a dedicated port (3051):

```bash
cd apps/web
npm run dev:docs
```

Then access at: `http://localhost:3051/documentation`

Or use the convenience script:
```bash
./start-docs-server.sh
```

## Documentation Sections

### 1. Product Overview
- **Introduction**: Overview of HealthForesight system
- **Core Principles**: Separation of concerns, traceability, behavioral modeling, transparency
- **Product Flow**: Continuous cycle from data ingestion to learning

### 2. System Architecture
- **Architecture Overview**: All 6 core components
- **Data Flow**: Detailed end-to-end data processing stages
  - Data Ingestion
  - Baseline Computation
  - Predicted Impact Generation
  - Observation Analysis
  - Learning Loop

### 3. Data Models
- **Core Data Models**: Complete JSON schemas for:
  - Data Period Model
  - Policy Model
  - Baseline Model
  - Observation Model
- **Metric Dictionary**: Complete list of all metrics (M1-M6+) with formulas, denominators, and units

### 4. Source Data Specifications
- **Claims Lines Schema**: Complete data contract with all fields, types, and requirements

### 5. Technical Documentation
- **API Endpoints**: Documentation for core endpoints
- **Implementation Details**: 
  - File-based storage structure
  - Policy scoping algorithm
  - Learning loop implementation

## Features

- **Side Navigation**: Quick access to all documentation sections
- **Tabbed Content**: Each section has multiple subsections with tabs
- **Code Examples**: JSON schemas and code snippets with syntax highlighting
- **Accordion Layout**: Expandable sections for detailed information
- **Table Formatting**: Well-formatted tables for metrics and schemas

## Adding More Documentation

To add more documentation sections:

1. Edit `apps/web/src/pages/DocumentationPortalPage.tsx`
2. Add new sections to the `documentationSections` array
3. Each section can have multiple subsections with React content
4. Use the same patterns for code blocks, tables, and accordions

## Notes

- The documentation portal is fully integrated with the main application
- All navigation links work within the portal
- Code examples use dark theme for better readability
- All content is client-side rendered for fast navigation
