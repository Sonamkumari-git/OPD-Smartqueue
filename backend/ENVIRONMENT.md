# Local Environment Variables

Create `backend/.env` locally and keep it outside source control. Use the following configuration, replacing `JWT_SECRET` with a long random value before any non-demo use.

```dotenv
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=opd_queue_management
JWT_SECRET=replace_with_a_long_random_local_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:3000
APP_ENV=development
APP_NAME=OPD SmartQueue API
APP_VERSION=0.1.0
APPROACHING_THRESHOLD=2
BASELINE_RECENT_WEIGHT=0.50
BASELINE_TODAY_WEIGHT=0.30
BASELINE_HISTORICAL_WEIGHT=0.20
```

The project does not commit a local `.env` file. `JWT_SECRET`, MongoDB connectivity information, and local frontend origin are deployment-specific values.
