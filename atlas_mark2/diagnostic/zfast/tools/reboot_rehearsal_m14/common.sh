# shared settings for the M14 reboot-resume rehearsal (sourced; PREDICTIONS_M14 section 6)
export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1; unset PYTHONOPTIMIZE
ZF=/Users/kiosk/atlas_mark2/diagnostic/zfast; ZA=$ZF/atlas_v5za; PY=/Users/kiosk/projects/atlas-rerun/.venv/bin/python
RR=$ZF/runs/m14/reboot                      # rehearsal records (fingerprints, results); the run itself lives in atlas_v5za/runs/
export ZFAST_THREADS=${ZFAST_THREADS:-4} ZFAST_WORKERS=${ZFAST_WORKERS:-8} V4_LIM_GB=${V4_LIM_GB:-1.0}   # the 10^28 production setting D4 W8
unset ZFAST_CENTER ZFAST_H ZFAST_DELTA ZFAST_K ZFAST_J ZFAST_STRICT ZFAST_CKPT ZFAST_TURING_GRID ZFAST_CKPT_ROLE ZFAST_CKPT_NONCE ZFAST_CKPT_KEY
drv_args() {   # T0 NAME [--resume] : the exact driver arguments (identical for start, resume and reference except the name)
  echo "atlas_v5.py $1 $1 $(echo "$1 + 10" | bc) --name $2 --zs-step 0.005 --gen-timeout 1209600 --wide --zfast-h 91.0 --zfast-delta 0.008 --turing-grid ${3:-}"; }
fingerprint() {  # environment facts a resume depends on (the library refuses on any pin change; this file only explains a refusal)
  echo "date $(date)"; echo "boottime $(sysctl -n kern.boottime)"; echo "osversion $(sysctl -n kern.osversion)"; sw_vers | tr '\t' ' '
  echo "hw_model $(sysctl -n hw.model)"; shasum -a 256 $ZF/bin/libzfast.v14d.dylib /opt/homebrew/lib/libflint.dylib /opt/homebrew/lib/libgmp.dylib /opt/homebrew/lib/libmpfr.dylib 2>&1
  echo "auto_update $(defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates 2>&1)"; }
no_production() {
  if pgrep -f "gen_target5.py|replay_target5.py|atlas_v5.py" > /dev/null; then echo "REFUSING: an Atlas pipeline is running:"; pgrep -fl "gen_target5.py|replay_target5.py|atlas_v5.py"; return 1; fi
  fr=$(df -g /Users/kiosk | awk 'NR==2{print $4}'); [ "$fr" -lt 2 ] && { echo "REFUSING: free disk ${fr} GB < 2"; return 1; }
  return 0; }
