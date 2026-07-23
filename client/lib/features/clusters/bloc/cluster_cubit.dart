import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/models/cluster_detail.dart';
import '../../../core/repositories/cluster_repository.dart';

part 'cluster_state.dart';

class ClusterCubit extends Cubit<ClusterState> {
  ClusterCubit({required ClusterRepository repository})
    : _repository = repository,
      super(const ClusterInitial());

  final ClusterRepository _repository;

  Future<void> load(int id) async {
    emit(const ClusterLoading());
    try {
      final detail = await _repository.getCluster(id);
      emit(ClusterLoaded(detail: detail));
    } on Exception catch (e) {
      emit(ClusterError(message: e.toString()));
    }
  }
}
