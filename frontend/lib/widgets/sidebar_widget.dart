import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/filesystem_provider.dart';
import '../theme/tokens.dart';
import 'file_tree_widget.dart';

class SidebarWidget extends StatefulWidget {
  final double width;

  const SidebarWidget({
    super.key,
    this.width = 250,
  });

  @override
  State<SidebarWidget> createState() => _SidebarWidgetState();
}

class _SidebarWidgetState extends State<SidebarWidget> {
  final TextEditingController _searchController = TextEditingController();
  bool _isSearching = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final provider = context.watch<FilesystemProvider>();

    return Container(
      width: widget.width,
      color: theme.colorScheme.surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          _buildHeader(context, theme),

          const Divider(height: 1),

          // Search bar
          _buildSearchBar(context, theme),

          // Tree or loading/error state
          Expanded(
            child: _buildContent(context, theme, provider),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context, ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.md,
        vertical: Spacing.sm,
      ),
      child: Row(
        children: [
          Icon(
            Icons.folder_special,
            size: IconSizes.md,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(width: Spacing.sm),
          Text(
            'Notes',
            style: TextStyle(
              fontSize: TypeScale.lg,
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onSurface,
            ),
          ),
          const Spacer(),
          // New folder button
          IconButton(
            icon: const Icon(Icons.create_new_folder, size: IconSizes.sm),
            tooltip: 'New Folder',
            onPressed: () => _showNewFolderDialog(context),
            padding: const EdgeInsets.all(Spacing.xs),
            constraints: const BoxConstraints(),
          ),
          // New file button
          IconButton(
            icon: const Icon(Icons.note_add, size: IconSizes.sm),
            tooltip: 'New File',
            onPressed: () => _showNewFileDialog(context),
            padding: const EdgeInsets.all(Spacing.xs),
            constraints: const BoxConstraints(),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar(BuildContext context, ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(Spacing.sm),
      child: TextField(
        controller: _searchController,
        decoration: InputDecoration(
          hintText: 'Search files...',
          prefixIcon: const Icon(Icons.search, size: IconSizes.sm),
          suffixIcon: _isSearching
              ? IconButton(
                  icon: const Icon(Icons.close, size: IconSizes.sm),
                  onPressed: () {
                    _searchController.clear();
                    setState(() => _isSearching = false);
                  },
                )
              : null,
          isDense: true,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: Spacing.sm,
            vertical: Spacing.sm,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(Radii.md),
          ),
        ),
        style: const TextStyle(fontSize: TypeScale.sm),
        onChanged: (value) {
          setState(() => _isSearching = value.isNotEmpty);
        },
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    ThemeData theme,
    FilesystemProvider provider,
  ) {
    if (provider.isLoading && provider.rootNodes.isEmpty) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (provider.errorMessage != null && provider.rootNodes.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.lg),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.error_outline,
                size: IconSizes.xxl,
                color: theme.colorScheme.error,
              ),
              const SizedBox(height: Spacing.md),
              Text(
                'Failed to load files',
                style: TextStyle(
                  color: theme.colorScheme.error,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: Spacing.sm),
              TextButton(
                onPressed: () => provider.loadTree(),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (provider.rootNodes.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.lg),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.folder_open,
                size: IconSizes.xxl,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
              ),
              const SizedBox(height: Spacing.md),
              Text(
                'No files yet',
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
              ),
              const SizedBox(height: Spacing.sm),
              TextButton.icon(
                onPressed: () => _showNewFileDialog(context),
                icon: const Icon(Icons.add),
                label: const Text('Create a note'),
              ),
            ],
          ),
        ),
      );
    }

    // Show search results or tree
    if (_isSearching && _searchController.text.isNotEmpty) {
      return _buildSearchResults(context, theme, provider);
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(vertical: Spacing.sm),
      child: FileTreeWidget(nodes: provider.rootNodes),
    );
  }

  Widget _buildSearchResults(
    BuildContext context,
    ThemeData theme,
    FilesystemProvider provider,
  ) {
    return FutureBuilder(
      future: provider.searchFiles(_searchController.text),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        final results = snapshot.data ?? [];

        if (results.isEmpty) {
          return Center(
            child: Text(
              'No results found',
              style: TextStyle(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.symmetric(vertical: Spacing.sm),
          itemCount: results.length,
          itemBuilder: (context, index) {
            final node = results[index];
            return ListTile(
              dense: true,
              leading: Icon(
                node.isFolder ? Icons.folder : Icons.description,
                size: IconSizes.sm,
              ),
              title: Text(
                node.name,
                style: const TextStyle(fontSize: TypeScale.sm),
              ),
              subtitle: Text(
                node.path,
                style: TextStyle(
                  fontSize: TypeScale.xs,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
              onTap: () {
                provider.selectNode(node);
                provider.openFile(node);
                _searchController.clear();
                setState(() => _isSearching = false);
              },
            );
          },
        );
      },
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
              provider.createFolder('/', name);
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
                provider.createFolder('/', name);
                Navigator.of(context).pop();
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
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
              provider.createFile('/', name);
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
                provider.createFile('/', name);
                Navigator.of(context).pop();
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

}
