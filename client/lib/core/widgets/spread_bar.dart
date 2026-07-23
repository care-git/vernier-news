import 'package:flutter/material.dart';

import '../models/cluster_summary.dart';

/// Horizontal bar showing a cluster's political coverage range (min→max shaded)
/// with a mean marker, normalised from the [-1, 1] leaning scale to [0, 1].
///
/// Deliberately colour-agnostic: the track and marker use theme-neutral colours
/// rather than partisan red/blue, consistent with the platform's agnosticism.
class SpreadBar extends StatelessWidget {
  const SpreadBar({super.key, required this.spread});

  final PoliticalSpread spread;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    final minFrac = ((spread.min + 1) / 2).clamp(0.0, 1.0);
    final maxFrac = ((spread.max + 1) / 2).clamp(0.0, 1.0);
    final meanFrac = ((spread.mean + 1) / 2).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'L',
              style: Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: cs.onSurfaceVariant),
            ),
            Text(
              'Political spread',
              style: Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: cs.onSurfaceVariant),
            ),
            Text(
              'R',
              style: Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: cs.onSurfaceVariant),
            ),
          ],
        ),
        const SizedBox(height: 4),
        LayoutBuilder(
          builder: (context, constraints) {
            final w = constraints.maxWidth;
            return SizedBox(
              height: 8,
              child: Stack(
                children: [
                  // Track
                  Container(
                    height: 8,
                    decoration: BoxDecoration(
                      color: cs.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  // Coverage range
                  Positioned(
                    left: minFrac * w,
                    width: (maxFrac - minFrac) * w,
                    top: 0,
                    bottom: 0,
                    child: Container(
                      decoration: BoxDecoration(
                        color: cs.primary.withValues(alpha: 0.3),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ),
                  // Mean marker
                  Positioned(
                    left: (meanFrac * w - 2).clamp(0, w - 4),
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
              ),
            );
          },
        ),
      ],
    );
  }
}
