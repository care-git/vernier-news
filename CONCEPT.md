# Concept Document — Vernier News

### A Richly Textured Information Landscape Platform

*Working Document — v0.4 — May 2026*

---

## 1\. Vision & Mission

### What this is

This project is not a news aggregator. News aggregators collect and present news. This platform maps the entire terrain of how events are being reported — by whom, from what position, with what relationships and interests, with what coverage patterns, and across what geographic and political contexts. The news is raw material. The product is clarity about the news.

The closest analogies in existence are all partial. Ground News surfaces political bias per story. Palantir performs deep graph analysis but operates on closed datasets at enormous cost. Media Cloud offers academic-grade media analysis with poor accessibility. The Bloomberg Terminal provides financial news depth but is expensive, siloed, and not transparency-focused. None combine genuine depth with genuine accessibility. None are built around editorial agnosticism as a structural principle rather than a marketing claim. None give the user the full information landscape and trust them to draw their own conclusions.

### Mission statement

To give every person — regardless of technical ability, background, or means — access to the most complete, transparent, and unbiased view of the global information landscape currently possible, so that they can form their own understanding of events without being dependent on the editorial choices of any single outlet, organisation, or algorithm.

### What we are not

We are not reporters. We do not editorially assess the truthfulness of any claim. We do not make inferences about outcomes or intentions. We do not tell users what to think. We surface the full landscape of what is being reported, by whom, under what structural conditions, and let users navigate that landscape with the best available tools. The platform is the map, not the guide.

---

## 2\. Core Principles

These principles are not marketing language. They are structural constraints that govern every design and product decision.

**Agnosticism.** The platform takes no editorial position on any story, political question, or factual dispute. Every design choice — from which sources are included, to how visualisations are framed, to what categories exist — must be interrogated for implicit editorial bias. Where bias is unavoidable, it must be acknowledged publicly.

**Transparency about the assessor.** A platform built for transparency about the news must be equally transparent about itself. The methodology behind every analysis — political leaning calculations, feature analysis dimensions, clustering algorithms, influence graph construction — must be fully documented and publicly readable. Users should be able to assess the platform with the same rigour they use to assess the sources it analyses.

**Progressive depth without compromise.** A casual user checking a morning digest and a government analyst running a deep provenance query deserve equal quality of experience. The surface layer and the deep research layer must be independently excellent. Simplifying the surface must never mean removing depth from the product. Depth must never make the surface inaccessible.

**Factual grounding only.** Every data point presented to users must be traceable to a documented, verifiable source. The platform does not infer, speculate, or model outcomes. Stakeholder relationships are presented because they are documented, not because they are suspected. Political leaning is calculated from measurable textual and behavioural signals, not assigned editorially.

**Open source by necessity.** A platform that calculates political leanings, assesses source independence, and maps media ownership cannot ask users to trust a black box. The code must be open. The methodology must be open. The data generation process must be auditable. This is not a commercial sacrifice — it is the condition of the platform's credibility.

**Equal access across use cases.** No tier of user should receive a degraded experience. No platform version is secondary. The free tier is not a crippled version of the paid tier — it is a differently scoped version of the same complete product. The CLI is not a reduced version of the GUI — it is the same product without visual rendering. Enterprise depth does not come at the expense of personal accessibility.

**Universal citation.** Every data point in the platform — every article, every relationship in the influence graph, every entry in an entity profile, every stakeholder interest — must be sourced to a verifiable, documented origin. If it cannot be sourced, it is not included.

---

## 3\. Data Collection Architecture

### Philosophy of collection

The goal is the most comprehensive legally compliant collection of news and information currently achievable. Breadth is a core product value — a story covered only by three sources tells the user something. A story covered by three hundred sources, half of which share a parent company, tells them something very different. Volume enables the platform's analytical capabilities.

All collection respects `robots.txt` directives, crawl delay specifications, and terms of service. The platform identifies itself honestly in its user-agent string. Every collected item retains full citation metadata — source, author, URL, timestamp, collection method — from the moment of ingestion. Nothing enters the platform without a traceable origin.

### Layer 1 — Structured feeds (primary)

RSS and Atom feeds form the foundation. The majority of news publishers maintain feeds specifically designed for aggregation. A curated and continuously expanded OPML library targeting thousands of sources across categories, languages, and geographic regions provides the bulk of collection with zero scraping concerns.

Supplementing this: The Guardian API (full article text, generous free tier), GNews API, Currents API, and the New York Times and BBC developer APIs. Each provides structured, well-formed data with clear licensing for personal and research use. NewsAPI.org (~150,000 source index) is introduced in Phase 4 once commercial API terms can be funded — its free tier explicitly prohibits commercial use.

### Layer 2 — Specialist datasets

**GDELT Project** — near real-time global news monitoring covering sources in over 100 languages, fully free, already structured. Particularly valuable for non-English and regional coverage that Western-centric feeds miss.

**Reddit** — r/worldnews, r/politics, r/technology, r/science, and hundreds of niche and regional subreddits surface smaller publications, regional press, and community-flagged stories that never appear in mainstream aggregators. Reddit's API provides structured access. Reddit content is treated as a signal pointing to source articles, not as a primary source itself.

**Hacker News API** — invaluable for technology, science, and policy stories. The community curation surfaces high-signal content from sources that don't maintain RSS feeds.

**Academic and institutional sources** — arXiv, PubMed, SSRN, and institutional press release feeds provide primary-source scientific and policy content that rarely surfaces in news aggregation but is frequently the origin of major stories.

**Government and official sources** — Hansard, congressional records, official government press release feeds, court filings, and regulatory announcements. These are primary sources that most aggregators ignore entirely but are often the root node in a story's provenance chain.

**Podcast and long-form** — Podcast RSS feeds, particularly for investigative journalism podcasts, add a dimension no mainstream aggregator touches. Transcripts are obtained via two routes, both maintaining a clean primary-source citation chain: (1) the Podcasting 2.0 transcript namespace — when a podcast includes a transcript file (SRT, WebVTT, or HTML) in its RSS feed, it is the creator's own published document and is ingested directly at no cost; (2) for high-value investigative journalism podcasts where no transcript is provided, transcripts are generated locally using Whisper (open source, self-hosted as a Celery background job) from the original audio, cited explicitly as generated rather than publisher-supplied. Third-party transcript services that independently process and re-host audio are not used as citation sources — they introduce an intermediary into the provenance chain that is not a primary source.

**Newsletter and Substack feeds** — Independent journalists publishing via Substack, Ghost, and similar platforms often produce the most independent reporting. RSS feeds are available for most and are treated as full source-level entries in the platform.

### Layer 3 — Institutional social media sources

