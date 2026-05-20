import 'package:flutter/material.dart';

abstract final class AppTheme {
  // Deep navy seed — gives a neutral blue-grey Material 3 palette
  // that suits an editorial, information-dense product.
  static const _seed = Color(0xFF1A3050);

  static ThemeData get light => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: _seed,
          brightness: Brightness.light,
        ),
      );

  static ThemeData get dark => ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: _seed,
          brightness: Brightness.dark,
        ),
      );
}
