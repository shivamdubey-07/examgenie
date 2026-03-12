# Frontend Setup Guide

## Overview

The ExamGenie frontend is a React application built with Vite. It provides a user interface for exam creation, taking, and reviewing results.

## Technology Stack

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **React Router v7** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Styling

## Quick Start

### Without Docker

```bash
cd examgenie_frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Will start on http://localhost:5173
```

### With Docker

```bash
cd examgenie  # Root directory
docker-compose up -d

# Frontend available at http://localhost (via nginx proxy)
# Or direct: http://localhost:5173
```

## Project Structure

```
examgenie_frontend/
├── src/
│   ├── pages/
│   │   ├── Landing.jsx         (Home/intro)
│   │   ├── Register.jsx        (Sign up)
│   │   ├── Login.jsx           (Sign in)
│   │   ├── Dashboard.jsx       (Main dashboard)
│   │   ├── Generate.jsx        (Create exams)
│   │   ├── Exam.jsx            (Take exam)
│   │   └── Results.jsx         (View results)
│   ├── services/
│   │   └── api.js              (Axios client)
│   ├── assets/                 (Images, fonts)
│   ├── App.jsx                 (Root component)
│   └── main.jsx                (Entry point)
├── public/                      (Static files)
├── index.html                   (HTML template)
├── vite.config.js              (Vite config)
├── tailwind.config.js          (Tailwind config)
├── postcss.config.js           (PostCSS config)
├── eslint.config.js            (ESLint config)
└── package.json                 (Dependencies)
```

## Development Workflow

### 1. Make Changes

Any changes to `src/` are automatically hot-reloaded:

```bash
# Edit a page
nano src/pages/Dashboard.jsx

# Changes appear immediately in browser!
```

### 2. Create Components

```javascript
// src/components/ExamCard.jsx
export default function ExamCard({ exam }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-bold">{exam.title}</h3>
      <p className="text-gray-600">{exam.questions_count} questions</p>
    </div>
  );
}
```

Use in page:

```javascript
// src/pages/Dashboard.jsx
import ExamCard from "../components/ExamCard";

export default function Dashboard() {
  return (
    <div>
      {exams.map((exam) => (
        <ExamCard key={exam.id} exam={exam} />
      ))}
    </div>
  );
}
```

### 3. Make API Calls

Setup API client (`src/services/api.js`):

```javascript
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost/api";

const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export const getExams = () => apiClient.get("/exams");
export const createExam = (data) => apiClient.post("/exams", data);
export const startAttempt = (examId) =>
  apiClient.post("/attempts", { exam_id: examId });

export default apiClient;
```

Use in component:

```javascript
import { useEffect, useState } from "react";
import { getExams } from "../services/api";

export default function ExamList() {
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getExams()
      .then((res) => setExams(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="grid gap-4">
      {exams.map((exam) => (
        <div key={exam.id} className="border rounded p-4">
          {exam.title}
        </div>
      ))}
    </div>
  );
}
```

### 4. Use React Router

Setup routing in `App.jsx`:

```javascript
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Exam from "./pages/Exam";
import Results from "./pages/Results";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/exams/:id" element={<Exam />} />
        <Route path="/results/:id" element={<Results />} />
      </Routes>
    </BrowserRouter>
  );
}
```

Navigate programmatically:

```javascript
import { useNavigate } from "react-router-dom";

export default function ExamCard({ exam }) {
  const navigate = useNavigate();

  return (
    <button onClick={() => navigate(`/exams/${exam.id}`)}>Start Exam</button>
  );
}
```

## Environment Variables

Create `.env` in `examgenie_frontend/`:

```env
VITE_API_URL=http://localhost/api
VITE_APP_NAME=ExamGenie
VITE_DEBUG=true
```

Access in code:

```javascript
const API_URL = import.meta.env.VITE_API_URL;
const APP_NAME = import.meta.env.VITE_APP_NAME;
```

## Styling with Tailwind CSS

All CSS utilities are available:

```javascript
export default function Button({ children, primary }) {
  return (
    <button
      className={`
      px-4 py-2 rounded
      ${
        primary
          ? "bg-blue-500 text-white hover:bg-blue-600"
          : "bg-gray-200 text-gray-800 hover:bg-gray-300"
      }
    `}
    >
      {children}
    </button>
  );
}
```

