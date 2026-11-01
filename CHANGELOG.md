# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Vendor the draft-ietf-vcon-vcon-core-05 Appendix C JSON schema and Appendix D CDDL verbatim under `tests/schema/`, with the Appendix B examples in `tests/schema/examples/` and `tests/test_core05_examples.py` validating them.
- `VCON_SYNTAX` is `"0.5.0"`. The builder now emits the core-05 model: `new_vcon()` creates one Session (index 0), receivers go on the Session, contributors on the Dialog, and attachments carry `party` plus `dialog` or `session`.
- `add_lawful_basis()` scopes the attachment with `party` plus `session` (was `party` plus `dialog`). The `dialog=` argument is replaced by `session=`; it defaults to the only Session and raises `ValueError` when the vCon has several.
- Require `vcon>=1.0.0,<2` (vcon-lib core-05 line).
- Docs (README, USAGE, CONTRIBUTING, config.example.yaml) describe the Session/Event model and the new attachment scope. Test fixtures and the compliance helper accept `dialog` or `session` scope.

### Added
- `describe_session()` in `vcon_builder.py` to fill in a Session (start, duration, receivers, originator, session_id).
- Tests for Session handling and the ambiguous-Session lawful-basis case.
- Initial scaffold generated from [vcon-adapter-template](https://github.com/vcon-dev/vcon-adapter-template).
