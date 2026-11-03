First official build of libzfast v14c (2026-11-02 20:34; libzfast.v14c.dylib sha 2e648e10..., testhooks 38b86612...).
SUPERSEDED before any claim-bearing use: the M13 light fuzz (runs/m13/neg/asan/fuzz_m13_build1.log) found a second FLINT abort class
(mag_set_arf_dump on a radius mantissa that a mag cannot hold exactly; 3/300 cases).  Fixed in src/v14c (parse_arb_strict no longer
calls arb_load_str) and rebuilt as bin/libzfast.v14c.dylib.  Moved here (not deleted) under the no-delete rule; never use.
