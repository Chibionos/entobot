import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/device_credentials.dart';
import '../models/pairing_data.dart';
import '../api/auth_service.dart';
import '../api/websocket_client.dart';
import '../api/rest_client.dart';

/// Authentication state
class AuthState {
  final bool isAuthenticated;
  final String? deviceId;
  final DeviceCredentials? credentials;
  final bool isLoading;
  final String? error;

  const AuthState({
    this.isAuthenticated = false,
    this.deviceId,
    this.credentials,
    this.isLoading = false,
    this.error,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    String? deviceId,
    DeviceCredentials? credentials,
    bool? isLoading,
    String? error,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      deviceId: deviceId ?? this.deviceId,
      credentials: credentials ?? this.credentials,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Authentication state notifier
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthService _authService;

  AuthNotifier(this._authService) : super(const AuthState()) {
    _checkAuthentication();
  }

  /// Check if already authenticated
  Future<void> _checkAuthentication() async {
    state = state.copyWith(isLoading: true);

    try {
      final credentials = await _authService.getCredentials();

      if (credentials != null) {
        // Try to connect
        final success = await _authService.authenticateWithCredentials();

        if (success) {
          state = AuthState(
            isAuthenticated: true,
            deviceId: credentials.deviceId,
            credentials: credentials,
            isLoading: false,
          );
        } else {
          // Credentials invalid, clear them
          await _authService.logout();
          state = const AuthState(isLoading: false);
        }
      } else {
        state = const AuthState(isLoading: false);
      }
    } catch (e) {
      state = AuthState(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Pair with QR code
  Future<bool> pairWithQrCode(PairingData pairingData) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final credentials = await _authService.pairWithQrCode(pairingData);

      if (credentials != null) {
        state = AuthState(
          isAuthenticated: true,
          deviceId: credentials.deviceId,
          credentials: credentials,
          isLoading: false,
        );
        return true;
      } else {
        state = state.copyWith(
          isLoading: false,
          error: 'Pairing failed',
        );
        return false;
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
      return false;
    }
  }

  /// Refresh authentication
  Future<void> refresh() async {
    await _checkAuthentication();
  }

  /// Logout
  Future<void> logout() async {
    state = state.copyWith(isLoading: true);

    try {
      await _authService.logout();
      state = const AuthState(isLoading: false);
    } catch (e) {
      state = AuthState(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(error: null);
  }
}

/// WebSocket client provider
final websocketClientProvider = Provider<WebSocketClient>((ref) {
  return WebSocketClient();
});

/// REST client provider
final restClientProvider = Provider<RestClient>((ref) {
  return RestClient();
});

/// Auth service provider
final authServiceProvider = Provider<AuthService>((ref) {
  final wsClient = ref.watch(websocketClientProvider);
  final restClient = ref.watch(restClientProvider);
  return AuthService(wsClient: wsClient, restClient: restClient);
});

/// Auth state provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final authService = ref.watch(authServiceProvider);
  return AuthNotifier(authService);
});
