import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../bloc/onboarding_cubit.dart';

// ─── Static data ─────────────────────────────────────────────────────────────

typedef _Option = ({
  String value,
  String label,
  String description,
  IconData icon,
});

const _purposes = <_Option>[
  (
    value: 'general',
    label: 'General reader',
    description: 'Stay informed on the topics I care about',
    icon: Icons.newspaper_outlined,
  ),
  (
    value: 'journalist',
    label: 'Journalist',
    description: 'Track stories and monitor media coverage',
    icon: Icons.edit_note_outlined,
  ),
  (
    value: 'researcher',
    label: 'Researcher',
    description: 'Analyse coverage patterns and source diversity',
    icon: Icons.manage_search_outlined,
  ),
  (
    value: 'analyst',
    label: 'Analyst',
    description: 'Follow markets, business and technology',
    icon: Icons.bar_chart_outlined,
  ),
];

const _categories = <({String slug, String label})>[
  (slug: 'politics', label: 'Politics'),
  (slug: 'business', label: 'Business'),
  (slug: 'technology', label: 'Technology'),
  (slug: 'science', label: 'Science'),
  (slug: 'health', label: 'Health'),
  (slug: 'environment', label: 'Environment'),
  (slug: 'world', label: 'World'),
  (slug: 'culture', label: 'Culture & Arts'),
  (slug: 'sport', label: 'Sport'),
];

const _depths = <_Option>[
  (
    value: 'brief',
    label: 'Brief',
    description: 'Key facts and headlines — fast to read',
    icon: Icons.flash_on_outlined,
  ),
  (
    value: 'standard',
    label: 'Standard',
    description: 'Balanced summaries with context',
    icon: Icons.article_outlined,
  ),
  (
    value: 'deep',
    label: 'Deep',
    description: 'Full analysis, sourcing detail and political spread',
    icon: Icons.library_books_outlined,
  ),
];

// Purpose → pre-selected category slugs shown on step 2.
const _purposeDefaults = <String, List<String>>{
  'general': [],
  'journalist': ['politics', 'world', 'business'],
  'researcher': ['science', 'technology', 'world'],
  'analyst': ['business', 'technology', 'science'],
};

// ─── Screen ──────────────────────────────────────────────────────────────────

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _pageController = PageController();
  int _page = 0;
  String _purpose = 'general';
  final Set<String> _interests = {};
  String _depth = 'standard';

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _selectPurpose(String purpose) {
    setState(() {
      _purpose = purpose;
      _interests
        ..clear()
        ..addAll(_purposeDefaults[purpose] ?? []);
    });
  }

  void _toggleInterest(String slug) {
    setState(() {
      if (_interests.contains(slug)) {
        _interests.remove(slug);
      } else {
        _interests.add(slug);
      }
    });
  }

  void _goTo(int page) => _pageController.animateToPage(
        page,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: BlocConsumer<OnboardingCubit, OnboardingState>(
        listener: (context, state) {
          if (state is OnboardingError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message)),
            );
          }
          // OnboardingComplete is handled by AuthCubit.completeOnboarding(),
          // which fires GoRouterRefreshStream and redirects to /digest.
        },
        builder: (context, state) {
          final isLoading = state is OnboardingLoading;
          return SafeArea(
            child: Column(
              children: [
                _StepDots(current: _page, total: 3),
                Expanded(
                  child: PageView(
                    controller: _pageController,
                    physics: const NeverScrollableScrollPhysics(),
                    onPageChanged: (i) => setState(() => _page = i),
                    children: [
                      _PurposePage(
                        selected: _purpose,
                        onSelected: _selectPurpose,
                      ),
                      _CategoriesPage(
                        selected: _interests,
                        onToggle: _toggleInterest,
                      ),
                      _DepthPage(
                        selected: _depth,
                        onSelected: (d) => setState(() => _depth = d),
                      ),
                    ],
                  ),
                ),
                _NavBar(
                  page: _page,
                  isLoading: isLoading,
                  onBack: _page > 0 ? () => _goTo(_page - 1) : null,
                  onNext: _page < 2 ? () => _goTo(_page + 1) : null,
                  onSubmit: _page == 2
                      ? () => context.read<OnboardingCubit>().submit(
                            purpose: _purpose,
                            interests: _interests.toList(),
                            depthPreference: _depth,
                          )
                      : null,
                  onSkip: () => context.read<OnboardingCubit>().skip(),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

// ─── Step dots ───────────────────────────────────────────────────────────────

class _StepDots extends StatelessWidget {
  const _StepDots({required this.current, required this.total});

  final int current;
  final int total;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(total, (i) {
          final active = i == current;
          return AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            margin: const EdgeInsets.symmetric(horizontal: 4),
            width: active ? 24 : 8,
            height: 8,
            decoration: BoxDecoration(
              color: active ? cs.primary : cs.outlineVariant,
              borderRadius: BorderRadius.circular(4),
            ),
          );
        }),
      ),
    );
  }
}

// ─── Page 1 — Purpose ────────────────────────────────────────────────────────

class _PurposePage extends StatelessWidget {
  const _PurposePage({required this.selected, required this.onSelected});

  final String selected;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return _PageShell(
      title: 'What brings you to Vernier?',
      subtitle: "We'll use this to suggest relevant coverage.",
      child: Column(
        children: _purposes
            .map(
              (p) => _SelectCard(
                label: p.label,
                description: p.description,
                icon: p.icon,
                selected: selected == p.value,
                onTap: () => onSelected(p.value),
              ),
            )
            .toList(),
      ),
    );
  }
}

