# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- No unreleased changes so far

## [0.8] - 2026-01-04
### Changed
- CarConnectivity 0.11 compatibility

Note: This plugin is required for compatibility with CarConnectivity version 0.11 and higher.

## [0.7] - 2025-11-02
### Added
- Support for hiding location when sending data to ABRP
- Support for overwriting location when sending data to ABRP

## [0.6.1] - 2025-10-15
### Fixed
- Catch exception in _get_next_charge to avoid breaking the plugin if ABRP is not reachable or returns unexpected data

## [0.6] - 2025-04-17
### Changed
- Updated dependencies

## [0.5] - 2025-04-02
### Fixed
- Allowes to have multiple instances of this plugin running

### Added
- Support for transmitting altitude (for supported vehicles, currently only Volvo)
- Support for transmitting heading (for supported vehicles, currently only Volvo)
- Support for transmitting target climatization temperature (for supported vehicles)

### Changed
- Updated dependencies

## [0.4] - 2025-03-20
### Changed
- Bump carconnectivity dependency to 0.5

## [0.3] - 2025-03-02
### Added
- Improved access to connection state
- Improved access to health state

## [0.2.1] - 2025-02-20
### Fixed
- Fixes bug due to template ambiguity
- Named threads for better debugging

### Added
- Plugin UI root

## [0.2] - 2025-02-19
### Added
- Adds Plugin WebUI

## [0.1] - 2025-01-25
Initial release, let's go and give this to the public to try out...

[unreleased]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/compare/v0.8...HEAD
[0.8]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.8
[0.7]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.7
[0.6.1]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.6.1
[0.6]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.6
[0.5]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.5
[0.4]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.4
[0.3]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.3
[0.2.1]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.2.1
[0.2]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.2
[0.1]: https://github.com/tillsteinbach/CarConnectivity-plugin-abrp/releases/tag/v0.1
