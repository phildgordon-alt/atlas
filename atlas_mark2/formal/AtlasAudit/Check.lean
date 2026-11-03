/-
Atlas audit — the executable checks (core Lean only: no Mathlib, so that `lake exe atlas_audit` links
without compiling Mathlib).

Every function here is a Boolean check on exact rationals (`Rat`, core). Its correctness theorem —
"check = true ⇒ the set-theoretic statement over ℝ" — is proved in `Atlas/Audit.lean` (which imports
Mathlib). The executable `AtlasAudit/Main.lean` runs exactly these functions on the exported data.
-/

namespace AtlasAudit

/-- a candidate region [x0, x1] × [d0, d1] -/
structure Reg where
  x0 : Rat
  x1 : Rat
  d0 : Rat
  d1 : Rat

/-- a sign-change interval [t1, t2] -/
structure Iv where
  t1 : Rat
  t2 : Rat

/-- one box of a v4 all-open model: `on` = [lo, hi] × {0} with f = 1, `off` = [lo, hi] × [0, 1/2], f = 2 -/
structure Var where
  on : Bool
  lo : Rat
  hi : Rat
  dlo : Rat
  dhi : Rat

/-- the exported data of one certificate (only the exact/combinatorial part; rows and duals stay with Arb) -/
structure CertD where
  group : String
  file : String
  np : Bool          -- a no-parity (S-layer) certificate, region [s0, s1] × {0}
  passed : Bool      -- TRUSTED: the Arb replay verdict, plain AND hardened
  nc : Bool          -- marked as a negative control
  wlo : Rat
  whi : Rat
  regions : List Reg
  ivs : List Iv
  central : Option Nat
  vars : List Var

/-! ### per-certificate checks -/

/-- region inside the window, nondegenerate, d-range exactly [0, 1/2] (main) or {0} (no-parity). -/
def regionOk (np : Bool) (wlo whi : Rat) (r : Reg) : Bool :=
  decide (wlo ≤ r.x0) && decide (r.x0 < r.x1) && decide (r.x1 ≤ whi) && decide (r.d0 = 0) &&
    (if np then decide (r.d1 = 0) else decide (r.d1 = 1 / 2))

/-- interval inside the window, t1 < t2 -/
def ivOk (wlo whi : Rat) (i : Iv) : Bool :=
  decide (wlo ≤ i.t1) && decide (i.t1 < i.t2) && decide (i.t2 ≤ whi)

/-- consecutive intervals strictly separated: t2_k < t1_{k+1} (sorted and pairwise disjoint) -/
def sortedDisjoint : List Iv → Bool
  | [] => true
  | [_] => true
  | a :: b :: l => decide (a.t2 < b.t1) && sortedDisjoint (b :: l)

/-- the closed interval meets 0 -/
def meets0 (i : Iv) : Bool := decide (i.t1 ≤ 0) && decide (0 ≤ i.t2)

def CertD.m0 (c : CertD) : Nat := c.central.getD 0

/-- the reduction is used (m0 ≠ 0) -/
def CertD.used (c : CertD) : Bool := decide (c.m0 ≠ 0)

/-- the window contains the central ordinate 0 in its interior -/
def CertD.has0 (c : CertD) : Bool := decide (c.wlo < 0) && decide (0 < c.whi)

/-- central policy (THEORY_389A §3, §6 (4)), with `expect` = the proved central order (2 for 389.a, 0 otherwise):
a central entry is recorded iff the reduction is used; the reduction is used iff the window contains 0 (and
expect ≠ 0); if used, m0 = expect and no sign-change interval meets 0. -/
def centralOk (expect : Nat) (c : CertD) : Bool :=
  (c.central.isSome == c.used) && (c.used == (c.has0 && decide (expect ≠ 0))) &&
    (!c.used || (decide (c.m0 = expect) && c.ivs.all (fun i => !meets0 i)))

