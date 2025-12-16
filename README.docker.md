# Docker Deployment Instructions

## Prerequisites
- Docker
- Docker Compose

## Configuration
The system uses an external PostgreSQL database. The configuration is set in `docker-compose.yml`.

- **DB_HOST**: 121.43.104.161
- **DB_PORT**: 6432
- **DB_USER**: OKR
- **DB_NAME**: OKR

## Building and Running

1. **Build the containers**:
   ```bash
   docker-compose build
   ```

2. **Start the services**:
   ```bash
   docker-compose up
   ```
   - The backend API will be available at `http://localhost:8000`
   - The frontend application will be available at `http://localhost:3000`

3. **Run in background**:
   ```bash
   docker-compose up -d
   ```

4. **Stop the services**:
   ```bash
   docker-compose down
   ```

## Backend Details
- The backend uses `gunicorn` for the application server.
- Static files are served using `WhiteNoise`.
- `docker-entrypoint.sh` automatically:
  - Waits for the database to be ready
  - Runs database migrations
  - Collects static files

## Frontend Details
- The frontend is a React application.
- In this configuration, it runs in development mode (`npm start`) to allow for hot-reloading if mounted volumes are used.
- For production deployment of the frontend, a build step and Nginx server would be recommended.
