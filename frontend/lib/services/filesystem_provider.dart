import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/fs_node.dart';
import 'api_service.dart';

class FilesystemProvider extends ChangeNotifier {
  List<FsNode> _rootNodes = [];
  FsNode? _selectedNode;
  FsNode? _currentFile;
  Set<String> _expandedPaths = {};
  bool _isLoading = false;
  bool _isLoadingFile = false;
  String? _errorMessage;
  DateTime _selectedDate = DateTime.now();

  // Getters
  List<FsNode> get rootNodes => _rootNodes;
  FsNode? get selectedNode => _selectedNode;
  FsNode? get currentFile => _currentFile;
  Set<String> get expandedPaths => _expandedPaths;
  bool get isLoading => _isLoading;
  bool get isLoadingFile => _isLoadingFile;
  String? get errorMessage => _errorMessage;
  DateTime get selectedDate => _selectedDate;

  FilesystemProvider() {
    _loadExpandedState();
  }

  // Load the full tree from the server
  Future<void> loadTree() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final nodes = await ApiService.getTree();
      _rootNodes = _buildTree(nodes);
      _applyExpandedState();
    } catch (e) {
      _errorMessage = e.toString();
    }

    _isLoading = false;
    notifyListeners();
  }

  // Build tree structure from flat list
  List<FsNode> _buildTree(List<FsNode> flatNodes) {
    final Map<String, FsNode> nodeMap = {};
    final List<FsNode> rootNodes = [];

    // First pass: create a map of all nodes by path
    for (final node in flatNodes) {
      nodeMap[node.path] = node;
    }

    // Second pass: build parent-child relationships
    for (final node in flatNodes) {
      if (node.parentPath == '/') {
        rootNodes.add(node);
      } else {
        final parent = nodeMap[node.parentPath];
        if (parent != null) {
          parent.children.add(node);
        } else {
          // Parent not found, treat as root
          rootNodes.add(node);
        }
      }
    }

    // Sort children: folders first, then by name
    void sortChildren(List<FsNode> nodes) {
      nodes.sort((a, b) {
        if (a.isFolder && b.isFile) return -1;
        if (a.isFile && b.isFolder) return 1;
        if (a.sortOrder != b.sortOrder) {
          return a.sortOrder.compareTo(b.sortOrder);
        }
        return a.name.compareTo(b.name);
      });
      for (final node in nodes) {
        if (node.isFolder) {
          sortChildren(node.children);
        }
      }
    }

    sortChildren(rootNodes);
    return rootNodes;
  }

  // Apply expanded state from saved preferences
  void _applyExpandedState() {
    void applyToNodes(List<FsNode> nodes) {
      for (final node in nodes) {
        node.isExpanded = _expandedPaths.contains(node.path);
        if (node.isFolder) {
          applyToNodes(node.children);
        }
      }
    }
    applyToNodes(_rootNodes);
  }

  // Load children for a specific folder
  Future<void> loadChildren(FsNode folder) async {
    if (!folder.isFolder) return;

    folder.isLoading = true;
    notifyListeners();

    try {
      final children = await ApiService.getTree(parentPath: folder.path);
      folder.children = children;
      // Sort children
      folder.children.sort((a, b) {
        if (a.isFolder && b.isFile) return -1;
        if (a.isFile && b.isFolder) return 1;
        return a.name.compareTo(b.name);
      });
    } catch (e) {
      _errorMessage = e.toString();
    }

    folder.isLoading = false;
    notifyListeners();
  }

  // Toggle folder expanded state
  void toggleFolderExpanded(FsNode folder) {
    if (!folder.isFolder) return;

    folder.isExpanded = !folder.isExpanded;

    if (folder.isExpanded) {
      _expandedPaths.add(folder.path);
    } else {
      _expandedPaths.remove(folder.path);
    }

    _saveExpandedState();
    notifyListeners();
  }

  // Select a node
  void selectNode(FsNode? node) {
    _selectedNode = node;
    notifyListeners();
  }

  // Open a file for editing
  Future<void> openFile(FsNode node) async {
    if (!node.isFile) return;

    _isLoadingFile = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // Fetch full content if needed
      if (node.id != null) {
        final fullNode = await ApiService.getNodeById(node.id!);
        _currentFile = fullNode;
      } else {
        _currentFile = node;
      }
      _selectedNode = _currentFile;
    } catch (e) {
      _errorMessage = e.toString();
    }

    _isLoadingFile = false;
    notifyListeners();
  }

  // Close the current file
  void closeFile() {
    _currentFile = null;
    notifyListeners();
  }

  // Create a new folder
  Future<FsNode?> createFolder(String parentPath, String name) async {
    try {
      final newFolder = FsNode.folder(name: name, parentPath: parentPath);
      final created = await ApiService.createNode(newFolder);
      await loadTree(); // Refresh tree
      return created;
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return null;
    }
  }

  // Create a new file
  Future<FsNode?> createFile(String parentPath, String name, {String? content}) async {
    try {
      final newFile = FsNode.file(
        name: name,
        parentPath: parentPath,
        content: content ?? '',
      );
      final created = await ApiService.createNode(newFile);
      await loadTree(); // Refresh tree
      return created;
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return null;
    }
  }

  // Update a node (save content)
  Future<void> updateNode(FsNode node) async {
    try {
      final updated = await ApiService.updateNode(node);
      if (_currentFile?.id == node.id) {
        _currentFile = updated;
      }
      // Update in tree
      _updateNodeInTree(updated);
      notifyListeners();
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  void _updateNodeInTree(FsNode updated) {
    void updateInList(List<FsNode> nodes) {
      for (int i = 0; i < nodes.length; i++) {
        if (nodes[i].id == updated.id) {
          final oldNode = nodes[i];
          nodes[i] = updated.copyWith(
            children: oldNode.children,
            isExpanded: oldNode.isExpanded,
          );
          return;
        }
        if (nodes[i].isFolder) {
          updateInList(nodes[i].children);
        }
      }
    }
    updateInList(_rootNodes);
  }

  // Delete a node
  Future<void> deleteNode(FsNode node) async {
    try {
      await ApiService.deleteNode(node.id!);
      if (_currentFile?.id == node.id) {
        _currentFile = null;
      }
      if (_selectedNode?.id == node.id) {
        _selectedNode = null;
      }
      await loadTree(); // Refresh tree
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  // Move or rename a node
  Future<void> moveNode(FsNode node, {String? newParentPath, String? newName}) async {
    try {
      await ApiService.moveNode(node.id!, newParentPath: newParentPath, newName: newName);
      await loadTree(); // Refresh tree
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
    }
  }

  // Get or create today's daily note
  Future<FsNode?> getTodayNote() async {
    return getDailyNote(DateTime.now());
  }

  // Get or create a daily note for a specific date
  Future<FsNode?> getDailyNote(DateTime date) async {
    _isLoadingFile = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final note = await ApiService.getOrCreateDailyNote(date);
      _currentFile = note;
      _selectedNode = note;
      _selectedDate = date;

      // Ensure the tree is refreshed to include the new note
      await loadTree();

      // Expand the /daily folder
      _expandedPaths.add('/daily');
      _applyExpandedState();
      _saveExpandedState();

      _isLoadingFile = false;
      notifyListeners();
      return note;
    } catch (e) {
      _errorMessage = e.toString();
      _isLoadingFile = false;
      notifyListeners();
      return null;
    }
  }

  // Set selected date (for date picker integration)
  void setSelectedDate(DateTime date) {
    _selectedDate = date;
    notifyListeners();
  }

  // Search files
  Future<List<FsNode>> searchFiles(String query) async {
    try {
      return await ApiService.searchFiles(query);
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return [];
    }
  }

  // Migrate existing notes to filesystem
  Future<Map<String, dynamic>?> migrateNotes() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final result = await ApiService.migrateToFilesystem();
      await loadTree(); // Refresh tree after migration
      _isLoading = false;
      notifyListeners();
      return result;
    } catch (e) {
      _errorMessage = e.toString();
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  // Find a node by path in the tree
  FsNode? findNodeByPath(String path) {
    FsNode? find(List<FsNode> nodes) {
      for (final node in nodes) {
        if (node.path == path) return node;
        if (node.isFolder) {
          final found = find(node.children);
          if (found != null) return found;
        }
      }
      return null;
    }
    return find(_rootNodes);
  }

  // Get breadcrumb path for current file
  List<FsNode> getBreadcrumb(FsNode node) {
    final List<FsNode> breadcrumb = [];
    String currentPath = node.parentPath;

    while (currentPath != '/') {
      final parent = findNodeByPath(currentPath);
      if (parent != null) {
        breadcrumb.insert(0, parent);
        currentPath = parent.parentPath;
      } else {
        break;
      }
    }

    breadcrumb.add(node);
    return breadcrumb;
  }

  // Clear error message
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  // Persistence for expanded state
  Future<void> _loadExpandedState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final expanded = prefs.getStringList('fs_expanded_paths');
      if (expanded != null) {
        _expandedPaths = expanded.toSet();
      }
    } catch (e) {
      // Ignore errors loading preferences
    }
  }

  Future<void> _saveExpandedState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setStringList('fs_expanded_paths', _expandedPaths.toList());
    } catch (e) {
      // Ignore errors saving preferences
    }
  }
}
