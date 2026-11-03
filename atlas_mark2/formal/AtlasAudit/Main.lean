/-
`lake exe atlas_audit FILE...` — reads the exact exports written by `export/export_certs.py` and runs the
checks of `AtlasAudit.Check` (whose correctness theorems are in `Atlas/Audit.lean`).
Exit code 0 iff no violation in any non-negative-control dataset (a dataset whose name ends in `_nc` is a
negative control: its violations are reported, not failed on).
TRUSTED here (not proved): this parser and the exporter (both small; the exporter converts each binary64
to its exact rational), and the `passed` verdicts (the Arb replays).
-/
import AtlasAudit.Check

open AtlasAudit

namespace AtlasAudit

def parseRat (s : String) : Except String Rat :=
  match s.splitOn "/" with
  | [p] => match p.toInt? with
    | some n => .ok (n : Rat)
    | none => .error s!"bad rational {s}"
  | [p, q] => match p.toInt?, q.toNat? with
    | some n, some d => if d = 0 then .error s!"zero denominator {s}" else .ok (mkRat n d)
    | _, _ => .error s!"bad rational {s}"
  | _ => .error s!"bad rational {s}"

def parseBit (s : String) : Except String Bool :=
  if s = "1" then .ok true else if s = "0" then .ok false else .error s!"bad bit {s}"

structure Target where
  name : String
  lo : Rat
  hi : Rat
  groups : List String

structure Dataset where
  name : String := ""
  expect : Nat := 0
  model : Bool := false
  certs : Array CertD := #[]
  targets : Array Target := #[]
  claimB : Array String := #[]

def toks (l : String) : List String := (l.splitOn " ").filter (· ≠ "")

