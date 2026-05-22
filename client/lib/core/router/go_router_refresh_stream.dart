import 'dart:async';

import 'package:flutter/foundation.dart';

/// Adapts a [Stream] to [ChangeNotifier] so go_router's [refreshListenable]
/// can re-evaluate the redirect guard whenever the stream emits.
class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    // Notify immediately so the router evaluates state on first render.
    notifyListeners();
    _subscription = stream.listen((_) => notifyListeners());
  }

  late final StreamSubscription<dynamic> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
