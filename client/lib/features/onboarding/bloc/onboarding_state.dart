part of 'onboarding_cubit.dart';

sealed class OnboardingState {
  const OnboardingState();
}

final class OnboardingInitial extends OnboardingState {
  const OnboardingInitial();
}

final class OnboardingLoading extends OnboardingState {
  const OnboardingLoading();
}

final class OnboardingComplete extends OnboardingState {
  const OnboardingComplete();
}

final class OnboardingError extends OnboardingState {
  const OnboardingError({required this.message});

  final String message;
}
