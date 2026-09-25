# Vendored schema source

- Repo: `ietf-wg-vcon/draft-ietf-vcon-vcon-core`
- Path: `vcon_json_schema.json`
- Branch: `main`
- Commit SHA: `fdcf2f5f420b726f7e70d16683ba0977d4610a1f`
- Fetched: 2026-09-25T20:55:05Z, via:
  ```
  gh api repos/ietf-wg-vcon/draft-ietf-vcon-vcon-core/contents/vcon_json_schema.json --jq .content | base64 -d
  gh api repos/ietf-wg-vcon/draft-ietf-vcon-vcon-core/commits/HEAD --jq .sha
  ```

This is the schema from the -04 appendix (`draft-ietf-vcon-vcon-core-04`,
published 2026-09-07; the project retargeted from -02 to -04 on
2026-09-25). It already matches -04's rule that with `encoding: "json"`,
`body` is the raw JSON value, not a string (Attachment/Analysis `body`:
"Any type for encoding=json, otherwise it must be a string") — no schema
change was needed for the retarget, only the code and tests that built
`json.dumps()`'d bodies under the old (incorrect) reading.

Do not hand-edit `vcon_json_schema.json`. Re-fetch with the commands above to
refresh, and update the commit SHA and fetch date here.
