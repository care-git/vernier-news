import 'package:equatable/equatable.dart';

class OutletSummary extends Equatable {
  const OutletSummary({
    required this.id,
    required this.name,
    required this.domain,
    this.country,
    this.politicalLeaningLr,
  });

  final int id;
  final String name;
  final String domain;
  final String? country;

  // -1.0 (far left) to 1.0 (far right); null if unknown.
  final double? politicalLeaningLr;

  factory OutletSummary.fromJson(Map<String, dynamic> json) => OutletSummary(
        id: json['id'] as int,
        name: json['name'] as String,
        domain: json['domain'] as String,
        country: json['country'] as String?,
        politicalLeaningLr: (json['political_leaning_lr'] as num?)?.toDouble(),
      );

  @override
  List<Object?> get props => [id];
}

class OutletDetail extends OutletSummary {
  const OutletDetail({
    required super.id,
    required super.name,
    required super.domain,
    super.country,
    super.politicalLeaningLr,
    this.languagePrimary,
    this.politicalLeaningSource,
    this.parentOrgName,
    required this.active,
  });

  final String? languagePrimary;
  final String? politicalLeaningSource;
  final String? parentOrgName;
  final bool active;

  factory OutletDetail.fromJson(Map<String, dynamic> json) => OutletDetail(
        id: json['id'] as int,
        name: json['name'] as String,
        domain: json['domain'] as String,
        country: json['country'] as String?,
        politicalLeaningLr: (json['political_leaning_lr'] as num?)?.toDouble(),
        languagePrimary: json['language_primary'] as String?,
        politicalLeaningSource: json['political_leaning_source'] as String?,
        parentOrgName: json['parent_org_name'] as String?,
        active: json['active'] as bool,
      );

  @override
  List<Object?> get props => [id, active];
}
