import 'package:flutter/material.dart';
import 'dart:io'; // for running python scripts

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Device Configuration App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: Colors.blue, useMaterial3: true),
      home: const MainWindow(),
    );
  }
}

class MainWindow extends StatefulWidget {
  const MainWindow({super.key});

  @override
  State<MainWindow> createState() => _MainWindowState();
}

class _MainWindowState extends State<MainWindow> {
  String? selectedDevice;
  String? selectedConfig;
  String outputText = '';
  bool isRunning = false;

  // 🔽 Device options
  final List<String> devices = ['Auto Sort Touch', 'AutoFlex', 'Grain Tracker'];

  // ⚙️ Configuration options
  final List<String> configs = [
    'Network Configuration',
    'Device Configuration',
    'Display Configuration',
  ];

  // 🧠 Select correct Python script
  String _getScriptForSelection() {
    if (selectedDevice == 'Auto Sort Touch' &&
        selectedConfig == 'Display Configuration') {
      return 'python_scripts/display_config.py';
    }
    return 'python_scripts/hello_world.py';
  }

  // ▶️ Run Python Script
  Future<void> runPythonScript() async {
    setState(() {
      isRunning = true;
      outputText = 'Running script...';
    });

    try {
      final scriptPath = _getScriptForSelection();

      final result = await Process.run(
        '/home/dhairya/venv/bin/python', // your Python virtual env
        [scriptPath],
      );

      setState(() {
        isRunning = false;
        outputText = result.stdout.toString().trim().isNotEmpty
            ? result.stdout.toString()
            : result.stderr.toString();
      });
    } catch (e) {
      setState(() {
        isRunning = false;
        outputText = 'Error running script: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF74ABE2), Color(0xFF5563DE), Color(0xFF3A1C71)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 🧭 Menu Bar
            MenuBar(
              children: [
                SubmenuButton(
                  menuChildren: [
                    MenuItemButton(onPressed: () {}, child: const Text('Exit')),
                  ],
                  child: const Text('File'),
                ),
                SubmenuButton(
                  menuChildren: [
                    MenuItemButton(
                      onPressed: () {},
                      child: const Text('About'),
                    ),
                  ],
                  child: const Text('Help'),
                ),
              ],
            ),

            // ⚙️ Device / Config / Run Row
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  // Device Dropdown
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.9),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: DropdownButton<String>(
                      hint: const Text('Device'),
                      value: selectedDevice,
                      underline: const SizedBox(),
                      items: devices
                          .map(
                            (device) => DropdownMenuItem(
                              value: device,
                              child: Text(device),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        setState(() {
                          selectedDevice = value;
                          selectedConfig = null;
                        });
                      },
                    ),
                  ),

                  const SizedBox(width: 12),

                  // Configuration Dropdown
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    decoration: BoxDecoration(
                      color: selectedDevice == null
                          ? Colors.grey.shade300
                          : Colors.white.withOpacity(0.9),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: DropdownButton<String>(
                      hint: const Text('Configuration'),
                      value: selectedConfig,
                      underline: const SizedBox(),
                      items: configs
                          .map(
                            (config) => DropdownMenuItem(
                              value: config,
                              child: Text(config),
                            ),
                          )
                          .toList(),
                      onChanged: selectedDevice == null
                          ? null
                          : (value) {
                              setState(() {
                                selectedConfig = value;
                              });
                            },
                    ),
                  ),

                  const SizedBox(width: 12),

                  // RUN Button
                  ElevatedButton(
                    onPressed:
                        (selectedDevice != null &&
                            selectedConfig != null &&
                            !isRunning)
                        ? () async {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(
                                  'Running $selectedDevice with $selectedConfig...',
                                ),
                              ),
                            );
                            await runPythonScript();
                          }
                        : null,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 14,
                      ),
                      backgroundColor: Colors.blueAccent,
                      disabledBackgroundColor: Colors.grey.shade400,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: isRunning
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                              strokeWidth: 2.2,
                            ),
                          )
                        : const Text(
                            'RUN',
                            style: TextStyle(fontSize: 16, color: Colors.white),
                          ),
                  ),
                ],
              ),
            ),

            // Output Area
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.all(16),
                  child: SingleChildScrollView(
                    child: Text(
                      outputText.isEmpty
                          ? 'Select a device and configuration to run the process.'
                          : outputText,
                      style: const TextStyle(
                        fontSize: 18,
                        color: Colors.white,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
