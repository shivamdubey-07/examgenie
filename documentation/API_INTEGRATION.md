# API Integration Guide

## Backend API Overview

The ExamGenie backend is built with FastAPI, providing RESTful endpoints for exam management, student attempts, and user authentication.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://yourdomain.com`

## Authentication

### JWT Token Flow

```
1. POST /auth/register         → Register user
2. POST /auth/login            → Get JWT token
3. Authorization header        → Include token in requests
4. POST /auth/refresh          → Get new token when expired
```

### Using JWT Token

Include in Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Example:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/exams
```

## API Endpoints

### Authentication

```
POST   /auth/register      - Register new user
POST   /auth/login         - Login user
POST   /auth/logout        - Logout user
POST   /auth/refresh       - Refresh token
```

**POST /auth/register**

```json
Request:
{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}

Response (201):
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-03-18T10:30:00"
}
```

**POST /auth/login**

```json
Request:
{
  "email": "user@example.com",
  "password": "secure_password"
}

Response (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Users

```
GET    /users/{id}         - Get user profile
PUT    /users/{id}         - Update user profile
GET    /users/me           - Get current user
DELETE /users/{id}         - Delete user
```

### Exams

```
GET    /exams              - List all exams
POST   /exams              - Create exam
GET    /exams/{id}         - Get exam details
PUT    /exams/{id}         - Update exam
DELETE /exams/{id}         - Delete exam
POST   /exams/{id}/generate - Generate with AI
```

**POST /exams/generate**

```json
Request:
{
  "topic": "Python Programming",
  "num_questions": 10,
  "difficulty": "intermediate",
  "question_type": "multiple_choice"
}

Response (202 - Accepted):
{
  "id": 1,
  "status": "pending",
  "topic": "Python Programming",
  "num_questions": 10
}

# Poll for completion
GET /exams/1
Response (200 - when ready):
{
  "id": 1,
  "status": "ready",
  "questions": [...],
  "created_at": "2024-03-18T10:30:00"
}
```

### Questions

```
GET    /exams/{id}/questions           - Get questions for exam
GET    /questions/{id}                 - Get question details
GET    /questions/{id}/explanation     - Get AI explanation
```

### Exam Attempts

```
GET    /attempts                       - List user's attempts
POST   /attempts                       - Start new attempt
GET    /attempts/{id}                  - Get attempt details
POST   /attempts/{id}/answer           - Submit single answer
POST   /attempts/{id}/submit           - Complete attempt
```

**POST /attempts**

```json
Request:
{
  "exam_id": 1
}

Response (201):
{
  "id": 1,
  "exam_id": 1,
  "user_id": 1,
  "status": "in_progress",
  "started_at": "2024-03-18T10:30:00"
}
```

**POST /attempts/{id}/answer**

```json
Request:
{
  "question_id": 1,
  "selected_option_id": 3
}

Response (200):
{
  "attempt_id": 1,
  "question_id": 1,
  "answer_saved": true
}
```

**POST /attempts/{id}/submit**

```json
Response (200):
{
  "id": 1,
  "exam_id": 1,
  "status": "completed",
  "score": 85,
  "total_questions": 10,
  "correct_answers": 8.5,
  "submitted_at": "2024-03-18T10:35:00",
  "results": [
    {
      "question_id": 1,
      "correct": true,
      "explanation": "Python uses indentation..."
    }
  ]
}
```

### Analytics

```
GET    /analytics/exams/{id}           - Exam statistics
GET    /analytics/questions/{id}       - Question statistics
GET    /analytics/user                 - User performance
```

### Health Check

```
GET    /health                         - Service health
GET    /readiness                      - Readiness check
```

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message",
  "error_code": "INVALID_REQUEST",
  "status_code": 400
}
```

### Common Status Codes

| Code | Meaning                                     |
| ---- | ------------------------------------------- |
| 200  | OK - Request succeeded                      |
| 201  | Created - Resource created                  |
| 202  | Accepted - Request queued (for async tasks) |
| 400  | Bad Request - Invalid input                 |
| 401  | Unauthorized - Missing/invalid token        |
| 403  | Forbidden - User lacks permission           |
| 404  | Not Found - Resource doesn't exist          |
| 409  | Conflict - Resource already exists          |
| 422  | Unprocessable - Validation error            |
| 429  | Too Many Requests - Rate limited            |
| 500  | Server Error - Internal error               |
| 503  | Unavailable - Service down                  |

### Error Examples

**Missing Token (401)**

```json
{
  "detail": "Not authenticated",
  "status_code": 401
}
```

**Validation Error (422)**

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

**Rate Limited (429)**

```json
{
  "detail": "Rate limit exceeded",
  "status_code": 429,
  "retry_after": 60
}
```

## API Documentation

### Interactive Documentation

Visit **http://localhost:8000/docs** for Swagger UI:

- Try endpoints directly
- See request/response examples
- View parameter descriptions
- Download OpenAPI schema

### Alternative Documentation

Visit **http://localhost:8000/redoc** for ReDoc (read-only)

### OpenAPI Schema

Download JSON schema:

```
http://localhost:8000/openapi.json
```

## Pagination

List endpoints support pagination:

```
GET /exams?skip=0&limit=10
```

Response:

```json
{
  "items": [...],
  "total": 50,
  "skip": 0,
  "limit": 10
}
```

## Filtering & Sorting

Some endpoints support filtering:

```
GET /exams?difficulty=intermediate&sort_by=created_at&order=desc
```

## Rate Limiting

```
General endpoints:     10 requests/second
Login endpoint:        5 requests/minute per IP
```

Headers in response:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1234567890
```

