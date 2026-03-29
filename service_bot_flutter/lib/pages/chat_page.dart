import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../api_service.dart';
import '../i18n.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _sending = false;

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
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
      setState(() {
        _messages.add(_ChatMessage(t('connectionError'), false));
        _sending = false;
      });
    }
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final timeFormat = DateFormat.Hm();
    return Scaffold(
      appBar: AppBar(title: Text(t('chatTitle'))),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(8.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return Container(
                  margin: const EdgeInsets.symmetric(vertical: 4.0),
                  alignment:
                      msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Column(
                    crossAxisAlignment: msg.isUser
                        ? CrossAxisAlignment.end
                        : CrossAxisAlignment.start,
                    children: [
                      DecoratedBox(
                        decoration: BoxDecoration(
                          color:
                              msg.isUser ? Colors.blue[100] : Colors.grey[200],
                          borderRadius: BorderRadius.circular(12.0),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                              vertical: 8.0, horizontal: 12.0),
                          child: Text(msg.text),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(top: 2, left: 4, right: 4),
                        child: Text(
                          timeFormat.format(msg.timestamp),
                          style: TextStyle(
                              fontSize: 10, color: Colors.grey[500]),
                        ),
                      ),
                    ],
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
  _ChatMessage(this.text, this.isUser) : timestamp = DateTime.now();
}
