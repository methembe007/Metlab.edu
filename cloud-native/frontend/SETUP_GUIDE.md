# Frontend Setup Guide

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

## Important: WSL/Windows Users

If you're running this project from WSL but accessing it from Windows (or vice versa), you may encounter file permission issues with `node_modules`. 

**Recommended Solutions:**

1. **Run everything from within WSL** (recommended):
   ```bash
   # From WSL terminal
   cd /home/metrix/git/Metlab.edu/cloud-native/frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run dev
   ```

2. **Run everything from Windows**:
   ```cmd
   # From Windows terminal
   cd C:\path\to\project\cloud-native\frontend
   rmdir /s /q node_modules
   del package-lock.json
   npm install
   npm run dev
   ```

3. **Use Docker** (see Docker section below)

## Initial Setup

### 1. Clean Installation (if needed)

If you encounter issues with existing node_modules:

**On Linux/WSL:**
```bash
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**On Windows:**
```cmd
rmdir /s /q node_modules
del package-lock.json
npm cache clean --force
npm install
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` to configure your API endpoint:

```env
VITE_API_URL=http://localhost:8080/api
NODE_ENV=development
```

### 3. Verify Installation

Check that all dependencies are installed:

```bash
npm list --depth=0
```

Expected key dependencies:
- @tanstack/start
- @tanstack/react-router
- @tanstack/react-query
- react & react-dom
- tailwindcss
- typescript
- vinxi

## Development

### Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Features Available in Dev Mode

- Hot Module Replacement (HMR)
- TanStack Router Devtools (bottom-right)
- TanStack Query Devtools (bottom-left)
- TypeScript type checking
- Tailwind CSS with JIT compilation

## Project Structure Overview

```
app/
├── routes/                    # File-based routes
│   ├── __root.tsx            # Root layout with providers
│   ├── index.tsx             # Home page (/)
│   ├── teacher/              # Teacher portal routes
│   └── student/              # Student portal routes
│
├── components/               # Reusable components
│   └── layout/              # Layout components
│       ├── Header.tsx       # Top navigation bar
│       ├── Footer.tsx       # Site footer
│       ├── Sidebar.tsx      # Side navigation
│       ├── Layout.tsx       # Main layout wrapper
│       └── index.ts         # Barrel export
│
├── lib/                     # Utilities and configurations
│   ├── queryClient.ts       # TanStack Query setup
│   └── apiClient.ts         # API client for backend
│
├── hooks/                   # Custom React hooks
│   ├── useAuth.ts          # Authentication hook
│   └── index.ts            # Barrel export
│
├── types/                   # TypeScript type definitions
│   └── index.ts            # Shared types
│
├── client.tsx              # Client entry point
├── router.tsx              # Router configuration
├── ssr.tsx                 # SSR entry point
└── styles.css              # Global styles (Tailwind)
```

## Key Concepts

### File-Based Routing

Routes are automatically generated from the `app/routes/` directory structure:

- `routes/index.tsx` → `/`
- `routes/teacher/dashboard.tsx` → `/teacher/dashboard`
- `routes/student/videos.tsx` → `/student/videos`

### Layout Components

Use the `Layout` component to wrap your pages:

```tsx
import { Layout } from '~/components/layout'

function MyPage() {
  return (
    <Layout
      showSidebar={true}
      sidebarLinks={[
        { to: '/dashboard', label: 'Dashboard' },
        { to: '/videos', label: 'Videos' },
      ]}
      userRole="teacher"
      userName="John Doe"
      onLogout={() => console.log('Logout')}
    >
      <h1>My Page Content</h1>
    </Layout>
  )
}
```

### Data Fetching with TanStack Query

```tsx
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '~/lib/apiClient'

function VideoList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['videos'],
    queryFn: () => apiClient.get('/videos'),
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      {data.videos.map(video => (
        <div key={video.id}>{video.title}</div>
      ))}
    </div>
  )
}
```

### Authentication

Use the `useAuth` hook for authentication state:

```tsx
import { useAuth } from '~/hooks'

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth()

  if (!isAuthenticated) {
    return <div>Please log in</div>
  }

  return (
    <div>
      <p>Welcome, {user.fullName}</p>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

## Building for Production

### Build the Application

```bash
npm run build
```

This creates an optimized production build in the `.output` directory.

### Start Production Server

```bash
npm run start
```

The production server will start on port 3000.

## Testing

### Run Tests

```bash
npm run test
```

### Run Tests in Watch Mode

```bash
npm run test -- --watch
```

## Linting

### Check for Linting Errors

```bash
npm run lint
```

### Auto-fix Linting Errors

```bash
npm run lint -- --fix
```

## Troubleshooting

### TypeScript Errors

If you see TypeScript errors about missing types:

1. Ensure all dependencies are installed: `npm install`
2. Restart your IDE/editor
3. Check `tsconfig.json` configuration

### Module Resolution Issues

If imports are not resolving:

1. Check the `paths` configuration in `tsconfig.json`
2. Ensure you're using the `~/` alias for app imports
3. Restart the dev server

### Tailwind CSS Not Working

1. Verify `tailwind.config.js` includes your files
2. Check that `styles.css` imports Tailwind directives
3. Restart the dev server

### Port Already in Use

If port 3000 is already in use:

```bash
# Kill the process using port 3000
# On Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# On Linux/Mac:
lsof -ti:3000 | xargs kill -9
```

Or change the port in `app.config.ts`.

## Next Steps

1. **Create Authentication Pages**: Implement login/signup pages in `routes/teacher/` and `routes/student/`
2. **Add Protected Routes**: Create route guards for authenticated pages
3. **Implement API Integration**: Connect to backend services using the API client
4. **Build Feature Pages**: Create pages for videos, homework, PDFs, etc.
5. **Add Real-time Features**: Implement WebSocket connections for chat

## Resources

- [TanStack Start Documentation](https://tanstack.com/start)
- [TanStack Router Documentation](https://tanstack.com/router)
- [TanStack Query Documentation](https://tanstack.com/query)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
