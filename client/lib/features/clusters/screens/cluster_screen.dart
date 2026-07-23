import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/models/cluster_detail.dart';
import '../../../core/widgets/spread_bar.dart';
import '../bloc/cluster_cubit.dart';

class ClusterScreen extends StatelessWidget {
  const ClusterScreen({super.key, required this.clusterId});

  final int clusterId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Story')),
      body: BlocBuilder<ClusterCubit, ClusterState>(
        builder: (context, state) {
          return switch (state) {
            ClusterInitial() || ClusterLoading() => const Center(
              child: CircularProgressIndicator(),
            ),
            ClusterError(:final message) => _ErrorState(
              message: message,
              onRetry: () => context.read<ClusterCubit>().load(clusterId),
            ),
            ClusterLoaded(:final detail) => _ClusterContent(detail: detail),
          };
        },
      ),
    );
  }
}

// ─── Loaded content ───────────────────────────────────────────────────────────

class _ClusterContent extends StatelessWidget {
  const _ClusterContent({required this.detail});

  final ClusterDetail detail;

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final cs = Theme.of(context).colorScheme;

    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                detail.headline.isNotEmpty
                    ? detail.headline
                    : 'Story #${detail.id}',
                style: tt.titleLarge?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 12,
                runSpacing: 4,
                children: [
                  _MetaChip(
                    icon: Icons.article_outlined,
                    label: '${detail.totalSourceCount} sources',
                  ),
                  _MetaChip(
                    icon: Icons.hub_outlined,
                    label: '${detail.independentSourceCount} independent',
                  ),
                  if (detail.category != null)
                    _MetaChip(
                      icon: Icons.label_outline,
                      label: detail.category!,
                    ),
                ],
              ),
              if (detail.politicalSpread != null) ...[
                const SizedBox(height: 16),
                SpreadBar(spread: detail.politicalSpread!),
              ],
            ],
          ),
        ),
        if (detail.countryCounts.isNotEmpty)
          _CoverageSection(counts: detail.countryCounts),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
          child: Text(
            'Sources (${detail.sources.length})',
            style: tt.labelLarge?.copyWith(
              color: cs.primary,
              letterSpacing: 1.2,
            ),
          ),
        ),
        if (detail.sources.isEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Text(
              'Individual sources are not available for this story yet.',
              style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
            ),
          )
        else
          ...detail.sources.map((s) => _SourceTile(source: s)),
      ],
    );
  }
}

// ─── Coverage (geographic spread) ─────────────────────────────────────────────

class _CoverageSection extends StatelessWidget {
  const _CoverageSection({required this.counts});

  final List<CountryCount> counts;

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final cs = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'COVERAGE',
            style: tt.labelLarge?.copyWith(
              color: cs.primary,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final c in counts)
                Chip(
                  visualDensity: VisualDensity.compact,
                  label: Text('${_flag(c.country)}  ${c.country} · ${c.count}'),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── Source row ───────────────────────────────────────────────────────────────

class _SourceTile extends StatelessWidget {
  const _SourceTile({required this.source});

  final ClusterSource source;

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final cs = Theme.of(context).colorScheme;
    final o = source.outlet;

    return ListTile(
      onTap: () => _showOutletCard(context, source),
      isThreeLine: true,
      title: Row(
        children: [
          Expanded(
            child: Text(
              o.name,
              style: tt.titleSmall?.copyWith(fontWeight: FontWeight.w600),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (o.country != null) ...[
            const SizedBox(width: 8),
            Text(_flag(o.country!), style: tt.bodyMedium),
          ],
        ],
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 2),
          Text(
            source.title,
            style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              _MiniLeaning(leaning: o.politicalLeaningLr),
              if (source.publishedAt != null) ...[
                const SizedBox(width: 8),
                Text(
                  _relativeTime(source.publishedAt!),
                  style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
                ),
              ],
              const Spacer(),
              if (source.wireTier != null && source.wireTier! <= 1)
                const _Badge(label: 'wire'),
            ],
          ),
        ],
      ),
      trailing: const Icon(Icons.chevron_right),
    );
  }
}

// ─── Outlet inline card (bottom sheet) ────────────────────────────────────────

void _showOutletCard(BuildContext context, ClusterSource source) {
  showModalBottomSheet<void>(
    context: context,
    showDragHandle: true,
    builder: (_) => _OutletCard(source: source),
  );
}

class _OutletCard extends StatelessWidget {
  const _OutletCard({required this.source});

