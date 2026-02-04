# Architecture

## Backend

This is an API wrapping the database. It serves the frontend.

## Database

This is shared database logic

## Hardware

This is the hardware logic

## To decide

- Do we need a `scheduler` that will handle the scheduling?
  - No, can just live in the fastapi since that's the only place that needs it.
  - Ah, but need to call a cron script regularly to update the database.
  - But also need to update it in the API.
  - So yes, put in the `core/scheduler` package
- How to handle database updates from API (signals?)