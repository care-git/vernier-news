import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/repositories/preferences_repository.dart';
import '../../auth/bloc/auth_cubit.dart';

part 'onboarding_state.dart';

class OnboardingCubit extends Cubit<OnboardingState> {
  OnboardingCubit({
    required PreferencesRepository repository,
    required AuthCubit authCubit,
  })  : _repository = repository,
        _authCubit = authCubit,
        super(const OnboardingInitial());

  final PreferencesRepository _repository;
  final AuthCubit _authCubit;

  /// Saves preferences then signals the auth cubit to leave onboarding.
  Future<void> submit({
    required String purpose,
    required List<String> interests,
    required String depthPreference,
  }) async {
    emit(const OnboardingLoading());
    try {
      await _repository.updatePreferences(
        purpose: purpose,
        interests: interests,
        depthPreference: depthPreference,
      );
      emit(const OnboardingComplete());
      _authCubit.completeOnboarding();
    } on Exception catch (e) {
      emit(OnboardingError(message: e.toString()));
    }
  }

  /// Saves default preferences and skips to the digest.
  Future<void> skip() => submit(
        purpose: 'general',
        interests: [],
        depthPreference: 'standard',
      );
}
