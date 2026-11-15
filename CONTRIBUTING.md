# Contributing

Start with [AGENTS.md](AGENTS.md), the [context index](context/README.md), and the [small-commits and verification rules](context/44-small-commits-and-continuous-verification.md).

This repository currently contains research, a build specification and a reading website. The astrology application is not implemented. Do not describe documentation checks as proof that the proposed application is production-ready.

## Before each commit

- Make one coherent, reviewable change. Keep its relevant tests and contract updates together.
- Run `node scripts/check-docs.mjs` from the repository root and inspect its result.
- For website behavior/layout changes, check the affected desktop/mobile and keyboard flows in a browser.
- Review staged changes for secrets, personal data, unauthorized book text and unrelated edits.
- Fix required failing checks before committing. Record what was tested; mark unrun checks honestly.

Use a descriptive commit message such as `docs: clarify the pilot launch gates`. Avoid unrelated cleanup in a behavior change. Re-run affected checks after later edits and verify the final integrated tree before pushing.

## Working with agents

Give agents disjoint file ownership and explicit interfaces. Each implementer tests its change; an independent reviewer checks consequential behavior. Parallel tests run against a stable identified snapshot, and the coordinator verifies the final integrated result. See the [full collaboration/testing policy](context/44-small-commits-and-continuous-verification.md).

## When implementation starts

Follow the [implementation plan](context/15-implementation-plan.md), [code standards](context/14-code-standards-and-testing.md), and [CI/release strategy](context/37-ci-testing-and-release-strategy.md). Future Python checks must be configured and run against real implementation; their presence in the plan is not a passing result. Authentication, ownership, calculations, rights, retrieval and provider changes require appropriate regression tests and independent review.

Use short-lived branches and pull requests for application changes. Configure required CI/review protection before relying on it. No branch-protection or production-readiness claim should be made without checking the actual repository settings and release evidence.