  final ClusterSource source;

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final cs = Theme.of(context).colorScheme;
    final o = source.outlet;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              o.name,
              style: tt.titleLarge?.copyWith(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 2),
            Text(
              o.domain,
              style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant),
            ),
            const SizedBox(height: 16),
            _InfoRow(
              icon: Icons.public,
              label: 'Country',
              value: o.country != null
                  ? '${_flag(o.country!)}  ${o.country}'
                  : 'Unknown',
            ),
            if (o.parentOrgName != null)
              _InfoRow(
                icon: Icons.account_tree_outlined,
                label: 'Parent organisation',
                value: o.parentOrgName!,
              ),
            _InfoRow(
              icon: Icons.balance_outlined,
              label: 'Political leaning',
              valueWidget: Row(
                children: [
                  _MiniLeaning(leaning: o.politicalLeaningLr),
                  const SizedBox(width: 8),
                  Text(
                    _leaningLabel(o.politicalLeaningLr),
                    style: tt.bodyMedium,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text(source.title, style: tt.bodyMedium),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () => _openArticle(context, source.url),
                icon: const Icon(Icons.open_in_new),
                label: const Text('Read original article'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    this.value,
    this.valueWidget,
  });

  final IconData icon;
  final String label;
  final String? value;
  final Widget? valueWidget;

  @override
  Widget build(BuildContext context) {
    final tt = Theme.of(context).textTheme;
    final cs = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: cs.onSurfaceVariant),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
                ),
                const SizedBox(height: 2),
                valueWidget ?? Text(value ?? '', style: tt.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

Future<void> _openArticle(BuildContext context, String url) async {
  final messenger = ScaffoldMessenger.of(context);
  final uri = Uri.tryParse(url);
  if (uri == null) {
    messenger.showSnackBar(
      const SnackBar(content: Text('Invalid article link')),
    );
    return;
  }
  final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
  if (!ok) {
    messenger.showSnackBar(
      const SnackBar(content: Text('Could not open the article')),
    );
  }
}

// ─── Small building blocks ────────────────────────────────────────────────────

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: cs.onSurfaceVariant),
        const SizedBox(width: 4),
        Text(label, style: tt.bodySmall?.copyWith(color: cs.onSurfaceVariant)),
      ],
    );
  }
}

/// Compact position marker on the L–R scale — colour-agnostic (theme neutral),
/// matching [SpreadBar]. Shows a dash when the leaning is unknown.
class _MiniLeaning extends StatelessWidget {
  const _MiniLeaning({required this.leaning});

  final double? leaning;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    if (leaning == null) {
      return Text(
        '—',
        style: Theme.of(
          context,
        ).textTheme.labelSmall?.copyWith(color: cs.onSurfaceVariant),
      );
    }
    final frac = ((leaning! + 1) / 2).clamp(0.0, 1.0);
    return SizedBox(
      width: 44,
      height: 8,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final w = constraints.maxWidth;
          return Stack(
            children: [
              Container(
                decoration: BoxDecoration(
                  color: cs.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              Positioned(
                left: (frac * w - 2).clamp(0, w - 4),
                top: 0,
                bottom: 0,
                child: Container(
                  width: 4,
                  decoration: BoxDecoration(
                    color: cs.primary,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: cs.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: tt.labelSmall?.copyWith(color: cs.onSurfaceVariant),
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
              'Could not load this story',
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

// ─── Helpers ──────────────────────────────────────────────────────────────────

/// Convert an ISO 3166-1 alpha-2 country code to its flag emoji.
String _flag(String code) {
  if (code.length != 2) return code;
  final upper = code.toUpperCase();
  return String.fromCharCodes(upper.codeUnits.map((c) => 0x1F1E6 + (c - 0x41)));
}

/// Descriptive label for a seeded left/right leaning value on the [-1, 1] scale.
String _leaningLabel(double? leaning) {
  if (leaning == null) return 'Not available';
  final v = leaning.toStringAsFixed(2);
  if (leaning <= -0.6) return 'Left ($v)';
  if (leaning <= -0.2) return 'Centre-left ($v)';
  if (leaning < 0.2) return 'Centre ($v)';
  if (leaning < 0.6) return 'Centre-right ($v)';
  return 'Right ($v)';
}

String _relativeTime(DateTime dt) {
  final diff = DateTime.now().difference(dt);
  if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
  if (diff.inHours < 24) return '${diff.inHours}h ago';
  return '${diff.inDays}d ago';
}
