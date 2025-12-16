import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/fs_node.dart';
import '../services/filesystem_provider.dart';
import '../theme/tokens.dart';

class FileTreeWidget extends StatelessWidget {
  final List<FsNode> nodes;
  final int depth;

  const FileTreeWidget({
    super.key,
    required this.nodes,
    this.depth = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: nodes.map((node) => FileTreeItem(
        node: node,
        depth: depth,
      )).toList(),
    );
  }
}

class FileTreeItem extends StatelessWidget {
  final FsNode node;
  final int depth;

  const FileTreeItem({
    super.key,
    required this.node,
    required this.depth,
  });

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<FilesystemProvider>();
    final isSelected = provider.selectedNode?.path == node.path;
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () => _onTap(context),
          onLongPress: () => _showContextMenu(context),
          child: Container(
            padding: EdgeInsets.only(
              left: Spacing.md + (depth * Spacing.lg),
              right: Spacing.sm,
              top: Spacing.xs,
              bottom: Spacing.xs,
            ),
            decoration: BoxDecoration(
              color: isSelected
                  ? theme.colorScheme.primary.withOpacity(0.15)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(Radii.sm),
            ),
            child: Row(
              children: [
                // Expand/collapse icon for folders
                if (node.isFolder)
                  GestureDetector(
                    onTap: () => _toggleExpand(context),
                    child: Padding(
                      padding: const EdgeInsets.only(right: Spacing.xs),
                      child: Icon(
                        node.isExpanded
                            ? Icons.keyboard_arrow_down
                            : Icons.keyboard_arrow_right,
                        size: IconSizes.sm,
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  )
                else
                  const SizedBox(width: IconSizes.sm + Spacing.xs),

                // Node icon
                Icon(
                  _getNodeIcon(),
                  size: IconSizes.sm,
                  color: _getIconColor(context),
                ),
                const SizedBox(width: Spacing.sm),

                // Node name
                Expanded(
                  child: Text(
                    node.name,
                    style: TextStyle(
                      fontSize: TypeScale.sm,
                      fontWeight: isSelected ? FontWeight.w500 : FontWeight.normal,
                      color: theme.colorScheme.onSurface,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),

                // Loading indicator
                if (node.isLoading)
                  SizedBox(
                    width: IconSizes.sm,
                    height: IconSizes.sm,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: theme.colorScheme.primary,
                    ),
                  ),
              ],
            ),
          ),
        ),

        // Children (if expanded folder)
        if (node.isFolder && node.isExpanded && node.children.isNotEmpty)
          FileTreeWidget(
            nodes: node.children,
            depth: depth + 1,
          ),
      ],
    );
  }

  IconData _getNodeIcon() {
    if (node.isFolder) {
      if (node.path == '/daily') {
        return Icons.calendar_today;
      }
      return node.isExpanded ? Icons.folder_open : Icons.folder;
    }

    // File icons
    if (node.isDaily) {
      return Icons.event_note;
    }
    if (node.isMarkdown) {
      return Icons.description;
    }
    return Icons.insert_drive_file;
  }

  Color _getIconColor(BuildContext context) {
    final theme = Theme.of(context);

    if (node.isFolder) {
      if (node.path == '/daily') {
        return theme.colorScheme.primary;
      }
      return theme.colorScheme.secondary;
    }

    if (node.isDaily) {
      return theme.colorScheme.primary;
    }

    return theme.colorScheme.onSurface.withOpacity(0.7);
  }

  void _onTap(BuildContext context) {
    final provider = context.read<FilesystemProvider>();

    if (node.isFolder) {
      provider.toggleFolderExpanded(node);
    } else {
      provider.selectNode(node);
      provider.openFile(node);
    }
  }

  void _toggleExpand(BuildContext context) {
    final provider = context.read<FilesystemProvider>();
    provider.toggleFolderExpanded(node);
  }

  void _showContextMenu(BuildContext context) {
    final RenderBox renderBox = context.findRenderObject() as RenderBox;
    final position = renderBox.localToGlobal(Offset.zero);

    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(
        position.dx,
        position.dy + renderBox.size.height,
        position.dx + renderBox.size.width,
        position.dy + renderBox.size.height,
      ),
      items: [
        if (node.isFolder) ...[
          const PopupMenuItem(
            value: 'new_file',
            child: Row(
              children: [
                Icon(Icons.add, size: IconSizes.sm),
                SizedBox(width: Spacing.sm),
                Text('New File'),
              ],
            ),
          ),
          const PopupMenuItem(
            value: 'new_folder',
            child: Row(
              children: [
                Icon(Icons.create_new_folder, size: IconSizes.sm),
                SizedBox(width: Spacing.sm),
                Text('New Folder'),
              ],
            ),
          ),
        ],
        const PopupMenuItem(
          value: 'rename',
          child: Row(
            children: [
              Icon(Icons.edit, size: IconSizes.sm),
              SizedBox(width: Spacing.sm),
              Text('Rename'),
            ],
          ),
        ),
        const PopupMenuItem(
          value: 'delete',
          child: Row(
            children: [
              Icon(Icons.delete, size: IconSizes.sm, color: Colors.red),
              SizedBox(width: Spacing.sm),
              Text('Delete', style: TextStyle(color: Colors.red)),
            ],
          ),
        ),
      ],
    ).then((value) {
      if (value == null) return;

      switch (value) {
        case 'new_file':
          _showNewFileDialog(context);
          break;
        case 'new_folder':
          _showNewFolderDialog(context);
          break;
        case 'rename':
          _showRenameDialog(context);
          break;
        case 'delete':
          _showDeleteDialog(context);
          break;
      }
    });
  }

  void _showNewFileDialog(BuildContext context) {
    final controller = TextEditingController();
    final provider = context.read<FilesystemProvider>();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('New File'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'filename.md',
            labelText: 'File name',
          ),
          onSubmitted: (_) {
            final name = controller.text.trim();
            if (name.isNotEmpty) {
              provider.createFile(node.path, name);
              Navigator.of(context).pop();
            }
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              final name = controller.text.trim();
              if (name.isNotEmpty) {
                provider.createFile(node.path, name);
                Navigator.of(context).pop();
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  void _showNewFolderDialog(BuildContext context) {
    final controller = TextEditingController();
    final provider = context.read<FilesystemProvider>();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('New Folder'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            hintText: 'Folder name',
            labelText: 'Name',
          ),
          onSubmitted: (_) {
            final name = controller.text.trim();
            if (name.isNotEmpty) {
              provider.createFolder(node.path, name);
              Navigator.of(context).pop();
            }
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              final name = controller.text.trim();
              if (name.isNotEmpty) {
                provider.createFolder(node.path, name);
                Navigator.of(context).pop();
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  void _showRenameDialog(BuildContext context) {
    final controller = TextEditingController(text: node.name);
    final provider = context.read<FilesystemProvider>();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Rename'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'New name',
          ),
          onSubmitted: (_) {
            final newName = controller.text.trim();
            if (newName.isNotEmpty && newName != node.name) {
              provider.moveNode(node, newName: newName);
              Navigator.of(context).pop();
            }
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              final newName = controller.text.trim();
              if (newName.isNotEmpty && newName != node.name) {
                provider.moveNode(node, newName: newName);
                Navigator.of(context).pop();
              }
            },
            child: const Text('Rename'),
          ),
        ],
      ),
    );
  }

  void _showDeleteDialog(BuildContext context) {
    final provider = context.read<FilesystemProvider>();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete'),
        content: Text(
          node.isFolder
              ? 'Are you sure you want to delete "${node.name}" and all its contents?'
              : 'Are you sure you want to delete "${node.name}"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              provider.deleteNode(node);
              Navigator.of(context).pop();
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }
}
