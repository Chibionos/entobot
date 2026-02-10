import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('About'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppTheme.spacing16),
        children: [
          // App Icon and Name
          Center(
            child: Column(
              children: [
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(
                    Icons.smart_toy,
                    size: 60,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: AppTheme.spacing16),
                Text(
                  'Entobot',
                  style: theme.textTheme.headlineMedium,
                ),
                const SizedBox(height: AppTheme.spacing4),
                Text(
                  'Version 1.0.0',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: AppTheme.spacing32),

          // Description
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacing16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'About Entobot',
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: AppTheme.spacing12),
                  Text(
                    'Entobot is an enterprise-grade AI assistant mobile app '
                    'that connects securely to your desktop Entobot instance '
                    'via QR code pairing.',
                    style: theme.textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: AppTheme.spacing16),

          // Features
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacing16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Features',
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: AppTheme.spacing12),
                  _buildFeatureItem(
                    icon: Icons.qr_code_scanner,
                    title: 'QR Code Pairing',
                    subtitle: 'Secure pairing with your desktop app',
                  ),
                  _buildFeatureItem(
                    icon: Icons.security,
                    title: 'End-to-End Security',
                    subtitle: 'JWT authentication and encrypted storage',
                  ),
                  _buildFeatureItem(
                    icon: Icons.chat,
                    title: 'Real-time Chat',
                    subtitle: 'WebSocket-based instant messaging',
                  ),
                  _buildFeatureItem(
                    icon: Icons.tune,
                    title: 'Configurable',
                    subtitle: 'Customize model, temperature, and more',
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: AppTheme.spacing16),

          // Technology Stack
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacing16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Built With',
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: AppTheme.spacing12),
                  Text(
                    '• Flutter 3.x\n'
                    '• Material Design 3\n'
                    '• Riverpod State Management\n'
                    '• WebSocket Communication\n'
                    '• Secure Storage',
                    style: theme.textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: AppTheme.spacing32),

          // Copyright
          Center(
            child: Text(
              '© 2024 Entobot. All rights reserved.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ),

          const SizedBox(height: AppTheme.spacing16),
        ],
      ),
    );
  }

  Widget _buildFeatureItem({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppTheme.spacing12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 24),
          const SizedBox(width: AppTheme.spacing12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 13),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
