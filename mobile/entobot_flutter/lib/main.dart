import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'core/providers/auth_provider.dart';
import 'features/pairing/qr_scan_screen.dart';
import 'features/chat/chat_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/settings/bot_config_screen.dart';
import 'features/settings/security_screen.dart';
import 'features/settings/about_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(
    const ProviderScope(
      child: EntobotApp(),
    ),
  );
}

class EntobotApp extends ConsumerWidget {
  const EntobotApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = _createRouter(ref);

    return MaterialApp.router(
      title: 'Entobot',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }

  GoRouter _createRouter(WidgetRef ref) {
    return GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) {
            // Check auth state to determine initial screen
            final authState = ref.watch(authProvider);

            if (authState.isLoading) {
              return const Scaffold(
                body: Center(
                  child: CircularProgressIndicator(),
                ),
              );
            }

            if (authState.isAuthenticated) {
              return const ChatScreen();
            } else {
              return const QrScanScreen();
            }
          },
        ),
        GoRoute(
          path: '/chat',
          builder: (context, state) => const ChatScreen(),
        ),
        GoRoute(
          path: '/scan',
          builder: (context, state) => const QrScanScreen(),
        ),
        GoRoute(
          path: '/settings',
          builder: (context, state) => const SettingsScreen(),
        ),
        GoRoute(
          path: '/settings/bot',
          builder: (context, state) => const BotConfigScreen(),
        ),
        GoRoute(
          path: '/settings/security',
          builder: (context, state) => const SecurityScreen(),
        ),
        GoRoute(
          path: '/settings/about',
          builder: (context, state) => const AboutScreen(),
        ),
      ],
      redirect: (context, state) {
        final authState = ref.read(authProvider);

        // If not authenticated and trying to access protected routes
        if (!authState.isAuthenticated && !authState.isLoading) {
          if (state.matchedLocation != '/' && state.matchedLocation != '/scan') {
            return '/';
          }
        }

        return null; // No redirect needed
      },
    );
  }
}
