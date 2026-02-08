# Bindicator Frontend - Quick Start Guide

## Prerequisites

- Node.js 18 or higher
- npm
- Backend API running at http://localhost:8000 (or configure NUXT_PUBLIC_API_URL)

## Installation Steps

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install all required packages including:
- Nuxt 3 and Vue
- TanStack Query for API state management
- FullCalendar for the calendar view
- Nuxt UI components
- date-fns for date handling
- VueUse for utilities
- openapi-typescript for type generation

### 2. Configure Environment

Create a `.env` file in the `frontend` directory:

```bash
NUXT_PUBLIC_API_URL=http://localhost:8000
```

Or use the default `/api` path if running through proxy.

### 3. Generate TypeScript Types

```bash
npm run generate:types
```

This fetches the OpenAPI schema from your backend and generates TypeScript types in `types/api.ts`.

**Note:** The backend API must be running for this step.

### 4. Start Development Server

```bash
npm run dev
```

The application will be available at http://localhost:3000

## Development Workflow

### Making Changes

1. **API Changes**: If the backend API changes, regenerate types:
   ```bash
   npm run generate:types
   ```

2. **Adding Features**: Follow the pattern:
   - Add API calls in `composables/use*Query.ts`
   - Use TanStack Query for data fetching
   - Mutations automatically invalidate queries
   - Toasts show automatically on success/error

3. **Styling**: Use Nuxt UI components and Tailwind CSS classes

### File Structure Quick Reference

```
app/
├── composables/          # API hooks (TanStack Query)
│   ├── useApi.ts
│   ├── useBinsQuery.ts
│   ├── useSchedulesQuery.ts
│   ├── useBinDayReplacementsQuery.ts
│   └── useSettingsQuery.ts
├── components/
│   ├── BinConfigRow.vue  # Bin editor component
│   └── layouts/
│       └── Default.vue   # Main layout
├── pages/
│   ├── index.vue         # Bins management (/)
│   ├── schedule.vue      # Calendar & schedules (/schedule)
│   └── settings.vue      # Settings (/settings)
└── plugins/
    └── store.ts          # TanStack Query setup
```

## Features Overview

### Bins Page (/)
- View all bins ordered by position
- Add new bins
- Edit bin name and color inline
- Delete bins (with confirmation)
- Reorder bins via:
  - Drag and drop
  - Up/down arrow buttons

### Schedule Page (/schedule)
- **Calendar View**:
  - See all future bin collection dates
  - Drag bins from sidebar onto calendar to create schedules
  - Navigate months with prev/next buttons
- **Schedules Table**:
  - View all configured schedules
  - Edit schedule details (start, end, repeat weeks)
  - Delete schedules
- **Bin Day Replacements**:
  - Add replacement dates (e.g., for holidays)
  - Move collection from one date to another
  - Delete replacements

### Settings Page (/settings)
- Configure display timeout (1-3600 seconds)
- Adjust with slider or number input
- Save changes with button

## Common Tasks

### Adding a New Bin

1. Go to Bins page (/)
2. Click "Add Bin"
3. Edit name and color
4. Reorder as needed

### Creating a Schedule

**Method 1: Drag and Drop**
1. Go to Schedule page
2. Drag a bin from sidebar onto a calendar date
3. Fill in optional end date and repeat weeks
4. Click Create

**Method 2: Manual Entry**
1. Go to Schedule page
2. Click "Add Schedule"
3. Select bin, start date, optional end date, repeat weeks
4. Click Create

### Adding a Holiday Replacement

1. Go to Schedule page
2. Scroll to "Bin Day Replacements" section
3. Click "Add Replacement"
4. Select "Replace Date" (original collection date)
5. Select "Replace With Date" (new collection date)
6. Click Create

## Troubleshooting

### Types Not Generating
- Ensure backend API is running
- Check `NUXT_PUBLIC_API_URL` in `.env`
- Verify backend has `/openapi.json` endpoint
- Check console for error messages

### Calendar Not Showing Events
- Backend needs to implement `GET /api/schedules/calendar` endpoint
- See `BACKEND_CALENDAR_ENDPOINT.md` for specification
- Check browser console for API errors

### Drag and Drop Not Working
- Ensure FullCalendar is properly initialized
- Check for JavaScript errors in console
- Try refreshing the page

### Data Not Updating
- TanStack Query caches data for 5 minutes
- Mutations automatically invalidate caches
- You can manually refresh with the retry button on error states

## Building for Production

```bash
npm run build
npm run preview
```

The build output will be in `.output/` directory.

## Next Steps

- Read `IMPLEMENTATION.md` for detailed implementation notes
- Check `BACKEND_CALENDAR_ENDPOINT.md` for required backend endpoint
- Review individual component files for inline documentation
- Explore Nuxt UI documentation: https://ui.nuxt.com
- Review TanStack Query docs: https://tanstack.com/query/latest/docs/vue/overview

## Getting Help

- Check browser console for errors
- Review TanStack Query devtools (will show in dev mode)
- Ensure backend API is returning expected data format
- Check that all environment variables are set correctly