## Async Operations

Some operations are async (queued for processing):

### Polling Pattern

```
1. POST /exams/1/generate
   Response: status = "pending"

2. Poll: GET /exams/1
   While status != "ready", wait 1 second

3. GET /exams/1/results
   When ready, get full results
```

### WebSocket (Future)

For real-time updates (coming soon):

```
ws://localhost:8000/ws/exams/{id}
```

## Best Practices

### Authentication

- Store token securely (httpOnly cookie preferred)
- Refresh token before expiry
- Clear token on logout
- Don't expose token in logs

### Error Handling

- Always check response status code
- Parse error details from response body
- Implement retry logic for 5xx errors
- Log errors for debugging

### Performance

- Use pagination for large datasets
- Cache frequently accessed data
- Batch operations when possible
- Use indexes for search filters

### Security

- Validate user input on frontend
- Use HTTPS in production (not HTTP)
- Include CSRF token if using cookies
- Validate file uploads

## Testing API

### Curl Examples

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# Get exams (with token)
curl http://localhost:8000/exams \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create exam
curl -X POST http://localhost:8000/exams \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Python Basics","difficulty":"beginner"}'
```

### Python Client

```python
import requests

API_URL = "http://localhost:8000"
token = None

# Login
response = requests.post(f"{API_URL}/auth/login", json={
    "email": "test@example.com",
    "password": "pass123"
})
token = response.json()["access_token"]

# Get exams
response = requests.get(f"{API_URL}/exams", headers={
    "Authorization": f"Bearer {token}"
})
exams = response.json()
print(exams)
```

### JavaScript/Axios Client

```javascript
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

let token = null;

// Login
api
  .post("/auth/login", {
    email: "test@example.com",
    password: "pass123",
  })
  .then((res) => {
    token = res.data.access_token;
  });

// Get exams
api
  .get("/exams", {
    headers: { Authorization: `Bearer ${token}` },
  })
  .then((res) => console.log(res.data));
```

## API Versioning

Current API version: **v1**

For future versions, endpoints will be prefixed:

```
/api/v1/exams
/api/v2/exams
```

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for API changes between versions.

## Support

For API issues:

1. Check interactive docs: http://localhost:8000/docs
2. Review error messages carefully
3. Check logs: `docker-compose logs api`
4. Create GitHub issue with full error details
