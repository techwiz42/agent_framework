# Agent Framework Frontend

This is the frontend application for the Agent Framework, built with Next.js, TypeScript, and Tailwind CSS.

## Getting Started

### Prerequisites

- Node.js 18.x or later
- npm or yarn

### Installation

1. Install dependencies:

```bash
npm install
# or
yarn
```

2. Set up environment variables:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your settings:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_NAME=Agent Framework
```

3. Start the development server:

```bash
npm run dev
# or
yarn dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## Project Structure

```
src/
├── app/               # Next.js app directory
│   ├── auth/          # Authentication pages
│   │   ├── login/     # Login page
│   │   └── register/  # Registration page
│   ├── conversations/ # Conversation pages
│   │   ├── page.tsx   # Conversation list page
│   │   ├── new/       # New conversation page
│   │   └── [id]/      # Specific conversation page
│   ├── agents/        # Agent information pages
│   └── layout.tsx     # Root layout
├── components/        # React components
│   ├── layout/        # Layout components
│   │   ├── Header.tsx # App header
│   │   └── Footer.tsx # App footer
│   ├── ui/            # UI components
│   │   ├── button.tsx # Button component
│   │   └── logo/      # Logo components
│   ├── auth/          # Auth-related components
│   └── conversation/  # Conversation components
├── context/           # React context providers
│   └── AuthContext.tsx # Authentication context
├── hooks/             # Custom React hooks
│   ├── useAuth.ts     # Authentication hook
│   └── useWebSocket.ts # WebSocket connection hook
├── lib/               # Utility functions
├── services/          # API service clients
│   ├── api.ts         # Base API client
│   ├── auth.ts        # Authentication service
│   └── agents.ts      # Agents service
└── types/             # TypeScript type definitions
```

## Key Features

### Authentication

- Login/Registration system
- JWT token handling
- Protected routes

### Conversations

- Create new conversations
- View conversation history
- Real-time messaging with WebSocket
- File uploading and document processing

### Agent Interaction

- Automatic query routing to specialized agents
- Support for all agent types (MODERATOR, BUSINESS, etc.)
- Rich message formatting with Markdown

### External Integrations

- Google Drive connection
- OneDrive connection
- Document search and analysis

## Customization

### Adding New Components

1. Create a new component in the appropriate directory:

```tsx
// src/components/example/NewComponent.tsx
import React from 'react';

interface NewComponentProps {
  title: string;
}

export const NewComponent: React.FC<NewComponentProps> = ({ title }) => {
  return (
    <div className="p-4 bg-white rounded shadow">
      <h2>{title}</h2>
    </div>
  );
};
```

2. Import and use the component as needed.

### Adding New Pages

1. Create a new page in the app directory:

```tsx
// src/app/new-page/page.tsx
'use client'
import React from 'react';

export default function NewPage() {
  return (
    <div>
      <h1>New Page</h1>
      <p>This is a new page.</p>
    </div>
  );
}
```

### Styling

The application uses Tailwind CSS for styling. To customize:

1. Modify `tailwind.config.js` for theme customization
2. Use Tailwind classes directly in components
3. For complex components, consider using CSS modules

## Development Workflow

### Code Style

- We follow a consistent code style using ESLint and Prettier
- Run `npm run lint` to check for code style issues
- Use TypeScript for all components and functions

### Component Guidelines

- Use functional components with hooks
- Keep components small and focused
- Use TypeScript interfaces for props
- Document complex components with comments

### State Management

- Use React Context for global state
- Use React hooks (useState, useReducer) for component state
- Consider using SWR for data fetching and caching

## Building for Production

```bash
npm run build
# or
yarn build
```

To start the production server:

```bash
npm run start
# or
yarn start
```

## Testing

```bash
npm run test
# or
yarn test
```