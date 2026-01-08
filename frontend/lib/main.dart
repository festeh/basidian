import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:window_manager/window_manager.dart';
import 'screens/home_screen.dart';
import 'services/notes_provider.dart';
import 'services/theme_provider.dart';
import 'services/asr_settings_provider.dart';
import 'services/filesystem_provider.dart';
import 'services/audio_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Validate required environment variables at startup
  AudioService.validateConfig();

  // Configure window on desktop platforms
  if (Platform.isLinux || Platform.isWindows || Platform.isMacOS) {
    await windowManager.ensureInitialized();
    await windowManager.setTitleBarStyle(TitleBarStyle.hidden);
    await windowManager.setTitle('Basidian');
  }

  runApp(const BasidianApp());
}

class BasidianApp extends StatelessWidget {
  const BasidianApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => NotesProvider()),
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => ASRSettingsProvider()),
        ChangeNotifierProvider(create: (_) => FilesystemProvider()),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, child) {
          return MaterialApp(
            title: 'Basidian',
            theme: themeProvider.themeData,
            home: const HomeScreen(),
            debugShowCheckedModeBanner: false,
          );
        },
      ),
    );
  }
}
