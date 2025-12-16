import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/filesystem_provider.dart';
import '../theme/tokens.dart';
import 'file_tree_widget.dart';

class SidebarWidget extends StatefulWidget {
  final double width;
  final VoidCallback? onTodayPressed;

  const SidebarWidget({
    super.key,
    this.width = 250,
    this.onTodayPressed,
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

          // Quick actions
          _buildQuickActions(context, theme, provider),

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

  Widget _buildQuickActions(
    BuildContext context,
    ThemeData theme,
    FilesystemProvider provider,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.sm,
        vertical: Spacing.xs,
      ),
      child: Row(
        children: [
          Expanded(
            child: _QuickActionButton(
              icon: Icons.today,
              label: 'Today',
              onPressed: () async {
                await provider.getTodayNote();
                widget.onTodayPressed?.call();
              },
            ),
          ),
          const SizedBox(width: Spacing.sm),
          Expanded(
            child: _QuickActionButton(
              icon: Icons.calendar_month,
              label: 'Calendar',
              onPressed: () => _showDatePicker(context, provider),
            ),
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
                color: theme.colorScheme.onSurface.withOpacity(0.4),
              ),
              const SizedBox(height: Spacing.md),
              Text(
                'No files yet',
                style: TextStyle(
                  color: theme.colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
              const SizedBox(height: Spacing.sm),
              TextButton.icon(
                onPressed: () => provider.getTodayNote(),
                icon: const Icon(Icons.add),
                label: const Text('Create today\'s note'),
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
                color: theme.colorScheme.onSurface.withOpacity(0.6),
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
                node.isDaily ? Icons.event_note : Icons.description,
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
                  color: theme.colorScheme.onSurface.withOpacity(0.5),
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

  void _showDatePicker(BuildContext context, FilesystemProvider provider) async {
    final date = await showDatePicker(
      context: context,
      initialDate: provider.selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );

    if (date != null) {
      await provider.getDailyNote(date);
    }
  }
}

class _QuickActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  const _QuickActionButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: theme.colorScheme.primary.withOpacity(0.1),
      borderRadius: BorderRadius.circular(Radii.md),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(Radii.md),
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: Spacing.sm,
            vertical: Spacing.sm,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: IconSizes.sm,
                color: theme.colorScheme.primary,
              ),
              const SizedBox(width: Spacing.xs),
              Text(
                label,
                style: TextStyle(
                  fontSize: TypeScale.sm,
                  fontWeight: FontWeight.w500,
                  color: theme.colorScheme.primary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
