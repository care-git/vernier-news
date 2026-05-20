import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'endpoints.dart';

const _kAccessKey = 'access_token';
const _kRefreshKey = 'refresh_token';

class AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_kAccessKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      final refreshed = await _tryRefresh();
      if (refreshed) {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString(_kAccessKey);
        final opts = err.requestOptions;
        if (token != null) opts.headers['Authorization'] = 'Bearer $token';
        try {
          final retryDio = Dio(BaseOptions(baseUrl: Endpoints.baseUrl));
          final response = await retryDio.fetch(opts);
          return handler.resolve(response);
        } catch (_) {}
      }
    }
    handler.next(err);
  }

  Future<bool> _tryRefresh() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString(_kRefreshKey);
    if (refreshToken == null) return false;

    try {
      final dio = Dio(BaseOptions(baseUrl: Endpoints.baseUrl));
      final response = await dio.post<Map<String, dynamic>>(
        Endpoints.refresh,
        data: {'refresh_token': refreshToken},
      );
      final data = response.data!;
      await prefs.setString(_kAccessKey, data['access_token'] as String);
      await prefs.setString(_kRefreshKey, data['refresh_token'] as String);
      return true;
    } catch (_) {
      return false;
    }
  }
}
