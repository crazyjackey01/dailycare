import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const DailyCareApp());
}

class DailyCareApp extends StatelessWidget {
  const DailyCareApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'DailyCare',
      theme: ThemeData(
        colorSchemeSeed: Colors.teal,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  Map<String, dynamic>? data;

  bool loading = true;
  bool useOllama = true;

  static const String apiUrl = String.fromEnvironment(
    "API_URL", defaultValue: "http://127.0.0.1:8000",
  );

  @override
  void initState() {
    super.initState();
    fetchSummary();
  }

  Future<void> fetchSummary() async {
    setState(() {
      loading = true;
    });

    try {
      final response = await http.get(
        Uri.parse(
          "$apiUrl/summary?use_ollama=$useOllama",
        ),
      );

      final decoded = jsonDecode(
        utf8.decode(response.bodyBytes),
      );

      final safeMessage =
        decoded["message"] ??
        decoded["ruleBasedMessage"] ??
        "메시지를 불러오지 못했습니다.";

      decoded["message"] = safeMessage;

      setState(() {
        data = decoded;
        loading = false;
      });
    } catch (e) {
      setState(() {
        loading = false;
      });

      debugPrint(e.toString());
    }
  }

  Color getRiskColor(String level) {
    switch (level) {
      case "위험":
        return Colors.red;
      case "주의":
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  @override
  Widget build(BuildContext context) {
    final analysis =
    (data?["analysis"] as Map<String, dynamic>?) ?? {};

    final riskLevel =
      analysis["riskLevel"]?.toString() ?? "-";

    final finalScore =
      analysis["finalScore"]?.toString() ?? "0";

    final message =
      data?["message"]?.toString() ??
      "메시지를 불러오지 못했습니다.";

    return Scaffold(
      appBar: AppBar(
        title: const Text("DailyCare"),
        actions: [
          IconButton(
            onPressed: fetchSummary,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: loading
          ? const Center(
              child: CircularProgressIndicator(),
            )
          : RefreshIndicator(
              onRefresh: fetchSummary,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment:
                            CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "오늘 생활 패턴 상태",
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),

                          const SizedBox(height: 20),

                          Row(
                            children: [
                              CircleAvatar(
                                radius: 36,
                                backgroundColor:
                                    getRiskColor(riskLevel),
                                child: Text(
                                  "$finalScore",
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 22,
                                    fontWeight:
                                        FontWeight.bold,
                                  ),
                                ),
                              ),

                              const SizedBox(width: 20),

                              Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    riskLevel,
                                    style: TextStyle(
                                      fontSize: 30,
                                      fontWeight:
                                          FontWeight.bold,
                                      color: getRiskColor(
                                        riskLevel,
                                      ),
                                    ),
                                  ),

                                  Text(
                                    "모드: ${data?["messageMode"]}",
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  SwitchListTile(
                    title: const Text("Ollama 자연어 요약 사용"),
                    value: useOllama,
                    onChanged: (value) async {
                      setState(() {
                        useOllama = value;
                      });

                      await fetchSummary();
                    },
                  ),

                  const SizedBox(height: 12),

                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Text(
                        message,
                        style: const TextStyle(
                          fontSize: 16,
                          height: 1.5,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  if (analysis["zones"] != null)
                    ...buildZoneCards(
                      Map<String, dynamic>.from(analysis["zones"]),
                    ),
                ],
              ),
            ),
    );
  }

  String zoneName(String key, Map<String, dynamic> zone) {
  if (zone["name"] != null) {
    return zone["name"].toString();
  }

  switch (key) {
    case "kitchen":
      return "주방";
    case "frontDoor":
      return "현관";
    case "bedroom":
      return "침실";
    case "bathroom":
      return "화장실";
    case "livingRoom":
      return "거실";
    default:
      return key;
  }
}




  List<Widget> buildZoneCards(
  Map<String, dynamic> zones,
) {
  return zones.entries.map((entry) {
    final zone = Map<String, dynamic>.from(entry.value ?? {});

    return Card(
      child: ListTile(
        title: Text(zoneName(entry.key, zone)),
        subtitle: Text(
          "오늘 ${zone["today"]?.toString() ?? "-"}분 / 평균 ${zone["baseline"]?.toString() ?? "-"}분",
        ),
        trailing: Text(
          "${zone["deviationPercent"]?.toString() ?? "0"}%",
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }).toList();
}
}