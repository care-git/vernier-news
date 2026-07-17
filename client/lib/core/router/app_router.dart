import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/bloc/auth_cubit.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
<<<<<<< Updated upstream
import '../../features/digest/bloc/digest_cubit.dart';
import '../../features/digest/screens/digest_screen.dart';
=======
>>>>>>> Stashed changes
import '../../features/onboarding/bloc/onboarding_cubit.dart';
import '../../features/onboarding/screens/onboarding_screen.dart';
import '../di/injection.dart';
import 'go_router_refresh_stream.dart';

abstract final class AppRoute {
  static const login = '/login';
  static const register = '/register';
  static const onboarding = '/onboarding';
  static const digest = '/digest';
  static const preferences = '/preferences';

  // Route patterns — used in GoRouter path definitions.
  static const clusterPattern = '/cluster/:id';
  static const outletPattern = '/outlet/:domain';

  // Navigation helpers — used with context.go() / context.push().
  static String cluster(int id) => '/cluster/$id';
  static String outlet(String domain) => '/outlet/$domain';
}

abstract final class AppRouter {
  AppRouter._();

  static final router = GoRouter(
    initialLocation: AppRoute.digest,
    refreshListenable: GoRouterRefreshStream(sl<AuthCubit>().stream),
    redirect: _redirect,
    routes: [
      GoRoute(
        path: AppRoute.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: AppRoute.register,
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: AppRoute.onboarding,
        builder: (context, state) => BlocProvider.value(
          value: sl<OnboardingCubit>(),
          child: const OnboardingScreen(),
        ),
      ),
      GoRoute(
        path: AppRoute.digest,
        builder: (context, state) => BlocProvider.value(
          value: sl<DigestCubit>(),
          child: const DigestScreen(),
        ),
      ),
      GoRoute(
        path: AppRoute.clusterPattern,
        builder: (context, state) => _Placeholder(
          label: 'Cluster ${state.pathParameters['id']}',
        ),
      ),
      GoRoute(
        path: AppRoute.outletPattern,
        builder: (context, state) => _Placeholder(
          label: 'Outlet ${state.pathParameters['domain']}',
        ),
      ),
      GoRoute(
        path: AppRoute.preferences,
        builder: (context, state) => const _Placeholder(label: 'Preferences'),
      ),
    ],
  );

  static String? _redirect(BuildContext context, GoRouterState state) {
    final authState = sl<AuthCubit>().state;
    final path = state.uri.path;

    // Let the loading / initial states settle without redirecting.
    if (authState is AuthInitial || authState is AuthLoading) return null;

    final isAuthRoute =
        path == AppRoute.login || path == AppRoute.register;

    if (authState is AuthUnauthenticated) {
      // Send unauthenticated users to login, but leave them on auth routes.
      return isAuthRoute ? null : AppRoute.login;
    }

    if (authState is AuthAuthenticated) {
      if (authState.isNewUser) {
        // New users must complete onboarding — hold them there until done.
        return path == AppRoute.onboarding ? null : AppRoute.onboarding;
      }
      // Established users: redirect away from auth routes, root, and the
      // onboarding page (reached after completeOnboarding() fires).
      if (isAuthRoute || path == '/' || path == AppRoute.onboarding) {
        return AppRoute.digest;
      }
    }

    return null;
  }
}

class _Placeholder extends StatelessWidget {
  const _Placeholder({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text(label, style: Theme.of(context).textTheme.headlineMedium),
      ),
    );
  }
}
