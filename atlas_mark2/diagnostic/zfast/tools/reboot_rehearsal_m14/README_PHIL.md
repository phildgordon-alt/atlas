# Reboot-resume rehearsal for the 10^28 window (M14; prepared, NOT yet run)

**Why.** The 10^28 window runs for about four days, and its checkpoint exists so that a reboot or power cut does not lose that work.
No one has yet tested a resume across a real reboot (review_v14c, condition 3.3). This rehearsal does that at 10^20, where the whole
thing takes minutes. Rebooting is your action; nothing here reboots the Mac.

**What it uses.** atlas_v5za on libzfast.v14d, D4 W8 (the planned 10^28 setting), nice 19, window [10^20, 10^20 + 10].

## Before you start

1. Make sure no Atlas window is running: `pgrep -fl atlas_v5.py` should print nothing. The scripts also refuse if one is running.
2. Do not install or update anything between step 1 and step 2: no macOS update and no `brew` command. Any OS or library change makes
   the library refuse the resume. That refusal is by design, but it would make the rehearsal inconclusive.
3. Expect at least 2 GB of free disk space. The scripts refuse with less.

## Steps

1. Open Terminal and run:

   ```
   /Users/kiosk/atlas_mark2/diagnostic/zfast/tools/reboot_rehearsal_m14/step1_start_and_stop.sh
   ```

   It starts the window, waits until the checkpoint has 300 lines (well under a minute), then kills the pipeline the way a power cut
   would. It prints a name like `rr_20261103_101500`. **Write the name down.**
2. Restart the Mac: Apple menu > Restart. Log in as usual.
3. Open Terminal and run, with the name from step 1:

   ```
   /Users/kiosk/atlas_mark2/diagnostic/zfast/tools/reboot_rehearsal_m14/step2_resume_after_reboot.sh rr_20261103_101500
   ```

   It checks that a reboot really happened, resumes the window from its checkpoint, then runs the same window again without
   interruption and compares the two. Expect it to take tens of minutes. It ends by printing `PASS` or `FAIL`.
4. Tell the Atlas agent the name. The result is in `diagnostic/zfast/runs/m14/reboot/<name>/result.json`.

## What PASS means

PASS means all of the following:

- the resumed run finished;
- it reloaded the checkpoint lines written before the kill and recomputed 64 of them identically;
- every certificate, the sign changes, the measurements and the Turing grid are identical to the uninterrupted run.

If the fingerprint changed (an OS or library update happened anyway), step 2 says so and the library refuses the resume with its
reason. That is the designed behaviour, not a bug, but the rehearsal must then be repeated.

Nothing is deleted. The run directories stay under `diagnostic/zfast/atlas_v5za/runs/`, and new keys are added to
`diagnostic/zfast/ckpt_keys/`.
