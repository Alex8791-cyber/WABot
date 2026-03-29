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

  // Runtime config
  bool _loadingRuntimeConfig = true;
  bool _savingRuntimeConfig = false;
  late TextEditingController _modelNameController;
  late TextEditingController _handoffThresholdController;
  late TextEditingController _maxHistoryController;
  late TextEditingController _rateLimitRequestsController;
  late TextEditingController _rateLimitWindowController;
  late TextEditingController _waVerifyTokenController;
  late TextEditingController _waApiTokenController;
  late TextEditingController _waPhoneNumberIdController;
  late TextEditingController _paystackKeyController;
  late TextEditingController _googleCredentialsController;
  late TextEditingController _googleCalendarIdController;
  late TextEditingController _businessAddressController;
  late TextEditingController _businessLatController;
  late TextEditingController _businessLngController;
  late TextEditingController _timezoneController;

  @override
  void initState() {
    super.initState();
    _baseUrlController = TextEditingController(text: ApiService.baseUrl);
    _whisperModelController = TextEditingController();
    _visionApiKeyController = TextEditingController();
    _modelNameController = TextEditingController();
    _handoffThresholdController = TextEditingController();
    _maxHistoryController = TextEditingController();
    _rateLimitRequestsController = TextEditingController();
    _rateLimitWindowController = TextEditingController();
    _waVerifyTokenController = TextEditingController();
    _waApiTokenController = TextEditingController();
    _waPhoneNumberIdController = TextEditingController();
    _paystackKeyController = TextEditingController();
    _googleCredentialsController = TextEditingController();
    _googleCalendarIdController = TextEditingController();
    _businessAddressController = TextEditingController();
    _businessLatController = TextEditingController();
    _businessLngController = TextEditingController();
    _timezoneController = TextEditingController();
    _loadAgentConfig();
    _loadFeaturesConfig();
    _loadRuntimeConfig();
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
    _modelNameController.dispose();
    _handoffThresholdController.dispose();
    _maxHistoryController.dispose();
    _rateLimitRequestsController.dispose();
    _rateLimitWindowController.dispose();
    _waVerifyTokenController.dispose();
    _waApiTokenController.dispose();
    _waPhoneNumberIdController.dispose();
    _paystackKeyController.dispose();
    _googleCredentialsController.dispose();
    _googleCalendarIdController.dispose();
    _businessAddressController.dispose();
    _businessLatController.dispose();
    _businessLngController.dispose();
    _timezoneController.dispose();
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

  Future<void> _loadRuntimeConfig() async {
    try {
      final config = await ApiService.fetchRuntimeConfig();
      setState(() {
        _loadingRuntimeConfig = false;
        _modelNameController.text = config['MODEL_NAME']?.toString() ?? '';
        _handoffThresholdController.text = config['HANDOFF_THRESHOLD']?.toString() ?? '';
        _maxHistoryController.text = config['MAX_HISTORY_MESSAGES']?.toString() ?? '';
        _rateLimitRequestsController.text = config['RATE_LIMIT_REQUESTS']?.toString() ?? '';
        _rateLimitWindowController.text = config['RATE_LIMIT_WINDOW']?.toString() ?? '';
        _waVerifyTokenController.text = config['WHATSAPP_VERIFY_TOKEN']?.toString() ?? '';
        _waApiTokenController.text = (config['WHATSAPP_API_TOKEN'] == '***') ? '' : config['WHATSAPP_API_TOKEN']?.toString() ?? '';
        _waPhoneNumberIdController.text = config['WHATSAPP_PHONE_NUMBER_ID']?.toString() ?? '';
        _paystackKeyController.text = (config['PAYSTACK_SECRET_KEY'] == '***') ? '' : config['PAYSTACK_SECRET_KEY']?.toString() ?? '';
        _googleCredentialsController.text = config['GOOGLE_CREDENTIALS_FILE']?.toString() ?? '';
        _googleCalendarIdController.text = config['GOOGLE_CALENDAR_ID']?.toString() ?? '';
        _businessAddressController.text = config['BUSINESS_ADDRESS']?.toString() ?? '';
        _businessLatController.text = config['BUSINESS_LAT']?.toString() ?? '';
        _businessLngController.text = config['BUSINESS_LNG']?.toString() ?? '';
        _timezoneController.text = config['TIMEZONE']?.toString() ?? '';
      });
    } catch (e) {
      setState(() => _loadingRuntimeConfig = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('failedToLoadRuntimeConfig')}: $e')),
        );
      }
    }
  }

  Future<void> _saveRuntimeConfig() async {
    if (_savingRuntimeConfig) return;
    setState(() => _savingRuntimeConfig = true);
    try {
      final updates = <String, String>{};
      if (_modelNameController.text.isNotEmpty) updates['MODEL_NAME'] = _modelNameController.text;
      if (_handoffThresholdController.text.isNotEmpty) updates['HANDOFF_THRESHOLD'] = _handoffThresholdController.text;
      if (_maxHistoryController.text.isNotEmpty) updates['MAX_HISTORY_MESSAGES'] = _maxHistoryController.text;
      if (_rateLimitRequestsController.text.isNotEmpty) updates['RATE_LIMIT_REQUESTS'] = _rateLimitRequestsController.text;
      if (_rateLimitWindowController.text.isNotEmpty) updates['RATE_LIMIT_WINDOW'] = _rateLimitWindowController.text;
      if (_waVerifyTokenController.text.isNotEmpty) updates['WHATSAPP_VERIFY_TOKEN'] = _waVerifyTokenController.text;
      if (_waApiTokenController.text.isNotEmpty) updates['WHATSAPP_API_TOKEN'] = _waApiTokenController.text;
      if (_waPhoneNumberIdController.text.isNotEmpty) updates['WHATSAPP_PHONE_NUMBER_ID'] = _waPhoneNumberIdController.text;
      if (_paystackKeyController.text.isNotEmpty) updates['PAYSTACK_SECRET_KEY'] = _paystackKeyController.text;
      if (_googleCredentialsController.text.isNotEmpty) updates['GOOGLE_CREDENTIALS_FILE'] = _googleCredentialsController.text;
      if (_googleCalendarIdController.text.isNotEmpty) updates['GOOGLE_CALENDAR_ID'] = _googleCalendarIdController.text;
      if (_businessAddressController.text.isNotEmpty) updates['BUSINESS_ADDRESS'] = _businessAddressController.text;
      if (_businessLatController.text.isNotEmpty) updates['BUSINESS_LAT'] = _businessLatController.text;
      if (_businessLngController.text.isNotEmpty) updates['BUSINESS_LNG'] = _businessLngController.text;
      if (_timezoneController.text.isNotEmpty) updates['TIMEZONE'] = _timezoneController.text;

      await ApiService.updateRuntimeConfig(updates);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('runtimeConfigSaved'))),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('failedToSaveRuntimeConfig')}: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _savingRuntimeConfig = false);
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

          const SizedBox(height: 24),

          // Runtime Configuration
          Text(t('runtimeConfig'), style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          _loadingRuntimeConfig
              ? const Center(child: CircularProgressIndicator())
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // LLM Settings
                    Text(t('llmSettings'), style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(controller: _modelNameController, decoration: InputDecoration(labelText: t('modelName'), hintText: 'gpt-4o-mini')),
                    const SizedBox(height: 8),
                    TextFormField(controller: _handoffThresholdController, decoration: InputDecoration(labelText: t('handoffThreshold')), keyboardType: TextInputType.number),
                    const SizedBox(height: 8),
                    TextFormField(controller: _maxHistoryController, decoration: InputDecoration(labelText: t('maxHistoryMessages')), keyboardType: TextInputType.number),

                    const SizedBox(height: 16),
                    Text(t('rateLimiting'), style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(controller: _rateLimitRequestsController, decoration: InputDecoration(labelText: t('requestsPerWindow')), keyboardType: TextInputType.number),
                    const SizedBox(height: 8),
                    TextFormField(controller: _rateLimitWindowController, decoration: InputDecoration(labelText: t('windowSeconds')), keyboardType: TextInputType.number),

                    const SizedBox(height: 16),
                    Text(t('whatsappConfig'), style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(controller: _waVerifyTokenController, decoration: InputDecoration(labelText: t('verifyToken'))),
                    const SizedBox(height: 8),
                    TextFormField(controller: _waApiTokenController, decoration: InputDecoration(labelText: t('apiToken')), obscureText: true),
                    const SizedBox(height: 8),
                    TextFormField(controller: _waPhoneNumberIdController, decoration: InputDecoration(labelText: t('phoneNumberId'))),

                    const SizedBox(height: 16),
                    Text(t('paystackConfig'), style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(controller: _paystackKeyController, decoration: InputDecoration(labelText: t('secretKey')), obscureText: true),

                    const SizedBox(height: 16),
                    Text(t('calendarConfig'), style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(controller: _googleCredentialsController, decoration: InputDecoration(labelText: t('credentialsFile'))),
                    const SizedBox(height: 8),
                    TextFormField(controller: _googleCalendarIdController, decoration: InputDecoration(labelText: t('calendarId'), hintText: 'primary')),

                    const SizedBox(height: 16),
                    Text(t('businessLocation'), style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(controller: _businessAddressController, decoration: InputDecoration(labelText: t('businessAddress'), hintText: '123 Main Road, Sandton, Johannesburg')),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(child: TextFormField(controller: _businessLatController, decoration: InputDecoration(labelText: t('businessLat')), keyboardType: TextInputType.number)),
                        const SizedBox(width: 8),
                        Expanded(child: TextFormField(controller: _businessLngController, decoration: InputDecoration(labelText: t('businessLng')), keyboardType: TextInputType.number)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    TextFormField(controller: _timezoneController, decoration: InputDecoration(labelText: t('timezone'), hintText: 'Africa/Johannesburg')),

                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _savingRuntimeConfig ? null : _saveRuntimeConfig,
                      child: _savingRuntimeConfig
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                          : Text(t('saveRuntimeConfig')),
                    ),
                  ],
                ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }
}
