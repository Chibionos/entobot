/// Bot configuration model
class BotConfig {
  final String model;
  final double temperature;
  final int maxTokens;
  final String systemPrompt;

  const BotConfig({
    required this.model,
    required this.temperature,
    required this.maxTokens,
    this.systemPrompt = '',
  });

  factory BotConfig.fromJson(Map<String, dynamic> json) {
    return BotConfig(
      model: json['model'] as String? ?? 'gpt-4',
      temperature: (json['temperature'] as num?)?.toDouble() ?? 0.7,
      maxTokens: json['max_tokens'] as int? ?? 2000,
      systemPrompt: json['system_prompt'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'model': model,
      'temperature': temperature,
      'max_tokens': maxTokens,
      'system_prompt': systemPrompt,
    };
  }

  BotConfig copyWith({
    String? model,
    double? temperature,
    int? maxTokens,
    String? systemPrompt,
  }) {
    return BotConfig(
      model: model ?? this.model,
      temperature: temperature ?? this.temperature,
      maxTokens: maxTokens ?? this.maxTokens,
      systemPrompt: systemPrompt ?? this.systemPrompt,
    );
  }

  factory BotConfig.defaultConfig() {
    return const BotConfig(
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 2000,
      systemPrompt: 'You are a helpful AI assistant.',
    );
  }
}

/// Provider model for available AI providers
class Provider {
  final String id;
  final String name;
  final List<String> models;

  const Provider({
    required this.id,
    required this.name,
    required this.models,
  });

  factory Provider.fromJson(Map<String, dynamic> json) {
    return Provider(
      id: json['id'] as String,
      name: json['name'] as String,
      models: (json['models'] as List<dynamic>).cast<String>(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'models': models,
    };
  }
}
