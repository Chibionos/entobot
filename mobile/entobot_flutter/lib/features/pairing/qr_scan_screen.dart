import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:go_router/go_router.dart';
import '../../core/models/pairing_data.dart';
import '../../core/providers/auth_provider.dart';
import '../../theme/app_theme.dart';

class QrScanScreen extends ConsumerStatefulWidget {
  const QrScanScreen({super.key});

  @override
  ConsumerState<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends ConsumerState<QrScanScreen> {
  final MobileScannerController _scannerController = MobileScannerController();
  bool _isPairing = false;
  String? _errorMessage;

  @override
  void dispose() {
    _scannerController.dispose();
    super.dispose();
  }

  Future<void> _handleQrCode(String qrData) async {
    if (_isPairing) return; // Already processing

    setState(() {
      _isPairing = true;
      _errorMessage = null;
    });

    try {
      // Parse QR code data
      final json = jsonDecode(qrData) as Map<String, dynamic>;
      final pairingData = PairingData.fromJson(json);

      // Validate
      if (pairingData.isExpired()) {
        setState(() {
          _errorMessage = 'QR code has expired. Please scan a new one.';
          _isPairing = false;
        });
        return;
      }

      // Attempt pairing
      final success = await ref
          .read(authProvider.notifier)
          .pairWithQrCode(pairingData);

      if (!mounted) return;

      if (success) {
        // Navigate to chat screen
        context.go('/chat');
      } else {
        final authState = ref.read(authProvider);
        setState(() {
          _errorMessage = authState.error ?? 'Pairing failed. Please try again.';
          _isPairing = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Invalid QR code. Please scan a valid Entobot QR code.';
        _isPairing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan QR Code'),
      ),
      body: Stack(
        children: [
          // Camera view
          MobileScanner(
            controller: _scannerController,
            onDetect: (capture) {
              final List<Barcode> barcodes = capture.barcodes;
              if (barcodes.isNotEmpty && barcodes.first.rawValue != null) {
                _handleQrCode(barcodes.first.rawValue!);
              }
            },
          ),

          // Overlay with instructions
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.black.withOpacity(0.7),
                  Colors.transparent,
                  Colors.transparent,
                  Colors.black.withOpacity(0.7),
                ],
                stops: const [0.0, 0.3, 0.7, 1.0],
              ),
            ),
          ),

          // Center frame
          Center(
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                border: Border.all(
                  color: Colors.white,
                  width: 3,
                ),
                borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
              ),
            ),
          ),

          // Instructions
          Positioned(
            top: 60,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: const Text(
                'Position the QR code within the frame',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w500,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),

          // Bottom card with status
          Positioned(
            bottom: 40,
            left: 16,
            right: 16,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_isPairing) ...[
                      const CircularProgressIndicator(),
                      const SizedBox(height: 16),
                      const Text(
                        'Pairing with Entobot...',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ] else if (_errorMessage != null) ...[
                      Icon(
                        Icons.error_outline,
                        color: AppTheme.errorColor,
                        size: 48,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _errorMessage!,
                        style: TextStyle(
                          color: AppTheme.errorColor,
                          fontSize: 14,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {
                          setState(() {
                            _errorMessage = null;
                          });
                        },
                        child: const Text('Try Again'),
                      ),
                    ] else ...[
                      const Icon(
                        Icons.qr_code_scanner,
                        size: 48,
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'Scan the QR code from your desktop app',
                        style: TextStyle(fontSize: 14),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),

          // Flashlight toggle
          Positioned(
            top: 16,
            right: 16,
            child: SafeArea(
              child: IconButton(
                icon: ValueListenableBuilder(
                  valueListenable: _scannerController.torchState,
                  builder: (context, state, child) {
                    return Icon(
                      state == TorchState.on
                          ? Icons.flash_on
                          : Icons.flash_off,
                      color: Colors.white,
                    );
                  },
                ),
                onPressed: () => _scannerController.toggleTorch(),
                style: IconButton.styleFrom(
                  backgroundColor: Colors.black.withOpacity(0.5),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
