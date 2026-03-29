import 'package:flutter/material.dart';

import '../api_service.dart';
import '../i18n.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  bool _loading = true;
  bool _healthy = false;
  String _model = '';
  List<dynamic> _payments = [];

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    try {
      final health = await ApiService.fetchHealth();
      _healthy = true;
      _model = (health['model'] ?? health['status'] ?? '').toString();
    } catch (_) {
      _healthy = false;
      _model = '';
    }
    try {
      _payments = await ApiService.fetchPayments();
    } catch (_) {
      _payments = [];
    }
    if (mounted) setState(() => _loading = false);
  }

  int _countByStatus(String status) =>
      _payments.where((p) => p['status'] == status).length;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(t('dashboard')),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loading ? null : _refresh,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Health
                  Card(
                    child: ListTile(
                      leading: Icon(Icons.circle,
                          color: _healthy ? Colors.green : Colors.red,
                          size: 16),
                      title:
                          Text(_healthy ? t('healthOk') : t('healthDown')),
                      subtitle: _model.isNotEmpty
                          ? Text('${t('model')}: $_model')
                          : null,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Stats cards
                  Row(
                    children: [
                      _StatCard(
                          label: t('totalPayments'),
                          value: '${_payments.length}',
                          color: Colors.blue),
                      const SizedBox(width: 8),
                      _StatCard(
                          label: t('paidPayments'),
                          value: '${_countByStatus('paid')}',
                          color: Colors.green),
                      const SizedBox(width: 8),
                      _StatCard(
                          label: t('pendingPayments'),
                          value: '${_countByStatus('pending')}',
                          color: Colors.orange),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Recent payments
                  Text(t('recentPayments'),
                      style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  if (_payments.isEmpty)
                    Center(child: Text(t('noPayments')))
                  else
                    ..._payments.take(5).map((p) {
                      final status = (p['status'] ?? 'unknown').toString();
                      final amount = p['amount'] ?? p['total'] ?? '';
                      final ref = p['reference'] ?? p['payment_reference'] ?? '';
                      return Card(
                        child: ListTile(
                          title: Text('$ref'),
                          subtitle: Text('ZAR $amount'),
                          trailing: _StatusBadge(status: status),
                        ),
                      );
                    }),
                ],
              ),
            ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatCard(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        color: color.withValues(alpha: 0.1),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
          child: Column(
            children: [
              Text(value,
                  style: Theme.of(context)
                      .textTheme
                      .headlineMedium
                      ?.copyWith(color: color, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(label,
                  style: TextStyle(color: color, fontSize: 12)),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color bg;
    switch (status) {
      case 'paid':
        bg = Colors.green;
        break;
      case 'pending':
        bg = Colors.orange;
        break;
      case 'failed':
        bg = Colors.red;
        break;
      default:
        bg = Colors.grey;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration:
          BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
      child: Text(status,
          style:
              const TextStyle(color: Colors.white, fontSize: 12)),
    );
  }
}
