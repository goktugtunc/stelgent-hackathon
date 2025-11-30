'use client';

import { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder, Plus, Trash2, Edit2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function FileTree({ files, onFileSelect, onFileCreate, onFileDelete, onFileRename, selectedFile }) {
  const [expandedFolders, setExpandedFolders] = useState(new Set());
  const [renamingFile, setRenamingFile] = useState(null);
  const [newName, setNewName] = useState('');
  const [creatingNew, setCreatingNew] = useState(null);
  const [newFileName, setNewFileName] = useState('');

  const buildTree = (files) => {
    const tree = {};
    files.forEach(file => {
      const parts = file.path.split('/');
      let current = tree;
      parts.forEach((part, index) => {
        if (!current[part]) {
          current[part] = index === parts.length - 1 && file.type === 'file' 
            ? { ...file, isFile: true }
            : { children: {}, isFile: false };
        }
        if (!current[part].isFile) {
          current = current[part].children || {};
        }
      });
    });
    return tree;
  };

  const toggleFolder = (path) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const handleRename = async (file) => {
    if (newName && newName !== file.path) {
      await onFileRename(file.id, newName);
      setRenamingFile(null);
      setNewName('');
    }
  };

  const handleCreate = async (parentPath) => {
    if (newFileName) {
      const fullPath = parentPath ? `${parentPath}/${newFileName}` : newFileName;
      await onFileCreate(fullPath, newFileName.endsWith('/') ? 'folder' : 'file');
      setCreatingNew(null);
      setNewFileName('');
    }
  };

  const renderTree = (tree, parentPath = '') => {
    return Object.entries(tree).map(([name, node]) => {
      const currentPath = parentPath ? `${parentPath}/${name}` : name;
      const isExpanded = expandedFolders.has(currentPath);

      if (node.isFile) {
        return (
          <div
            key={node.id}
            className={`flex items-center gap-2 px-2 py-1 hover:bg-gray-700 rounded cursor-pointer group ${
              selectedFile?.id === node.id ? 'bg-gray-700' : ''
            }`}
            style={{ paddingLeft: `${(parentPath.split('/').length) * 16 + 8}px` }}
          >
            {renamingFile === node.id ? (
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onBlur={() => handleRename(node)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRename(node);
                  if (e.key === 'Escape') setRenamingFile(null);
                }}
                className="bg-gray-800 text-white text-sm h-6"
                autoFocus
              />
            ) : (
              <>
                <File className="h-4 w-4 text-gray-400" />
                <span
                  className="flex-1 text-sm text-gray-300"
                  onClick={() => onFileSelect(node)}
                >
                  {name}
                </span>
                <div className="hidden group-hover:flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      setRenamingFile(node.id);
                      setNewName(node.path);
                    }}
                  >
                    <Edit2 className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      onFileDelete(node.id);
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </>
            )}
          </div>
        );
      }

      return (
        <div key={currentPath}>
          <div
            className="flex items-center gap-2 px-2 py-1 hover:bg-gray-700 rounded cursor-pointer group"
            style={{ paddingLeft: `${(parentPath.split('/').filter(p => p).length) * 16 + 8}px` }}
            onClick={() => toggleFolder(currentPath)}
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-400" />
            )}
            <Folder className="h-4 w-4 text-gray-400" />
            <span className="flex-1 text-sm text-gray-300">{name}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 hidden group-hover:block"
              onClick={(e) => {
                e.stopPropagation();
                setCreatingNew(currentPath);
              }}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </div>
          {isExpanded && (
            <div>
              {creatingNew === currentPath && (
                <div
                  className="flex items-center gap-2 px-2 py-1"
                  style={{ paddingLeft: `${(currentPath.split('/').length) * 16 + 24}px` }}
                >
                  <Input
                    value={newFileName}
                    onChange={(e) => setNewFileName(e.target.value)}
                    onBlur={() => handleCreate(currentPath)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreate(currentPath);
                      if (e.key === 'Escape') setCreatingNew(null);
                    }}
                    placeholder="filename.js or folder/"
                    className="bg-gray-800 text-white text-sm h-6"
                    autoFocus
                  />
                </div>
              )}
              {renderTree(node.children, currentPath)}
            </div>
          )}
        </div>
      );
    });
  };

  const tree = buildTree(files);

  return (
    <div className="w-full h-full bg-gray-800 overflow-y-auto">
      <div className="p-2 border-b border-gray-700 flex items-center justify-between">
        <span className="text-sm font-semibold text-gray-300">EXPLORER</span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => setCreatingNew('root')}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <div className="p-2">
        {creatingNew === 'root' && (
          <div className="flex items-center gap-2 px-2 py-1 mb-2">
            <Input
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              onBlur={() => handleCreate('')}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreate('');
                if (e.key === 'Escape') setCreatingNew(null);
              }}
              placeholder="filename.js or folder/"
              className="bg-gray-800 text-white text-sm h-6"
              autoFocus
            />
          </div>
        )}
        {renderTree(tree)}
      </div>
    </div>
  );
}
