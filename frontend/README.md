# Bindicator Frontend

A Nuxt 3 Vue frontend for the Bindicator bin collection management system.

## Features
- **Bins Management**: Add, edit, delete, and reorder bins with drag-and-drop
- **Schedule Management**: Create schedules by dragging bins onto a calendar, view all future bin days
- **Bin Day Replacements**: Manage holiday replacements and special collection dates
- **Settings**: Configure display timeout and other preferences

## Tech Stack
- **Nuxt 3** - Vue framework
- **TanStack Query (Vue Query)** - API state management with automatic caching and invalidation
- **FullCalendar** - Interactive calendar with drag-and-drop
- **Nuxt UI** - UI component library
- **date-fns** - Date formatting and manipulation
- **VueUse** - Composables for drag-and-drop
- **TypeScript** - Auto-generated types from OpenAPI schema

## Setup

### Prerequisites
- Node.js 18+ and npm
- Backend API running (for type generation)

### Installation
1. 
2. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
NUXT_PUBLIC_API_URL=http://localhost:8000
```

3. Generate TypeScript types from API:
```bash
npm run generate:types
```

### Development

```bash
npm run dev
```
The app will be available at `http://localhost:3000`

### Build for Production
```bash
npm run build
npm run preview
```

## Type Generation

The frontend uses `openapi-typescript` to generate TypeScript types from the OpenAPI schema:

```bash
npm run generate:types
```

This should be run:
- After initial setup
- When API schema changes
- After pulling updates that modify the backend

## Development Notes

### Date Handling
All dates are sent to the API as ISO date strings (YYYY-MM-DD) without time components.
Use `date-fns` `format()` function with `'yyyy-MM-dd'` format for API calls.
