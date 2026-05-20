import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

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
    redirect: (context, state) {
      if (state.uri.path == '/') return AppRoute.digest;
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoute.login,
        builder: (context, state) => const _Placeholder(label: 'Login'),
      ),
      GoRoute(
        path: AppRoute.register,
        builder: (context, state) => const _Placeholder(label: 'Register'),
      ),
      GoRoute(
        path: AppRoute.onboarding,
        builder: (context, state) => const _Placeholder(label: 'Onboarding'),
      ),
      GoRoute(
        path: AppRoute.digest,
        builder: (context, state) => const _Placeholder(label: 'Digest'),
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