/-- parse one exported dataset file -/
def parseDataset (lines : Array String) : Except String Dataset := do
  let mut ds : Dataset := {}
  let mut cur : Option CertD := none
  let mut ln := 0
  for l in lines do
    ln := ln + 1
    match toks l with
    | [] => pure ()
    | ["DATASET", n, e, m] =>
      let some e' := e.toNat? | throw s!"line {ln}: bad expect"
      ds := { ds with name := n, expect := e', model := (← parseBit m) }
    | ["CERT", g, f, k, p, nc, wlo, whi] =>
      if cur.isSome then throw s!"line {ln}: CERT inside CERT"
      let np ← if k = "np" then pure true else if k = "main" then pure false else throw s!"line {ln}: kind"
      cur := some { group := g, file := f, np := np, passed := (← parseBit p), nc := (← parseBit nc),
                    wlo := (← parseRat wlo), whi := (← parseRat whi), regions := [], ivs := [],
                    central := none, vars := [] }
    | ["REG", a, b, c, d] =>
      let some c0 := cur | throw s!"line {ln}: REG outside CERT"
      cur := some { c0 with regions := c0.regions ++ [⟨← parseRat a, ← parseRat b, ← parseRat c, ← parseRat d⟩] }
    | ["IV", a, b] =>
      let some c0 := cur | throw s!"line {ln}: IV outside CERT"
      cur := some { c0 with ivs := ⟨← parseRat a, ← parseRat b⟩ :: c0.ivs }   -- reversed below
    | ["CENTRAL", m] =>
      let some c0 := cur | throw s!"line {ln}: CENTRAL outside CERT"
      let some m' := m.toNat? | throw s!"line {ln}: bad m0"
      if c0.central.isSome then throw s!"line {ln}: two CENTRAL lines"
      cur := some { c0 with central := some m' }
    | ["VAR", k, a, b, c, d] =>
      let some c0 := cur | throw s!"line {ln}: VAR outside CERT"
      let on ← if k = "on" then pure true else if k = "off" then pure false else throw s!"line {ln}: var kind"
      cur := some { c0 with vars := ⟨on, ← parseRat a, ← parseRat b, ← parseRat c, ← parseRat d⟩ :: c0.vars }
    | ["END"] =>
      let some c0 := cur | throw s!"line {ln}: END outside CERT"
      ds := { ds with certs := ds.certs.push { c0 with ivs := c0.ivs.reverse, vars := c0.vars.reverse } }
      cur := none
    | ["TARGET", n, a, b, gs] =>
      ds := { ds with targets := ds.targets.push ⟨n, ← parseRat a, ← parseRat b, gs.splitOn ","⟩ }
    | ["CLAIMB", g] => ds := { ds with claimB := ds.claimB.push g }
    | _ => throw s!"line {ln}: cannot parse: {l.take 80}"
  if cur.isSome then throw "unterminated CERT"
  return ds

/-- which conditions fail, for the report -/
def diagnose (expect : Nat) (model : Bool) (c : CertD) : List String :=
  (if c.regions.isEmpty then ["no region"] else []) ++
  (if c.regions.all (regionOk c.np c.wlo c.whi) then [] else ["region not in window / d-range"]) ++
  (if c.ivs.all (ivOk c.wlo c.whi) then [] else ["interval not in window or t1 >= t2"]) ++
  (if sortedDisjoint c.ivs then [] else ["intervals not sorted/disjoint"]) ++
  (if centralOk expect c then [] else [s!"central policy (m0 = {c.m0}, recorded = {c.central.isSome}, window ∋ 0: {c.has0})"]) ++
  (if !model || modelOk c then [] else ["v4 model: bins malformed or do not cover the window"])

def runDataset (ds : Dataset) : IO Nat := do
  let isNC := ds.name.endsWith "_nc"
  let cs := ds.certs.toList
  let main := cs.filter (!·.np)
  let np := cs.filter (·.np)
  let nIv := cs.foldl (fun s c => s + c.ivs.length) 0
  let nReg := cs.foldl (fun s c => s + c.regions.length) 0
  let nCentral := cs.filter (·.used) |>.length
  let nPassed := cs.filter (·.passed) |>.length
  let nVars := cs.foldl (fun s c => s + c.vars.length) 0
  let mut viol : Nat := 0
  let mut lines : Array String := #[]
  for c in cs do
    if !certOk ds.expect ds.model c then
      viol := viol + 1
      if lines.size < 40 then lines := lines.push s!"  CERT {c.group}/{c.file}: {diagnose ds.expect ds.model c}"
    if !isNC && c.nc then
      viol := viol + 1; lines := lines.push s!"  CERT {c.group}/{c.file}: marked negative_control in a real dataset"
    if !isNC && !c.passed then
      lines := lines.push s!"  note: {c.group}/{c.file} did not pass the replay (not used for coverage)"
  let mut tOk := 0
  let mut nT := 0
  let mut dOk := 0
  let mut nD := 0
  for t in ds.targets do
    if t.name.endsWith ":decimal" then
      -- the claimed DECIMAL endpoints (exact decimal rationals), when they differ from the stored binary64:
      -- reported separately (a claim-wording precision check, not a certificate-file violation)
      nD := nD + 1
      if targetOk t.lo t.hi t.groups cs then dOk := dOk + 1
      else lines := lines.push s!"  decimal-endpoint check: {t.name} [{t.lo}, {t.hi}] not covered (binary64 target is)"
    else
      nT := nT + 1
      if targetOk t.lo t.hi t.groups cs then tOk := tOk + 1
      else
        viol := viol + 1; lines := lines.push s!"  TARGET {t.name} [{t.lo}, {t.hi}] NOT covered"
  let mut bOk := 0
  for g in ds.claimB do
    if claimBOk g cs then bOk := bOk + 1
    else
      viol := viol + 1; lines := lines.push s!"  CLAIM (B) {g}: S-layer coverage fails"
  IO.println s!"dataset {ds.name}{if isNC then " (NEGATIVE CONTROLS: violations expected where the control breaks a checked condition)" else ""}"
  IO.println s!"  certificates {cs.length} (main {main.length}, no-parity {np.length}), replay-passed {nPassed}, regions {nReg}, intervals {nIv}, central reductions {nCentral}, model boxes {nVars}"
  IO.println s!"  expect_m0 {ds.expect}; per-certificate checks passed {cs.length - (cs.filter (fun c => !certOk ds.expect ds.model c)).length}/{cs.length}"
  IO.println s!"  targets covered (target x [0,1/2], exact, binary64 endpoints as stored) {tOk}/{nT}; claim (B) groups {bOk}/{ds.claimB.size}; decimal-endpoint versions covered {dOk}/{nD}"
  for l in lines do IO.println l
  IO.println s!"  VIOLATIONS {viol}"
  return (if isNC then 0 else viol)

end AtlasAudit

def main (args : List String) : IO UInt32 := do
  let mut total := 0
  for f in args do
    let ls ← IO.FS.lines f
    match parseDataset ls with
    | .error e => IO.eprintln s!"{f}: PARSE ERROR {e}"; total := total + 1
    | .ok ds => total := total + (← runDataset ds)
  IO.println s!"TOTAL VIOLATIONS (non-control datasets): {total}"
  return (if total = 0 then 0 else 1)