Social media is included as a source layer, with a strict scope constraint: only accounts operated by organisations, companies, government bodies, verified journalists publishing primary-source reporting, and newsletters qualify for inclusion. Individual commentary and opinion — regardless of follower count or verification status — is excluded. The purpose is to capture official statements, breaking institutional announcements, and primary-source reporting published in social formats, not to aggregate public discourse.

Platforms covered: Bluesky (open API, increasingly significant for breaking journalism) and Mastodon (decentralised, open API, strong journalist presence) from Phase 4. LinkedIn (corporate and institutional announcements) and X/Twitter are both deferred to Phase 5/6. LinkedIn requires advance application to the LinkedIn Partner Program or Marketing Developer Platform before API access is granted — this application process has no guaranteed timeline and must be initiated during Phase 4 to be ready for Phase 5. X/Twitter API costs have increased substantially and require a cost-justified commercial evaluation before integration. Each social entry carries full citation: account name, platform, timestamp, follower context where available, and account category (government, media organisation, journalist, NGO, corporation, or official body).

Social sources are particularly valuable for primary announcements that precede formal press releases, for journalists publishing thread-form investigative reporting, and for official government communications in regions where press access is limited.

### Layer 4 — Polite scraping

For sources not covered by feeds or APIs, a Scrapy-based crawler with full `robots.txt` compliance, randomised delays, honest user-agent identification, and Playwright/Playwright-stealth for JavaScript-rendered pages. This layer is explicitly tertiary and supplements rather than replaces the feed and specialist dataset layers.

### OpenClaw integration

OpenClaw (formerly Clawdbot) is a self-hosted messaging gateway that connects chat applications to AI agents via a custom AgentSkills system. It is not the pipeline orchestration layer — Celery and Celery Beat own all scheduled and background jobs. OpenClaw's role in this platform is as the developer-facing monitoring and control interface: custom skills (each a `SKILL.md` file) expose pipeline operations and system state through a preferred chat channel, allowing the developer to trigger ingestion runs, review health metrics, query clustering stats, and manage the source library conversationally without logging into the VPS.

OpenClaw is model-agnostic and can route agent requests to cloud LLMs (Claude, GPT) or fully local Ollama models depending on the task, cost, and privacy requirements. The skills themselves are lightweight wrappers over the FastAPI backend and Celery task queue — OpenClaw surfaces the platform's operational state; the platform's own infrastructure does the work.

### Collection scope target

Combining all layers, a realistic collection scope is tens of thousands of sources across all languages and regions, updated continuously. This meaningfully exceeds any commercial aggregator's coverage, particularly for regional, non-English, independent, and institutional sources.

---

## 4\. Information Processing Pipeline

### Stage 1 — Ingestion and normalisation

All collected items pass through a normalisation layer: HTML stripping, encoding normalisation, metadata extraction (author, publication date, outlet, URL, language, collection source), and language detection. Items are stored with full provenance metadata intact from the point of ingestion. Citation chain is established at this stage and is immutable — the origin of any piece of data can always be traced.

### Stage 2 — Deduplication vs. clustering (the critical distinction)

**Deduplication** identifies the same article republished across multiple outlets (wire copy syndication). These are collapsed into a single record with a list of syndication destinations — they represent one piece of reporting, not multiple.

**Clustering** identifies different articles about the same event or story. These are preserved as distinct records and grouped — they represent multiple independent perspectives on the same subject, which is the core value unit of the platform.

The distinction is made through a combination of: semantic similarity scoring (sentence-transformer embeddings, cosine similarity), named entity overlap (people, places, organisations, dates extracted via spaCy), temporal proximity, and textual independence scoring (high similarity \+ simultaneous publication \= likely wire copy; lower similarity \+ temporal spread \= likely independent coverage).

### Stage 3 — Story clustering

Articles that pass the deduplication check and share entity overlap and semantic similarity above threshold are grouped into story clusters. Clusters are dynamic — they grow as new coverage arrives, decay in prominence as coverage slows, and can merge if two initially separate story threads converge.

A cluster's metadata includes: first published timestamp, most recent update, total source count, independent source count (adjusted for ownership and textual overlap), geographic coverage spread, language coverage spread, and a provenance chain linking back to the earliest identifiable origin.

### Stage 4 — Categorisation

Separate from clustering, each article is independently categorised. Two-layer taxonomy: broad categories (World, Politics, Technology, Science, Business, Health, Environment, Culture, Sport, and others) with user-definable sub-niches beneath them. A user can follow "AI regulation" as a niche that surfaces across both Technology and Politics without being forced to follow either category wholesale.

Categorisation uses a locally-run LLM (via Ollama) for classification — a cheap inference task that small models handle reliably. Categories are not mutually exclusive; a single story can and often should appear in multiple categories.

### Stage 5 — Entity extraction and linking

Named entities (people, organisations, companies, governments, geographic locations) are extracted from every article using spaCy's NER pipeline. Extracted entities are linked to the platform's entity knowledge graph via Wikidata entity resolution — not just tagged, but connected to persistent entity profiles that accumulate information across all stories over time. The resolution methodology is detailed in Section 10\.

### Stage 6 — Feature analysis computation

Runs on a daily cycle (detailed in Section 5). Updates source, author, and organisation feature profiles based on the previous 24 hours of data.

### Stage 7 — Translation and language processing

Translation is on-demand from Phase 4: articles are translated when a user views them, not at ingest. The translated version is cached permanently on first generation; the original is always retained alongside it. This stage therefore does not sit in the ingest pipeline — it is triggered at read time and is transparent to all upstream processing stages (clustering, entity extraction, feature analysis) which operate on original-language text.

The translation engine is OPUS-MT (Helsinki-NLP, self-hosted) from Phase 4 launch, replaced by DeepL API in Phase 5 once revenue supports the cost. Translation confidence metadata accompanies every translated article. Full pipeline detail is in Section 13.

### Stage 8 — Pre-computation and caching

All data that casual users will see — daily digests, story cluster summaries, category feeds, surface-level visualisations — is pre-computed on a rolling basis and cached. This means the surface layer always responds with near-zero latency regardless of the depth of data beneath it. The analytical layer (deep graph queries, historical research, provenance chains) hits the full database on demand and operates asynchronously where needed.

---

## 5\. Feature Analysis System

### Naming and framing

The system is explicitly called **Feature Analysis**, not reputation scoring, credibility rating, or trustworthiness assessment. It presents documented, measurable attributes of outlets, authors, and organisations — contributing factors the user can weigh themselves. The platform makes no judgement about whether any source is "good" or "reliable." This framing is both philosophically consistent with the mission and legally important. The platform presents facts; conclusions belong to the user.

