import 'package:flutter/material.dart';

import 'api_service.dart';
import 'i18n.dart';
import 'pages/dashboard_page.dart';
import 'pages/chat_page.dart';
import 'pages/calendar_page.dart';
import 'pages/payments_page.dart';
import 'pages/settings_page.dart';

void main() {
  runApp(const ServiceBotApp());
}

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
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.blue,
        brightness: Brightness.light,
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1565C0),
          foregroundColor: Colors.white,
          elevation: 2,
        ),
      ),
      home: HomePage(onLanguageChanged: _setLanguage),
    );
  }
}

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
    final pages = <Widget>[
      const DashboardPage(),
      ChatPage(key: ValueKey(ApiService.baseUrl)),
      const CalendarPage(),
      const PaymentsPage(),
      SettingsPage(
        onBaseUrlChanged: _onBaseUrlChanged,
        onLanguageChanged: widget.onLanguageChanged,
      ),
    ];

    return Scaffold(
      body: IndexedStack(index: _selectedIndex, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: [
          NavigationDestination(
              icon: const Icon(Icons.dashboard), label: t('dashboard')),
          NavigationDestination(
              icon: const Icon(Icons.chat), label: t('chat')),
          NavigationDestination(
              icon: const Icon(Icons.calendar_month), label: t('calendar')),
          NavigationDestination(
              icon: const Icon(Icons.payment), label: t('payments')),
          NavigationDestination(
              icon: const Icon(Icons.settings), label: t('settings')),
        ],
      ),
    );
  }
}
