// fileTypes.ts
export interface FileTypeConfig {
  extension: string;
  mimeType: string;
  description: string;
  aceMode: string;
  processContent: (content: string) => string;
}

export const FILE_TYPES: Record<string, FileTypeConfig> = {
  'js': {
    extension: 'js',
    mimeType: 'application/javascript',
    description: 'JavaScript',
    aceMode: 'javascript',
    processContent: (content) => content,
  },
  'py': {
    extension: 'py',
    mimeType: 'text/x-python',
    description: 'Python',
    aceMode: 'python',
    processContent: (content) => content,
  },
  'ts': {
    extension: 'ts',
    mimeType: 'application/typescript',
    description: 'TypeScript',
    aceMode: 'typescript',
    processContent: (content) => content,
  },
  'tsx': {
    extension: 'tsx',
    mimeType: 'application/typescript',
    description: 'TypeScript React',
    aceMode: 'typescript',
    processContent: (content) => content,
  },
  'jsx': {
    extension: 'jsx',
    mimeType: 'application/javascript',
    description: 'JavaScript React',
    aceMode: 'javascript',
    processContent: (content) => content,
  },
  'html': {
    extension: 'html',
    mimeType: 'text/html',
    description: 'HTML',
    aceMode: 'html',
    processContent: (content) => content,
  },
  'css': {
    extension: 'css',
    mimeType: 'text/css',
    description: 'CSS',
    aceMode: 'css',
    processContent: (content) => content,
  },
  'json': {
    extension: 'json',
    mimeType: 'application/json',
    description: 'JSON',
    aceMode: 'json',
    processContent: (content) => {
      try {
        const obj = JSON.parse(content);
        return JSON.stringify(obj, null, 2);
      } catch {
        return content;
      }
    },
  },
  'yaml': {
    extension: 'yaml',
    mimeType: 'text/yaml',
    description: 'YAML',
    aceMode: 'yaml',
    processContent: (content) => content,
  },
  'yml': {
    extension: 'yml',
    mimeType: 'text/yaml',
    description: 'YAML',
    aceMode: 'yaml',
    processContent: (content) => content,
  },
  'md': {
    extension: 'md',
    mimeType: 'text/markdown',
    description: 'Markdown',
    aceMode: 'markdown',
    processContent: (content) => content,
  },
  'sql': {
    extension: 'sql',
    mimeType: 'text/x-sql',
    description: 'SQL',
    aceMode: 'sql',
    processContent: (content) => content,
  },
  'xml': {
    extension: 'xml',
    mimeType: 'text/xml',
    description: 'XML',
    aceMode: 'xml',
    processContent: (content) => content,
  },
  'rs': {
    extension: 'rs',
    mimeType: 'text/x-rust',
    description: 'Rust',
    aceMode: 'rust',
    processContent: (content) => content,
  },
  'java': {
    extension: 'java',
    mimeType: 'text/x-java',
    description: 'Java',
    aceMode: 'java',
    processContent: (content) => content,
  },
  'cpp': {
    extension: 'cpp',
    mimeType: 'text/x-c++src',
    description: 'C++',
    aceMode: 'c_cpp',
    processContent: (content) => content,
  },
  'c': {
    extension: 'c',
    mimeType: 'text/x-csrc',
    description: 'C',
    aceMode: 'c_cpp',
    processContent: (content) => content,
  },
  'cs': {
    extension: 'cs',
    mimeType: 'text/x-csharp',
    description: 'C#',
    aceMode: 'csharp',
    processContent: (content) => content,
  },
  'go': {
    extension: 'go',
    mimeType: 'text/x-go',
    description: 'Go',
    aceMode: 'golang',
    processContent: (content) => content,
  },
  'rb': {
    extension: 'rb',
    mimeType: 'text/x-ruby',
    description: 'Ruby',
    aceMode: 'ruby',
    processContent: (content) => content,
  },
  'php': {
    extension: 'php',
    mimeType: 'text/x-php',
    description: 'PHP',
    aceMode: 'php',
    processContent: (content) => content,
  },
  'txt': {
    extension: 'txt',
    mimeType: 'text/plain',
    description: 'Plain Text',
    aceMode: 'text',
    processContent: (content) => content,
  },
  'csv': {
    extension: 'csv',
    mimeType: 'text/csv',
    description: 'CSV',
    aceMode: 'text',
    processContent: (content) => 
      content.split('\n')
        .map(line => line.split(' ').join(','))
        .join('\n'),
  }
};
