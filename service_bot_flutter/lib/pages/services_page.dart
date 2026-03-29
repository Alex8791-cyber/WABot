import 'package:flutter/material.dart';
import '../api_service.dart';
import '../i18n.dart';

class ServicesPage extends StatefulWidget {
  const ServicesPage({super.key});

  @override
  State<ServicesPage> createState() => _ServicesPageState();
}

class _ServicesPageState extends State<ServicesPage> {
  List<Map<String, dynamic>> _services = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadServices();
  }

  Future<void> _loadServices() async {
    setState(() => _loading = true);
    try {
      final services = await ApiService.fetchServices();
      setState(() {
        _services = services.cast<Map<String, dynamic>>();
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('error')}: $e')),
        );
      }
    }
  }

  Future<void> _deleteService(String serviceId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(t('deleteService')),
        content: Text(t('confirmDelete')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ApiService.deleteService(serviceId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('serviceDeleted'))),
        );
      }
      _loadServices();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('error')}: $e')),
        );
      }
    }
  }

  void _openEditor([Map<String, dynamic>? service]) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => _ServiceEditorPage(
          service: service,
          onSaved: () {
            _loadServices();
            Navigator.pop(context);
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(t('serviceEditor'))),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openEditor(),
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _services.isEmpty
              ? Center(child: Text(t('noServices')))
              : ListView.builder(
                  padding: const EdgeInsets.all(8),
                  itemCount: _services.length,
                  itemBuilder: (context, index) {
                    final s = _services[index];
                    return Card(
                      child: ListTile(
                        title: Text(s['name'] ?? ''),
                        subtitle: Text(
                          '${s['delivery_mode'] ?? ''} · ${s['average_duration'] ?? ''} · ${s['average_value'] ?? ''}',
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.edit, size: 20),
                              onPressed: () => _openEditor(s),
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete, size: 20, color: Colors.red),
                              onPressed: () => _deleteService(s['id']),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

class _ServiceEditorPage extends StatefulWidget {
  final Map<String, dynamic>? service;
  final VoidCallback onSaved;

  const _ServiceEditorPage({this.service, required this.onSaved});

  @override
  State<_ServiceEditorPage> createState() => _ServiceEditorPageState();
}

class _ServiceEditorPageState extends State<_ServiceEditorPage> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _idController;
  late TextEditingController _nameController;
  late TextEditingController _descriptionController;
  late TextEditingController _durationController;
  late TextEditingController _valueController;
  String _deliveryMode = 'Remote';
  bool _proposalRequired = true;
  bool _saving = false;

  bool get _isEditing => widget.service != null;

  @override
  void initState() {
    super.initState();
    final s = widget.service;
    _idController = TextEditingController(text: s?['id'] ?? '');
    _nameController = TextEditingController(text: s?['name'] ?? '');
    _descriptionController = TextEditingController(text: s?['description'] ?? '');
    _durationController = TextEditingController(text: s?['average_duration'] ?? '');
    _valueController = TextEditingController(text: s?['average_value'] ?? '');
    _deliveryMode = s?['delivery_mode'] ?? 'Remote';
    _proposalRequired = s?['proposal_required'] ?? true;
  }

  @override
  void dispose() {
    _idController.dispose();
    _nameController.dispose();
    _descriptionController.dispose();
    _durationController.dispose();
    _valueController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (_saving) return;
    setState(() => _saving = true);

    final service = {
      'id': _idController.text.trim(),
      'name': _nameController.text.trim(),
      'description': _descriptionController.text.trim(),
      'delivery_mode': _deliveryMode,
      'average_duration': _durationController.text.trim(),
      'average_value': _valueController.text.trim(),
      'proposal_required': _proposalRequired,
      'questions': widget.service?['questions'] ?? [
        {'id': 'company_name', 'label': 'Company Name', 'type': 'text'},
        {'id': 'website', 'label': 'Website', 'type': 'text'},
        {'id': 'company_size', 'label': 'Company Size', 'type': 'select', 'options': ['1-50', '51-200', '201-1000', '1000+']},
        {'id': 'industry', 'label': 'Industry', 'type': 'text'},
        {'id': 'urgency', 'label': 'Urgency', 'type': 'select', 'options': ['Low', 'Medium', 'High']},
      ],
    };

    try {
      if (_isEditing) {
        await ApiService.updateService(widget.service!['id'], service);
      } else {
        // Add to existing catalog
        final existing = await ApiService.fetchServices();
        final catalog = existing.cast<Map<String, dynamic>>();
        catalog.add(service);
        await ApiService.updateServicesCatalog(catalog);
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(t('serviceSaved'))),
        );
      }
      widget.onSaved();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${t('error')}: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditing ? t('editService') : t('addService')),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _idController,
              decoration: InputDecoration(labelText: t('serviceId')),
              enabled: !_isEditing,
              validator: (v) => (v == null || v.trim().isEmpty) ? t('error') : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _nameController,
              decoration: InputDecoration(labelText: t('serviceName')),
              validator: (v) => (v == null || v.trim().isEmpty) ? t('error') : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _descriptionController,
              decoration: InputDecoration(labelText: t('serviceDescription')),
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _deliveryMode,
              decoration: InputDecoration(labelText: t('deliveryMode')),
              items: ['Remote', 'Onsite', 'Hybrid'].map((m) =>
                DropdownMenuItem(value: m, child: Text(m))
              ).toList(),
              onChanged: (v) { if (v != null) setState(() => _deliveryMode = v); },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _durationController,
              decoration: InputDecoration(labelText: t('averageDuration')),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _valueController,
              decoration: InputDecoration(labelText: t('averageValue')),
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              title: Text(t('proposalRequired')),
              value: _proposalRequired,
              onChanged: (v) => setState(() => _proposalRequired = v),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(_isEditing ? t('editService') : t('addService')),
            ),
          ],
        ),
      ),
    );
  }
}
