# Product Tour System Documentation

## Overview

The HealthForesight platform includes a comprehensive product tour system that provides:
- **First-time onboarding tours** - Automatically shown to new users
- **Module-specific tours** - On-demand tours for each major feature/module
- **Tour buttons** - Available on every page for easy access
- **Progress tracking** - Remembers which tours have been completed

## Architecture

### Components

1. **TourContext** (`src/contexts/TourContext.tsx`)
   - Manages tour state (running, completed tours, first-time status)
   - Persists state to localStorage
   - Provides hooks for starting/stopping tours

2. **TourManager** (`src/components/tour/TourManager.tsx`)
   - Renders the Joyride tour overlay
   - Handles tour step navigation
   - Manages tour completion

3. **TourButton** (`src/components/tour/TourButton.tsx`)
   - Reusable button component for triggering tours
   - Shows badge for uncompleted tours
   - Customizable size and tooltip

4. **FirstTimeTourHandler** (`src/components/tour/FirstTimeTourHandler.tsx`)
   - Automatically starts first-time tour on dashboard
   - Only runs once per user

5. **Tour Configurations** (`src/config/tours.ts`)
   - Defines all tour steps for each module
   - Includes rich content with images placeholders
   - Customizable step targeting

## Available Tours

### 1. Dashboard Tour (`dashboard`)
- **Trigger**: Automatic on first visit, or click tour button
- **Steps**: 6 steps covering:
  - Dashboard overview and persona views
  - Key metrics cards
  - Decision recommendations
  - Cost trend forecast
  - Risk register
  - Policy performance charts

### 2. Policy Catalog Tour (`policies`)
- **Trigger**: Click tour button on Policy Catalog page
- **Steps**: 4 steps covering:
  - Policy catalog overview
  - Search and filters
  - Policy list and cards
  - Creating new policies

### 3. Policy Builder Tour (`policy-builder`)
- **Trigger**: Click tour button on Policy Builder page
- **Steps**: 4 steps covering:
  - Builder overview
  - Builder steps navigation
  - Policy scope configuration
  - Policy levers configuration

### 4. Policy Workspace Tour (`policy-workspace`)
- **Trigger**: Click tour button on Policy Workspace page
- **Steps**: 4 steps covering:
  - Workspace tabs overview
  - Assumptions manager
  - Guardrails manager
  - Policy versions

### 5. Analysis Workspace Tour (`analysis-workspace`)
- **Trigger**: Click tour button on Analysis Workspace page
- **Steps**: 4 steps covering:
  - Analysis workspace overview
  - Analysis tabs
  - Impact results
  - Trust panel

### 6. What-If Analysis Tour (`whatif`)
- **Trigger**: Click tour button on What-If Analysis page
- **Steps**: 3 steps covering:
  - What-If analysis overview
  - Scenario builder
  - Scenario comparison

### 7. Data Ingestion Tour (`ingestions`)
- **Trigger**: Click tour button on Ingestion Dashboard
- **Steps**: 3 steps covering:
  - Ingestion dashboard overview
  - Upload data section
  - Ingestion history

## Adding Tours to New Pages

### Step 1: Add Tour Configuration

Edit `src/config/tours.ts` and add a new tour configuration:

```typescript
export const myNewTour: TourConfig = {
  module: 'my-module',
  title: 'My Module Tour',
  description: 'Learn about my module',
  steps: [
    {
      target: '.my-header',
      content: (
        <div>
          <h3>Welcome to My Module</h3>
          <p>This is the first step of the tour.</p>
        </div>
      ),
      placement: 'bottom',
      disableBeacon: true,
    },
    // Add more steps...
  ],
}

// Add to allTours object
export const allTours: Record<string, TourConfig> = {
  // ... existing tours
  'my-module': myNewTour,
}
```

### Step 2: Add Tour Module Type

Edit `src/contexts/TourContext.tsx` and add your module to the `TourModule` type:

```typescript
export type TourModule = 
  | 'dashboard'
  | 'policies'
  // ... existing modules
  | 'my-module'  // Add your module
```

### Step 3: Add Tour Button to Page

Add the tour button to your page header:

```typescript
import TourButton from '../components/tour/TourButton'

// In your component:
<Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
  <Typography variant="h4">My Page</Typography>
  <TourButton module="my-module" showBadge={true} />
</Box>
```

