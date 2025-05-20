// types.ts
export interface EditorTab {
  content: string;
  fileName: string;
  fileType: string;
  lastEditBy?: string;
  lastSavedContent?: string;
}

export interface EditorParticipant {
  email: string;
  name?: string;
  lastActive: Date;
  cursor?: CursorPosition;
}

export interface CollaborativeEditorState {
  sessionId: string;
  conversationId: string;
  participants: EditorParticipant[];
  activeEditor?: string; // Email of user currently editing
}

export interface FindReplaceState {
  visible: boolean;
  findText: string;
  replaceText: string;
  matchCase: boolean;
  wholeWord: boolean;
  matches: number;
  currentMatch: number;
}

export interface AutoSaveState {
  enabled: boolean;
  interval: number;
  lastSaved: Date | null;
}

export interface ThemeState {
  isDark: boolean;
  currentTheme: string;
  availableThemes: string[];
}

export interface FoldingState {
  enabled: boolean;
  foldedLines: Set<number>;
}

export interface CursorPosition {
  line: number;
  column: number;
}

// Define file types and their mapping to Prism language names
export const FILE_TYPE_MAP: Record<string, string> = {
  // Web languages
  'js': 'javascript',
  'jsx': 'jsx',
  'ts': 'typescript',
  'tsx': 'tsx',
  'html': 'markup',
  'htm': 'markup',
  'xml': 'markup',
  'svg': 'markup',
  'css': 'css',
  
  // Programming languages
  'py': 'python',
  'java': 'java',
  'c': 'c',
  'h': 'c',
  'cpp': 'cpp',
  'cc': 'cpp',
  'cxx': 'cpp',
  'hpp': 'cpp',
  'cs': 'csharp',
  'go': 'go',
  'rb': 'ruby',
  'rs': 'rust',
  'scala': 'scala',
  'r': 'r',
  'm': 'matlab',
  
  // Data formats & config
  'json': 'json',
  
  // Shell scripts
  'sh': 'bash',
  'bash': 'bash',
  'zsh': 'bash'
};
