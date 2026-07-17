import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/auth/bloc/auth_cubit.dart';
import '../../features/digest/bloc/digest_cubit.dart';
import '../../features/onboarding/bloc/onboarding_cubit.dart';
import '../api/api_client.dart';
import '../repositories/auth_repository.dart';
import '../repositories/digest_repository.dart';
import '../repositories/preferences_repository.dart';

final GetIt sl = GetIt.instance;

Future<void> configureDependencies() async {
  final prefs = await SharedPreferences.getInstance();
  sl.registerSingleton<SharedPreferences>(prefs);
  sl.registerLazySingleton<ApiClient>(ApiClient.new);
  sl.registerLazySingleton<AuthRepository>(
    () => AuthRepository(
      apiClient: sl<ApiClient>(),
      prefs: sl<SharedPreferences>(),
    ),
  );
  sl.registerLazySingleton<AuthCubit>(
    () => AuthCubit(repository: sl<AuthRepository>()),
  );
  sl.registerLazySingleton<PreferencesRepository>(
    () => PreferencesRepository(apiClient: sl<ApiClient>()),
  );
  sl.registerLazySingleton<OnboardingCubit>(
    () => OnboardingCubit(
      repository: sl<PreferencesRepository>(),
      authCubit: sl<AuthCubit>(),
    ),
  );
  sl.registerLazySingleton<DigestRepository>(
    () => DigestRepository(apiClient: sl<ApiClient>()),
  );
  sl.registerLazySingleton<DigestCubit>(
    () => DigestCubit(repository: sl<DigestRepository>()),
  );
}
