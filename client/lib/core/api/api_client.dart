import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'api_exception.dart';
import 'auth_interceptor.dart';
import 'endpoints.dart';

class ApiClient {
  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: Endpoints.baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 30),
        contentType: 'application/json',
      ),
    )..interceptors.add(AuthInterceptor());

    if (kDebugMode) {
      _dio.interceptors.add(
        LogInterceptor(requestBody: true, responseBody: true),
      );
    }
  }

  late final Dio _dio;

  Future<Map<String, dynamic>> get(String path) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(path);
      return response.data!;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Future<List<dynamic>> getList(String path) async {
    try {
      final response = await _dio.get<List<dynamic>>(path);
      return response.data!;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Future<Map<String, dynamic>> post(String path, {Object? body}) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(path, data: body);
      return response.data!;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  Future<Map<String, dynamic>> put(String path, {Object? body}) async {
    try {
      final response = await _dio.put<Map<String, dynamic>>(path, data: body);
      return response.data!;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  ApiException _mapError(DioException e) {
    final code = e.response?.statusCode ?? 0;
    final detail = e.response?.data;
    final message = detail is Map
        ? detail['detail']?.toString() ?? e.message ?? 'Unknown error'
        : e.message ?? 'Unknown error';
    return ApiException(statusCode: code, message: message);
  }
}
