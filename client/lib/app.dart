import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'core/di/injection.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/bloc/auth_cubit.dart';

class VernierApp extends StatefulWidget {
  const VernierApp({super.key});

  @override
  State<VernierApp> createState() => _VernierAppState();
}

class _VernierAppState extends State<VernierApp> {
  late final AuthCubit _authCubit;

  @override
  void initState() {
    super.initState();
    _authCubit = sl<AuthCubit>();
    _authCubit.checkAuth();
  }

  @override
  Widget build(BuildContext context) {
    // BlocProvider.value is used because the cubit is owned by get_it and
    // must not be closed when this widget is disposed.
    return BlocProvider.value(
      value: _authCubit,
      child: MaterialApp.router(
        title: 'Vernier News',
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: ThemeMode.system,
        routerConfig: AppRouter.router,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
