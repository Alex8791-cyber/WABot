import 'package:flutter/material.dart';

import '../api_service.dart';
import '../i18n.dart';

class SettingsPage extends StatefulWidget {
  final VoidCallback onBaseUrlChanged;
  final void Function(String)? onLanguageChanged;

  const SettingsPage({
    super.key,
    required this.onBaseUrlChanged,
    this.onLanguageChanged,
  });

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _backendFormKey = GlobalKey<FormState>();
  late TextEditingController _baseUrlController;
  final TextEditingController _agentsController = TextEditingController();
  final TextEditingController _soulController = TextEditingController();
  final TextEditingController _apiKeyController = TextEditingController();
  final TextEditingController _adminTokenController = TextEditingController();
  bool _loadingConfig = true;
  bool _savingConfig = false;

  // Feature state
  bool _loadingFeatures = true;
  bool _savingFeatures = false;
  bool _enableAudio = false;
  bool _enableImages = false;
  bool _enableTts = false;
  late TextEditingController _whisperModelController;
  late TextEditingController _visionApiKeyController;

  @override
  void initState() {
    super.initState();
    _baseUrlController = TextEditingController(text: ApiService.baseUrl);
    _whisperModelController = TextEditingController();
    _visionApiKeyController = TextEditingController();
    _loadAgentConfig();
    _loadFeaturesConfig();
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _agentsController.dispose();
    _soulController.dispose();
    _apiKeyController.dispose();
    _adminTokenController.dispose();
    _whisperModelController.dispose();
    _visionApiKeyController.dispose();
    super.dispose();
  }

