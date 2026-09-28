# aas-corner-fe — AAS corner method, FE calibration campaign (code_aster v8 model)

Non-linear 3D damage model (ENDO_FISS_EXP + 3D_GRAD_VARI) of a two-face concrete corner with
one anchor per face, h_ef = 100 mm, d = 16 mm, C30/37. Purpose: measure the FE interaction of
the two legs so the AAS secondary-leg factor r(c/h_ef) can be given the same bias against FE
that EN 1992-4 has on the single legs. Written by Claude for Yves de Lathouwer (אדיט), Sep 2026.

## Layout
- `mesh/`     three MED meshes: c = 50 (95 117 nodes), 75 (111 469), 100 (135 682)
- `jobs/`     one-step command files `<job>_sNN.comm` + multi-stage `<job>.export`
- `results/`  curves (`<job>.curve`, one line per converged load step), `camp.progress`, logs
- `run_campaign.sh`  the runner: resume from checkpoint, push results after every step
- `genjob.py` regenerates a job: `python3 genjob.py TAG MESH LOADS UMAX NSTEP SEG`

## Jobs (queue order)
`v8c75_TV` · `v8c50_TV` · `v8c100_V` · `v8c100_TV` · `v8c75_TV2` (shear head displaced 2×).
Done elsewhere, curves already in `results/`: `v8c75_T` (peak 73.05 kN @ 0.26 mm),
`v8c75_V` (16.47 kN @ 0.12), `v8c50_V` (8.12 kN @ 0.06). `v8c75_TV` is partial (to 0.12 mm).

## Setup (Linux, ~10 min, ~2 GB)
```bash
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
./bin/micromamba create -y -p $HOME/mm/envs/aster -c conda-forge code-aster=18.1.6 gmsh python-gmsh
export PATH=$HOME/mm/envs/aster/bin:$PATH     # provides run_aster
```
## Run
```bash
./run_campaign.sh                       # whole queue
JOBS="v8c100_V v8c100_TV" ./run_campaign.sh   # a subset
```
Memory: each combined job needs ~4 GB with MUMPS out-of-core; on an 8 GB machine keep
`P memory_limit` ≤ 3000 in the export. From step 0.14 mm the c75 combined job runs with `NEWTON/MATR_RIGI_SYME='OUI'`
(symmetrised tangent, half the factor memory), `MIXER_PRECISION='OUI'` and `PCENT_PIVOT=10`,
because the full non-symmetric double-precision factorisation was killed by the kernel there
(8 GB machine). This conda build has no PETSc.

## What "done" means
A job is finished only when its curve ends with `STOP peak <N>` (total force fell below
0.9 × peak). `STOP solver` means the Newton scheme failed after 5 subdivisions.
Curve columns: u [mm] · total [N] · tension head [N] · shear head [N] (half model ×2).
