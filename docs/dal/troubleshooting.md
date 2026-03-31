# Troubleshooting

## DAL endpoint does not respond

Symptoms:

- timeout on DAL calls
- connection refused errors

Checks:

1. verify endpoint URL and port
2. verify network/VPN route
3. verify DAL process/container is running
4. probe endpoint with authenticated request

```bash
curl -H "access-token: <DAL_ACCESS_TOKEN>" <DAL_BASE_URL>/experiments
```

## Authentication failures

Symptoms:

- `401 Unauthorized`
- `Invalid or missing access-token`

Checks:

- token value is correct for the selected DAL
- correct header name is used: `access-token`
- no extra spaces/quotes in env vars

## ProActive Java module warnings/errors

If Java module access issues appear with ProActive client libraries:

```bash
JDK_JAVA_OPTIONS="--add-opens java.base/java.util=ALL-UNNAMED --add-opens java.base/java.util.concurrent=ALL-UNNAMED --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.lang.reflect=ALL-UNNAMED"
```

## Experiment starts but metrics are missing

Checks:

- verify workflow reached finished state
- confirm metric creation calls succeed
- inspect task logs for exceptions before metric write

## Data consistency issues in NEW DAL

Checks:

- confirm DB migrations are applied before test runs
- confirm write endpoints return successful status codes during execution
- verify no stale containers are serving an outdated image
- validate that timestamps/timezones are interpreted consistently