Feature analysis operates at three distinct levels: **outlet-level**, **author-level**, and **organisation-level**. These are deliberately separate because a credible outlet can publish weak articles, a credible journalist can work for a biased outlet, and a credible parent organisation can own outlets with radically different editorial practices.

### The independence problem — correcting naive cross-citation

The most important methodological decision in the feature analysis system is that citation counts do not equal independent confirmation. Apparent consensus can be manufactured through several mechanisms:

**Ownership consolidation** — outlets sharing a parent company represent one editorial voice, not many. The ownership graph (detailed in Section 7\) is used to weight citations from related outlets as a fraction of a fully independent citation.

**Wire copy propagation** — sixty outlets publishing the same AP report within thirty minutes is one source, not sixty. Detected via a four-tier system at ingest: known wire service outlets (AP, Reuters, AFP, and equivalents) are flagged at source level; high-confidence wire copies are identified by embedding similarity above 0.88 within a 6-hour window; probable wire copies are identified by similarity 0.70–0.88 combined with temporal or byline signals; suspected copies enter a calibration review queue. Tiers 0 and 1 are collapsed to a single record with a syndication list; Tiers 2 and 3 contribute fractional independent source weights rather than counting as zero or full. All thresholds are stored in a settings table and tuned empirically against the live corpus.

**Single primary source chains** — forty articles all citing the same government press release or think-tank report are not independently confirming anything. NLP extraction of cited primary sources within article bodies identifies when apparent corroboration traces to a single origin. When this is detected, it is surfaced to the user as a signal, not hidden.

**Publication timing** — genuine independent corroboration takes time and looks textually different. Simultaneous publication of semantically similar articles \= wire propagation. Temporally spaced publication of textually divergent articles citing different primary sources \= genuine independent corroboration. Both the temporal gap and textual divergence score feed into the independence quality weight of each citation.

An independent citation is therefore scored across four axes: ownership separation, textual divergence, temporal spacing, and primary source diversity. Citations that fail multiple axes contribute a fractional weight.

### Outlet-level feature dimensions

**Textual independence score** — across all articles in the outlet's corpus, how often does it publish content that is genuinely independent (low similarity, temporally spaced, different primary sources) versus wire propagation or near-copies?

**Ownership and affiliation transparency** — documented parent company, known investors, advertising relationships where disclosed, government contracts where documented. Presented as facts, not assessments.

**Correction and retraction record** — frequency of issued corrections relative to publication volume, frequency of retractions, average time-to-correction, and whether corrections are prominently displayed or buried. Outlets that correct themselves are recorded differently from outlets that quietly delete or alter without acknowledgement.

**Original reporting ratio** — what proportion of articles represent original reporting (first to publish on an event, cite primary sources not appearing in prior coverage) versus republication or commentary on others' reporting?

**Vindication signal** — stories published by this outlet that initially had few corroborating sources but later accumulated wide corroboration. The "early and right" pattern. Computed over the outlet's full historical corpus and updated continuously.

**Contrarian vindication** — the most powerful and rarest signal. Stories where this outlet's reporting contradicted prevailing multi-source consensus at the time of publication, and where subsequent developments confirmed the outlet's version. This directly surfaces outlets that push back against coordinated narratives and are later proved correct.

**Coverage breadth** — what proportion of the outlet's output is original versus syndicated, what categories it covers, what geographic areas it focuses on.

**Primary source citation rate** — how frequently do articles cite specific documents, named individuals, data sets, or verifiable records versus relying on anonymous or unspecified sourcing?

**Peer-normalised consistency** — outlets are grouped into peer cohorts by reach and publication volume. Consistency scores are calculated within peer groups before normalisation, preventing large outlets from automatically outscoring small ones on volume-dependent metrics. This is a deliberate design choice: independent and smaller outlets are not penalised for their size on signals that are fundamentally proxies for reach rather than quality.

### Author-level feature dimensions

Author profiles are independent of outlet profiles and persist as journalists move between publications. Dimensions include: publication history across outlets, correction record, original reporting track record, affiliation history, known subject matter areas, political leaning signal from written work (see Section 6), and vindication signal from their bylined work. When reading any article, the user can see both the outlet's feature profile and the specific author's independent profile — these may differ significantly. A journalist's history does not reset when they change employer.

### Organisation-level feature dimensions

Parent companies and media ownership entities have their own profiles: known subsidiaries, documented financial relationships, political donation records where public, government contract relationships, advertising revenue dependencies where disclosed, lobbying activity where documented. These profiles feed directly into the influence graph (Section 7).

### Display model

Feature analysis is displayed as a multi-dimensional fingerprint rather than a single score. A set of labelled axes presented visually, showing the measurable dimensions without collapsing them into a number that implies false precision. The user sees what is documented about a source, not a verdict on it. Every data point in the fingerprint links to its source citation — the user can follow any claim back to the document that substantiates it.

---

## 6\. Political Leaning Analysis

### Why content-based, not self-reported

Self-reported political positioning is unreliable. Outlets have commercial incentives to appear more centrist than they are, or more oppositional than they are, depending on their audience. The platform calculates political leaning from measurable signals in the content itself, making the calculation auditable rather than editorial.

### Surface layer — familiar left/right spectrum

The default display for casual users is the familiar left-right spectrum, because most people have an intuitive grasp of it even if they acknowledge its limitations. This is a conscious accessibility decision. It is the entry point, not the conclusion. Users who want nothing more than a quick orientation to a source's general position can get it here without being asked to engage with political science.

### Deep layer — multi-axis model

One tap or click below the surface reveals the multi-axis breakdown: economic axis (interventionist to laissez-faire), social axis (progressive to conservative), institutional axis (establishment to anti-establishment). These three axes capture meaningful political variation that the left/right spectrum collapses. An outlet can be economically left and socially conservative. A publication can be strongly anti-establishment while holding economically centrist views. These distinctions matter and the platform surfaces them for users who want them.

### Cultural contextualisation

Left/right as a political frame is primarily a Western, and often specifically American, construct. Applied globally it becomes actively misleading — political landscapes in India, Brazil, Hungary, Japan, or West Africa do not map onto it cleanly. The multi-axis model is therefore culturally contextualised: what the axes mean, and how they are calibrated, adjusts based on the regional political context of the source. This is technically more complex but is the honest version of the feature. The surface left/right display for international sources is labelled clearly as a simplified approximation, with the contextualised multi-axis view always accessible one layer down.

### Calculation signals

