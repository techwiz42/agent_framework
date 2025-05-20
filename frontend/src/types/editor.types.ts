// src/types/editor.types.ts
import { IAceEditorProps } from 'react-ace';

export interface AceEditorRef {
  editor: {
    getValue(): string;
    setValue(value: string, cursorPos?: number): void;
    focus(): void;
    findAll(needle: string, options?: object): void;
    replace(replacement: string, options?: object): void;
    selectAll(): void;
    undo(): void;
    redo(): void;
    [method: string]: unknown;
  };
}

// Extend the original props to include ref
export interface ExtendedAceEditorProps extends IAceEditorProps {
  ref?: React.RefObject<AceEditorRef>;
}
