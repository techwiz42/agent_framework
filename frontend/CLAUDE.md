# CLAUDE.md - Coding Guidelines

## Build Commands
- `npm run dev` - Start development server (port 3001)
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Code Style Guidelines
- **TypeScript**: Use strict typing with interfaces/types for all objects
- **Imports**: Group imports by external libraries, then internal paths
- **Naming**: PascalCase for components, camelCase for functions/variables
- **Components**: Each component in its own file, organized by feature
- **Error Handling**: Use try/catch blocks and ErrorBoundary for UI failures
- **State Management**: Use hooks for local state, context for global state
- **File Structure**:
  - `/components` - UI components grouped by feature or common UI
  - `/lib` - Utility functions and shared logic
  - `/app` - Next.js app directory with page components
  - `/services` - API and external service integrations

## Formatting
- Use prettier with defaults (semi-colons, single quotes when possible)
- Max line length of 80 characters
- Use Arrow functions for component definitions
- Always use named exports over default exports