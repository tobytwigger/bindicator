# Bindicator Frontend Implementation Summary

## What Has Been Implemented

### 1. Project Setup & Configuration

#### Dependencies Added (package.json)
- `@tanstack/vue-query` - API state management
- `@fullcalendar/vue3`, `@fullcalendar/daygrid`, `@fullcalendar/interaction` - Calendar with drag-and-drop
- `@vueuse/core` - Composables including sortable for drag-and-drop
- `date-fns` - Date formatting and manipulation
- `openapi-typescript` - Type generation from OpenAPI schema

#### Configuration Files
- `.env` - Environment configuration with `NUXT_PUBLIC_API_URL`
- `nuxt.config.ts` - Added runtime config for API URL
- `scripts/generate-types.js` - Script to fetch OpenAPI schema and generate TypeScript types
- `app/plugins/store.ts` - Configured TanStack Query with defaults

### 2. API Layer (Composables)

#### `composables/useApi.ts`
- Base API fetch wrapper
- Typed fetch function using generated schemas
- Error handling
- Automatic JSON parsing

#### `composables/useBinsQuery.ts`
- `useBinsQuery()` - Query for fetching bins list
- `useBinMutations()` - Mutations for:
  - Create bin
  - Update bin (name, colour)
  - Delete bin
  - Move bin earlier/later
  - Set bin position
- Toast notifications on success/error
- Automatic query invalidation after mutations

#### `composables/useSchedulesQuery.ts`
- `useSchedulesQuery()` - Query for fetching schedules
- `useCalendarQuery(start, end)` - Query for calendar events in date range
- `useScheduleMutations()` - Mutations for:
  - Create schedule (with date conversion to YYYY-MM-DD)
  - Update schedule
  - Delete schedule
- Invalidates both schedules and calendar queries

#### `composables/useBinDayReplacementsQuery.ts`
- `useBinDayReplacementsQuery()` - Query for replacements
- `useBinDayReplacementMutations()` - Mutations for:
  - Create replacement
  - Delete replacement
- Date conversion to YYYY-MM-DD format

#### `composables/useSettingsQuery.ts`
- `useSettingsQuery()` - Query for settings
- `useSettingsMutations()` - Update settings mutation

### 3. Pages

#### `pages/index.vue` - Bins Management
**Features:**
- List all bins ordered by position
- Skeleton loading states
- Drag-and-drop reordering using `@vueuse/core` sortable
- Add new bin button
- Empty state with prompt to add first bin
- Error state with retry button
- Uses `BinConfigRow` component for each bin

**Drag-and-Drop:**
- Bins container is sortable
- On drop, calls `setBinPosition` mutation with new position
- Visual feedback during drag

#### `pages/schedule.vue` - Schedule & Calendar Management
**Features:**
- **Bins Sidebar**: Shows all bins as draggable items
- **FullCalendar**: 
  - Month view
  - Displays events from `/schedules/calendar` endpoint
  - Accepts dropped bins to create schedules
  - Navigable with prev/next/today buttons
  - Auto-updates date range on navigation
- **Schedules Table**: 
  - Lists all schedules
  - Shows bin (with color), start/end dates, repeat weeks
  - Edit and delete actions
- **Bin Day Replacements Table**:
  - Lists all replacements
  - Shows replace date and replace_with date
  - Delete action
- **Add Schedule Modal**:
  - Bin selector dropdown
  - Start date picker
  - Optional end date picker
  - Repeat weeks number input
  - Opens when:
    - Clicking "Add Schedule" button
    - Dropping a bin on calendar (pre-fills bin and date)
- **Add Replacement Modal**:
  - Replace date picker
  - Replace with date picker

**Calendar Integration:**
- Draggable bins from sidebar
- Drop zones on calendar dates
- Visual feedback during drag
- Events colored by bin colour
- Events show bin name

#### `pages/settings.vue` - Settings Management
**Features:**
- Timeout slider (1-3600 seconds)
- Numeric input for precise value
- Range indicator (1 second to 1 hour)
- Save button (only enabled when changed)
- Skeleton loading state
- Error state with retry
- About section with tips

### 4. Components

#### `components/BinConfigRow.vue`
**Features:**
- Drag handle for reordering
- Bin icon with color preview
- Name input (inline editing)
- Color picker (native HTML color input)
- Up/down arrow buttons (disabled at boundaries)
- Delete button
- Auto-saves on blur or Enter key
- Emits events for update, delete, move-earlier, move-later

