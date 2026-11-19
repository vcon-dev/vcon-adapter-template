# Vendored schema source

- Repo: `ietf-wg-vcon/draft-ietf-vcon-vcon-core`
- Tag: `draft-ietf-vcon-vcon-core-05`
- `vcon_json_schema.json`: Appendix C JSON Schema, verbatim from the tag
- `vcon.cddl`: Appendix D CDDL, verbatim from the tag
- `examples/B*.json`: Appendix B examples (B1 to B9), verbatim from the draft

The JSON schema covers the unsigned form only. B6 (JWS) is validated through
its decoded payload and B7 (JWE) cannot be validated without the key; see
`tests/test_core05_examples.py`.

Do not hand-edit these files. Refresh from the tag, for example:

```
git show draft-ietf-vcon-vcon-core-05:vcon_json_schema.json
git show draft-ietf-vcon-vcon-core-05:vcon.cddl
```
