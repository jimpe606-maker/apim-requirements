# Security policy

This repository contains security requirements that organisations may copy into tenders and
platform configurations. A flaw in a requirement can therefore lead to insecure systems.

## What to report privately

* A requirement or acceptance criterion that, if followed, would weaken security (for
  example an outdated algorithm, an unsafe default, or a test that passes an insecure
  implementation).
* A reference to a standard that has a known vulnerability or has been superseded in a way
  that matters for security.
* A vulnerability in the tooling (`tools/`).

Please use GitHub's **private vulnerability reporting** ("Report a vulnerability" on the
Security tab) instead of a public issue. Include the requirement ID, the problem, and a
reference if you have one.

## What to report publicly

Wording, coverage gaps and disagreements about priority or scoring are not security issues;
open a normal issue for those.

## Supported versions

Only the latest release is maintained while the project is in alpha.
