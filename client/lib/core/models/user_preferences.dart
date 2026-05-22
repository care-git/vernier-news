import 'package:equatable/equatable.dart';

class UserPreferences extends Equatable {
  const UserPreferences({
    required this.purpose,
    required this.interests,
    required this.depthPreference,
  });

  final String purpose;
  final List<String> interests;
  final String depthPreference;

  factory UserPreferences.fromJson(Map<String, dynamic> json) => UserPreferences(
        purpose: json['purpose'] as String? ?? 'general',
        interests: (json['interests'] as List<dynamic>?)?.cast<String>() ?? [],
        depthPreference: json['depth_preference'] as String? ?? 'standard',
      );

  @override
  List<Object?> get props => [purpose, interests, depthPreference];
}
