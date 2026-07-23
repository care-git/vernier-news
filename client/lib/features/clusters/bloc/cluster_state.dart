part of 'cluster_cubit.dart';

sealed class ClusterState {
  const ClusterState();
}

final class ClusterInitial extends ClusterState {
  const ClusterInitial();
}

final class ClusterLoading extends ClusterState {
  const ClusterLoading();
}

final class ClusterLoaded extends ClusterState {
  const ClusterLoaded({required this.detail});

  final ClusterDetail detail;
}

final class ClusterError extends ClusterState {
  const ClusterError({required this.message});

  final String message;
}