/-- the all-open model: the boxes come in pairs on [lo,hi]×{0}, off [lo,hi]×[0,1/2]; returns the bins. -/
def binsOf : List Var → Option (List (Rat × Rat))
  | [] => some []
  | [_] => none
  | a :: b :: l =>
    if a.on && !b.on && decide (a.lo = b.lo) && decide (a.hi = b.hi) && decide (a.dlo = 0) &&
        decide (a.dhi = 0) && decide (b.dlo = 0) && decide (b.dhi = 1 / 2) then
      (binsOf l).map ((a.lo, a.hi) :: ·)
    else none

/-! ### exact 1-D covering (sweep) -/

/-- one step: `none` = nothing of [lo, …] covered yet; `some c` = [lo, c] covered. -/
def sweepStep (lo : Rat) : Option Rat → Rat × Rat → Option Rat
  | none, p => if p.1 ≤ lo ∧ lo ≤ p.2 then some p.2 else none
  | some c, p => if p.1 ≤ c then (if c ≤ p.2 then some p.2 else some c) else some c

def sweep (lo : Rat) (L : List (Rat × Rat)) : Option Rat := L.foldl (sweepStep lo) none

/-- [lo, hi] ⊂ ⋃ [a, b] over L. The list is sorted first (any order is SOUND; sorting only makes the
greedy sweep complete). -/
def coversB (lo hi : Rat) (L : List (Rat × Rat)) : Bool :=
  match sweep lo (L.mergeSort (fun p q => decide (p.1 ≤ q.1))) with
  | some c => decide (hi ≤ c)
  | none => false

/-- the model's bins cover the window -/
def modelOk (c : CertD) : Bool :=
  match binsOf c.vars with
  | some bs => coversB c.wlo c.whi bs
  | none => false

/-- all per-certificate conditions -/
def certOk (expect : Nat) (model : Bool) (c : CertD) : Bool :=
  !c.regions.isEmpty && c.regions.all (regionOk c.np c.wlo c.whi) && c.ivs.all (ivOk c.wlo c.whi) &&
    sortedDisjoint c.ivs && centralOk expect c && (!model || modelOk c)

/-! ### targets and claim (B) -/

/-- x-projections of the full-height regions (d0 ≤ 0, d1 ≥ 1/2) of PASSED main certificates in `groups` -/
def certRegions (groups : List String) (cs : List CertD) : List (Rat × Rat) :=
  (cs.filter (fun c => c.passed && !c.np && groups.contains c.group)).flatMap fun c =>
    (c.regions.filter (fun r => decide (r.d0 ≤ 0) && decide (1 / 2 ≤ r.d1))).map fun r => (r.x0, r.x1)

/-- exact tiling: [tlo, thi] × [0, 1/2] covered by regions of passed certificates -/
def targetOk (tlo thi : Rat) (groups : List String) (cs : List CertD) : Bool :=
  coversB tlo thi (certRegions groups cs)

/-- regions of the PASSED no-parity certificates of group g -/
def npSegs (g : String) (cs : List CertD) : List (Rat × Rat) :=
  (cs.filter (fun c => c.passed && c.np && c.group == g)).flatMap fun c => c.regions.map fun r => (r.x0, r.x1)

def rmax (a b : Rat) : Rat := if a ≤ b then b else a
def rmin (a b : Rat) : Rat := if a ≤ b then a else b

/-- claim (B) coverage (atlas_v4 §10 (iii)): for every passed main certificate of group g, every region and
every interval, cl(I) ∩ [x0, x1] is covered by regions of passed no-parity certificates of g. -/
def claimBOk (g : String) (cs : List CertD) : Bool :=
  (cs.filter (fun c => c.passed && !c.np && c.group == g)).all fun c =>
    c.regions.all fun r => c.ivs.all fun i =>
      if decide (i.t1 ≤ r.x1) && decide (r.x0 ≤ i.t2) then
        coversB (rmax i.t1 r.x0) (rmin i.t2 r.x1) (npSegs g cs)
      else true

end AtlasAudit
