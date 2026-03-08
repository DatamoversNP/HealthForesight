# Database Viewer Module

## Overview

A new database viewer module has been created to allow viewing database tables and data directly from the web interface. This is useful for developers and administrators to inspect the database structure and contents.

## Features

### Backend API (`apps/api/src/uepi_api/routers/database_viewer.py`)

1. **List Tables** - `GET /api/v1/database/tables`
   - Returns all tables in the database with row counts
   - Response: `[{name: string, row_count: number | null}]`

2. **Get Table Schema** - `GET /api/v1/database/tables/{table_name}/schema`
   - Returns detailed schema information:
     - Columns (name, type, nullable, default, primary key)
     - Primary keys
     - Foreign keys
     - Indexes

3. **Get Table Data** - `GET /api/v1/database/tables/{table_name}/data`
   - Returns paginated table data
   - Parameters:
     - `limit` (1-1000, default: 100)
     - `offset` (default: 0)
     - `order_by` (optional, e.g., "id DESC")
   - Response includes total count and pagination info

4. **Get Table Count** - `GET /api/v1/database/tables/{table_name}/count`
   - Returns row count for a table

### Frontend Page (`apps/web/src/pages/DatabaseViewerPage.tsx`)

Features:
- **Table List** (left sidebar):
  - Searchable list of all database tables
  - Shows row count for each table
  - Click to select a table

- **Schema View** (top right):
  - Displays all columns with types, nullable status, defaults
  - Shows primary keys (with key icon)
  - Lists foreign key relationships
  - Shows indexes

- **Data View** (bottom right):
  - Paginated table view of data
  - Shows 50 rows per page by default
  - Pagination controls
  - Displays NULL values clearly
  - Handles JSON/object values

## Access

1. **Route**: `/database-viewer`
2. **Menu**: Added to navigation menu as "Database Viewer" with Storage icon
3. **Authentication**: Requires authentication (uses `get_demo_current_user`)

## Security

- All endpoints require authentication
- Uses existing authentication middleware
- SQL injection protection:
  - Table names validated against inspector
  - Order by parameter sanitized with regex
  - Uses parameterized queries where possible

## Usage

1. Navigate to "Database Viewer" in the menu
2. Select a table from the left sidebar
3. View schema information in the top panel
4. Browse data in the bottom panel
5. Use pagination to navigate through large tables

## Files Created/Modified

### Created:
- `apps/api/src/uepi_api/routers/database_viewer.py` - Backend API endpoints
- `apps/web/src/pages/DatabaseViewerPage.tsx` - Frontend page component

### Modified:
- `apps/api/src/uepi_api/main.py` - Registered database_viewer router
- `apps/web/src/App.tsx` - Added route for DatabaseViewerPage
- `apps/web/src/components/Layout.tsx` - Added menu item and StorageIcon import

## Testing

To test the module:

1. Start the API server:
   ```bash
   cd apps/api/src
   python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Start the frontend:
   ```bash
   cd apps/web
   npm run dev
   ```

3. Navigate to `http://localhost:3050/database-viewer`

4. Test endpoints directly:
   ```bash
   curl http://localhost:8000/api/v1/database/tables \
     -H "Authorization: Bearer dev-token-123"
   ```

## Future Enhancements

Potential improvements:
- Export table data to CSV/JSON
- Filter/search within table data
- Execute custom SQL queries (with proper security)
- View table relationships graph
- Compare table schemas
- View table statistics (size, indexes usage, etc.)
