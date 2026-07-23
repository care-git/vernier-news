import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/models/cluster_summary.dart';
import '../../../core/router/app_router.dart';
import '../../../core/widgets/spread_bar.dart';
import '../../auth/bloc/auth_cubit.dart';
import '../bloc/digest_cubit.dart';

class DigestScreen extends StatefulWidget {
  const DigestScreen({super.key});

  @override
  State<DigestScreen> createState() => _DigestScreenState();
}

class _DigestScreenState extends State<DigestScreen> {
  @override
  void initState() {
    super.initState();
    context.read<DigestCubit>().load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Vernier News'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_outlined),
            tooltip: 'Sign out',
            onPressed: () => sl<AuthCubit>().logout(),
          ),
        ],
      ),
      body: BlocBuilder<DigestCubit, DigestState>(
        builder: (context, state) {
          return switch (state) {
            DigestLoading() || DigestInitial() => const Center(
                child: CircularProgressIndicator(),
              ),
            DigestEmpty() => const _EmptyState(),
            DigestError(:final message) => _ErrorState(
                message: message,
                onRetry: () => context.read<DigestCubit>().load(),
              ),
            DigestLoaded(:final digest) => RefreshIndicator(
                onRefresh: () => context.read<DigestCubit>().refresh(),
                child: ListView.builder(
                  padding: const EdgeInsets.only(bottom: 24),
                  itemCount: _countItems(digest.categories),
                  itemBuilder: (context, index) =>
                      _buildItem(context, digest.categories, index),
                ),
              ),
          };
        },
      ),
    );
  }

  // Builds a flat list of category headers + cluster cards.
  // Each category contributes 1 header + N card items.
  int _countItems(Map<String, List<ClusterSummary>> categories) {
    return categories.entries.fold(
      0,
      (sum, e) => sum + 1 + e.value.length,
    );
  }

  Widget _buildItem(
    BuildContext context,
    Map<String, List<ClusterSummary>> categories,
    int index,
  ) {
    var remaining = index;
    for (final entry in categories.entries) {
      if (remaining == 0) {
        return _CategoryHeader(label: entry.key);
      }
      remaining--;
      if (remaining < entry.value.length) {
        return ClusterCard(cluster: entry.value[remaining]);
      }
      remaining -= entry.value.length;
    }
    return const SizedBox.shrink();
  }
}

// ─── Category header ─────────────────────────────────────────────────────────

class _CategoryHeader extends StatelessWidget {
  const _CategoryHeader({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              letterSpacing: 1.2,
            ),
      ),
    );
  }
}

// ─── Empty / error states ────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.inbox_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.outlineVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'Your digest is being prepared',
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Check back shortly — the data pipeline runs every few hours.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'Could not load your digest',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Try again'),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Cluster card ─────────────────────────────────────────────────────────────

class ClusterCard extends StatelessWidget {
  const ClusterCard({super.key, required this.cluster});

  final ClusterSummary cluster;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => context.push(AppRoute.cluster(cluster.id)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Headline
              Text(
                cluster.headline.isNotEmpty
                    ? cluster.headline
                    : 'Story #${cluster.id}',
                style: tt.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 10),

              // Meta row: sources + age
              Row(
                children: [
                  Icon(Icons.article_outlined, size: 14, color: cs.onSurfaceVariant),
                  const SizedBox(width: 4),
                  Text(
                    '${cluster.totalSourceCount} sources'
                    ' · ${cluster.independentSourceCount} independent',
                    style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                  ),
                  const Spacer(),
                  Text(
                    _relativeTime(cluster.lastUpdatedAt),
                    style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                  ),
                ],
              ),

              // Political spread bar
              if (cluster.politicalSpread != null) ...[
                const SizedBox(height: 10),
                SpreadBar(spread: cluster.politicalSpread!),
              ],

              // Countries
              if (cluster.countries.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  cluster.countries.join(' · '),
                  style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  String _relativeTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}
