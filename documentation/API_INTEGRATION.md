# API Integration Guide

## Backend API Overview

The ExamGenie backend is built with FastAPI, providing RESTful endpoints for exam generation, user authentication, and result tracking.

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: `https://yourdomain.com/api`

## API Response Format

All responses are JSON. Successful requests return status `200-202` with data:

```json
{
  "id": "uuid",
  "status": "success",
  "data": {
    /* endpoint-specific */
  }
}
```

Errors return appropriate status codes with detail:

```json
{
  "detail": "Error description"
}
```

## Authentication

### JWT Token Flow

```
1. POST /auth/register         → Register user, get token
2. POST /auth/login            → Login user, get token
3. Include token in requests   → Authorization header
```

### Using JWT Token

Include in Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Example:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/exam/generate
```

## API Endpoints

### Authentication

#### POST /auth/register

Register a new user account.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### POST /auth/login

Login and get JWT access token.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### Exam Endpoints

#### POST /exam/generate

Create a new exam and queue it for AI generation. Returns immediately with status `generating`.

**Request:**

```json
{
  "title": "Python Basics",
  "subject": "Programming",
  "topic": "Python",
  "difficulty": "intermediate",
  "num_questions": 10
}
```

**Response (202 - Accepted):**

```json
{
  "exam_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "generating",
  "message": "Exam generation queued. Check status endpoint for updates."
}
```

**Frontend should poll** for completion. See [Polling for Exam Status](#polling-for-exam-status) below.

### Health Check

#### GET /health

Simple health check endpoint (no auth required).

**Response (200):**

```json
{
  "status": "ok"
}
```

## Common Patterns

### Polling for Exam Status

After generating an exam, poll the status endpoint:

```javascript
// Frontend - poll until ready
const pollExamStatus = async (examId) => {
  const response = await apiClient.get(`/exam/status/${examId}`);

  if (response.data.status === "ready") {
    // Exam is ready - now get questions
    return response.data;
  } else if (response.data.status === "generating") {
    // Wait and poll again
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return pollExamStatus(examId);
  } else if (response.data.status === "failed") {
    throw new Error(response.data.failure_reason);
  }
};
```

### Error Handling

```javascript
import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api",
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem("token");
      window.location.href = "/login";
    } else if (error.response?.status === 422) {
      // Validation error
      console.error("Validation error:", error.response.data.detail);
    }
    return Promise.reject(error);
  },
);

export default apiClient;
```

### Authorization Headers

```javascript
// Automatically add token to all requests
const token = localStorage.getItem("token");

if (token) {
  apiClient.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}
```

## Status Codes

- **200 OK** - Successful request
- **201 Created** - Resource created successfully
- **202 Accepted** - Request queued (e.g., exam generation)
- **400 Bad Request** - Invalid input
- **401 Unauthorized** - Missing or invalid token
- **403 Forbidden** - Authenticated but not authorized
- **404 Not Found** - Resource doesn't exist
- **422 Unprocessable Entity** - Validation error
- **500 Internal Server Error** - Server error

````

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
````

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
