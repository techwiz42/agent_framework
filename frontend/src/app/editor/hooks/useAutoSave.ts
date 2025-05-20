// hooks/useAutoSave.ts
import { useState, useEffect, useRef } from 'react';
import { AutoSaveState, EditorTab } from '../types';

export function useAutoSave(sessionId: string | null, tabs: EditorTab[]) {
  // Auto-save state
  const [autoSave, setAutoSave] = useState<AutoSaveState>({
    enabled: true,
    interval: 30000, // 30 seconds
    lastSaved: null
  });
  
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Save current tabs to localStorage
  const saveToLocalStorage = () => {
    if (!sessionId) return;
    
    try {
      // Before saving, update each tab with the lastSavedContent
      const tabsWithSavedContent = tabs.map(tab => ({
        ...tab,
        lastSavedContent: tab.content
      }));
      
      localStorage.setItem(sessionId, JSON.stringify({ tabs: tabsWithSavedContent }));
      setAutoSave(prev => ({ ...prev, lastSaved: new Date() }));
      console.log("Auto-saved at", new Date().toLocaleTimeString());
      return true;
    } catch (error) {
      console.error("Failed to auto-save:", error);
      return false;
    }
  };
  
  // Toggle auto-save
  const toggleAutoSave = () => {
    setAutoSave(prev => ({ ...prev, enabled: !prev.enabled }));
  };
  
  // Change auto-save interval
  const setAutoSaveInterval = (interval: number) => {
    if (interval < 5000) {
      console.warn("Auto-save interval must be at least 5 seconds");
      interval = 5000;
    }
    
    setAutoSave(prev => ({ ...prev, interval }));
  };
  
  // Auto-save functionality
  useEffect(() => {
    // Clear existing timer
    if (autoSaveTimerRef.current) {
      clearInterval(autoSaveTimerRef.current);
      autoSaveTimerRef.current = null;
    }
    
    // Set up new timer if auto-save is enabled
    if (autoSave.enabled && sessionId && tabs.length > 0) {
      autoSaveTimerRef.current = setInterval(() => {
        saveToLocalStorage();
      }, autoSave.interval);
    }
    
    // Clean up on unmount
    return () => {
      if (autoSaveTimerRef.current) {
        clearInterval(autoSaveTimerRef.current);
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoSave.enabled, autoSave.interval, tabs, sessionId]);
  
  // Force an immediate save
  const forceSave = () => {
    return saveToLocalStorage();
  };
  
  // Load auto-save settings from localStorage
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem('editor-autosave-settings');
      if (savedSettings) {
        const parsedSettings = JSON.parse(savedSettings);
        setAutoSave(prev => ({
          ...prev,
          enabled: parsedSettings.enabled !== undefined ? parsedSettings.enabled : prev.enabled,
          interval: parsedSettings.interval || prev.interval
        }));
      }
    } catch (error) {
      console.error('Failed to load auto-save settings:', error);
    }
  }, []);
  
  // Save auto-save settings to localStorage when they change
  useEffect(() => {
    try {
      localStorage.setItem('editor-autosave-settings', JSON.stringify({
        enabled: autoSave.enabled,
        interval: autoSave.interval
      }));
    } catch (error) {
      console.error('Failed to save auto-save settings:', error);
    }
  }, [autoSave.enabled, autoSave.interval]);
  
  return {
    autoSave,
    toggleAutoSave,
    setAutoSaveInterval,
    saveToLocalStorage,
    forceSave
  };
}