**Props:**
- `bin` - Bin object
- `isFirst` - Disable up arrow
- `isLast` - Disable down arrow

#### `components/layouts/Default.vue`
**Features:**
- Header with title "The Bindicator"
- Color mode selector (system/light/dark)
- Navigation tabs for Bins (/) / Schedule / Settings
- Active tab highlighting based on current route
- Wraps page content in card

### 5. Type Generation

#### `types/api.ts` (Auto-generated)
- Generated from OpenAPI schema
- Used throughout app for type safety
- Includes all API schemas:
  - Bin, BinCreate, BinEdit
  - Schedule, ScheduleCreate, ScheduleEdit
  - BinDayReplacement, BinDayReplacementCreate
  - Settings, SettingsEdit
  - PaginationResponse types

#### Generation Script
- `scripts/generate-types.js` fetches from `${NUXT_PUBLIC_API_URL}/openapi.json`
- Run with `npm run generate:types`

### 6. Setup Integration

Updated `scripts/setup.sh` to:
1. Navigate to frontend directory
2. Run `npm install`
3. Display message about generating types after API is running

## What Still Needs Implementation (Backend)

### Required Backend Endpoint

#### `GET /schedules/calendar`
**Query Parameters:**
- `start` - ISO date string (YYYY-MM-DD)
- `end` - ISO date string (YYYY-MM-DD)

**Response Format:**
```json
[
  {
    "date": "2026-02-15",
    "bins": [
      {
        "id": 1,
        "name": "Recycling",
        "colour": "#2ecc40"
      },
      {
        "id": 2,
        "name": "General Waste",
        "colour": "#444444"
      }
    ]
  },
  {
    "date": "2026-02-22",
    "bins": [
      {
        "id": 3,
        "name": "Garden Waste",
        "colour": "#ffdc00"
      }
    ]
  }
]
```

**Implementation Notes:**
- Calculate bin collection dates from schedules within date range
- Consider `repeat_weeks` to compute all occurrences
- Apply bin day replacements (replace dates with replace_with)
- Group by date
- Return bins for each date

## Testing Checklist

### Bins Page
- [ ] Load bins list
- [ ] Create new bin
- [ ] Edit bin name inline
- [ ] Edit bin color
- [ ] Delete bin (with confirmation)
- [ ] Reorder bins with drag-and-drop
- [ ] Move bin up with arrow
- [ ] Move bin down with arrow
- [ ] Skeleton shows while loading
- [ ] Empty state shows when no bins
- [ ] Toast notifications show on success/error

### Schedule Page
- [ ] Load schedules list
- [ ] Load calendar events (after backend endpoint implemented)
- [ ] Drag bin from sidebar onto calendar
- [ ] Create schedule from dropped bin
- [ ] Create schedule from "Add Schedule" button
- [ ] Edit schedule
- [ ] Delete schedule (with confirmation)
- [ ] Calendar navigation (prev/next/today)
- [ ] Load replacements list
- [ ] Create replacement
- [ ] Delete replacement (with confirmation)
- [ ] Skeleton shows while loading

### Settings Page
- [ ] Load current timeout setting
- [ ] Change timeout with slider
- [ ] Change timeout with number input
- [ ] Save button disabled when no changes
- [ ] Save settings
- [ ] Toast notification on save
- [ ] Skeleton shows while loading

### General
- [ ] Navigation between pages works
- [ ] Active tab highlights correctly
- [ ] Dark mode toggle works
- [ ] All error states show properly
- [ ] All loading states show properly
- [ ] Toast notifications appear and disappear

## Running the Application

1. Ensure backend API is running
2. Generate types: `cd frontend && npm run generate:types`
3. Start dev server: `npm run dev`
4. Open `http://localhost:3000`

## Next Steps

1. Implement `GET /schedules/calendar` endpoint in backend
2. Test all CRUD operations
3. Add form validation where needed
4. Consider adding optimistic updates for better UX
5. Add keyboard shortcuts (e.g., Esc to close modals)
6. Add loading spinners for inline actions
7. Consider adding undo functionality for destructive actions
8. Add pagination controls if needed (currently loads 100 items per query)
