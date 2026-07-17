part of 'digest_cubit.dart';

sealed class DigestState {
  const DigestState();
}

final class DigestInitial extends DigestState {
  const DigestInitial();
}

final class DigestLoading extends DigestState {
  const DigestLoading();
}

final class DigestLoaded extends DigestState {
  const DigestLoaded({required this.digest});

  final DigestResponse digest;
}

final class DigestEmpty extends DigestState {
  const DigestEmpty();
}

final class DigestError extends DigestState {
  const DigestError({required this.message});

  final String message;
}
