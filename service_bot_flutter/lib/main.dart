import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const ServiceBotApp());
}

// ---------------------------------------------------------------------------
// Internationalization
// ---------------------------------------------------------------------------

String currentLanguageCode = 'en';

const Map<String, Map<String, String>> _translations = {
  'en': {
    'appTitle': 'AI Service Bot',
    'chat': 'Chat',
    'settings': 'Settings',
    'error': 'Error',
    'backendConfiguration': 'Backend Configuration',
    'apiBaseUrl': 'API Base URL',
    'saveApiUrl': 'Save API URL',
    'agentConfiguration': 'AI Agent Configuration',
    'saveAgentSettings': 'Save Agent Settings',
    'settingsSaved': 'Agent configuration saved',
    'llmApiKey': 'LLM API Key',
    'adminToken': 'Admin Token',
    'agentsMd': 'AGENTS.md (behavior rules)',
    'soulMd': 'SOUL.md (personality)',
    'backendSaved': 'API base URL updated to',
    'failedToLoadConfig': 'Failed to load agent config',
    'failedToSaveConfig': 'Failed to save config',
    'language': 'Language',
    'english': 'English',
    'german': 'German',
    'chatTitle': 'AI Chat',
    'typeMessage': 'Type your message...',
    'connectionError': 'Connection error — check backend URL in settings.',
    'featuresConfigTitle': 'Multimedia Features',
    'enableAudio': 'Enable audio processing',
    'enableImages': 'Enable image processing',
    'enableTts': 'Enable voice replies',
    'whisperModel': 'Whisper model (optional)',
    'visionApiKey': 'Vision API Key',
    'saveFeatures': 'Save Features',
    'featuresSaved': 'Features configuration saved',
    'failedToLoadFeatures': 'Failed to load features config',
    'failedToSaveFeatures': 'Failed to save features config',
  },
  'de': {
    'appTitle': 'KI-Service-Bot',
    'chat': 'Chat',
    'settings': 'Einstellungen',
    'error': 'Fehler',
    'backendConfiguration': 'Backend-Konfiguration',
    'apiBaseUrl': 'API-Basis-URL',
    'saveApiUrl': 'API-URL speichern',
    'agentConfiguration': 'KI-Agent-Konfiguration',
    'saveAgentSettings': 'Agenteneinstellungen speichern',
    'settingsSaved': 'Agentenkonfiguration gespeichert',
    'llmApiKey': 'LLM-API-Schlüssel',
    'adminToken': 'Admin-Token',
    'agentsMd': 'AGENTS.md (Verhaltensregeln)',
    'soulMd': 'SOUL.md (Persönlichkeit)',
    'backendSaved': 'API-Basis-URL aktualisiert auf',
    'failedToLoadConfig': 'Fehler beim Laden der Agenten-Konfiguration',
    'failedToSaveConfig': 'Fehler beim Speichern der Konfiguration',
    'language': 'Sprache',
    'english': 'Englisch',
    'german': 'Deutsch',
    'chatTitle': 'KI-Chat',
    'typeMessage': 'Geben Sie Ihre Nachricht ein...',
    'connectionError': 'Verbindungsfehler — prüfen Sie die Backend-URL in den Einstellungen.',
    'featuresConfigTitle': 'Multimedia-Funktionen',
    'enableAudio': 'Audioverarbeitung aktivieren',
    'enableImages': 'Bildverarbeitung aktivieren',
    'enableTts': 'Sprachausgabe aktivieren',
    'whisperModel': 'Whisper-Modell (optional)',
    'visionApiKey': 'Vision-API-Schlüssel',
    'saveFeatures': 'Funktionen speichern',
    'featuresSaved': 'Funktionskonfiguration gespeichert',
    'failedToLoadFeatures': 'Fehler beim Laden der Funktionskonfiguration',
    'failedToSaveFeatures': 'Fehler beim Speichern der Funktionskonfiguration',
  },
};

String t(String key) {
  return _translations[currentLanguageCode]?[key] ?? key;
}

