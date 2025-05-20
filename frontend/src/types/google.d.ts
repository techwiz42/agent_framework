declare global {
  interface Window {
    google: {
      picker: {
        PickerBuilder: new () => GooglePicker;
        DocsView: new () => GoogleDocsView;
        Feature: {
          MULTISELECT_ENABLED: string;
        };
        Action: {
          PICKED: string;
        };
      };
    };
    gapi: {
      load: (api: string, callback: () => void) => void;
    };
    pickerInited: boolean;
  }
}

interface GooglePicker {
  addView: (view: GoogleDocsView) => GooglePicker;
  setOAuthToken: (token: string) => GooglePicker;
  enableFeature: (feature: string) => GooglePicker;
  setCallback: (callback: (data: PickerData) => void) => GooglePicker;
  build: () => GooglePicker;
  setVisible: (visible: boolean) => void;
}

interface GoogleDocsView {
  setIncludeFolders: (include: boolean) => GoogleDocsView;
  setMimeTypes: (types: string[]) => GoogleDocsView;
  setSelectFolderEnabled: (enabled: boolean) => GoogleDocsView;
}

interface PickerData {
  action: string;
  docs: Array<{
    id: string;
    name: string;
    mimeType: string;
  }>;
}

export {};
