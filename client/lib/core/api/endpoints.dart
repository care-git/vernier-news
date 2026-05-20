abstract final class Endpoints {
  // Pass --dart-define=API_BASE_URL=http://localhost:8000 for local dev.
  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://vernier.news',
  );

  static const _v1 = '/api/v1';

  static const register = '$_v1/auth/register';
  static const login = '$_v1/auth/login';
  static const refresh = '$_v1/auth/refresh';
  static const me = '$_v1/users/me';
  static const digest = '$_v1/digest/';
  static const clusters = '$_v1/clusters/';
  static const outlets = '$_v1/outlets/';

  static String cluster(int id) => '$_v1/clusters/$id';
  static String outlet(int id) => '$_v1/outlets/$id';
}
