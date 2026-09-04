# Forge Fitness v14.19 — Nutrition Provider Stabilization

Provider-layer stabilization for Smart Food Logging.

- Classifies authentication, rate-limit, network, timeout, invalid-response, and no-match failures.
- Adds a User-Agent and Accept header to provider requests.
- Keeps USDA and Open Food Facts as independent fallbacks.
- Adds `GET /nutrition/providers/status` for live diagnostics on the machine running Forge.
- Adds a Provider status control to the Coach.
- Preserves v14.18.2 query broadening, fluid-ounce parsing, zero-calorie acceptance, and generic zero-sugar fallback.
- Uses Open Food Facts' legacy `/cgi/search.pl` for text lookup. Open Food Facts documents that v2 search is structured/filter-based and does not support plain-text `search_term` queries.

After starting Forge, use Provider status in Coach or open the status endpoint to identify credential/network/provider problems.
