import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';
import '../api/endpoints.dart';
import '../models/token_response.dart';
import '../models/user.dart';

// Must stay in sync with the keys used in auth_interceptor.dart.
const _kAccessKey = 'access_token';
const _kRefreshKey = 'refresh_token';

class AuthRepository {
  AuthRepository({
    required ApiClient apiClient,
    required SharedPreferences prefs,
  })  : _apiClient = apiClient,
        _prefs = prefs;

  final ApiClient _apiClient;
  final SharedPreferences _prefs;

  /// True when a (possibly expired) access token is stored locally.
  bool get hasToken => _prefs.getString(_kAccessKey) != null;

  /// Authenticates with [email] and [password]; persists returned tokens.
  ///
  /// Throws [ApiException] on invalid credentials or network failure.
  Future<void> login(String email, String password) async {
    final data = await _apiClient.post(
      Endpoints.login,
      body: {'email': email, 'password': password},
    );
    await _saveTokens(TokenResponse.fromJson(data));
  }

  /// Creates a new account with [email] and [password]; persists tokens.
  ///
  /// Throws [ApiException] on conflict (409) or network failure.
  Future<void> register(String email, String password) async {
    final data = await _apiClient.post(
      Endpoints.register,
      body: {'email': email, 'password': password},
    );
    await _saveTokens(TokenResponse.fromJson(data));
  }

  /// Fetches the current user from /users/me using the stored access token.
  ///
  /// Throws [ApiException] if the token is missing or invalid.
  Future<UserModel> getCurrentUser() async {
    final data = await _apiClient.get(Endpoints.me);
    return UserModel.fromJson(data);
  }

  /// Removes all stored tokens (logout).
  Future<void> clearTokens() async {
    await Future.wait([
      _prefs.remove(_kAccessKey),
      _prefs.remove(_kRefreshKey),
    ]);
  }

  Future<void> _saveTokens(TokenResponse tokens) async {
    await Future.wait([
      _prefs.setString(_kAccessKey, tokens.accessToken),
      _prefs.setString(_kRefreshKey, tokens.refreshToken),
    ]);
  }
}
