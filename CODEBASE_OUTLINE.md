# Codebase Outline

This document provides a high-level overview of the project structure and key files.

## Backend (`backend/`)
- `alembic.ini`: Alembic configuration for database migrations.
- `cred.txt`: (Sensitive, generally ignored by git) Credentials or sensitive information.
- `requirements.txt`: Python dependencies for the backend.
- `alembic/`: Database migration scripts.
    - `versions/`: Directory containing individual migration files.
- `app/`
    - `__init__.py`: Initializes the FastAPI application.
    - `main.py`: Main entry point for the FastAPI application.
    - `api/`
        - `__init__.py`: Initializes the API module.
        - `v1/`
            - `__init__.py`: Initializes API version 1.
            - `router.py`: Main API router for version 1, includes sub-routers.
            - `endpoints/`
                - `__init__.py`: Exposes API endpoints.
                - `auth.py`: Authentication-related API endpoints (registration, login, etc.).
    - `core/`
        - `__init__.py`: Initializes the core module.
        - `config.py`: Application configuration settings.
        - `database.py`: Database connection and session management (SQLAlchemy).
        - `dependencies.py`: FastAPI dependency injection for authentication, database sessions, etc.
        - `security.py`: Security utilities (password hashing, JWT token management, OAuth2).
    - `models/`
        - `__init__.py`: Initializes the models module.
        - `auth.py`: Database models for authentication (e.g., Refresh Tokens, Password Reset Tokens).
        - `user.py`: Database model for users.
        - `cache.py`: Cache related database models.
        - `fitness.py`: Fitness related database models.
        - `package.py`: Package tracking related database models.
        - `server.py`: Server monitoring related database models.
        - `widget.py`: Widget related database models.
    - `schemas/`
        - `__init__.py`: Exposes Pydantic schemas.
        - `auth.py`: Pydantic schemas for authentication (request/response models for user, token, etc.).
    - `services/`
        - `auth_service.py`: Business logic for authentication operations.
- `test.db`: SQLite database file used for testing or local development.
- `tests/`
    - `__init__.py`: Initializes the tests module.
    - `test_auth.py`: Unit tests for the authentication system.

## Frontend (`frontend/`)
- `.gitignore`: Git ignore rules for frontend.
- `eslint.config.js`: ESLint configuration.
- `index.html`: Main HTML file.
- `package-lock.json`: Node.js package lock file.
- `package.json`: Node.js project configuration and dependencies.
- `postcss.config.js`: PostCSS configuration.
- `README.md`: Frontend README.
- `tailwind.config.js`: Tailwind CSS configuration.
- `vite.config.js`: Vite build tool configuration.
- `node_modules/`: Node.js dependencies.
- `public/`: Static assets.
- `src/`: Frontend source code.
    - `App.css`: Main application CSS.
    - `App.jsx`: Main application component, handles routing and includes the `PrivateRoute` component for protected routes.
    - `index.css`: Main CSS.
    - `main.jsx`: Main entry point for the React application.
    - `assets/`: Static assets.
    - `components/`: React components.
        - `auth/`: Authentication components.
            - `LoginForm.jsx`: Component for user login form.
            - `RegisterForm.jsx`: Component for new user registration form.
        - `common/`: Common reusable components.
        - `layout/`: Layout components.
            - `AuthLayout.jsx`: Provides a consistent layout for authentication forms.
        - `widgets/`: Directory for individual widget components.
    - `contexts/`: React contexts.
        - `AuthContext.jsx`: Provides authentication context and state to the React application, managing user login/logout status and token.
    - `hooks/`: React hooks for custom logic.
    - `services/`: Frontend services (e.g., API calls).
        - `api.js`: Centralized API client configuration and utility functions.
        - `AuthService.js`: Handles authentication-related API calls (login, register, logout, refresh).
    - `styles/`: Stylesheets.
    - `utils/`: Utility functions.

## Documentation (`docs/`)
- `PROJECT_PLAN.md`: Overall project plan.
- `TECH_SPECS.md`: Technical specifications.
- `tasks/`: Directory for task-specific documentation (pending tasks).
    - `005_dashboard_layout_widget_framework.md`: Task for dashboard layout and widget framework.
    - `006_weather_widget.md`: Task for weather widget.
    - `007_stock_market_widget.md`: Task for stock market widget.
    - `008_cryptocurrency_widget.md`: Task for cryptocurrency widget.
    - `009_server_monitoring_dashboard.md`: Task for server monitoring dashboard.
    - `010_server_monitoring_agent.md`: Task for server monitoring agent.
    - `011_package_tracking_widget.md`: Task for package tracking widget.
    - `012_weather_widget.md`: Task for weather widget (duplicate, potentially to be resolved).
    - `013_stock_crypto_widgets.md`: Task for stock and crypto widgets.
    - `014_calendar_widget.md`: Task for calendar widget.
    - `015_news_widget.md`: Task for news widget.
    - `016_fitness_stats_widget.md`: Task for fitness stats widget.
    - `017_dashboard_layout_polish.md`: Task for dashboard layout polishing.
    - `completed_tasks.md`: List summarizing all completed tasks.
    - `completed/`: Directory for documentation of completed tasks.
        - `001_project_setup.md`: Documentation for initial project setup.
        - `002_database_models.md`: Documentation for database models.
        - `003_authentication_system.md`: Documentation for the authentication system.
        - `004_frontend_auth_ui.md`: Documentation for frontend authentication UI.
        - `token/`: Directory containing images related to token handling (e.g., `step_3.png`, `step_4.png`).

## Other
- `.gitignore`: Git ignore rules for the project root.
- `mysql_setup_instructions.sql`: SQL script for MySQL setup.
- `README.md`: Project README.