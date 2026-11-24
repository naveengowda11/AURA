#!/usr/bin/env python3
"""Read an Apple Health export (export.zip or export.xml) ON YOUR OWN COMPUTER and send only DAILY summaries to AURA.
Covers iPhone + Apple Watch data. Raw records never leave your machine.
  iPhone: Health app > profile picture > Export All Health Data.
  python import_apple_health.py export.zip --server http://localhost:8000 --token aura_dev_XXXX   (add --dry-run to preview)"""
import argparse, json, sys, zipfile, urllib.request, datetime as dt, xml.etree.ElementTree as ET
from collections import defaultdict
T={"HKQuantityTypeIdentifierRestingHeartRate":"rhr","HKQuantityTypeIdentifierStepCount":"steps","HKQuantityTypeIdentifierBodyMass":"weight_kg",
   "HKQuantityTypeIdentifierBloodPressureSystolic":"sbp","HKQuantityTypeIdentifierBloodGlucose":"glucose_mgdl","HKCategoryTypeIdentifierSleepAnalysis":"sleep_hours"}
def ts(s): return dt.datetime.strptime(s[:19],"%Y-%m-%d %H:%M:%S")
def parse(f,days=120):
    cut=dt.date.today()-dt.timedelta(days=days); acc=defaultdict(lambda:defaultdict(lambda:defaultdict(list)))
    for _,e in ET.iterparse(f):
        m=T.get(e.get("type")) if e.tag=="Record" else None
        if m:
            s,en,src=ts(e.get("startDate")),ts(e.get("endDate")),e.get("sourceName","?")
            if m=="sleep_hours":
                v=(en-s).total_seconds()/3600 if "Asleep" in e.get("value","") else None; d=en.date()   # InBed/Awake are ignored
            else:
                v=float(e.get("value")); d=s.date(); u=e.get("unit","")
                if m=="weight_kg" and u=="lb": v*=0.45359237
                if m=="glucose_mgdl" and u.startswith("mmol"): v*=18.016
            if v is not None and d>=cut: acc[d.isoformat()][m][src].append(v)
        e.clear()
    out=[]
    for d,ms in sorted(acc.items()):
        r={"date":d}
        for m,srcs in ms.items():   # steps/sleep: use the single most complete source (avoids iPhone+Watch double counting)
            r[m]=round(max(sum(v) for v in srcs.values()),2) if m in("steps","sleep_hours") else round(sum(x for v in srcs.values() for x in v)/sum(len(v) for v in srcs.values()),1)
        out.append(r)
    return out
def main():
    a=argparse.ArgumentParser(); a.add_argument("file"); a.add_argument("--days",type=int,default=120); a.add_argument("--server",default="http://localhost:8000"); a.add_argument("--token"); a.add_argument("--dry-run",action="store_true"); o=a.parse_args()
    if o.file.endswith(".zip"):
        z=zipfile.ZipFile(o.file); n=next(x for x in z.namelist() if x.endswith("export.xml")); f=z.open(n)
    else: f=open(o.file,"rb")
    recs=parse(f,o.days); print(f"{len(recs)} days summarised")
    if o.dry_run or not o.token: print(json.dumps(recs[:5],indent=1)); return print("(not sent: use --token to upload)" if not o.dry_run else "")
    for i in range(0,len(recs),300):
        rq=urllib.request.Request(o.server.rstrip("/")+"/api/ingest/daily",json.dumps({"records":recs[i:i+300],"source":"apple_health"}).encode(),{"Content-Type":"application/json","Authorization":"Bearer "+o.token})
        print(urllib.request.urlopen(rq,timeout=60).read().decode())
if __name__=="__main__": main()
