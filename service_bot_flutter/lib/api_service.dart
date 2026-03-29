import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;

import 'i18n.dart';

/// Centralised HTTP client for all backend API calls.
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

  /// Unique session ID for this app instance.
  static String get sessionId {
    _sessionId ??=
        'flutter-${DateTime.now().millisecondsSinceEpoch}-${Random().nextInt(99999)}';
    return _sessionId!;
  }

  static Map<String, String> get _adminHeaders => {
        'Content-Type': 'application/json',
        if (_adminToken.isNotEmpty) 'x-admin-token': _adminToken,
      };

  // ---------------------------------------------------------------------------
  // Health
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> fetchHealth() async {
    final response = await http.get(Uri.parse('$_baseUrl/health'));
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Health check failed (${response.statusCode})');
  }

  // ---------------------------------------------------------------------------
  // Agent
  // ---------------------------------------------------------------------------

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
      'session_id': sessionId,
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

  // ---------------------------------------------------------------------------
  // Features
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> fetchFeaturesConfig() async {
    final response = await http.get(Uri.parse('$_baseUrl/features/config'));
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception(
        'Failed to load features config (${response.statusCode})');
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
    throw Exception(
        'Failed to update features config (${response.statusCode})');
  }

  // ---------------------------------------------------------------------------
  // Services
  // ---------------------------------------------------------------------------

  static Future<List<dynamic>> fetchServices() async {
    final response = await http.get(Uri.parse('$_baseUrl/services'));
    if (response.statusCode == 200) {
      return json.decode(response.body) as List<dynamic>;
    }
    throw Exception('Failed to load services (${response.statusCode})');
  }

  static Future<Map<String, dynamic>> updateServicesCatalog(List<Map<String, dynamic>> services) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/services'),
      headers: _adminHeaders,
      body: json.encode(services),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to update services catalog (${response.statusCode})');
  }

  static Future<Map<String, dynamic>> updateService(String serviceId, Map<String, dynamic> service) async {
    final response = await http.put(
      Uri.parse('$_baseUrl/services/$serviceId'),
      headers: _adminHeaders,
      body: json.encode(service),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to update service (${response.statusCode})');
  }

  static Future<void> deleteService(String serviceId) async {
    final response = await http.delete(
      Uri.parse('$_baseUrl/services/$serviceId'),
      headers: _adminHeaders,
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to delete service (${response.statusCode})');
    }
  }

  // ---------------------------------------------------------------------------
  // Calendar
  // ---------------------------------------------------------------------------

  static Future<List<dynamic>> fetchCalendarEvents(
      String start, String end) async {
    final uri = Uri.parse('$_baseUrl/calendar/events')
        .replace(queryParameters: {'start': start, 'end': end});
    final response = await http.get(uri);
    if (response.statusCode == 200) {
      return json.decode(response.body) as List<dynamic>;
    }
    throw Exception('Failed to load calendar events (${response.statusCode})');
  }

  static Future<List<dynamic>> fetchAvailableSlots(
      String start, String end, int duration) async {
    final uri = Uri.parse('$_baseUrl/calendar/slots').replace(
        queryParameters: {
          'start': start,
          'end': end,
          'duration': duration.toString()
        });
    final response = await http.get(uri);
    if (response.statusCode == 200) {
      return json.decode(response.body) as List<dynamic>;
    }
    throw Exception('Failed to load available slots (${response.statusCode})');
  }

  static Future<Map<String, dynamic>> createCalendarEvent({
    required String summary,
    required String start,
    required String end,
  }) async {
    final body = <String, dynamic>{
      'summary': summary,
      'start': start,
      'end': end,
    };
    final response = await http.post(
      Uri.parse('$_baseUrl/calendar/events'),
      headers: _adminHeaders,
      body: json.encode(body),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to create event (${response.statusCode})');
  }

  static Future<void> deleteCalendarEvent(String eventId) async {
    final response = await http.delete(
      Uri.parse('$_baseUrl/calendar/events/$eventId'),
      headers: _adminHeaders,
    );
    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to delete event (${response.statusCode})');
    }
  }

  // ---------------------------------------------------------------------------
  // Payments
  // ---------------------------------------------------------------------------

  static Future<List<dynamic>> fetchPayments(
      {String? sessionId, String? status}) async {
    final params = <String, String>{};
    if (sessionId != null) params['session_id'] = sessionId;
    if (status != null) params['status'] = status;
    final uri =
        Uri.parse('$_baseUrl/payments/list').replace(queryParameters: params);
    final response = await http.get(uri);
    if (response.statusCode == 200) {
      final decoded = json.decode(response.body);
      if (decoded is List) return decoded;
      if (decoded is Map && decoded.containsKey('payments')) {
        return decoded['payments'] as List<dynamic>;
      }
      return <dynamic>[];
    }
    throw Exception('Failed to load payments (${response.statusCode})');
  }

  static Future<Map<String, dynamic>> fetchPaymentStatus(
      String reference) async {
    final response =
        await http.get(Uri.parse('$_baseUrl/payments/status/$reference'));
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load payment status (${response.statusCode})');
  }
}
