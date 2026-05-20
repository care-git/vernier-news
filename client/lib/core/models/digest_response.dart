import 'package:equatable/equatable.dart';
import 'cluster_summary.dart';

class DigestResponse extends Equatable {
  const DigestResponse({
    required this.userId,
    required this.generatedAt,
    required this.categories,
  });

  final int userId;
  final String generatedAt;
  final Map<String, List<ClusterSummary>> categories;

  bool get isEmpty => categories.isEmpty;

  factory DigestResponse.fromJson(Map<String, dynamic> json) => DigestResponse(
        userId: json['user_id'] as int,
        generatedAt: json['generated_at'] as String,
        categories: (json['categories'] as Map<String, dynamic>).map(
          (key, value) => MapEntry(
            key,
            (value as List<dynamic>)
                .map((e) => ClusterSummary.fromJson(e as Map<String, dynamic>))
                .toList(),
          ),
        ),
      );

  @override
  List<Object?> get props => [userId, generatedAt];
}
