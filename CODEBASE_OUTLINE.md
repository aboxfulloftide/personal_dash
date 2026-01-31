# Codebase Outline

This document provides a high-level overview of the project structure and key files.

## Backend (`backend/`)
- `alembic.ini`: Alembic configuration for database migrations.
- `cred.txt`: (Sensitive, generally ignored by git) Credentials or sensitive information.
- `requirements.txt`: Python dependencies for the backend.
- `alembic/`: Database migration scripts.
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
        - `database.py`: Database connection and session management.
        - `dependencies.py`: FastAPI dependency injection for authentication.
        - `security.py`: Security utilities (password hashing, JWT token management).
    - `models/`
        - `__init__.py`: Initializes the models module.
        - `auth.py`: Database models for authentication (Refresh Tokens, Password Reset Tokens).
        - `user.py`: Database model for users.
        - `cache.py`: Cache related database models.
        - `fitness.py`: Fitness related database models.
        - `package.py`: Package tracking related database models.
        - `server.py`: Server monitoring related database models.
        - `widget.py`: Widget related database models.
    - `schemas/`
        - `__init__.py`: Exposes Pydantic schemas.
        - `auth.py`: Pydantic schemas for authentication (request/response models).
    - `services/`
        - `auth_service.py`: Business logic for authentication operations.
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
        - `layout/`: Layout components.
            - `AuthLayout.jsx`: Provides a consistent layout for authentication forms.
    - `contexts/`: React contexts.
        - `AuthContext.jsx`: Provides authentication context and state to the React application.
    - `hooks/`: React hooks.
    - `services/`: Frontend services (e.g., API calls).
        - `AuthService.js`: Handles authentication-related API calls (login, register, logout, refresh).
    - `styles/`: Stylesheets.
    - `utils/`: Utility functions.

## Documentation (`docs/`)
- `PROJECT_PLAN.md`: Overall project plan.
- `TECH_SPECS.md`: Technical specifications.
- `tasks/`: Directory for task-specific documentation.
    - `003_authentication_system.md`: Details for authentication system implementation.
    - `completed_tasks.md`: List of completed tasks.
    - `completed/`: Directory for completed task documentation.

## Other
- `.gitignore`: Git ignore rules for the project root.
- `mysql_setup_instructions.sql`: SQL script for MySQL setup.
- `README.md`: Project README.