// ---------------------------------------------------------------------------
// API Service (Fix K-06 — session management, Fix K-02 — admin token)
// ---------------------------------------------------------------------------

class ApiService {
  static String _baseUrl = const String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
  static String _languageCode = currentLanguageCode;
  static String _adminToken = '';
  static String? _sessionId;

  static String get baseUrl => _baseUrl;
  static void setBaseUrl(String url) => _baseUrl = url;
  static void setLanguageCode(String code) => _languageCode = code;
  static void setAdminToken(String token) => _adminToken = token;

  /// Generate a unique session ID for this app instance (Fix K-06).
  static String get sessionId {
    _sessionId ??= 'flutter-${DateTime.now().millisecondsSinceEpoch}-${Random().nextInt(99999)}';
    return _sessionId!;
  }

  static Map<String, String> get _adminHeaders => {
        'Content-Type': 'application/json',
        if (_adminToken.isNotEmpty) 'x-admin-token': _adminToken,
      };

  static Future<Map<String, dynamic>> fetchAgentConfig() async {
    final response = await http.get(Uri.parse('$_baseUrl/agent/config'));
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load agent config (${response.statusCode})');
  }

  static Future<Map<String, dynamic>> updateAgentConfig({
    String? agents,
    String? soul,
    String? apiKey,
  }) async {
    final body = <String, dynamic>{};
    if (agents != null) body['agents'] = agents;
    if (soul != null) body['soul'] = soul;
    if (apiKey != null) body['api_key'] = apiKey;
    final response = await http.post(
      Uri.parse('$_baseUrl/agent/config'),
      headers: _adminHeaders,
      body: json.encode(body),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to update agent config (${response.statusCode})');
  }

  static Future<String> sendAgentMessage(String message) async {
    final body = <String, dynamic>{
      'message': message,
      'session_id': sessionId, // Fix K-06 — always send session
      'lang': _languageCode,
    };
    final response = await http.post(
      Uri.parse('$_baseUrl/agent/message'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );
    if (response.statusCode == 200) {
      final data = json.decode(response.body) as Map<String, dynamic>;
      return data['reply'] as String;
    }
    throw Exception('Server error (${response.statusCode})');
  }

  static Future<Map<String, dynamic>> fetchFeaturesConfig() async {
    final response = await http.get(Uri.parse('$_baseUrl/features/config'));
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load features config (${response.statusCode})');
  }

  static Future<Map<String, dynamic>> updateFeaturesConfig({
    bool? enableAudio,
    bool? enableImages,
    bool? enableTts,
    String? whisperModel,
    String? visionApiKey,
  }) async {
    final body = <String, dynamic>{};
    if (enableAudio != null) body['enable_audio'] = enableAudio;
    if (enableImages != null) body['enable_images'] = enableImages;
    if (enableTts != null) body['enable_tts'] = enableTts;
    if (whisperModel != null) body['whisper_model'] = whisperModel;
    if (visionApiKey != null) body['vision_api_key'] = visionApiKey;
    final response = await http.post(
      Uri.parse('$_baseUrl/features/config'),
      headers: _adminHeaders,
      body: json.encode(body),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to update features config (${response.statusCode})');
  }
}

// ---------------------------------------------------------------------------
// App root
// ---------------------------------------------------------------------------

class ServiceBotApp extends StatefulWidget {
  const ServiceBotApp({super.key});

  @override
  State<ServiceBotApp> createState() => _ServiceBotAppState();
}

class _ServiceBotAppState extends State<ServiceBotApp> {
  @override
  void initState() {
    super.initState();
    ApiService.setLanguageCode(currentLanguageCode);
  }

  void _setLanguage(String code) {
    setState(() {
      currentLanguageCode = code;
      ApiService.setLanguageCode(code);
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: t('appTitle'),
      theme: ThemeData(primarySwatch: Colors.blue),
      home: HomePage(onLanguageChanged: _setLanguage),
    );
  }
}

// ---------------------------------------------------------------------------
// Home page — Chat + Settings navigation
// ---------------------------------------------------------------------------

class HomePage extends StatefulWidget {
  final void Function(String)? onLanguageChanged;
  const HomePage({super.key, this.onLanguageChanged});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _selectedIndex = 0;

  void _onBaseUrlChanged() => setState(() {});

  @override
  Widget build(BuildContext context) {
    final pages = [
      ChatPage(key: ValueKey(ApiService.baseUrl)),
      SettingsPage(
        onBaseUrlChanged: _onBaseUrlChanged,
        onLanguageChanged: widget.onLanguageChanged,
      ),
    ];

    return Scaffold(
      body: pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        items: [
          BottomNavigationBarItem(icon: const Icon(Icons.chat), label: t('chat')),
          BottomNavigationBarItem(icon: const Icon(Icons.settings), label: t('settings')),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Chat page (Fix K-06, M-06, M-09)
// ---------------------------------------------------------------------------

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController(); // Fix M-06
  final List<_ChatMessage> _messages = [];
  bool _sending = false;

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    // Fix M-06 — auto-scroll on new message
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _messages.add(_ChatMessage(text, true));
      _messageController.clear();
    });
    _scrollToBottom();

    try {
      final reply = await ApiService.sendAgentMessage(text);
      setState(() {
        _messages.add(_ChatMessage(reply, false));
        _sending = false;
      });
    } catch (e) {
      // Fix M-09 — user-friendly error messages
      setState(() {
        _messages.add(_ChatMessage(t('connectionError'), false));
        _sending = false;
      });
    }
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(t('chatTitle'))),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController, // Fix M-06
              padding: const EdgeInsets.all(8.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return Container(
                  margin: const EdgeInsets.symmetric(vertical: 4.0),
                  alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: msg.isUser ? Colors.blue[100] : Colors.grey[200],
                      borderRadius: BorderRadius.circular(12.0),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 12.0),
                      child: Text(msg.text),
                    ),
                  ),
                );
              },
            ),
          ),
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    onSubmitted: (_) => _sendMessage(),
                    decoration: InputDecoration(hintText: t('typeMessage')),
                  ),
                ),
                IconButton(
                  icon: _sending
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send),
                  onPressed: _sending ? null : _sendMessage,
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  _ChatMessage(this.text, this.isUser) : timestamp = DateTime.now(); // Fix N-08
}

