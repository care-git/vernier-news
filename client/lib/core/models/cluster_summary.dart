import 'package:equatable/equatable.dart';

class PoliticalSpread extends Equatable {
  const PoliticalSpread({
    required this.mean,
    required this.min,
    required this.max,
  });

  // All values on the -1.0 (left) to 1.0 (right) scale.
  final double mean;
  final double min;
  final double max;

  factory PoliticalSpread.fromJson(Map<String, dynamic> json) => PoliticalSpread(
        mean: (json['mean'] as num).toDouble(),
        min: (json['min'] as num).toDouble(),
        max: (json['max'] as num).toDouble(),
      );

  @override
  List<Object?> get props => [mean, min, max];
}

class ClusterSummary extends Equatable {
  const ClusterSummary({
    required this.id,
    required this.headline,
    required this.totalSourceCount,
    required this.independentSourceCount,
    this.category,
    this.firstPublishedAt,
    required this.lastUpdatedAt,
    this.politicalSpread,
    required this.countries,
  });

  final int id;
  final String headline;
  final int totalSourceCount;
  final int independentSourceCount;
  final String? category;
  final DateTime? firstPublishedAt;
  final DateTime lastUpdatedAt;
  final PoliticalSpread? politicalSpread;
  final List<String> countries;

  factory ClusterSummary.fromJson(Map<String, dynamic> json) => ClusterSummary(
        id: json['id'] as int,
        headline: json['headline'] as String? ?? '',
        totalSourceCount: json['total_source_count'] as int,
        independentSourceCount: json['independent_source_count'] as int,
        category: json['category'] as String?,
        firstPublishedAt: json['first_published_at'] != null
            ? DateTime.parse(json['first_published_at'] as String)
            : null,
        lastUpdatedAt: DateTime.parse(json['last_updated_at'] as String),
        politicalSpread: json['political_spread'] != null
            ? PoliticalSpread.fromJson(
                json['political_spread'] as Map<String, dynamic>,
              )
            : null,
        countries: (json['countries'] as List<dynamic>).cast<String>(),
      );

  @override
  List<Object?> get props => [id];
}
