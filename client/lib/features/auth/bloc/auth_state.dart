part of 'auth_cubit.dart';

sealed class AuthState {
  const AuthState();
}

final class AuthInitial extends AuthState {
  const AuthInitial();
}

final class AuthLoading extends AuthState {
  const AuthLoading();
}

/// Emitted when the user is authenticated.
///
/// [isNewUser] is true immediately after registration — routes the user to
/// the onboarding flow rather than the digest.
final class AuthAuthenticated extends AuthState {
  const AuthAuthenticated({required this.isNewUser});

  final bool isNewUser;
}

/// Emitted when no valid session exists, or after logout.
///
/// [error] is set when this state follows a failed login/register attempt.
final class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated({this.error});

  final String? error;
}
