import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../api_service.dart';
import '../i18n.dart';

class PaymentsPage extends StatefulWidget {
  const PaymentsPage({super.key});

  @override
  State<PaymentsPage> createState() => _PaymentsPageState();
}

class _PaymentsPageState extends State<PaymentsPage> {
  bool _loading = true;
  List<dynamic> _payments = [];
  String? _statusFilter;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _payments = await ApiService.fetchPayments(status: _statusFilter);
    } catch (_) {
      _payments = [];
    }
    if (mounted) setState(() => _loading = false);
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'paid':
        return Colors.green;
      case 'pending':
        return Colors.orange;
      case 'failed':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'paid':
        return t('paid');
      case 'pending':
        return t('pending');
      case 'failed':
        return t('failed');
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(t('payments')),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: Column(
        children: [
          // Filter row
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Text(t('filterByStatus'),
                    style: const TextStyle(fontWeight: FontWeight.w500)),
                const SizedBox(width: 12),
                ChoiceChip(
                  label: Text(t('allStatuses')),
                  selected: _statusFilter == null,
                  onSelected: (_) {
                    _statusFilter = null;
                    _load();
                  },
                ),
                const SizedBox(width: 6),
                ChoiceChip(
                  label: Text(t('pending')),
                  selected: _statusFilter == 'pending',
                  selectedColor: Colors.orange[100],
                  onSelected: (_) {
                    _statusFilter = 'pending';
                    _load();
                  },
                ),
                const SizedBox(width: 6),
                ChoiceChip(
                  label: Text(t('paid')),
                  selected: _statusFilter == 'paid',
                  selectedColor: Colors.green[100],
                  onSelected: (_) {
                    _statusFilter = 'paid';
                    _load();
                  },
                ),
                const SizedBox(width: 6),
                ChoiceChip(
                  label: Text(t('failed')),
                  selected: _statusFilter == 'failed',
                  selectedColor: Colors.red[100],
                  onSelected: (_) {
                    _statusFilter = 'failed';
                    _load();
                  },
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // List
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _payments.isEmpty
                    ? Center(child: Text(t('noPaymentData')))
                    : ListView.builder(
                        padding: const EdgeInsets.all(8),
                        itemCount: _payments.length,
                        itemBuilder: (context, index) {
                          final p = _payments[index];
                          final status =
                              (p['status'] ?? 'unknown').toString();
                          final amount =
                              (p['amount'] ?? p['total'] ?? 0).toString();
                          final ref = (p['reference'] ??
                                  p['payment_reference'] ??
                                  '')
                              .toString();
                          final url =
                              (p['payment_url'] ?? p['url'] ?? '').toString();

                          return Card(
                            child: ListTile(
                              title: Text(ref.isNotEmpty ? ref : '—'),
                              subtitle: Text('ZAR $amount'),
                              trailing: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: _statusColor(status),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Text(
                                  _statusLabel(status),
                                  style: const TextStyle(
                                      color: Colors.white, fontSize: 12),
                                ),
                              ),
                              onTap: url.isNotEmpty
                                  ? () {
                                      Clipboard.setData(
                                          ClipboardData(text: url));
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(const SnackBar(
                                              content: Text(
                                                  'Payment URL copied')));
                                    }
                                  : null,
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
