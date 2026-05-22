import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/api/api_exception.dart';
import '../../../core/repositories/auth_repository.dart';

part 'auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  AuthCubit({required AuthRepository repository})
      : _repository = repository,
        super(const AuthInitial());

  final AuthRepository _repository;

  /// Checks whether a stored token can be used to reach the API.
  ///
  /// Emits [AuthAuthenticated] on success, [AuthUnauthenticated] if there is
  /// no token or if the server rejects it.
  Future<void> checkAuth() async {
    if (!_repository.hasToken) {
      emit(const AuthUnauthenticated());
      return;
    }
    emit(const AuthLoading());
    try {
      await _repository.getCurrentUser();
      emit(const AuthAuthenticated(isNewUser: false));
    } catch (_) {
      await _repository.clearTokens();
      emit(const AuthUnauthenticated());
    }
  }

  /// Authenticates with [email] and [password].
  Future<void> login(String email, String password) async {
    emit(const AuthLoading());
    try {
      await _repository.login(email, password);
      emit(const AuthAuthenticated(isNewUser: false));
    } on ApiException catch (e) {
      emit(AuthUnauthenticated(error: e.message));
    } catch (_) {
      emit(const AuthUnauthenticated(error: 'An unexpected error occurred.'));
    }
  }

  /// Registers a new account with [email] and [password].
  Future<void> register(String email, String password) async {
    emit(const AuthLoading());
    try {
      await _repository.register(email, password);
      emit(const AuthAuthenticated(isNewUser: true));
    } on ApiException catch (e) {
      emit(AuthUnauthenticated(error: e.message));
    } catch (_) {
      emit(const AuthUnauthenticated(error: 'An unexpected error occurred.'));
    }
  }

  /// Called when the user completes onboarding.
  ///
  /// Transitions from [AuthAuthenticated(isNewUser: true)] to
  /// [AuthAuthenticated(isNewUser: false)], causing the router to
  /// redirect to the digest.
  void completeOnboarding() {
    emit(const AuthAuthenticated(isNewUser: false));
  }

  /// Clears stored tokens and transitions to [AuthUnauthenticated].
  Future<void> logout() async {
    await _repository.clearTokens();
    emit(const AuthUnauthenticated());
  }
}
