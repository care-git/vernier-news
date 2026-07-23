import '../api/api_client.dart';
import '../api/endpoints.dart';
import '../models/cluster_detail.dart';

class ClusterRepository {
  ClusterRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<ClusterDetail> getCluster(int id) async {
    final data = await _apiClient.get(Endpoints.cluster(id));
    return ClusterDetail.fromJson(data);
  }
}