// ---------------------------------------------------------------------------
// Settings page (Fix K-02 — admin token, dead code removed)
// ---------------------------------------------------------------------------

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
  bool _savingConfig = false; // Fix M-07

  // Feature state
  bool _loadingFeatures = true;
  bool _savingFeatures = false; // Fix M-07
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
    if (_savingConfig) return; // Fix M-07
    setState(() => _savingConfig = true);
    try {
      await ApiService.updateAgentConfig(
        agents: _agentsController.text,
        soul: _soulController.text,
        apiKey: _apiKeyController.text.isNotEmpty ? _apiKeyController.text : null,
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
            (visionKey != null && visionKey != '***') ? visionKey as String : '';
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
    if (_savingFeatures) return; // Fix M-07
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
          Text(t('backendConfiguration'), style: Theme.of(context).textTheme.titleLarge),
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
                    if (value == null || value.isEmpty || !value.startsWith('http')) {
                      return t('error');
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 8),
                ElevatedButton(onPressed: _saveBaseUrl, child: Text(t('saveApiUrl'))),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Admin token (Fix K-02)
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
          Text(t('agentConfiguration'), style: Theme.of(context).textTheme.titleLarge),
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
                    Text(t('agentsMd'), style: Theme.of(context).textTheme.titleMedium),
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
                    Text(t('soulMd'), style: Theme.of(context).textTheme.titleMedium),
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
                              width: 16, height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(t('saveAgentSettings')),
                    ),
                  ],
                ),

          const SizedBox(height: 24),

          // Multimedia features
          Text(t('featuresConfigTitle'), style: Theme.of(context).textTheme.titleLarge),
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
                      onPressed: _savingFeatures ? null : _saveFeaturesConfig,
                      child: _savingFeatures
                          ? const SizedBox(
                              width: 16, height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
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