// ─── Page 2 — Categories ─────────────────────────────────────────────────────

class _CategoriesPage extends StatelessWidget {
  const _CategoriesPage({required this.selected, required this.onToggle});

  final Set<String> selected;
  final ValueChanged<String> onToggle;

  @override
  Widget build(BuildContext context) {
    return _PageShell(
      title: 'Which topics interest you?',
      subtitle: 'Select all that apply. You can change this later.',
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: _categories
            .map(
              (c) => FilterChip(
                label: Text(c.label),
                selected: selected.contains(c.slug),
                onSelected: (_) => onToggle(c.slug),
              ),
            )
            .toList(),
      ),
    );
  }
}

// ─── Page 3 — Depth ──────────────────────────────────────────────────────────

class _DepthPage extends StatelessWidget {
  const _DepthPage({required this.selected, required this.onSelected});

  final String selected;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return _PageShell(
      title: 'How much detail do you want?',
      subtitle: 'You can adjust this any time in preferences.',
      child: Column(
        children: _depths
            .map(
              (d) => _SelectCard(
                label: d.label,
                description: d.description,
                icon: d.icon,
                selected: selected == d.value,
                onTap: () => onSelected(d.value),
              ),
            )
            .toList(),
      ),
    );
  }
}

// ─── Navigation bar ──────────────────────────────────────────────────────────

class _NavBar extends StatelessWidget {
  const _NavBar({
    required this.page,
    required this.isLoading,
    required this.onBack,
    required this.onNext,
    required this.onSubmit,
    required this.onSkip,
  });

  final int page;
  final bool isLoading;
  final VoidCallback? onBack;
  final VoidCallback? onNext;
  final VoidCallback? onSubmit;
  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    final isLastPage = page == 2;
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              if (onBack != null)
                Expanded(
                  child: OutlinedButton(
                    onPressed: isLoading ? null : onBack,
                    child: const Text('Back'),
                  ),
                ),
              if (onBack != null) const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: FilledButton(
                  onPressed: isLoading ? null : (isLastPage ? onSubmit : onNext),
                  child: isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(isLastPage ? 'Get started' : 'Continue'),
                ),
              ),
            ],
          ),
          if (isLastPage) ...[
            const SizedBox(height: 8),
            TextButton(
              onPressed: isLoading ? null : onSkip,
              child: const Text('Skip and use defaults'),
            ),
          ],
        ],
      ),
    );
  }
}

// ─── Shared widgets ──────────────────────────────────────────────────────────

class _PageShell extends StatelessWidget {
  const _PageShell({
    required this.title,
    required this.subtitle,
    required this.child,
  });

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 24),
            child,
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _SelectCard extends StatelessWidget {
  const _SelectCard({
    required this.label,
    required this.description,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final String description;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected ? cs.primaryContainer : cs.surfaceContainerLow,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? cs.primary : cs.outlineVariant,
            width: selected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: selected ? cs.primary : cs.onSurfaceVariant,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          color: selected ? cs.onPrimaryContainer : null,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  Text(
                    description,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: selected
                              ? cs.onPrimaryContainer
                              : cs.onSurfaceVariant,
                        ),
                  ),
                ],
              ),
            ),
            if (selected)
              Icon(Icons.check_circle, color: cs.primary, size: 20),
          ],
        ),
      ),
    );
  }
}
