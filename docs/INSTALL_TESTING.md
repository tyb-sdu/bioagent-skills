# Installation testing boundaries

`automatic: true` means the reviewed installer can execute the route on a
matching target. It does not mean every architecture or dependency combination
has been installed successfully.

The [scientific smoke workflow](../.github/workflows/scientific-smoke.yml) tests
PDBFixer on disposable Linux, Windows, and macOS runners, AutoDock Vina and
FreeSASA on Linux and macOS runners, and PROPKA on Linux, macOS and Windows
runners. Open Babel, Meeko, MDTraj, ParmEd, Gemmi and ProLIF are also configured for disposable
Linux, Windows and macOS runners; PDB2PQR and APBS also have Linux, Windows and macOS jobs. OpenMMForceFields and GROMACS are configured for Linux and macOS only. OpenMM, RDKit, Psi4 and MDAnalysis have jobs on all three operating systems. Thus every declared operating-system route of every automatic recipe has a configured smoke job, but a configured job is not evidence of success. The workflow creates the recipe's fresh conda or Python environment,
executes its minimal verification, repeats the verification, checks that the
status/usage handoff recognizes the installed environment and matching receipt,
and retains the
verified local receipt as a GitHub Actions artifact. The actual OS and CPU are
printed by `doctor`, so a moving `*-latest` runner label should not be treated
as permanent coverage of a specific architecture. Only a completed successful
job is evidence for that tested runner.

On 2026-09-27, [the 50-job installation run](https://github.com/tyb-sdu/bioagent-skills/actions/runs/36325910741)
completed successfully on commit `669e827`. All 18 automatic recipes passed
their Linux job, and every declared operating-system route passed its configured
job in that run. This is a time-stamped installation observation, not a guarantee
about future package releases, other architectures, or scientific accuracy.

The initial Windows PDBFixer job exposed a launcher-resolution bug: the PATH
contained `condabin/conda.bat`, whereas the subprocess interface needed the
native `Scripts/conda.exe`. The installer now resolves that executable from the
same installation, uses it consistently for planning, probing and execution,
and rejects orphan batch launchers. It does not enable `shell=True` to work
around the bug. Regression tests exercise a prefix containing spaces.

The first OpenMMForceFields Windows conda installation job failed while its
Linux and macOS jobs passed. The public job summary identifies the failed
installation step but does not establish a root cause. The Windows-native
automatic route is therefore disabled; `plan` provides a non-executing WSL
fallback instead. This is a platform verification boundary, not proof that
every native Windows installation is impossible.

The handoff integration assertion in `tests/check_installed_handoff.py` reads
metadata and displays the installed invocation prefix; it does not execute the
displayed invocation. Unit tests separately cover missing/ambiguous environments,
version drift, corrupt/oversized receipts, shell quoting, and the rule that a
historical receipt cannot turn a missing environment into a present package.

These tests do not use a GPU, run a molecular simulation or docking experiment,
change user input structures, or validate scientific predictions. They do not
test the Windows Vina manual fallback. No test runner environment is distributed
to users, and no scientific software is installed on the maintainer's computer
by the workflow.

The local Windows/Python 3.12 PROPKA installation and `python -m propka --help`
check passed before adding its automatic recipe. The FreeSASA conda-forge
package release was reviewed for Linux and macOS architectures; this does not
replace a completed CI installation on each runner.

Top-level versions are pinned, but their dependencies and Miniforge bootstrap
can change. A receipt records the observed top-level version, command and
source; it is not a full reproducibility lockfile. ARM Linux, PowerPC Linux,
older OS releases, GPU variants, clusters and architectures not represented by
the runner matrix still need separate installation validation.

The [standard validation workflow](../.github/workflows/validate.yml) separately
checks recipe/Skill structure, routing and safety invariants, and builds and
loads the Python wheel outside the repository checkout. Passing unit tests
alone must never be reported as a real scientific-software installation.
