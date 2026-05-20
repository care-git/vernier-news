import 'package:equatable/equatable.dart';

class UserModel extends Equatable {
  const UserModel({
    required this.id,
    required this.email,
    required this.tier,
  });

  final int id;
  final String email;
  final String tier;

  bool get isFree => tier == 'free';

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as int,
        email: json['email'] as String,
        tier: json['tier'] as String,
      );

  @override
  List<Object?> get props => [id, email, tier];
}
