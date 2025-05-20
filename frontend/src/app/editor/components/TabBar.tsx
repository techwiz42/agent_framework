// components/TabBar.tsx (With responsive tab handling)
import React, { useState, useRef, useEffect } from 'react';
import { X, Edit, ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react';
import Image from 'next/image';
import { EditorTab } from '../types';

interface TabBarProps {
  tabs: EditorTab[];
  activeTab: number;
  setActiveTab: (index: number) => void;
  handleCloseTab: (index: number, e: React.MouseEvent) => void;
  handleAddTab: () => void;
  handleRenameTab: (index: number, newName: string) => void;
  isDarkTheme: boolean;
  logoSize?: number;
}

export function TabBar({ 
  tabs, 
  activeTab, 
  setActiveTab, 
  handleCloseTab, 
  handleAddTab,
  handleRenameTab,
  isDarkTheme,
  logoSize = 35 // Default logo size - set to 35px
}: TabBarProps) {
  const [isRenamingTab, setIsRenamingTab] = useState<boolean>(false);
  const [renamingTabIndex, setRenamingTabIndex] = useState<number>(-1);
  const [tabNewName, setTabNewName] = useState<string>('');
  const renameInputRef = useRef<HTMLInputElement>(null);
  
  // Overflow handling
  const containerRef = useRef<HTMLDivElement>(null);
  const tabsRef = useRef<HTMLDivElement>(null);
  const [overflow, setOverflow] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  
  // Check if tabs are overflowing
  useEffect(() => {
    const checkOverflow = () => {
      if (tabsRef.current && containerRef.current) {
        const isOverflowing = tabsRef.current.scrollWidth > containerRef.current.clientWidth;
        setOverflow(isOverflowing);
      }
    };
    
    checkOverflow();
    window.addEventListener('resize', checkOverflow);
    return () => window.removeEventListener('resize', checkOverflow);
  }, [tabs]);
  
  // Scroll to active tab when it changes
  useEffect(() => {
    if (tabsRef.current && containerRef.current && activeTab >= 0 && activeTab < tabs.length) {
      const tabElements = tabsRef.current.children;
      if (tabElements.length > activeTab) {
        const activeTabElement = tabElements[activeTab] as HTMLElement;
        const container = containerRef.current;
        
        // Check if active tab is outside the visible area
        const tabLeft = activeTabElement.offsetLeft;
        const tabRight = tabLeft + activeTabElement.offsetWidth;
        const containerLeft = container.scrollLeft;
        const containerRight = containerLeft + container.clientWidth;
        
        if (tabLeft < containerLeft) {
          // Scroll left to show the active tab
          container.scrollTo({ left: tabLeft - 10, behavior: 'smooth' });
        } else if (tabRight > containerRight) {
          // Scroll right to show the active tab
          container.scrollTo({ 
            left: tabRight - container.clientWidth + 10, 
            behavior: 'smooth' 
          });
        }
      }
    }
  }, [activeTab, tabs]);
  
  // Handle scrolling
  const scroll = (direction: 'left' | 'right') => {
    if (containerRef.current) {
      const container = containerRef.current;
      const scrollAmount = container.clientWidth / 2;
      const newPosition = direction === 'left' 
        ? Math.max(0, container.scrollLeft - scrollAmount)
        : container.scrollLeft + scrollAmount;
      
      container.scrollTo({ left: newPosition, behavior: 'smooth' });
    }
  };
  
  // Tab renaming functions
  const startRenameTab = (index: number) => {
    setIsRenamingTab(true);
    setRenamingTabIndex(index);
    setTabNewName(tabs[index].fileName);
    setActiveTab(index);
    
    // Focus the input field after rendering
    setTimeout(() => {
      if (renameInputRef.current) {
        renameInputRef.current.focus();
        renameInputRef.current.select();
      }
    }, 0);
  };
  
  const completeRenameTab = () => {
    if (!tabNewName.trim() || renamingTabIndex === -1) {
      cancelRenameTab();
      return;
    }
    
    handleRenameTab(renamingTabIndex, tabNewName);
    cancelRenameTab();
  };
  
  const cancelRenameTab = () => {
    setIsRenamingTab(false);
    setRenamingTabIndex(-1);
    setTabNewName('');
  };
  
  // Handle keyboard events in rename input
  const handleRenameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      completeRenameTab();
    } else if (e.key === 'Escape') {
      cancelRenameTab();
    }
  };
  
  // Create a unique label for each tab (in case of duplicate filenames)
  const getTabLabel = (tab: EditorTab, index: number): string => {
    const duplicateNames = tabs.filter(t => t.fileName === tab.fileName);
    if (duplicateNames.length > 1) {
      // Add a suffix to distinguish duplicate names
      return `${tab.fileName} (${index + 1})`;
    }
    return tab.fileName;
  };
  
  return (
    <div className="flex items-center">
      {/* Agent Framework logo and text */}
      <div className="flex items-center justify-center mr-3 flex-shrink-0">
        <div 
          className="relative flex items-center justify-center" 
          style={{ 
            width: `${logoSize}px`, 
            height: `${logoSize}px`,
            flexShrink: 0
          }}
        >
          <Image
            src="/icons/favicon-32x32.png"
            alt="Agent Framework"
            width={logoSize}
            height={logoSize}
            className="rounded-sm"
          />
        </div>
        <span className={`ml-2 font-bold text-lg ${isDarkTheme ? 'text-white' : 'text-black'}`}>
          Agent Framework
        </span>
      </div>
      
      {/* Left scroll button */}
      {overflow && (
        <button 
          onClick={() => scroll('left')}
          className={`px-1 flex-shrink-0 ${
            isDarkTheme ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-black'
          }`}
          title="Scroll left"
        >
          <ChevronLeft size={16} />
        </button>
      )}
      
      {/* Tabs container */}
      <div 
        ref={containerRef}
        className="flex-grow overflow-hidden"
      >
        <div 
          ref={tabsRef}
          className="flex space-x-1 overflow-x-auto scrollbar-hide"
          style={{ scrollBehavior: 'smooth' }}
        >
          {/* Tabs */}
          {tabs.map((tab, index) => (
            <div
              key={index}
              className={`flex items-center px-4 py-2 rounded-t flex-shrink-0 ${
                activeTab === index
                  ? 'bg-blue-500 text-white'
                  : isDarkTheme 
                    ? 'bg-gray-600 hover:bg-gray-500 text-gray-200' 
                    : 'bg-gray-200 hover:bg-gray-300'
              }`}
            >
              {isRenamingTab && renamingTabIndex === index ? (
                <input
                  ref={renameInputRef}
                  type="text"
                  value={tabNewName}
                  onChange={(e) => setTabNewName(e.target.value)}
                  onBlur={completeRenameTab}
                  onKeyDown={handleRenameKeyDown}
                  className="bg-transparent border-b border-white px-1 w-32 focus:outline-none"
                  autoFocus
                />
              ) : (
                <div className="flex items-center">
                  <button
                    className="mr-1 text-left"
                    onClick={() => setActiveTab(index)}
                    title={tab.fileName}
                  >
                    {getTabLabel(tab, index)}
                  </button>
                  <button
                    onClick={() => startRenameTab(index)}
                    className="ml-1 opacity-50 hover:opacity-100"
                    title="Rename tab"
                  >
                    <Edit className="h-3 w-3" />
                  </button>
                </div>
              )}
              <button
                onClick={(e) => handleCloseTab(index, e)}
                className={`ml-2 rounded-full h-5 w-5 flex items-center justify-center ${
                  activeTab === index
                    ? 'hover:bg-blue-600'
                    : isDarkTheme 
                      ? 'hover:bg-gray-500' 
                      : 'hover:bg-gray-400'
                }`}
                title="Close tab"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      </div>
      
      {/* Right scroll button */}
      {overflow && (
        <button 
          onClick={() => scroll('right')}
          className={`px-1 flex-shrink-0 ${
            isDarkTheme ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-black'
          }`}
          title="Scroll right"
        >
          <ChevronRight size={16} />
        </button>
      )}
      
      {/* Dropdown menu */}
      <div className="relative flex-shrink-0">
        <button 
          onClick={() => setShowDropdown(!showDropdown)}
          className={`p-1 ml-1 rounded ${
            isDarkTheme ? 'text-gray-300 hover:text-white hover:bg-gray-700' : 'text-gray-600 hover:text-black hover:bg-gray-200'
          }`}
          title="Show all tabs"
        >
          <MoreHorizontal size={16} />
        </button>
        
        {showDropdown && (
          <div 
            className={`absolute right-0 mt-1 z-10 w-64 rounded-md shadow-lg ${
              isDarkTheme ? 'bg-gray-700 border border-gray-600' : 'bg-white border border-gray-200'
            }`}
          >
            <div className="py-1 max-h-64 overflow-y-auto">
              {tabs.map((tab, index) => (
                <div
                  key={index}
                  className={`flex justify-between items-center px-4 py-2 cursor-pointer ${
                    activeTab === index
                      ? isDarkTheme ? 'bg-gray-600 text-white' : 'bg-gray-100 text-black'
                      : isDarkTheme ? 'text-gray-200 hover:bg-gray-600' : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={() => {
                    setActiveTab(index);
                    setShowDropdown(false);
                  }}
                >
                  <span className="truncate mr-2">{getTabLabel(tab, index)}</span>
                  <div className="flex items-center flex-shrink-0">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startRenameTab(index);
                        setShowDropdown(false);
                      }}
                      className="mx-1 opacity-70 hover:opacity-100"
                      title="Rename tab"
                    >
                      <Edit className="h-3 w-3" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCloseTab(index, e);
                      }}
                      className={`rounded-full h-5 w-5 flex items-center justify-center opacity-70 hover:opacity-100`}
                      title="Close tab"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Add new tab button */}
      <button
        className="px-2 py-1 rounded-full bg-green-500 text-white ml-2 flex-shrink-0"
        onClick={handleAddTab}
        title="Add new tab"
      >
        +
      </button>
    </div>
  );
}
