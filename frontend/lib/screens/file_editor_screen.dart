import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../models/fs_node.dart';
import '../services/filesystem_provider.dart';
import '../services/audio_service.dart';
import '../services/asr_settings_provider.dart';
import '../theme/tokens.dart';

class FileEditorScreen extends StatefulWidget {
  final FsNode? file;
  final bool embedded;

  const FileEditorScreen({
    super.key,
    this.file,
    this.embedded = false,
  });

  @override
  State<FileEditorScreen> createState() => _FileEditorScreenState();
}

class _FileEditorScreenState extends State<FileEditorScreen> {
  final _contentController = TextEditingController();
  final _contentFocusNode = FocusNode();
  final _audioService = AudioService();

  bool _hasChanges = false;
  bool _isSaving = false;
  bool _isRecording = false;
  bool _isTranscribing = false;

  late String _originalContent;
  FsNode? _currentFile;

  @override
  void initState() {
    super.initState();
    _currentFile = widget.file;
    _initializeContent();
    _contentController.addListener(_onTextChanged);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _contentFocusNode.requestFocus();
    });
  }

  void _initializeContent() {
    _originalContent = _currentFile?.content ?? '';
    _contentController.text = _originalContent;
  }

  @override
  void didUpdateWidget(FileEditorScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.file?.path != oldWidget.file?.path) {
      _currentFile = widget.file;
      _initializeContent();
      _hasChanges = false;
    }
  }

  @override
  void dispose() {
    _contentController.dispose();
    _contentFocusNode.dispose();
    _audioService.dispose();
    super.dispose();
  }

  void _onTextChanged() {
    final hasChanges = _contentController.text != _originalContent;
    if (hasChanges != _hasChanges) {
      setState(() {
        _hasChanges = hasChanges;
      });
    }
  }

  Future<void> _saveFile() async {
    if (_currentFile == null) return;

    setState(() {
      _isSaving = true;
    });

    try {
      final updatedFile = _currentFile!.copyWith(
        content: _contentController.text,
      );

      await context.read<FilesystemProvider>().updateNode(updatedFile);
      _originalContent = _contentController.text;

      setState(() {
        _hasChanges = false;
        _isSaving = false;
      });

      if (mounted && !widget.embedded) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('File saved')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error saving file: $e'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
      setState(() {
        _isSaving = false;
      });
    }
  }

  Future<bool> _onWillPop() async {
    if (!_hasChanges) {
      return true;
    }

    return await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Unsaved Changes'),
          content: const Text('Do you want to save your changes before leaving?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('Discard'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(false);
                _saveFile();
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    ) ?? false;
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      setState(() {
        _isRecording = false;
        _isTranscribing = true;
      });

      try {
        final filePath = await _audioService.stopRecording();
        if (filePath != null) {
          final languageCode = context.read<ASRSettingsProvider>().language.code;
          final transcription = await _audioService.transcribeAudio(
            filePath,
            languageCode: languageCode,
          );

          final currentText = _contentController.text;
          final selection = _contentController.selection;
          final newText = currentText.replaceRange(
            selection.start,
            selection.end,
            transcription,
          );

          _contentController.text = newText;
          _contentController.selection = TextSelection.collapsed(
            offset: selection.start + transcription.length,
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Error: $e'),
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isTranscribing = false;
          });
        }
      }
    } else {
      try {
        await _audioService.startRecording();
        setState(() {
          _isRecording = true;
        });
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Error starting recording: $e'),
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    // Watch for file changes from provider
    final provider = context.watch<FilesystemProvider>();
    if (provider.currentFile != null &&
        provider.currentFile?.path != _currentFile?.path) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        setState(() {
          _currentFile = provider.currentFile;
          _initializeContent();
          _hasChanges = false;
        });
      });
    }

    if (_currentFile == null) {
      return _buildEmptyState(context);
    }

    final content = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header with file info
        _buildHeader(context, colorScheme),

        const Divider(height: 1),

        // Content editor
        Expanded(
          child: Padding(
            padding: EdgeInsets.all(Spacing.lg),
            child: TextField(
              controller: _contentController,
              focusNode: _contentFocusNode,
              decoration: const InputDecoration(
                hintText: 'Start writing...',
                border: InputBorder.none,
                contentPadding: EdgeInsets.zero,
              ),
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontFamily: 'monospace',
                height: 1.6,
              ),
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
            ),
          ),
        ),

        // Bottom bar with save status
        if (_hasChanges) _buildBottomBar(context, colorScheme),
      ],
    );

    if (widget.embedded) {
      return Focus(
        autofocus: false,
        onKeyEvent: (node, event) {
          if (event is KeyDownEvent &&
              event.logicalKey == LogicalKeyboardKey.keyS &&
              (HardwareKeyboard.instance.isControlPressed ||
                  HardwareKeyboard.instance.isMetaPressed)) {
            _saveFile();
            return KeyEventResult.handled;
          }
          return KeyEventResult.ignored;
        },
        child: content,
      );
    }

    return Focus(
      autofocus: true,
      onKeyEvent: (node, event) {
        if (event is KeyDownEvent) {
          if (event.logicalKey == LogicalKeyboardKey.escape) {
            _onWillPop().then((canPop) {
              if (canPop && mounted) Navigator.pop(context);
            });
            return KeyEventResult.handled;
          }
          if (event.logicalKey == LogicalKeyboardKey.keyS &&
              (HardwareKeyboard.instance.isControlPressed ||
                  HardwareKeyboard.instance.isMetaPressed)) {
            _saveFile();
            return KeyEventResult.handled;
          }
        }
        return KeyEventResult.ignored;
      },
      child: PopScope(
        canPop: !_hasChanges,
        onPopInvokedWithResult: (didPop, result) async {
          if (didPop) return;
          final shouldPop = await _onWillPop();
          if (shouldPop && mounted) Navigator.pop(context);
        },
        child: Scaffold(
          appBar: AppBar(
            title: Text(_currentFile!.name),
            actions: _buildActions(colorScheme),
          ),
          body: content,
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.description_outlined,
            size: IconSizes.xxxl,
            color: colorScheme.onSurface.withValues(alpha: 0.3),
          ),
          SizedBox(height: Spacing.lg),
          Text(
            'Select a file to edit',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: colorScheme.onSurface.withValues(alpha: 0.5),
            ),
          ),
          SizedBox(height: Spacing.sm),
          Text(
            'or create a new one from the sidebar',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: colorScheme.onSurface.withValues(alpha: 0.4),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context, ColorScheme colorScheme) {
    final provider = context.read<FilesystemProvider>();
    final breadcrumb = provider.getBreadcrumb(_currentFile!);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: Spacing.lg,
        vertical: Spacing.md,
      ),
      child: Row(
        children: [
          // Breadcrumb
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (int i = 0; i < breadcrumb.length; i++) ...[
                    if (i > 0)
                      Padding(
                        padding: EdgeInsets.symmetric(horizontal: Spacing.xs),
                        child: Icon(
                          Icons.chevron_right,
                          size: IconSizes.sm,
                          color: colorScheme.onSurface.withValues(alpha: 0.4),
                        ),
                      ),
                    Text(
                      breadcrumb[i].name,
                      style: TextStyle(
                        fontSize: TypeScale.sm,
                        color: i == breadcrumb.length - 1
                            ? colorScheme.onSurface
                            : colorScheme.onSurface.withValues(alpha: 0.6),
                        fontWeight: i == breadcrumb.length - 1
                            ? FontWeight.w500
                            : FontWeight.normal,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),

          // Daily note indicator
          if (_currentFile!.isDaily)
            Container(
              padding: EdgeInsets.symmetric(
                horizontal: Spacing.sm,
                vertical: Spacing.xs,
              ),
              decoration: BoxDecoration(
                color: colorScheme.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(Radii.sm),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.event_note,
                    size: IconSizes.sm,
                    color: colorScheme.primary,
                  ),
                  SizedBox(width: Spacing.xs),
                  Text(
                    _currentFile!.dailyDate != null
                        ? DateFormat('MMM d, yyyy').format(_currentFile!.dailyDate!)
                        : 'Daily Note',
                    style: TextStyle(
                      fontSize: TypeScale.xs,
                      color: colorScheme.primary,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),

          SizedBox(width: Spacing.md),

          // Actions (for embedded mode)
          if (widget.embedded) ..._buildActions(colorScheme),
        ],
      ),
    );
  }

  List<Widget> _buildActions(ColorScheme colorScheme) {
    return [
      if (_isTranscribing)
        Padding(
          padding: EdgeInsets.all(Spacing.lg),
          child: SizedBox(
            width: IconSizes.md,
            height: IconSizes.md,
            child: const CircularProgressIndicator(strokeWidth: 2),
          ),
        )
      else
        IconButton(
          icon: Icon(
            _isRecording ? Icons.stop : Icons.mic,
            color: _isRecording ? colorScheme.error : null,
          ),
          onPressed: _toggleRecording,
          tooltip: _isRecording ? 'Stop Recording' : 'Start Recording',
        ),
      if (_isSaving)
        Padding(
          padding: EdgeInsets.all(Spacing.lg),
          child: SizedBox(
            width: IconSizes.md,
            height: IconSizes.md,
            child: const CircularProgressIndicator(strokeWidth: 2),
          ),
        )
      else
        TextButton(
          onPressed: _hasChanges ? _saveFile : null,
          child: const Text('Save'),
        ),
    ];
  }

  Widget _buildBottomBar(BuildContext context, ColorScheme colorScheme) {
    return Container(
      padding: EdgeInsets.all(Spacing.md),
      decoration: BoxDecoration(
        color: colorScheme.surface,
        border: Border(
          top: BorderSide(
            color: colorScheme.outline.withValues(alpha: 0.2),
          ),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.edit,
            size: IconSizes.sm,
            color: colorScheme.primary,
          ),
          SizedBox(width: Spacing.sm),
          Text(
            'Unsaved changes',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: colorScheme.primary,
            ),
          ),
          const Spacer(),
          TextButton(
            onPressed: _saveFile,
            child: const Text('Save (Ctrl+S)'),
          ),
        ],
      ),
    );
  }
}