## Building for Production

### Create Production Build

```bash
cd examgenie_frontend

# Build optimized bundle
npm run build

# Creates dist/ folder with optimized files
```

### Preview Production Build

```bash
# Test production build locally
npm run preview

# Serve on http://localhost:4173
```

### Build Size Analysis

```bash
# Analyze bundle size
npm install --save-dev rollup-plugin-visualizer

# Add to vite.config.js
import { visualizer } from 'rollup-plugin-visualizer';

export default {
  plugins: [
    visualizer()
  ]
}

npm run build
# Creates stats.html
```

## Docker Production Setup

### Multi-Stage Build

Create `Dockerfile.prod`:

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build -f Dockerfile.prod -t examgenie-frontend:latest .
docker run -p 80:80 examgenie-frontend:latest
```

## Code Quality

### Linting

```bash
# Run ESLint
npm run lint

# Fix issues automatically
npx eslint src --fix
```

### Formatting

```bash
# Format with Prettier
npm install --save-dev prettier
npx prettier --write src
```

## Debugging

### Browser DevTools

Press F12 to open Developer Tools:

1. **Console** - View errors and logs
2. **Network** - See API calls
3. **React DevTools** - Inspect component tree
4. **Storage** - View localStorage, sessionStorage

### React DevTools Extension

Install browser extension:

- Chrome: [React DevTools](https://chrome.google.com/webstore/detail/react-developer-tools/)
- Firefox: [React DevTools](https://addons.mozilla.org/firefox/addon/react-devtools/)

### Vite Debug Mode

Add to `vite.config.js`:

```javascript
export default {
  define: {
    __DEV__: true,
  },
};
```

Use in code:

```javascript
if (import.meta.env.DEV) {
  console.log("Development mode");
}
```

## Testing

### Unit Tests

```bash
# Install vitest
npm install --save-dev vitest

# Example test
// src/services/__tests__/api.test.js
import { describe, it, expect } from 'vitest';

describe('API', () => {
  it('should make requests', () => {
    expect(true).toBe(true);
  });
});

# Run tests
npm run test
```

### Integration Tests

```bash
# Install testing library
npm install --save-dev @testing-library/react @testing-library/jest-dom

// src/pages/__tests__/Dashboard.test.jsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../Dashboard';

test('renders dashboard', () => {
  render(<Dashboard />);
  expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
});
```

## Performance Optimization

### Code Splitting

Vite automatically splits code. Manually split large components:

```javascript
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("./pages/Dashboard"));

export default function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Dashboard />
    </Suspense>
  );
}
```

### Image Optimization

```javascript
// Use responsive images
<img
  src={import.meta.env.VITE_API_URL + "/images/logo.webp"}
  alt="Logo"
  className="w-32 h-auto"
/>
```

### Lazy Load Routes

```javascript
import { lazy } from "react";
import { useRoutes } from "react-router-dom";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Exam = lazy(() => import("./pages/Exam"));
const Results = lazy(() => import("./pages/Results"));

export default function App() {
  return useRoutes([
    { path: "/", element: <Dashboard /> },
    { path: "/exams/:id", element: <Exam /> },
    { path: "/results/:id", element: <Results /> },
  ]);
}
```

## Common Tasks

### Add New Page

1. Create component in `src/pages/NewPage.jsx`
2. Add route in `src/App.jsx`
3. Add navigation link in layout component

### Add API Integration

1. Add function to `src/services/api.js`
2. Use `useEffect` + `useState` in component
3. Handle loading and error states

### Style a Component

1. Use Tailwind classes
2. Or create component-scoped styles
3. Or edit `tailwind.config.js` for custom config

### Add State Management

```bash
# Option 1: useContext (simple)
# Option 2: Zustand (lightweight)
npm install zustand

# Option 3: Redux (full-featured)
npm install @reduxjs/toolkit react-redux
```

## Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for production deployment.

## Quick Commands

```bash
# Development
npm run dev                 # Start dev server
npm run build              # Build for production
npm run preview            # Preview production build
npm run lint               # Check code quality

# Docker
docker build -f Dockerfile.prod -t examgenie-frontend .
docker run -p 80:80 examgenie-frontend
```

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues.

## Related Documentation

- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker configuration
- [API_INTEGRATION.md](./API_INTEGRATION.md) - Backend API
- [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md) - Configuration
