# aas-corner-fe — AAS corner method, FE calibration campaign

The package is uploaded in two parts (GitHub web upload limit). **First step in any session:**

```bash
cat aas-corner-fe.tgz.part-00 aas-corner-fe.tgz.part-01 > aas-corner-fe.tar.gz
md5sum aas-corner-fe.tar.gz        # expect 4c93f3ec06b6e0098530a633d77949c2
tar xzf aas-corner-fe.tar.gz --strip-components=1   # unpacks mesh/, jobs/, results/, run_campaign.sh, genjob.py, and the full README
git add -A && git commit -m "unpack campaign package" && git push
```

Then follow the unpacked `README.md` (setup of code_aster 18.1.6 with micromamba, then `./run_campaign.sh`).
Written for Yves de Lathouwer (אדיט), 24 Sep 2026.
