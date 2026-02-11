# Bindicator

## Overview

Bindicator is a Raspberry Pi-based smart bin collection reminder system. It displays upcoming bin collection schedules on an LCD screen with physical bin buttons and LED indicators, helping you never miss bin day again. The system features a web interface for schedule management, automated scheduling logic, and real-time updates via MQTT.

For more information, visit the [project documentation](https://tobytwigger.github.io/projects/whenisbins).

## Architecture

The Bindicator project is built on a modular architecture with four main components:

### Backend (`backend/`)
A **FastAPI** REST API that serves as the primary interface for updating and managing data. The backend is purely focused on handling HTTP requests and updating an SQLite database. It provides endpoints for managing:
- Bin configurations
- Collection schedules
- Bin day replacements
- Put-out tracking
- Hardware settings

### Core (`core/`)
The core layer handles all database interactions and scheduling logic:
- **Database**: Uses a repository pattern to manage SQLite database operations, with models and schemas defined for all entities
- **Scheduler**: Creates and explores a Polars DataFrame for efficient handling of thousands of bin collections, allowing fast queries and date-based exploration of collection schedules
- Database migrations managed via Alembic

### Hardware (`hardware/`)
A Python application that runs on the Raspberry Pi to control physical components:
- **Drivers**: Abstractions for LCD display, LED lights, physical buttons, and MQTT communication
- **Screens**: State machine-based UI screens that display different views (today's bins, upcoming collections, settings)
- **App Runner**: Main event loop that handles input events, screen transitions, and output updates
- Communicates with the backend via MQTT for real-time database updates

### Frontend (`frontend/`)
A **Nuxt 3** web application that provides a user-friendly interface for managing schedules:
- Built as a static site (SSG) compiled to static HTML/CSS/JS
- Served through Nginx on the Raspberry Pi
- Provides interfaces for configuring bins, schedules, replacements, and viewing put-out history
- Responsive design suitable for both desktop and mobile devices

