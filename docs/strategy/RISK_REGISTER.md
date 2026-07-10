# Risk Register

| Severity | Risk | Mitigation | Owner | Escalate When |
|---|---|---|---|---|
| Critical | Raw WRDS/OptionMetrics data leaks | Keep raw data ignored/local; run data-policy guard; inspect bundles/logs | Codex/Heavy/user | Any raw data, credentials, restricted fields, or sensitive paths appear |
| High | Public claims overstate evidence | L4 claim audit; update claim/evidence map | Pro/Heavy | README/Results/WRDS claims change or are used externally |
| High | Metrics snapshot is stale vs current HEAD | Run current-HEAD reproduction or document deferral | Codex/Heavy | Reproduction fails or changes headline metrics materially |
| High | WRDS sample/live boundary is blurred | Label sample as regression harness; live/local requires review | Heavy/Codex | Sample result is used as live-market proof |
| High | Public docs reference missing artifacts | Inventory references; regenerate/remove/caveat | Codex | Any broken artifact reference remains public-facing |
| High | WRDS methodology leakage/lookahead | Locked protocol, as-of checks, poison tests, no post-result tuning | Codex/Heavy | Protocol changes after seeing results |
| High | Heston narrative is misleading | Do not claim superiority without evidence; de-headline QE if needed | Pro/Heavy/Codex | Heston becomes public headline |
| Medium-High | Performance claims are hardware-specific | Record hardware/compiler/flags/repeats; avoid generic claims | Codex/Heavy | New benchmark number is used publicly |
| Medium-High | Lost artifacts/data after server transfer | Inventory local/cache roots; create WRDS data request packet | User/Codex | Data needed for WRDS panel is unavailable |
| Medium | Package/install claims unverified | Verify wheel/install or correct docs | Codex/Heavy | README install claim is edited/promoted |
| Medium | Stale historical docs mislead future agents | Canonical docs first; clean only claim-affecting conflicts | Heavy/Codex | Ticket relies on archived stale status |
| Medium | Artifact churn without explanation | Before/after metrics diff and manifest review | Codex/Heavy | Regenerated artifacts change unexpectedly |
| Medium | Scope sprawl | Tie work to evidence/performance/WRDS goals | Heavy | Broad unrelated source changes appear |
| Medium | Circular review loops | One focused repair or backlog nonblockers | Heavy | Same nonblocking issue repeats |
