# Token owner correction and refusal sensitivity lock

Canonical owner wording: 项目负责人个人的 Hugging Face token，用于多个项目。
Prior ownership wording is corrected by appended entries in PREREG_LOG and OPS_LOG; historical lines and frozen files were not rewritten. Two operational-report statements are indexed in token_owner_wording_correction.json. Manuscript ownership wording matches:0.

Configuration audit:18 existing home/system profile files checked; only ~/.bashrc line156 exports HF_TOKEN. ~/.profile,/etc/profile,/etc/bash.bashrc and readable/etc/profile.d files show no matching variable. Global tmux and8 session environment records contain none of the three HF token variable names. This does not certify later in-shell exports or the whole account environment.

The three processes are one MTA pipeline,3542128 run_all_auto.sh ->3581097 python ->27351 python,with the MTA working directory. Their values match the current shell configuration by private in-memory equality comparison; no key or fingerprint is disclosed. They are not identified as Codex chats. Equality to the deleted download-cache value cannot be reconstructed because that value was not retained.

Official authenticated permission introspection of the current shell-configured credential returned fineGrained,canReadGatedRepos=true,global permissions empty,and scoped permissions only repo.content.read. Thus the requested write-to-read replacement condition is not met; no new/revoked token. The bashrc export was retained for other projects; its mode was tightened0664->0600 without changing content. Same-UID access remains. Account owner should coordinate eventual multi-project rotation.

User resolved the rule conflict: v2 remains primary, WildGuard is sensitivity. Addendum21 freezes unit-specific model-referenced agreement without a replacement threshold. Addendum22 freezes public sensitivity after WJB scoring. The existing public scope yields1779 benign rows*10 conditions=17790,plus200 unsafe-control rows*10=2000,total19790. About5.5 card-hours at1s/row before loading/transfer; not12000. Public classifier has not started, GPU0 queue waits for WJB conditions.

No WildGuard unit-effect or public vector outcomes were read during this update. Abstract remains methods-only; no absoluteASR in future abstract. Paired claims retain cross-judge and strata criteria. Public model sensitivity does not become human calibration or replace v2.
