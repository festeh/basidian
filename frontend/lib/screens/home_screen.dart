import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/filesystem_provider.dart';
import '../services/audio_service.dart';
import '../services/asr_settings_provider.dart';
import '../widgets/sidebar_widget.dart';
import '../theme/tokens.dart';
import 'file_editor_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final AudioService _audioService = AudioService();
  bool _isRecording = false;
  bool _isTranscribing = false;
  bool _sidebarCollapsed = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FilesystemProvider>().loadTree();
    });
  }

  @override
  void dispose() {
    _audioService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final screenWidth = MediaQuery.of(context).size.width;
    final isNarrow = screenWidth < 800;

    return Scaffold(
      body: SafeArea(
        child: Row(
          children: [
            // Sidebar (or drawer on narrow screens)
            if (!isNarrow && !_sidebarCollapsed)
              SidebarWidget(
                width: 280,
                onTodayPressed: () {},
              ),

            // Divider between sidebar and content
            if (!isNarrow && !_sidebarCollapsed)
              VerticalDivider(
                width: 1,
                thickness: 1,
                color: colorScheme.outline.withOpacity(0.2),
              ),

            // Main content area
            Expanded(
              child: Column(
                children: [
                  // Top bar
                  _buildTopBar(context, colorScheme, isNarrow),

                  const Divider(height: 1),

                  // File editor
                  Expanded(
                    child: Consumer<FilesystemProvider>(
                      builder: (context, provider, child) {
                        if (provider.isLoadingFile) {
                          return const Center(
                            child: CircularProgressIndicator(),
                          );
                        }

                        return FileEditorScreen(
                          file: provider.currentFile,
                          embedded: true,
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      drawer: isNarrow
          ? Drawer(
              child: SidebarWidget(
                width: 300,
                onTodayPressed: () {
                  Navigator.of(context).pop();
                },
              ),
            )
          : null,
      floatingActionButton: _buildFab(context, colorScheme),
    );
  }

  Widget _buildTopBar(BuildContext context, ColorScheme colorScheme, bool isNarrow) {
    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: Spacing.md,
        vertical: Spacing.sm,
      ),
      child: Row(
        children: [
          // Hamburger menu for narrow screens
          if (isNarrow)
            IconButton(
              icon: const Icon(Icons.menu),
              onPressed: () => Scaffold.of(context).openDrawer(),
              tooltip: 'Open sidebar',
            ),

          // Toggle sidebar button for wide screens
          if (!isNarrow)
            IconButton(
              icon: Icon(_sidebarCollapsed
                  ? Icons.chevron_right
                  : Icons.chevron_left),
              onPressed: () {
                setState(() {
                  _sidebarCollapsed = !_sidebarCollapsed;
                });
              },
              tooltip: _sidebarCollapsed ? 'Show sidebar' : 'Hide sidebar',
            ),

          SizedBox(width: Spacing.sm),

          // App title
          Text(
            'Basidian',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),

          const Spacer(),

          // Today button
          IconButton(
            icon: const Icon(Icons.today),
            onPressed: () {
              context.read<FilesystemProvider>().getTodayNote();
            },
            tooltip: 'Go to Today',
            style: IconButton.styleFrom(
              backgroundColor: colorScheme.primaryContainer,
            ),
          ),
          SizedBox(width: Spacing.xs),

          // Settings button
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SettingsScreen()),
              );
            },
            tooltip: 'Settings',
          ),
        ],
      ),
    );
  }

  Widget _buildFab(BuildContext context, ColorScheme colorScheme) {
    return Padding(
      padding: EdgeInsets.only(left: Spacing.xxxl),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          // Mic button
          FloatingActionButton(
            onPressed: _isTranscribing ? null : _toggleRecording,
            heroTag: 'mic_button',
            backgroundColor: _isRecording
                ? colorScheme.error
                : (_isTranscribing
                    ? colorScheme.outline
                    : colorScheme.secondary),
            child: _isTranscribing
                ? SizedBox(
                    width: IconSizes.lg,
                    height: IconSizes.lg,
                    child: CircularProgressIndicator(
                      color: colorScheme.onSecondary,
                      strokeWidth: 2,
                    ),
                  )
                : Icon(_isRecording ? Icons.stop : Icons.mic),
          ),
          SizedBox(width: Spacing.lg),

          // New file button
          FloatingActionButton(
            onPressed: _showNewFileDialog,
            heroTag: 'new_file_button',
            child: const Icon(Icons.add),
          ),
        ],
      ),
    );
  }

  void _showNewFileDialog() {
    final controller = TextEditingController();
    final provider = context.read<FilesystemProvider>();

    // Default to creating in /daily folder or root
    String parentPath = '/';
    if (provider.selectedNode?.isFolder == true) {
      parentPath = provider.selectedNode!.path;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('New File'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Creating in: $parentPath',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            SizedBox(height: Spacing.md),
            TextField(
              controller: controller,
              autofocus: true,
              decoration: const InputDecoration(
                hintText: 'filename.md',
                labelText: 'File name',
              ),
              onSubmitted: (_) async {
                final name = controller.text.trim();
                if (name.isNotEmpty) {
                  Navigator.of(context).pop();
                  final newFile = await provider.createFile(parentPath, name);
                  if (newFile != null) {
                    provider.openFile(newFile);
                  }
                }
              },
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              final name = controller.text.trim();
              if (name.isNotEmpty) {
                Navigator.of(context).pop();
                final newFile = await provider.createFile(parentPath, name);
                if (newFile != null) {
                  provider.openFile(newFile);
                }
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  Future<void> _toggleRecording() async {
    final provider = context.read<FilesystemProvider>();

    if (_isRecording) {
      setState(() {
        _isRecording = false;
        _isTranscribing = true;
      });

      try {
        final path = await _audioService.stopRecording();
        if (path != null && path.isNotEmpty) {
          final languageCode = context.read<ASRSettingsProvider>().language.code;
          final transcribedText = await _audioService.transcribeAudio(
            path,
            languageCode: languageCode,
          );

          // Create a new daily note with transcribed text
          final now = DateTime.now();
          final dailyNote = await provider.getDailyNote(now);

          if (dailyNote != null && mounted) {
            // Append transcription to daily note
            final existingContent = dailyNote.content ?? '';
            final timestamp = TimeOfDay.now().format(context);
            final newContent = existingContent.isEmpty
                ? '## $timestamp\n\n$transcribedText'
                : '$existingContent\n\n## $timestamp\n\n$transcribedText';

            final updatedNote = dailyNote.copyWith(content: newContent);
            await provider.updateNode(updatedNote);
            provider.openFile(updatedNote);
          }

          setState(() {
            _isTranscribing = false;
          });
        } else {
          setState(() {
            _isTranscribing = false;
          });
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Recording failed')),
            );
          }
        }
      } catch (e) {
        setState(() {
          _isTranscribing = false;
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }
      }
    } else {
      try {
        final path = await _audioService.startRecording();
        if (path != null) {
          setState(() {
            _isRecording = true;
          });
        } else {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Failed to start recording')),
            );
          }
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }
      }
    }
  }
}
