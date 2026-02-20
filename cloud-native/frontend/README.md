# Metlab.edu Frontend

Modern, cloud-native frontend application built with TanStack Start, React, and TypeScript.

## 🚀 Quick Start

### For WSL/Linux Users

```bash
cd /home/metrix/git/Metlab.edu/cloud-native/frontend
./setup.sh
npm run dev
```

### For Windows Users (Running WSL Project)

**Option 1: Use the batch script (Recommended)**
```cmd
setup-from-windows.bat
dev-from-windows.bat
```

**Option 2: Open WSL terminal and run**
```bash
cd /home/metrix/git/Metlab.edu/cloud-native/frontend
./setup.sh
npm run dev
```

📖 **See [QUICK_START.md](./QUICK_START.md) for detailed instructions**

## ⚠️ Important Note

This project is in a WSL filesystem. Always run npm commands from within WSL, not from Windows CMD/PowerShell. Windows cannot directly execute commands on WSL paths.

## Tech Stack

- **Framework**: TanStack Start (React-based SSR framework)
- **Routing**: TanStack Router (file-based routing)
- **Data Fetching**: TanStack Query (server state management)
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **Build Tool**: Vite (via Vinxi)

## Project Structure

```
app/
├── routes/              # File-based routes
│   ├── __root.tsx      # Root layout with providers
│   └── index.tsx       # Home page
├── components/          # Reusable components
│   └── layout/         # Layout components (Header, Footer, Sidebar)
├── lib/                # Utilities and configurations
│   ├── queryClient.ts  # TanStack Query configuration
│   └── apiClient.ts    # API client for backend communication
├── client.tsx          # Client entry point
├── router.tsx          # Router configuration
├── ssr.tsx            # SSR entry point
└── styles.css         # Global styles (Tailwind)
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

### Production

```bash
npm run start
```

## Key Features

### TanStack Router

File-based routing with automatic route generation. Routes are defined in the `app/routes/` directory.

- `__root.tsx` - Root layout component
- `index.tsx` - Home page (/)
- `teacher/` - Teacher portal routes
- `student/` - Student portal routes

### TanStack Query

Configured with sensible defaults:
- 1 minute stale time
- 5 minute garbage collection time
- 3 retry attempts for queries
- Automatic refetch disabled on window focus

### API Client

Centralized API client with:
- Automatic JWT token injection
- Request/response interceptors
- File upload support
- Type-safe requests

### Layout Components

Reusable layout components:
- **Header**: Navigation bar with user info and logout
- **Sidebar**: Collapsible navigation menu
- **Footer**: Site footer with links
- **Layout**: Wrapper component combining all layouts

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8080/api
```

## Development Tools

- **Router Devtools**: Bottom-right corner (development only)
- **Query Devtools**: Bottom-left corner (development only)
- **ESLint**: Code linting
- **Vitest**: Unit testing

## Testing

```bash
npm run test
```

## Linting

```bash
npm run lint
```

## Docker

Build the Docker image:

```bash
docker build -t metlab-frontend .
```

Run the container:

```bash
docker run -p 3000:3000 metlab-frontend
```

## Contributing

1. Create a new route in `app/routes/`
2. Use layout components from `app/components/layout/`
3. Use TanStack Query hooks for data fetching
4. Follow TypeScript best practices
5. Ensure responsive design with Tailwind CSS

## Architecture Decisions

### Why TanStack Start?

- Server-side rendering for better SEO and initial load
- File-based routing for intuitive organization
- Built-in code splitting
- Excellent TypeScript support

### Why TanStack Query?

- Automatic caching and background refetching
- Optimistic updates
- Request deduplication
- Built-in loading and error states

### Why Tailwind CSS?

- Utility-first approach for rapid development
- Small bundle size with purging
- Consistent design system
- Excellent responsive design support
