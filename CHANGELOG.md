# Changelog

All notable changes to the **TravelSDK** project will be documented in this file.

## [0.1.3] - 2026-04-19

### Improved
- **Smart Location Resolution**: Integrated `difflib` for genuine fuzzy matching across all transport modes (Hanoi, Flight, Bus).
- **CLI Robustness**: Resolved `AttributeError` in bus search mode and implemented dynamic versioning via `importlib.metadata`.
- **Search Intelligence**: Updated `SearchResult.summary()` to accurately find and report true minimum prices across disparate modes.
- **Authentication**: Refactored `TokenManager` to support iterative `refresh_token` flow and resolve asynchronous buffer detachment issues.
- **Test Infrastructure**: Fully modernized the test suite using `pytest-asyncio` markers and session-scoped fixtures.

### Fixed
- Fixed critical bug where CLI would crash when displaying bus operator names.
- Fixed `UnicodeEncodeError` on Windows consoles by optimizing output handling in test environments.
- Fixed recursive re-acquisition of tokens that caused race conditions in high-concurrency scenarios.

### Added
- Added `travel/py.typed` marker for PEP 561 compliance.
- Added comprehensive integration tests for regional location connectivity (e.g., secondary train stations).
- Added `tests/conftest.py` for standardized async client lifecycle management.

## [0.1.2] - 2026-04-19
- Initial formal release with Hierarchical Location Discovery.
- Registered `travel-sdk` CLI entry point.
- Integrated province-level hub mapping for District locations.

## [0.1.0] - 2026-04-18
- Initial internal beta with základ functionality for Flights, Trains, and Buses.
