import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../api_service.dart';
import '../i18n.dart';

class CalendarPage extends StatefulWidget {
  const CalendarPage({super.key});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  late DateTime _start;
  late DateTime _end;
  int _duration = 30;
  bool _loading = true;
  List<dynamic> _events = [];
  List<dynamic> _slots = [];

  @override
  void initState() {
    super.initState();
    _start = DateTime.now();
    _end = _start.add(const Duration(days: 7));
    _load();
  }

  String _iso(DateTime dt) => dt.toIso8601String().split('T').first;

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      _events = await ApiService.fetchCalendarEvents(_iso(_start), _iso(_end));
    } catch (_) {
      _events = [];
    }
    try {
      _slots = await ApiService.fetchAvailableSlots(
          _iso(_start), _iso(_end), _duration);
    } catch (_) {
      _slots = [];
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _pickRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      initialDateRange: DateTimeRange(start: _start, end: _end),
    );
    if (picked != null) {
      _start = picked.start;
      _end = picked.end;
      _load();
    }
  }

  Future<void> _deleteEvent(String id) async {
    try {
      await ApiService.deleteCalendarEvent(id);
      _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  Future<void> _showCreateDialog() async {
    final summaryCtrl = TextEditingController();
    DateTime eventStart = DateTime.now().add(const Duration(hours: 1));
    DateTime eventEnd = eventStart.add(const Duration(hours: 1));

    await showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: Text(t('createEvent')),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: summaryCtrl,
                decoration: InputDecoration(labelText: t('summary')),
              ),
              const SizedBox(height: 8),
              Text(
                  '${t('startTime')}: ${DateFormat.yMd().add_Hm().format(eventStart)}'),
              Text(
                  '${t('endTime')}: ${DateFormat.yMd().add_Hm().format(eventEnd)}'),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx), child: Text(t('cancel'))),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  await ApiService.createCalendarEvent(
                    summary: summaryCtrl.text.trim(),
                    start: eventStart.toIso8601String(),
                    end: eventEnd.toIso8601String(),
                  );
                  _load();
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context)
                        .showSnackBar(SnackBar(content: Text('$e')));
                  }
                }
              },
              child: Text(t('create')),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final dateFmt = DateFormat.yMd();
    final timeFmt = DateFormat.Hm();

    return Scaffold(
      appBar: AppBar(
        title: Text(t('calendar')),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateDialog,
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Date range + duration
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.date_range),
                        label: Text(
                            '${dateFmt.format(_start)} — ${dateFmt.format(_end)}'),
                        onPressed: _pickRange,
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      width: 100,
                      child: DropdownButtonFormField<int>(
                        value: _duration,
                        decoration: InputDecoration(
                            labelText: t('duration'), isDense: true),
                        items: const [
                          DropdownMenuItem(value: 15, child: Text('15')),
                          DropdownMenuItem(value: 30, child: Text('30')),
                          DropdownMenuItem(value: 60, child: Text('60')),
                        ],
                        onChanged: (v) {
                          if (v != null) {
                            _duration = v;
                            _load();
                          }
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Events
                Text(t('events'),
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                if (_events.isEmpty) Text(t('noEvents')),
                ..._events.map((e) {
                  final id = (e['id'] ?? '').toString();
                  final summary = e['summary'] ?? '';
                  final start = e['start'] ?? '';
                  final description = e['description'] ?? '';
                  return Card(
                    child: ListTile(
                      title: Text('$summary'),
                      subtitle: Text('$start${description.toString().isNotEmpty ? '\n$description' : ''}'),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        tooltip: t('deleteEvent'),
                        onPressed: () => _deleteEvent(id),
                      ),
                    ),
                  );
                }),

                const SizedBox(height: 24),

                // Available slots
                Text(t('availableSlots'),
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                if (_slots.isEmpty) Text(t('noSlots')),
                ..._slots.map((s) {
                  final slotStart = s['start'] ?? '';
                  final slotEnd = s['end'] ?? '';
                  DateTime? startDt = DateTime.tryParse(slotStart.toString());
                  DateTime? endDt = DateTime.tryParse(slotEnd.toString());
                  final label = (startDt != null && endDt != null)
                      ? '${dateFmt.format(startDt)} ${timeFmt.format(startDt)} — ${timeFmt.format(endDt)}'
                      : '$slotStart — $slotEnd';
                  return Card(
                    child: ListTile(
                      leading:
                          const Icon(Icons.access_time, color: Colors.green),
                      title: Text(label),
                    ),
                  );
                }),
              ],
            ),
    );
  }
}
