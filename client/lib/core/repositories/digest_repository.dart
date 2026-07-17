import '../api/api_client.dart';
import '../api/endpoints.dart';
import '../models/digest_response.dart';

class DigestRepository {
  DigestRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<DigestResponse> getDigest() async {
    final data = await _apiClient.get(Endpoints.digest);
    return DigestResponse.fromJson(data);
  }
}
