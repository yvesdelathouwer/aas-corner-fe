# Campaign results (code_aster v8, h_ef = 100 mm, d = 16 mm, C30/37)

| Job | Result | Peak total force | at u |
|---|---|---|---|
| v8c75_T  | STOP peak (earlier run) | 73.05 kN | 0.26 mm |
| v8c50_V  | STOP peak (earlier run) | 8.12 kN | 0.06 mm |
| v8c75_V  | peak (earlier run) | 16.47 kN | 0.12 mm |
| v8c100_V | no drop to 0.75 mm, plateau | 24.13 kN | 0.75 mm |
| v8c75_TV | STOP peak | 56.28 kN | 0.14 mm |
| v8c50_TV | STOP peak | 57.34 kN | 0.20 mm |
| v8c100_TV | STOP peak | 80.25 kN | 0.2045 mm |
| v8c75_TV2 | STOP peak | 51.87 kN | 0.14 mm |

## v8c100_V against EN 1992-4 (single-leg shear, concrete edge failure)
V_Rk,c = k1 · d^α · l_f^β · √f_ck · c^1.5, α = 0.1 (l_f/c)^0.5, β = 0.1 (d/c)^0.2,
d = 16, l_f = h_ef = 100, f_ck = 30, k1 = 2.4 (uncracked; the FE concrete is uncracked).

| c [mm] | EN 1992-4 [kN] | FE [kN] | FE / EN |
|---|---|---|---|
| 50  | 9.93  | 8.12  | 0.82 |
| 75  | 16.49 | 16.47 | 1.00 |
| 100 | 23.87 | 24.13 (plateau) | 1.01 |

v8c100_V follows the EN 1992-4 edge-shear equation (FE/EN = 1.01, same as c = 75),
so the load range was not enlarged further. Its capacity is the plateau value; no
post-peak drop (STOP peak rule) was reached within 0.75 mm.