  void _saveBaseUrl() {
    if (_backendFormKey.currentState?.validate() ?? false) {
      final newUrl = _baseUrlController.text.trim();
      ApiService.setBaseUrl(newUrl);
      widget.onBaseUrlChanged();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${t('backendSaved')} $newUrl')),
      );
    }
  }

  void _saveAdminToken() {
    ApiService.setAdminToken(_adminTokenController.text.trim());
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Admin token updated')),
    );
  }

  Future<void> _loadAgentConfig() async {
    try {
      final config = await ApiService.fetchAgentConfig();
      setState(() {
        _loadingConfig = false;
        _agentsController.text = config['agents'] ?? '';
        _soulController.text = config['soul'] ?? '';
        _apiKeyController.text = '';
      });
    } catch (e) {
      setState(() => _loadingConfig = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('failedToLoadConfig')}: $e')),
        );
      }
    }
  }

  Future<void> _saveAgentConfig() async {
    if (_savingConfig) return;
    setState(() => _savingConfig = true);
    try {
      await ApiService.updateAgentConfig(
        agents: _agentsController.text,
        soul: _soulController.text,
        apiKey:
            _apiKeyController.text.isNotEmpty ? _apiKeyController.text : null,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('settingsSaved'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('failedToSaveConfig')}: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _savingConfig = false);
    }
  }

  Future<void> _loadFeaturesConfig() async {
    try {
      final config = await ApiService.fetchFeaturesConfig();
      setState(() {
        _loadingFeatures = false;
        _enableAudio = (config['enable_audio'] ?? false) as bool;
        _enableImages = (config['enable_images'] ?? false) as bool;
        _enableTts = (config['enable_tts'] ?? false) as bool;
        _whisperModelController.text = config['whisper_model'] ?? '';
        final visionKey = config['vision_api_key'];
        _visionApiKeyController.text =
            (visionKey != null && visionKey != '***')
                ? visionKey as String
                : '';
      });
    } catch (e) {
      setState(() => _loadingFeatures = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('failedToLoadFeatures')}: $e')),
        );
      }
    }
  }

  Future<void> _saveFeaturesConfig() async {
    if (_savingFeatures) return;
    setState(() => _savingFeatures = true);
    try {
      await ApiService.updateFeaturesConfig(
        enableAudio: _enableAudio,
        enableImages: _enableImages,
        enableTts: _enableTts,
        whisperModel: _whisperModelController.text.trim(),
        visionApiKey: _visionApiKeyController.text.trim(),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('featuresSaved'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('failedToSaveFeatures')}: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _savingFeatures = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(t('settings'))),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Language selection
          Text(t('language'), style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: currentLanguageCode,
            items: [
              DropdownMenuItem(value: 'en', child: Text(t('english'))),
              DropdownMenuItem(value: 'de', child: Text(t('german'))),
            ],
            onChanged: (value) {
              if (value != null) {
                currentLanguageCode = value;
                ApiService.setLanguageCode(value);
                widget.onLanguageChanged?.call(value);
                setState(() {});
              }
            },
          ),

          const SizedBox(height: 24),

          // Backend URL
          Text(t('backendConfiguration'),
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Form(
            key: _backendFormKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextFormField(
                  controller: _baseUrlController,
                  decoration: InputDecoration(
                    labelText: t('apiBaseUrl'),
                    hintText: 'http://localhost:8000',
                  ),
                  validator: (value) {
                    if (value == null ||
                        value.isEmpty ||
                        !value.startsWith('http')) {
                      return t('error');
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 8),
                ElevatedButton(
                    onPressed: _saveBaseUrl, child: Text(t('saveApiUrl'))),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Admin token
          TextFormField(
            controller: _adminTokenController,
            decoration: InputDecoration(
              labelText: t('adminToken'),
              hintText: 'Token for protected endpoints',
            ),
            obscureText: true,
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _saveAdminToken,
            child: Text('Set ${t('adminToken')}'),
          ),

          const SizedBox(height: 24),

          // Agent configuration
          Text(t('agentConfiguration'),
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          _loadingConfig
              ? const Center(child: CircularProgressIndicator())
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    TextFormField(
                      controller: _apiKeyController,
                      decoration: InputDecoration(
                        labelText: t('llmApiKey'),
                        hintText: 'Your OpenAI API key',
                      ),
                      obscureText: true,
                    ),
                    const SizedBox(height: 16),
                    Text(t('agentsMd'),
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 4),
                    TextField(
                      controller: _agentsController,
                      maxLines: 8,
                      decoration: InputDecoration(
                        border: const OutlineInputBorder(),
                        hintText: t('agentsMd'),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(t('soulMd'),
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 4),
                    TextField(
                      controller: _soulController,
                      maxLines: 8,
                      decoration: InputDecoration(
                        border: const OutlineInputBorder(),
                        hintText: t('soulMd'),
                      ),
                    ),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: _savingConfig ? null : _saveAgentConfig,
                      child: _savingConfig
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child:
                                  CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(t('saveAgentSettings')),
                    ),
                  ],
                ),

          const SizedBox(height: 24),

          // Multimedia features
          Text(t('featuresConfigTitle'),
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          _loadingFeatures
              ? const Center(child: CircularProgressIndicator())
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SwitchListTile(
                      title: Text(t('enableAudio')),
                      value: _enableAudio,
                      onChanged: (v) => setState(() => _enableAudio = v),
                    ),
                    SwitchListTile(
                      title: Text(t('enableImages')),
                      value: _enableImages,
                      onChanged: (v) => setState(() => _enableImages = v),
                    ),
                    SwitchListTile(
                      title: Text(t('enableTts')),
                      value: _enableTts,
                      onChanged: (v) => setState(() => _enableTts = v),
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _whisperModelController,
                      decoration: InputDecoration(
                        labelText: t('whisperModel'),
                        hintText: 'base, medium, large, etc.',
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _visionApiKeyController,
                      decoration: InputDecoration(
                        labelText: t('visionApiKey'),
                        hintText: 'Optional API key for image analysis',
                      ),
                      obscureText: true,
                    ),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed:
                          _savingFeatures ? null : _saveFeaturesConfig,
                      child: _savingFeatures
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child:
                                  CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(t('saveFeatures')),
                    ),
                  ],
                ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }
}
