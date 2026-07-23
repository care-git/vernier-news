import 'package:equatable/equatable.dart';

import 'cluster_summary.dart';

/// Outlet fields shown on a source row and its inline card.
class ClusterSourceOutlet extends Equatable {
  const ClusterSourceOutlet({
    required this.id,
    required this.name,
    required this.domain,
    this.country,
    this.politicalLeaningLr,
    this.parentOrgName,
  });

  final int id;
  final String name;
  final String domain;
  final String? country;

  // -1.0 (far left) to 1.0 (far right); null if unknown.
  final double? politicalLeaningLr;
  final String? parentOrgName;

  factory ClusterSourceOutlet.fromJson(Map<String, dynamic> json) =>
      ClusterSourceOutlet(
        id: json['id'] as int,
        name: json['name'] as String,
        domain: json['domain'] as String,
        country: json['country'] as String?,
        politicalLeaningLr: (json['political_leaning_lr'] as num?)?.toDouble(),
        parentOrgName: json['parent_org_name'] as String?,
      );

  @override
  List<Object?> get props => [id];
}

/// A single member article of a cluster, with its outlet context.
class ClusterSource extends Equatable {
  const ClusterSource({
    required this.articleId,
    required this.title,
    required this.url,
    this.publishedAt,
    this.author,
    this.wireTier,
    required this.independenceScore,
    required this.outlet,
  });

  final int articleId;
  final String title;
  final String url;
  final DateTime? publishedAt;
  final String? author;
  final int? wireTier;
  final double independenceScore;
  final ClusterSourceOutlet outlet;

  factory ClusterSource.fromJson(Map<String, dynamic> json) => ClusterSource(
    articleId: json['article_id'] as int,
    title: json['title'] as String,
    url: json['url'] as String,
    publishedAt: json['published_at'] != null
        ? DateTime.parse(json['published_at'] as String)
        : null,
    author: json['author'] as String?,
    wireTier: json['wire_tier'] as int?,
    independenceScore: (json['independence_score'] as num).toDouble(),
    outlet: ClusterSourceOutlet.fromJson(
      json['outlet'] as Map<String, dynamic>,
    ),
  );

  @override
  List<Object?> get props => [articleId];
}

/// Article count for one country in a cluster's geographic spread.
class CountryCount extends Equatable {
  const CountryCount({required this.country, required this.count});

  final String country;
  final int count;

  factory CountryCount.fromJson(Map<String, dynamic> json) => CountryCount(
    country: json['country'] as String,
    count: json['count'] as int,
  );

  @override
  List<Object?> get props => [country, count];
}

/// Full cluster view: the summary fields plus the member source list.
class ClusterDetail extends ClusterSummary {
  const ClusterDetail({
    required super.id,
    required super.headline,
    required super.totalSourceCount,
    required super.independentSourceCount,
    super.category,
    super.firstPublishedAt,
    required super.lastUpdatedAt,
    super.politicalSpread,
    required super.countries,
    required this.sources,
    required this.countryCounts,
  });

  final List<ClusterSource> sources;
  final List<CountryCount> countryCounts;

  factory ClusterDetail.fromJson(Map<String, dynamic> json) => ClusterDetail(
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
    sources: (json['sources'] as List<dynamic>)
        .map((e) => ClusterSource.fromJson(e as Map<String, dynamic>))
        .toList(),
    countryCounts: (json['country_counts'] as List<dynamic>)
        .map((e) => CountryCount.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}
