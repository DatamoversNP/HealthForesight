# Start Web Server on Port 3050

The main application needs the web server running on port 3050.

## Quick Start

```bash
cd apps/web
npm run dev
```

This will start the Vite dev server on port 3050.

## Or from project root:

```bash
cd apps/web && npm run dev
```

## Or use the start script:

```bash
./start-both-servers.sh
```

This starts both API (port 8000) and Web (port 3050) servers.

## Verify

Once started, access:
- **Main App**: http://localhost:3050
- **Documentation Portal**: http://localhost:3051 (separate server)
