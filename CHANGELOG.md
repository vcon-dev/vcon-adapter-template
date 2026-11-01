# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Vendor the draft-ietf-vcon-vcon-core-05 Appendix C JSON schema and Appendix D CDDL verbatim under `tests/schema/`, with the Appendix B examples in `tests/schema/examples/` and `tests/test_core05_examples.py` validating them.
- `VCON_SYNTAX` is `"0.5.0"`. The builder does not yet emit the required `sessions` array; three `tests/test_spec_compliance.py` tests fail until the builder is ported to core-05.
- Require `vcon>=0.10.0`, the first vcon-lib release that writes draft-ietf-vcon-vcon-core-04 attachment defaults and raw JSON bodies, and omits empty `meta`/`metadata`.

### Added
- Initial scaffold generated from [vcon-adapter-template](https://github.com/vcon-dev/vcon-adapter-template).
