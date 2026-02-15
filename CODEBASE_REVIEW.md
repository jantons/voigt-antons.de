# Codebase Improvement Suggestions

## High-priority

1. **Fix accidental global variables in `assets/js/collapse.js`.**
   The click handler assigns `$header` and `$content` without `const`/`let`, which creates globals and can leak state across scripts. Use block-scoped variables and wrap the logic in an IIFE or `$(document).ready(...)` to avoid polluting global scope.

2. **Align `assets/js/collapse.js` with the main JS bundle.**
   `assets/js/collapse.js` is not included in the `uglify` pipeline (`package.json` only bundles `_main.js` + plugin files). If this behavior is intended for production, include it in the build script; otherwise remove dead/unreferenced script code.

3. **Replace interval-based resize polling with event-driven debounce in `assets/js/_main.js`.**
   The sticky footer recalculation currently uses `setInterval(..., 250)` and a `didResize` flag. This pattern runs forever and is less efficient than a debounced `resize` handler.

4. **Pin and lock Ruby dependencies for reproducible Jekyll builds.**
   The repository has a `Gemfile` but no `Gemfile.lock`. Add a lockfile and document the supported Ruby/Bundler versions to avoid environment drift.

## Medium-priority

5. **Correct configuration typos and stale defaults in `_config.yml`.**
   `publication_category.standardizations.title` currently says `Stradization Contributions`, which looks like a typo. Also `repository` still points to the upstream template (`academicpages/academicpages.github.io`) instead of this site repo.

6. **Normalize analytics provider type in `_config.yml`.**
   `analytics.provider` is currently the string `"false"` instead of a boolean `false`. This can lead to subtle Liquid condition mismatches.

7. **Modernize legacy social keys in `_config.yml`.**
   Keys like `google_plus` are deprecated and can be removed to simplify maintenance and reduce config noise.

## Nice-to-have

8. **Add CI checks for JS bundle and site build.**
   Add a workflow that runs `npm run build:js` and `bundle exec jekyll build` (after dependency install) so regressions are caught before deploy.

9. **Document local setup pitfalls in `README.md`.**
   Add a short troubleshooting section for network-restricted gem install failures and required tools (`ruby`, `bundler`, `jekyll`, `node`, `npm`).

10. **Add linting/formatting for custom JS.**
    Introduce ESLint + Prettier for `assets/js/*.js` to catch issues like implicit globals and keep style consistent.
