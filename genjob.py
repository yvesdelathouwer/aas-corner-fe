import os, sys
# genjob.py TAG MESH LOADS UMAX NSTEP SEG
TAG,MESH,LOADS,UMAX,NSTEP,SEG = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
D='__ROOT__'
dt=UMAX/NSTEP
targets=[round(dt*(i+1),10) for i in range(NSTEP)]
segs=[targets[i:i+SEG] for i in range(0,len(targets),SEG)]

HEAD = """DEBUT(LANG='EN', PAR_LOT='NON')
mesh=LIRE_MAILLAGE(UNITE=20, FORMAT='MED')
mesh=DEFI_GROUP(reuse=mesh, MAILLAGE=mesh, CREA_GROUP_NO=_F(GROUP_MA=('SYMZ','FARX','FARY','HEADT','HEADV')))
model=AFFE_MODELE(MAILLAGE=mesh, AFFE=(
    _F(GROUP_MA=('CONC','HZ'), PHENOMENE='MECANIQUE', MODELISATION='3D_GRAD_VARI'),
    _F(GROUP_MA=('STEEL','SLV','HZH'), PHENOMENE='MECANIQUE', MODELISATION='3D')))
mat=DEFI_MATER_GC(ENDO_FISS_EXP=_F(E=32836.56803133079, NU=0.2, FT=2.896468153816889, FC=38.0, GF=0.14050245330952899, P=1.5, LARG_BANDE=12, REST_RIGI_FC=0.))
matH=DEFI_MATER_GC(ENDO_FISS_EXP=_F(E=32836.56803133079, NU=0.2, FT=2.896468153816889, FC=76.0, GF=0.14050245330952899, P=1.5, LARG_BANDE=12, REST_RIGI_FC=0.))
matHH=DEFI_MATERIAU(ELAS=_F(E=32836.56803133079, NU=0.2))
stl=DEFI_MATERIAU(ELAS=_F(E=210000., NU=0.3))
slvm=DEFI_MATERIAU(ELAS=_F(E=10., NU=0.3))
fmat=AFFE_MATERIAU(MAILLAGE=mesh, AFFE=(_F(GROUP_MA='CONC', MATER=mat), _F(GROUP_MA='HZ', MATER=matH), _F(GROUP_MA='HZH', MATER=matHH), _F(GROUP_MA='STEEL', MATER=stl), _F(GROUP_MA='SLV', MATER=slvm)))
fix=AFFE_CHAR_MECA(MODELE=model, DDL_IMPO=(_F(GROUP_MA='SYMZ', DZ=0.), _F(GROUP_MA='FARX', DX=0.), _F(GROUP_MA='FARY', DY=0.)))
grp=[]
if 'T' in '__LOADS__': grp.append('HEADT')
if 'V' in '__LOADS__': grp.append('HEADV')
load=AFFE_CHAR_MECA(MODELE=model, DDL_IMPO=tuple(_F(GROUP_MA=g, DX=-(2.0 if (g=='HEADV' and '2' in '__LOADS__') else 1.0)) for g in grp))
ramp=DEFI_FONCTION(NOM_PARA='INST', VALE=(0.,0.,__UMAX__,__UMAX__))
steps=DEFI_LIST_REEL(DEBUT=0., INTERVALLE=_F(JUSQU_A=__UMAX__, NOMBRE=__NSTEP__))
times=DEFI_LIST_INST(DEFI_LIST=_F(LIST_INST=steps), ECHEC=_F(EVENEMENT='ERREUR', ACTION='DECOUPE', SUBD_METHODE='MANUEL', SUBD_PAS=2, SUBD_NIVEAU=5))
"""
BODY = """
LOADS='__LOADS__'
CURVE='__D__/__TAG__.curve'
common=dict(MODELE=model, CHAM_MATER=fmat, EXCIT=(_F(CHARGE=fix), _F(CHARGE=load, FONC_MULT=ramp)),
        COMPORTEMENT=(_F(RELATION='ENDO_FISS_EXP', GROUP_MA=('CONC','HZ')), _F(RELATION='ELAS', GROUP_MA=('STEEL','SLV','HZH'))),
        NEWTON=_F(MATRICE='TANGENTE', REAC_ITER=1),
        CONVERGENCE=_F(RESI_GLOB_RELA=1.E-4, ITER_GLOB_MAXI=30), ARCHIVAGE=_F(PAS_ARCH=1), SOLVEUR=_F(METHODE='MUMPS', GESTION_MEMOIRE='OUT_OF_CORE'))
import os, re
tcur=0.0; peak=0.0; stopped=False
if os.path.exists(CURVE):
    for line in open(CURVE):
        m=re.match(r'CURVE\\s+(\\S+)\\s+(\\S+)', line)
        if m:
            tcur=max(tcur, float(m.group(1))); peak=max(peak, float(m.group(2)))
        if line.startswith('STOP'): stopped=True
def reac(res, t):
    r2=CALC_CHAMP(RESULTAT=res, FORCE='REAC_NODA', INST=t)
    vals={}
    for g in ('HEADT','HEADV'):
        try:
            tb=POST_RELEVE_T(ACTION=_F(OPERATION='EXTRACTION', INTITULE='R', RESULTAT=r2, NOM_CHAM='REAC_NODA',
                                       GROUP_NO=g, RESULTANTE='DX', INST=t)).EXTR_TABLE().values()
            vals[g]=-tb['DX'][-1]*2
        except Exception:
            vals[g]=0.
    DETRUIRE(NOM=r2)
    return vals
TARGETS=__TARGETS__
for tn in TARGETS:
    if stopped or tn <= tcur+1e-9: continue
    try:
        if tcur < 1e-12 and '__FIRST__'=='1':
            res=STAT_NON_LINE(INCREMENT=_F(LIST_INST=times, INST_FIN=tn), **common)
        else:
            res=STAT_NON_LINE(reuse=res, ETAT_INIT=_F(EVOL_NOLI=res), INCREMENT=_F(LIST_INST=times, INST_FIN=tn), **common)
    except Exception as exc:
        print('AASSTOP at', tcur, exc, flush=True)
        open(CURVE,'a').write('STOP solver %g\\n'%tcur); stopped=True; break
    tcur=tn
    v=reac(res, tcur)
    tot=(v['HEADT'] if 'T' in LOADS else 0.)+(v['HEADV'] if 'V' in LOADS else 0.)
    peak=max(peak, tot)
    open(CURVE,'a').write('CURVE %g %g %g %g\\n'%(tcur,tot,v['HEADT'],v['HEADV']))
    print('AASCURVE %g %g %g %g'%(tcur,tot,v['HEADT'],v['HEADV']), flush=True)
    if tot < 0.9*peak:
        open(CURVE,'a').write('STOP peak %g\\n'%peak); stopped=True; break
FIN()
"""
def fill(s, first):
    return (s.replace('__LOADS__',LOADS).replace('__UMAX__',repr(UMAX)).replace('__NSTEP__',str(NSTEP))
             .replace('__D__',D).replace('__TAG__',TAG).replace('__FIRST__','1' if first else '0'))

files=[]
for k,seg in enumerate(segs):
    head = fill(HEAD, k==0) if k==0 else "POURSUITE(LANG='EN', PAR_LOT='NON')\n"
    body = fill(BODY, k==0).replace('__TARGETS__', repr(seg))
    fn='%s/%s_s%02d.comm'%(D,TAG,k)
    open(fn,'w').write(head+body); files.append(fn)
exp=['P time_limit 20000','P memory_limit 4200','P ncpus 2','P mpi_nbcpu 1']
for fn in files: exp.append('F comm %s D 1'%fn)
exp.append('F mmed %s/%s D 20'%(D,MESH))
exp.append('F mess %s/%s.mess R 6'%(D,TAG))
open('%s/%s.export'%(D,TAG),'w').write('\n'.join(exp)+'\n')
print('%s: %d segments, dt=%.4f, targets %s..%s'%(TAG,len(segs),dt,targets[0],targets[-1]))