Political leaning is calculated from: word embedding analysis (political language carries measurable distributional patterns), entity framing analysis (how are specific political figures, institutions, and policies described — language choices around the same entities differ measurably across the spectrum), comparative framing (how does this outlet's coverage of the same event compare to the distributional average of all coverage?), citation network analysis (what sources does this outlet treat as authoritative?), and historical consistency of these signals over time.

### Three separate leaning indicators per article

When reading any article: the political leaning signal for the **original article's author** (if the article is a reprint or response to prior reporting), the political leaning signal for the **current article's author**, and the political leaning signal for the **publishing outlet**. These three can and often do differ, and showing all three is more informative than collapsing them into one.

### Methodology transparency

The full calculation methodology is publicly documented. This is non-negotiable. A political leaning calculation that cannot be audited is itself a form of editorial power, which is precisely what this platform exists to counter.

---

## 7\. Visualisation Layer

### The unified influence graph

All relationship data — ownership, editorial partnerships, wire service subscriptions, funding sources, citation patterns, shared board memberships where documented — exists in a single graph model. Ownership graphs, echo chamber visualisations, and citation networks are not separate tools but different filtered views of the same underlying graph.

The graph is rendered in an Obsidian-style interactive network view. Nodes are outlets, authors, organisations, and entities. Edges represent documented relationships, colour-coded and weighted by relationship type. Clusters in the graph reveal echo chambers naturally — groups of outlets with dense internal citation networks and sparse external connections.

**Filtering** is a core interaction: users can isolate specific relationship types (ownership only, citation patterns only, funding relationships only), specific geographic regions, specific entity types, or specific time windows. A journalist investigating media consolidation filters to ownership edges. A researcher studying echo chambers filters to citation patterns. An analyst tracking a specific corporation filters to nodes connected to that entity. The same graph, interrogated through different lenses. Filter states can be saved, named, and shared.

### Corporate ownership tree

Parent company structures — which corporations own which outlets, and what other businesses those corporations operate — are visualised as navigable trees. Users can explore from any node in either direction: from a news article to its outlet to its owner to the owner's other holdings and interests. This data is sourced from publicly documented ownership records and updated as changes are reported.

### Global coverage map

A geographic heat map showing coverage density and framing divergence by region. For any story cluster, the map shows where coverage is concentrated and where coverage of the same event carries measurably different framing. Colour gradients represent coverage volume; divergence indicators flag regions where the story is being told in a substantively different way. This is one of the most visually powerful tools in the platform for understanding how geography shapes information.

### Story provenance visualisation

For any story cluster, a directed graph showing the information genealogy: the identified origin (earliest traceable publication or primary source), who picked it up and when, what was added or changed at each step, and where the narrative branched. Users can see that a story originating from a government press release has been reported by forty outlets, all of which cite only that single source — visible immediately as a star pattern from a single origin node. Compare this to a story where five independent investigations converged on the same facts — visible as multiple independent origin nodes converging on consensus. These two patterns look identical in a headline count but reveal entirely different information quality.

### Narrative evolution timeline

For ongoing stories, a chronological view of how the reported facts, the cast of cited sources, the framing, and the publication volume changed over time. Corrections, retractions, major new developments, and narrative pivots are all timestamped and visible. For any story that develops over weeks or months, this timeline shows the user not just what is currently being reported but how understanding of the event evolved — and where the gaps and reversals occurred.

### CLI equivalents

Every visualisation has a CLI equivalent that carries equivalent informational value without graphical rendering. The influence graph becomes a filterable adjacency table with edge-type columns. The provenance visualisation becomes a chronological text tree. The coverage map becomes a sorted region-by-region breakdown with counts and framing-divergence indicators. The narrative timeline becomes a dated log of significant changes. No information available in the GUI is withheld from the CLI — the difference is representation, not content.

---

## 8\. Stakeholder Analysis

### Framing

Originally conceived as a "prediction layer," this feature is deliberately reframed as **Stakeholder Analysis** to avoid any inference or speculation. The platform does not predict outcomes. It does not infer intentions. It does not model futures. It presents documented facts about which entities have a documented interest in the outcome of the events being reported.

This distinction is both legally important (presenting inference as fact creates liability) and philosophically essential (the moment the platform makes inferences, it becomes a participant in the narrative rather than a map of it).

### What is included

For any story cluster: identified entities with a documented stake in the outcome (financial, political, legal, regulatory), the nature of that stake as documented in public records, financial relationships between those entities and the outlets covering the story (where documented), and historical involvement of those entities in related stories.

**All data points must be sourced.** If a financial relationship cannot be documented, it is not included. If a conflict of interest is suspected but not documented, it is not included. The threshold is verifiable fact, not inference.

### What is excluded

Any claim that an entity "stands to gain" or "could be harmed" where this requires inference rather than documentation. Any assessment of motive. Any suggestion of coordinated action unless specifically documented. The platform maps who is at the table and what they have documented interests in — it does not speculate about what they might do with that position.

---

## 9\. Coverage Distribution Analysis

### The feature and its purpose

The platform tracks coverage density across stories, categories, regions, and languages globally and presents this data as a factual, descriptive account of where coverage is concentrated and where it is not. This is **Coverage Distribution** — a measurement, not an editorial judgement. The platform does not assert that any story is under- or over-covered. It shows, factually, where coverage exists. The user draws their own conclusions about what those distributions mean.

This distinction is structurally important. A "silence map" that flags stories as undercovered implies an editorial baseline for what coverage "should" look like — which is an inference, not a fact. Coverage Distribution avoids this by presenting only what is measurable: how many sources cover this story, from which regions, in which languages, and how that compares in raw terms to coverage of other stories in the same period.

### What is presented

For any story cluster: total source count by region, total source count by language, publication volume over time, and the geographic and linguistic distribution of that volume. For category-level views: coverage volume by region across all stories in the category, allowing a user to see that a given category receives dense coverage in some regions and sparse coverage in others.

When the same story receives markedly different coverage volumes across regions, that disparity is surfaced as a data point. When a story is covered extensively in one language group and sparsely in another, that is visible. The user can see these distributions and interrogate them. What they mean is for the user to determine.

### Framing divergence as a related but separate signal

Within any story cluster that spans multiple regions, measurable differences in how the story is framed — which entities are centred, which language is used, which aspects are emphasised — are surfaced as framing divergence data. This is distinct from coverage volume: a story can receive equal volume across two regions while being framed entirely differently in each. Both signals are present, clearly labelled, and factually grounded in the text of the articles themselves.

---

## 10\. Entity Tracking

### Entities as first-class objects

People, organisations, governments, and companies exist in the platform as persistent entities with their own profiles, independent of any individual article or outlet. When an entity appears in a story, the platform links to its profile: documented positions and statements over time, known affiliations and relationships, stories they have featured in, financial interests where documented, and their feature analysis profile (analogous to outlet-level feature analysis but applied to entities).

### Entity resolution — the canonical identity problem

The same real-world entity appears under dozens of surface forms across millions of articles in multiple languages. "Donald Trump," "Trump," "the former president," "the 45th President of the United States," and "Donald J. Trump" must all resolve to the same entity record. The resolution approach is layered:

**Wikidata as the canonical entity registry.** Wikidata assigns stable unique identifiers (Q-numbers) to real-world entities — Q22686 is Donald Trump regardless of language or surface form, permanently. Linking extracted entities to Wikidata Q-IDs gives the platform a stable canonical identity that persists across languages, aliases, and time. Wikidata also provides rich structured data about each entity — known relationships, documented roles, aliases, affiliation history — which seeds entity profiles without requiring the platform to build that knowledge from scratch.

**spaCy NER \+ entity linking.** spaCy's NER pipeline extracts entity mentions from articles at ingest. A linking step maps those mentions to Wikidata Q-IDs. For prominent global entities this resolves reliably. For less prominent entities — a regional politician, a small company — the linking is harder and confidence scores matter.

**Alias tables.** Every entity maintains a list of known surface forms beyond the canonical name: titles ("the Prime Minister," "the Fed Chair"), abbreviations, common informal references, and language-specific variants. These are seeded from Wikidata and supplemented by the platform's own corpus as new surface forms are encountered.

**Contextual disambiguation.** Where surface form alone is ambiguous, surrounding entity mentions and topic context feed into disambiguation. "Trump" in an article also mentioning "Mar-a-Lago," "Truth Social," and "2024 election" resolves differently from "Trump" in a 1987 article about Manhattan property development.

**Confidence scoring.** Not every resolution is certain. High-confidence links are displayed as resolved. Low-confidence links are flagged as probable and surfaced for community correction. The platform is transparent about resolution uncertainty rather than presenting all links as equally definitive.

**Community correction queue.** Users who identify an incorrect entity link can flag it with an explanation. Flagged links enter a review queue, are assessed, and corrected with a documented changelog entry if the flag is valid.

### The entity knowledge graph

Entities are connected to each other through documented relationships: employment, board membership, ownership, political affiliation, contractual relationship, legal proceedings, and others. This graph is the connective tissue between individual stories and the broader structural context in which they occur. A pharmaceutical executive appears in a story about drug pricing: the entity profile surfaces their documented financial interests, their board memberships, their prior statements on the topic, and what other stories they have appeared in.

### Persistence and history

Entity profiles accumulate over time. A politician's documented positions from five years ago remain accessible alongside their current statements. Corporate ownership structures are tracked historically — who owned what, and when, matters for understanding coverage at any given point in time. This historical depth is particularly valuable for research use cases.

---

## 11\. User Experience Design

### The surface with doors

Every element of the surface layer is an entry point into the layer beneath it. A casual user sees a clean daily digest. That digest is composed of story clusters. Each cluster has a coverage indicator and geographic spread. The cluster view opens the full source list with feature analysis fingerprints. The feature analysis fingerprint opens the full outlet profile. The outlet profile links to the influence graph. The influence graph connects to the ownership tree and entity profiles. The provenance chain links back to the originating source.

The depth is always present. The surface does not obscure it — it curates entry into it. A user can go from morning digest to complete provenance analysis in a linear sequence of intuitive steps, or stop at any layer that meets their current need. No use case should be more taxing to interact with than another.

### The central design constraint

The experience of a casual user checking three categories they follow must be as smooth, clear, and valuable as the experience of a researcher running a multi-year provenance analysis on a geopolitical story cluster. These are different interactions with the same platform, not different products with different quality levels.

Simplicity is not a reduction of the complex version — it is its own design challenge. The surface layer and the research layer must be developed with equal care and intention.

### Free tier and depth visibility

The free tier presents deduplicated data — one representative article per cluster, selected by the **Representative Article Score (RAS)**, with wire copy collapsed. The total number of articles in a cluster is always visible, even when access to individual articles beyond the representative version requires a paid tier.

The RAS is a transparent, multi-dimensional scoring system with publicly documented weights subject to the RFC process. It scores articles across six dimensions: completeness, originality (derived from the wire propagation tier), outlet peer-normalised quality, political centroid proximity, primary source density, and temporal position. The political centroid proximity dimension is the key anti-bias mechanism — it selects the article whose outlet sits closest to the political centre of gravity of all articles in the cluster, preventing systematic bias toward any part of the political spectrum in the default view. Full methodology and current weights are published alongside all other platform methodology documentation. Seeing "1 article displayed · 847 total sources covering this story" is genuinely informative — it tells a free user about the scale of coverage — while making the value of the paid tier legible without aggressive promotion.

This principle extends throughout the free tier. Counts, distributions, and summaries of deeper data are surfaced where they add value, without exposing the underlying data that generates them. The upgrade prompt is the data itself. No popups, no forced paywalls, no degraded loading states on purpose. Users who encounter a depth limit should understand immediately what they would gain by going further.

### User tiers by use case (not by feature access)

**The daily reader** — wants a clean, personalised digest of the categories and niches they follow. Sees story clusters presented cleanly, with a simple coverage indicator and basic political spread. Can optionally surface any depth they want but never needs to. The experience is as close to a well-curated newsletter as possible, but every element is a door if they want to go deeper.

**The engaged follower** — follows specific ongoing stories or entities. Wants notification when something significant changes in a story they track, or when an entity they follow appears in a new context. Uses the narrative evolution timeline. Comfortable going one or two layers below the surface regularly.

**The researcher or journalist** — uses the platform as a primary research tool. Deep graph queries, full provenance chains, historical analysis, entity relationship mapping, influence graph filtering, coverage distribution analysis, and bulk export of structured data. Needs API access and the ability to build custom queries.

**The enterprise or institutional user** — large organisations, government bodies, academic institutions, legal teams, NGOs. Needs custom dashboards built around specific entity sets or topic domains, real-time monitoring and alerting, bulk data export in structured formats, white-labelling options, SLA guarantees, and dedicated support. The underlying data is the same as every other tier. The interface and access modalities are purpose-built.

### Onboarding — three questions, three flows

Every new user passes through a three-question onboarding process before their first experience. Three questions is a deliberate constraint: enough to personalise the starting experience meaningfully, not enough to feel like configuration work. Everything beyond these three questions is available in settings, discovered progressively as the user engages with the platform.

**Question 1 — Purpose:** "What brings you here?" Options: staying informed on topics I follow / researching a specific story or subject / professional or work use / all of the above. This sets the default depth and interface mode. A "staying informed" user defaults to the digest surface. A "professional use" user defaults with more of the feature analysis layer visible.

**Question 2 — Categories:** "What do you want to follow?" A clean multi-select of the full category taxonomy, with the ability to type sub-niches directly. No minimum or maximum selection required. A user who selects nothing receives a broad global digest by default and can refine later.

**Question 3 — Depth preference:** "How do you like to engage with news?" Options: quick summaries and headlines / full stories with context / everything including sources and analysis. This maps directly to the progressive disclosure default — a "quick summaries" user sees the surface layer by default, with depth always accessible behind a tap. A "full analysis" user has more of the deeper layer surfaced by default from the outset.

The three onboarding flows are distinct in interaction design while asking identical questions:

**Mobile (iOS/Android):** Swipe-based or large tap-target selection. Minimal text input. Visual, fast, completable in under ninety seconds. Designed for thumb operation in portrait orientation.

**Desktop app (macOS/Windows):** Keyboard-navigable, slightly higher information density. The category selection shows more of the taxonomy at once. Completable in under two minutes. Designed for users who may want to make more considered selections before starting.

**CLI (Linux):** Sequential prompted questions in the terminal. Plain text input. No visual embellishment. Outputs a config file that governs the starting experience. Equally fast, equally complete.

All three flows write to the same user preference structure in the backend. The experience they produce is equivalent in quality and personalisation regardless of platform.

### Notifications and alerting

The notification system is opt-in at every level. The default on first launch is no notifications. The configuration screen is presented clearly during onboarding without pre-ticking any option. Opting out of notifications at any granularity is always one step from where the notification arrived.

**Notification levels** (all off by default, any combination configurable):

- **Digest** — one notification at a user-set time containing their personalised digest for the day  
- **Tracked topics** — notifications when story clusters in explicitly followed categories or entity tracks receive significant new developments  
- **Breaking** — high-volume coverage spikes indicating a major emerging story across any followed category

**Notification channels** (mobile and desktop app only; CLI is a pull interface and excludes push notifications):

- Personal updates feed (a dedicated browsable tab surfacing interest-specific story developments, entity appearances, and coverage changes — always present, refreshed continuously, never intrusive; the feed is the destination that push notifications point toward, not a duplicate of them)  
- Push notification (iOS/Android/macOS/Windows, opt-in)  
- Email digest (optional, configured with email address, opt-in)  
- SMS alert (optional, configured with phone number, opt-in, recommended for breaking alerts only given channel cost)

Email and SMS are available to all paid tier users. The level of alerting via each channel is independently configurable — a user might want push notifications for breaking events but only an email for their daily digest. All configurations are managed in one place and presented without dark patterns. The platform does not re-prompt users who have opted out of a notification type.

---

## 12\. Platform & Technical Architecture

### Guiding principle

The architecture is designed for the scale of a global enterprise product from the first line of code, even though the initial deployment is personal. Adding scale later is expensive and painful. The services are separated correctly from the start; the initial deployment is simply a small instance of a correctly architected system.

### Backend — VPS hosted, service-separated

**FastAPI** — the core API layer, serving all clients (web, mobile, CLI, enterprise API). REST with GraphQL available for complex enterprise queries.

**PostgreSQL** — primary data store for articles, clusters, entity profiles, feature analysis data, ownership relationships, and provenance chains. pgvector extension for storing and querying article embeddings directly in the database, avoiding a separate vector store.

**Redis** — caching layer for pre-computed surface data (digests, cluster summaries, category feeds) and job queue management.

**Celery \+ Redis** — task queue for scheduled and background jobs: feed ingestion, clustering passes, feature analysis updates, pre-computation cycles.

**OpenClaw** — human-facing monitoring and control interface. Custom AgentSkills expose pipeline operations and system health via a developer-preferred chat channel. Pipeline orchestration remains owned by Celery; OpenClaw surfaces operational state and accepts manual triggers.

**Ollama** — local LLM serving for categorisation, feature analysis signals, and summary generation. Model-agnostic; can route to cloud APIs (Claude, GPT) for tasks requiring larger models if cost is acceptable.

**spaCy** — NER pipeline for entity extraction and Wikidata entity linking at article ingest.

**Sentence-transformers** — embedding generation for clustering and deduplication. `all-MiniLM-L6-v2` as the default; upgradeable as hardware improves.

**Scrapy \+ Playwright** — polite scraping layer for sources not covered by feeds or APIs.

**OPUS-MT** (Helsinki-NLP, self-hosted) — machine translation engine from Phase 4 launch; zero per-character cost. **DeepL API** replaces OPUS-MT in Phase 5 once revenue supports the cost, providing substantially better handling of political, legal, and technical language.

### The two-layer compute separation

**Pre-computed layer** — runs on a continuous rolling cycle, always ahead of user requests. Produces: digests by category and user preference, story cluster summaries, feature analysis snapshots, influence graph snapshots, daily coverage distribution updates. All output is cached in Redis. Casual user interactions hit this layer only and always return near-instantly. Enterprise workloads and deep analytical queries never share compute with this layer.

**Analytical layer** — on-demand queries against the full database. Complex graph traversals, historical provenance queries, multi-decade entity tracking, bulk exports. Runs asynchronously where needed, with appropriate UI loading states. Never shares compute with the pre-computed layer.

### Frontend — Flutter

Flutter is chosen because it allows a single Dart codebase to compile to: web (PWA), iOS, Android, macOS, and Windows. The phased approach is:

**Phase 1** — Flutter Web (PWA) deployed for macOS browser access. Python CLI client for Linux, independently built against the same FastAPI backend.

**Phase 2** — Compile the existing Flutter codebase to native macOS, iOS, and Android. Minimal additional code required; platform-specific UX polish (navigation patterns, gestures) is the primary work. Windows native build from the same codebase.

**Phase 3** — App Store, Google Play, and independent desktop release distributions. The codebase is identical to Phase 2; this phase is distribution and compliance work.

### CLI — full parity, no compromise

The CLI client (Python, built against the FastAPI backend) is not a reduced version of the platform. It is the platform without graphical rendering. Every feature accessible in the GUI is accessible from the CLI. Visualisations are represented as their informational equivalents in text form — adjacency tables, chronological text trees, sorted regional breakdowns, dated change logs. A user fluent in CLI tools loses nothing except visual rendering, which for many CLI users is a preference rather than a deficit.

This is a stated design principle: no platform version is secondary. Development of the CLI client should be held to the same feature-completeness standard as the mobile and desktop applications.

### Enterprise API

The API layer serves two interfaces: **REST** for standard queries covering the majority of enterprise use cases (article retrieval, cluster summaries, entity lookups, feature analysis data, coverage distribution statistics), and **GraphQL** for complex relational queries (entity relationship traversal, custom influence graph queries, multi-entity correlation, historical provenance chains). REST is implemented first; GraphQL is added when enterprise query complexity justifies it.

**Authentication** is API key-based with defined permission scopes. A key can be granted read access to articles, entity data, feature analysis, coverage distribution, or the full dataset, depending on the subscription. This enables granular access control and clean metering by data type.

**Rate limiting** is tiered by subscription: requests per minute, data volume per day, and concurrent connection limits. Limits are generous enough for genuine enterprise workloads and clearly documented. Enterprise clients approaching their limits receive advance warning rather than hard cutoffs where possible.

**Webhook support** allows enterprise clients to register endpoints that receive structured payloads when tracked entities or topics cross defined thresholds — coverage volume spikes, new stakeholder entries, significant feature analysis changes, or entity profile updates. This enables integration with existing institutional monitoring and alerting infrastructure.

**Data export formats** include JSON (universal), CSV (spreadsheet-compatible), and JSON-LD (for semantic web and knowledge graph integration). Export schemas are versioned and stable — breaking changes require a version increment and a deprecation period. Documentation for all formats is public.

**Sandbox environment** — a fixed sample dataset environment is available for enterprise clients developing against the API before production access. This reduces integration friction and is standard practice for enterprise API products.

### Historical data depth

Historical data is always in service of understanding current events better, not historical record-keeping for its own sake. The phased approach reflects this:

**Phase 1 (initial deployment):** Live collection from the point of deployment, with lookback depth limited to what available APIs provide — typically one to three months. This is sufficient to establish entity profiles, provide context on developing stories, and seed the feature analysis system.

**Phase 2 (growth):** GDELT historical data extends the corpus significantly — GDELT coverage goes back to 1979 for some source types, with quality improving for more recent decades. Internet Archive CDX API access provides additional historical depth for specific sources and stories. This phase is driven by research user demand.

**Phase 3 (maturity):** Common Crawl data (available from 2008\) and deeper Wayback Machine integration extend the corpus further for research queries. The practical limit is storage cost and indexing time relative to the research value of older data.

At every phase, historical depth is surfaced primarily for research users and entity profile enrichment. Casual users encounter it only when they specifically navigate into a story's history. The platform's core experience is present-tense; history is the foundation, not the facade.

### Scaling path

The service-separated architecture scales horizontally at each layer independently. When traffic demands it: the ingestion layer handles more sources by adding workers, the analytical layer gets additional compute, the API layer adds instances behind a load balancer, the database adds read replicas for heavy read workloads. A separate data warehouse (columnar store, e.g. ClickHouse) is added when analytical query volume justifies it, separating heavy analytical workloads from the operational database. Kubernetes orchestration is the deployment target for enterprise-scale operation, with the initial personal deployment being a simplified Docker Compose setup on a single VPS.

---

## 13\. Internationalisation

### Philosophy

The platform aspires to be genuinely global — not a Western news platform that also covers international stories, but a platform that gives equal treatment to reporting in all languages and from all regions. Internationalisation is therefore a core architectural concern, not a localisation afterthought.

### Translation pipeline

Non-English articles pass through a three-stage translation process:

**Stage 1 — Machine translation.** The translation engine is phased: OPUS-MT (Helsinki-NLP, self-hosted, zero per-character cost) is used from the initial translation feature launch; DeepL API is introduced in Phase 5 once revenue supports the cost ($25/1M characters). DeepL is the target production engine for its substantially better handling of nuanced political, legal, and technical language — OPUS-MT is the bridge that allows the pipeline to be built and used by early paid users before that cost is sustainable. The swap between engines is transparent to the rest of the pipeline.

**Stage 2 — LLM review pass.** An LLM reviews the translated text against the original with a specific and narrow brief: not to rewrite, but to flag. It identifies idioms translated literally that lose meaning in English, culturally specific terms with no clean equivalent, sentence-level logic that reads correctly in the source language but becomes ambiguous in translation, and news-specific terminology that may have been handled generically. The LLM produces a set of flagged spans with brief explanations — it does not alter the translation.

**Stage 3 — Confidence annotation.** Flagged spans are annotated in the stored article. The count and nature of flags inform an overall translation confidence indicator. Articles with high confidence are displayed with a standard translation notice. Articles with significant flags display a clear notice that the translation may not fully preserve the original meaning, with the flagged spans marked inline. The original text is always accessible alongside the translation for any span, and for the full article, regardless of confidence level.

### UI and interface localisation

The platform interface itself is internationalised for right-to-left language support (Arabic, Hebrew, Farsi, and others), date and number format localisation by region, and — over time — native-language interface options for major language groups. Initial deployment is English-interface only; interface localisation follows user demand.

### Political leaning contextualisation by region

The political leaning calculation (Section 6\) is calibrated per regional political context. What constitutes a left-leaning or establishment position in the UK differs from what it means in Brazil, Japan, or Nigeria. The multi-axis model is the mechanism for this — the axes themselves are stable, but what occupies each position on each axis is culturally contextualised. The methodology for each regional calibration is publicly documented.

### Non-English entity resolution

Wikidata Q-IDs are language-agnostic — an entity is the same entity regardless of the language in which it appears. This means entity resolution (Section 10\) works across languages without duplication. A French article about "Donald Trump" and an Arabic article about the same person link to the same entity profile. Alias tables include language-specific variants for all major entities.

---

## 14\. Open Source Strategy & Business Model

### Why open source is necessary

The platform calculates political leanings, assesses source independence, maps media ownership, and presents coverage distributions. Any of these activities carried out by a black box creates exactly the kind of opaque information authority the platform is designed to counteract. The code and the methodology must be open for the platform's credibility to be genuine rather than claimed. This is a structural requirement, not a marketing decision.

### AGPL licensing

The core platform code is licensed under AGPL (GNU Affero General Public License). AGPL is specifically designed for network-deployed software: any organisation running a modified version of the platform as a public service must open source their modifications. This prevents commercial forks without contribution back, while allowing free self-hosting. Organisations that require deployment without AGPL obligations — common in enterprise procurement environments with restrictive open source policies — can purchase a commercial licence alongside the AGPL version. This dual-licensing model is standard practice for open source businesses.

### The data as the commercial asset

The code being open source does not mean the data is. The continuously updated dataset — the ownership graph, the historical feature analysis, the trained models, the story corpus, the entity knowledge graph — is generated by running the open code continuously at scale over time. It is not produced by running the code once. An organisation wishing to self-host would need to deploy the software, build all of that data infrastructure, and operate it continuously — a significant ongoing commitment. Most organisations, even large technical ones, would rather pay for a managed service. This is how every major open source business operates successfully.

### Tiered service model

**Personal (free)** — deduplicated data view, full feature depth on deduplicated content, source counts visible for all clusters, standard update cadence, no API access, community support. This tier is not a crippled version. It is the complete product scoped for individual use. The total article count visible on every cluster means free users always understand the scale of coverage beneath what they see.

**Professional** — access to full article cluster data (all sources, not just deduplicated), API access, multi-device sync, faster update cycles, data export in structured formats, bulk download, email and SMS notification options, priority support. Targeted at journalists, independent researchers, freelancers, and engaged individuals who use the platform as a professional tool.

**Academic/NGO** — equivalent to Professional, with research-appropriate data export formats, extended historical data access, and citation-ready data provenance documentation. Pricing adjusted for non-commercial research contexts.

**Enterprise** — custom dashboards built around specific entity sets or topics, real-time alerting via webhook, white-labelling options, SLA guarantees, dedicated support, custom data pipeline integration, and volume API access. Pricing negotiated per deployment. This tier serves large media organisations, government bodies, legal teams, financial institutions, and NGOs with institutional information needs.

**Supporter/Patron** — a voluntary tier above Personal for users who believe in the project and want to support its independence beyond what they functionally need. No additional features; this tier exists because a platform built around transparency and independence from commercial influence is strengthened by a community of financially committed supporters who are not paying for commercial value. Modelled on the patronage structures used by Wikipedia, open source foundations, and independent journalism organisations.

### Payment infrastructure

Stripe handles payment processing, recurring subscription billing, invoicing, geographic tax compliance, and currency localisation. It is the industry standard for this type of tiered SaaS model and significantly reduces the payment infrastructure that needs to be built and maintained internally.

### Geographic pricing

A purchasing-power-adjusted pricing model for the Personal and Professional tiers allows the platform to serve a genuine global user base without pricing out users in lower-income markets, while maintaining full pricing in markets where it is sustainable. This is consistent with the mission of universal access and is how several major SaaS products (Notion, Figma, and others) have approached global expansion.

### The transparency advantage

Open source methodology is not a commercial sacrifice in this market — it is a differentiator. Institutions and governments paying for enterprise access are paying for something they can verify and audit. A political leaning calculation that a government body or major news organisation can inspect, challenge, and validate is worth significantly more than one they must accept on faith. This is particularly true in academic, journalistic, and regulatory markets where methodology credibility is a condition of use, not a preference.

---

## 15\. Community Feedback & Methodology Transparency

### The RFC process

Methodology changes — adjustments to scoring weights, changes to category definitions, updates to the political leaning calculation — go through a publicly visible Request for Comments (RFC) process. Proposals are published openly with full reasoning, a comment period is held, responses are documented, and decisions are published with explanations. This is standard open source project governance applied to editorial methodology.

### What community feedback can and cannot do

Users can flag factual errors in the data — a wrong ownership relationship, a missing outlet, an incorrectly attributed article, an incorrect entity link — with a source citation. These go into a public review queue, are assessed, and accepted or rejected with documented reasoning.

Users cannot directly vote on political classifications, scoring weights, or methodology parameters. This is the vector through which politically motivated actors would attempt to game the system. Feedback improves accuracy of documented facts; it does not adjust the political temperature of outputs.

### The public methodology changelog

Every change to any aspect of the platform's analytical methodology produces a public changelog entry: what changed, why, what evidence it was based on, and what the expected effect on outputs is. This makes the platform's evolution transparent and allows users to understand how and why their experience changes over time.

### Acknowledging imperfection

The platform is transparent that it is a work in progress. No methodology for assessing media independence, political leaning, or source feature analysis is perfect. The platform's value is not in being infallible — it is in being more transparent about its methods than any alternative, and in giving users the tools to interrogate those methods. User feedback on information clarity and accessibility is specifically solicited and treated as valuable input into ongoing development.

---

## 16\. Legal Considerations

**Web crawling** — full `robots.txt` compliance, crawl delay respect, honest user-agent identification, and terms of service adherence. Collection is structured around feeds and APIs as the primary layer, with polite scraping as a supplement.

**Social media collection** — limited to institutional and journalist accounts with public APIs or publicly accessible content. No collection from private accounts or content requiring authentication beyond standard API access.

**Feature analysis framing** — the deliberate choice of "feature analysis" over "reputation scoring" or "credibility rating" is legally important. The platform presents documented, verifiable attributes. It does not assert that any source is unreliable, untrustworthy, or inaccurate. Documented facts about ownership, correction records, and affiliation are not defamatory; editorial opinions about quality could be.

**Stakeholder analysis** — only documented, verifiable facts are presented. No inference about motive or intent. No claim that any entity has done anything improper. Documented relationships and documented interests, sourced.

**Political leaning calculation** — the methodology is fully public and auditable. Any outlet that objects to its calculated leaning can scrutinise and challenge the methodology. Transparency is both ethically right and a legal protection.

**AGPL licensing** — provides protection against closed commercial forks. Commercial licensing available alongside for organisations with policy restrictions on AGPL deployment.

**Data protection** — user data (preferences, reading history, research queries) is stored minimally, used only for the user's own experience, and never sold or used for advertising. This is both a legal obligation in most jurisdictions and a product principle consistent with the platform's values.

**Translation and citation** — translated articles are clearly marked as translations, with the original language and source cited. Translation confidence indicators are displayed. The platform does not present translated content as equivalent to the original without qualification.

---

## 17\. Areas Requiring Further Development

The following areas have been identified and discussed but require further detail before the project plan stage:

**The feedback queue tooling and governance structure** — the RFC process and factual error flagging are described at a principle level. The specific tooling, workflow, and moderation governance for managing community contributions at scale are deferred to a later stage of planning.

**Brand and name** — the project is named **Vernier News**. A vernier scale is the precision measurement mechanism that allows readings beyond the resolution of the main instrument — measuring what blunt tools miss. The name reflects the platform's core purpose: a finer analytical lens on the media landscape. The public-facing brand is "Vernier News" (ensuring audience clarity and domain distinctiveness); the pip package, CLI config paths, and repository will use `vernier-news`. The `vernier` PyPI namespace is clean. The one existing Vernier brand (Vernier Science Education, STEM lab tools) operates in a categorically unrelated market with no shared audience or domain.

**Tier pricing specifics** — geographic-adjusted pricing bands, specific price points for Professional and Academic tiers, and the commercial licence pricing structure alongside AGPL require market research closer to launch. The model is defined; the numbers are not.

**Enterprise go-to-market approach** — the enterprise tier's commercial structure and sales approach (direct outreach, inbound, partnership) are not yet detailed. This is appropriate at the concept stage.

**Sub-niche taxonomy** — the broad category structure is defined. The recommended sub-niche taxonomy beneath it — and the mechanism by which users define their own sub-niches — needs a dedicated design pass.

**Onboarding edge cases** — the three-question onboarding flow handles the standard case well. Edge cases (users who skip all questions, users who change their answers significantly shortly after onboarding, enterprise users whose experience needs are different from individual users) need design attention.

---

*End of Concept Document v0.4* *Status: Approved for development — v0.4*  
