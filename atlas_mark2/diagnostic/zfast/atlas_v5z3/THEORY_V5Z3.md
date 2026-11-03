# atlas_v5z3 = atlas_v5z2 with libzfast.v13b (2026-10-19)

The provider is re-pinned from libzfast.v12a to libzfast.v13b, which is v12a plus the review2 fixes:
- **m1:** `ok = 0` rows are indeterminate;
- **m2:** the session guards;
- **m3:** the bucket-remainder abort is removed, because short remainders are finished in the head;
- **m4:** full printed balls.

Mathematics and code paths are otherwise identical (THEORY_V5Z2.md, THEORY_M5, THEORY_M5b). The run scripts point at this tree. Every
other file is a byte copy of atlas_v5z2.
