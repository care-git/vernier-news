import '../api/api_client.dart';
import '../api/endpoints.dart';
import '../models/user_preferences.dart';

class PreferencesRepository {
  PreferencesRepository({required ApiClient apiClient})
      : _apiClient = apiClient;

  final ApiClient _apiClient;

  /// Creates or replaces the current user's preferences.
  Future<UserPreferences> updatePreferences({
    required String purpose,
    required List<String> interests,
    required String depthPreference,
  }) async {
    final data = await _apiClient.put(
      Endpoints.preferences,
      body: {
        'purpose': purpose,
        'interests': interests,
        'depth_preference': depthPreference,
      },
    );
    return UserPreferences.fromJson(data);
  }
}