### Step 4: Add Class Names for Targeting

Add class names to elements you want to highlight in the tour:

```typescript
<Box className="my-header">
  {/* Content */}
</Box>

<Grid className="my-feature-section">
  {/* Content */}
</Grid>
```

## Tour Step Configuration

Each tour step can have the following properties:

- **target**: CSS selector or class name of the element to highlight
- **content**: React component or string with the step content
- **placement**: Position of tooltip (`top`, `bottom`, `left`, `right`, `auto`)
- **disableBeacon**: Whether to show the pulsing beacon (default: false for first step)

### Rich Content in Steps

You can include rich content in tour steps:

```typescript
{
  target: '.my-feature',
  content: (
    <div>
      <h3>Feature Title</h3>
      <p>Description of the feature.</p>
      <ul>
        <li>Point 1</li>
        <li>Point 2</li>
      </ul>
      <p style={{ marginTop: '10px', fontSize: '0.9em', color: '#666' }}>
        <strong>💡 Tip:</strong> Helpful tip for users.
      </p>
    </div>
  ),
  placement: 'right',
}
```

## Screenshots and Images

To add screenshots to tour steps, you can include images:

```typescript
{
  target: '.my-feature',
  content: (
    <div>
      <h3>Feature Overview</h3>
      <p>Description of the feature.</p>
      <img 
        src="/screenshots/my-feature.png" 
        alt="My Feature Screenshot"
        style={{ 
          width: '100%', 
          maxWidth: '500px', 
          marginTop: '10px',
          borderRadius: '8px',
          border: '1px solid #ddd'
        }}
      />
      <p style={{ marginTop: '10px', fontSize: '0.9em', color: '#666' }}>
        Screenshot showing the feature in action.
      </p>
    </div>
  ),
}
```

## First-Time Tour

The first-time tour automatically starts when:
1. User visits the dashboard for the first time
2. User hasn't seen the first-time tour before
3. No tour is currently running

To reset the first-time tour (for testing):

```typescript
import { useTour } from '../contexts/TourContext'

const { resetFirstTimeTour } = useTour()
resetFirstTimeTour()
```

## Tour State Management

Tour state is persisted in localStorage:
- `uepi_tour_state`: Array of completed tour modules
- `uepi_first_time_tour`: Boolean indicating if first-time tour was seen

## Styling

Tour styling can be customized in `TourManager.tsx`:

```typescript
styles: {
  options: {
    primaryColor: '#1976d2',  // Primary color
    zIndex: 10000,            // Z-index for overlay
  },
  tooltip: {
    borderRadius: 8,
    fontSize: 14,
  },
  // ... more styles
}
```

## Best Practices

1. **Keep tours concise**: 3-6 steps per tour is ideal
2. **Use clear targeting**: Add class names to key elements
3. **Provide context**: Explain why features matter, not just what they do
4. **Include tips**: Add helpful tips in tour steps
5. **Test thoroughly**: Ensure tours work on all screen sizes
6. **Update regularly**: Keep tours in sync with UI changes

## Troubleshooting

### Tour not starting
- Check that `TourProvider` wraps your app
- Verify `TourManager` is included in App.tsx
- Check browser console for errors

### Steps not highlighting correctly
- Verify class names exist on target elements
- Check that elements are rendered when tour starts
- Use browser DevTools to inspect selectors

### Tour state not persisting
- Check localStorage permissions
- Verify localStorage is not disabled
- Check for errors in console

## Future Enhancements

Potential improvements:
- [ ] Video tours for complex features
- [ ] Interactive tours with user actions
- [ ] Tour analytics (completion rates, drop-off points)
- [ ] Customizable tour paths based on user role
- [ ] Tour builder UI for non-developers
- [ ] Multi-language tour support

## Installation

The tour system uses `react-joyride`. To install:

```bash
cd apps/web
npm install react-joyride @types/react-joyride
```

## Dependencies

- `react-joyride`: ^2.5.2 - Tour library
- `@types/react-joyride`: TypeScript types

## Support

For questions or issues with the tour system, please refer to:
- [react-joyride documentation](https://docs.react-joyride.com/)
- This documentation file
- Code comments in tour components

