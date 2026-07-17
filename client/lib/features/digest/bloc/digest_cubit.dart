import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/models/digest_response.dart';
import '../../../core/repositories/digest_repository.dart';

part 'digest_state.dart';

class DigestCubit extends Cubit<DigestState> {
  DigestCubit({required DigestRepository repository})
      : _repository = repository,
        super(const DigestInitial());

  final DigestRepository _repository;

  Future<void> load() async {
    emit(const DigestLoading());
    await _fetch();
  }

  /// Called by pull-to-refresh — re-fetches without showing the full
  /// loading state so the existing content stays visible.
  Future<void> refresh() => _fetch();

  Future<void> _fetch() async {
    try {
      final digest = await _repository.getDigest();
      if (digest.isEmpty) {
        emit(const DigestEmpty());
      } else {
        emit(DigestLoaded(digest: digest));
      }
    } on Exception catch (e) {
      emit(DigestError(message: e.toString()));
    }
  }
}
