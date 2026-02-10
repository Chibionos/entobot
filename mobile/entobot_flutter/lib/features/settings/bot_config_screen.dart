import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/models/bot_config.dart';
import '../../core/providers/auth_provider.dart';
import '../../theme/app_theme.dart';

// Bot config state provider
final botConfigProvider = FutureProvider<BotConfig>((ref) async {
  final restClient = ref.watch(restClientProvider);
  return await restClient.getBotConfig();
});

class BotConfigScreen extends ConsumerStatefulWidget {
  const BotConfigScreen({super.key});

  @override
  ConsumerState<BotConfigScreen> createState() => _BotConfigScreenState();
}

class _BotConfigScreenState extends ConsumerState<BotConfigScreen> {
  late TextEditingController _modelController;
  late double _temperature;
  late int _maxTokens;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _modelController = TextEditingController();
    _temperature = 0.7;
    _maxTokens = 2000;
  }

  @override
  void dispose() {
    _modelController.dispose();
    super.dispose();
  }

  Future<void> _saveConfig() async {
    setState(() => _isSaving = true);

    try {
      final restClient = ref.read(restClientProvider);
      final config = BotConfig(
        model: _modelController.text,
        temperature: _temperature,
        maxTokens: _maxTokens,
      );

      final success = await restClient.updateBotConfig(config);

      if (!mounted) return;

      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Configuration saved successfully'),
            backgroundColor: AppTheme.successColor,
          ),
        );
        ref.invalidate(botConfigProvider);
      } else {
        throw Exception('Failed to save configuration');
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: AppTheme.errorColor,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final configAsync = ref.watch(botConfigProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bot Configuration'),
        actions: [
          if (_isSaving)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            )
          else
            IconButton(
              icon: const Icon(Icons.save),
              onPressed: _saveConfig,
              tooltip: 'Save',
            ),
        ],
      ),
      body: configAsync.when(
        data: (config) {
          // Initialize controllers with loaded data
          if (_modelController.text.isEmpty) {
            _modelController.text = config.model;
            _temperature = config.temperature;
            _maxTokens = config.maxTokens;
          }

          return ListView(
            padding: const EdgeInsets.all(AppTheme.spacing16),
            children: [
              // Model selection
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppTheme.spacing16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Model',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppTheme.spacing8),
                      TextField(
                        controller: _modelController,
                        decoration: const InputDecoration(
                          hintText: 'e.g., gpt-4, claude-3-opus',
                          helperText: 'Enter the AI model name',
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppTheme.spacing16),

              // Temperature slider
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppTheme.spacing16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Temperature: ${_temperature.toStringAsFixed(2)}',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppTheme.spacing8),
                      Slider(
                        value: _temperature,
                        min: 0.0,
                        max: 2.0,
                        divisions: 20,
                        label: _temperature.toStringAsFixed(2),
                        onChanged: (value) {
                          setState(() => _temperature = value);
                        },
                      ),
                      Text(
                        'Controls randomness. Lower is more focused, higher is more creative.',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurface
                                  .withOpacity(0.6),
                            ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppTheme.spacing16),

              // Max tokens slider
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppTheme.spacing16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Max Tokens: $_maxTokens',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppTheme.spacing8),
                      Slider(
                        value: _maxTokens.toDouble(),
                        min: 100,
                        max: 8000,
                        divisions: 79,
                        label: _maxTokens.toString(),
                        onChanged: (value) {
                          setState(() => _maxTokens = value.toInt());
                        },
                      ),
                      Text(
                        'Maximum length of AI responses.',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurface
                                  .withOpacity(0.6),
                            ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: AppTheme.spacing24),

              // Save button
              ElevatedButton(
                onPressed: _isSaving ? null : _saveConfig,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _isSaving
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Save Configuration'),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(AppTheme.spacing24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.error_outline,
                  size: 64,
                  color: AppTheme.errorColor,
                ),
                const SizedBox(height: AppTheme.spacing16),
                Text(
                  'Failed to load configuration',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: AppTheme.spacing8),
                Text(
                  error.toString(),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: AppTheme.spacing16),
                ElevatedButton.icon(
                  onPressed: () => ref.invalidate(botConfigProvider),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
