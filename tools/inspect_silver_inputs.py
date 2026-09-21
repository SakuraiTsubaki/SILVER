#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROM_EXTS={".gb",".gbc"}
SAVE_EXTS={".sav"}

def hashes(data: bytes) -> dict[str,str]:
    return {"sha1": hashlib.sha1(data).hexdigest(), "sha256": hashlib.sha256(data).hexdigest()}

def inspect_rom(path: Path) -> dict:
    data=path.read_bytes()
    if len(data) < 0x150:
        raise ValueError(f"{path}: too small for a Game Boy header")
    out={"kind":"rom","file":path.name,"size":len(data),**hashes(data)}
    out["header"]={
        "title": data[0x134:0x143].decode("ascii","replace").rstrip("\0"),
        "cgb_flag": data[0x143],
        "sgb_flag": data[0x146],
        "cartridge_type": data[0x147],
        "rom_size_code": data[0x148],
        "ram_size_code": data[0x149],
        "destination_code": data[0x14A],
        "version": data[0x14C],
        "header_checksum": data[0x14D],
        "global_checksum": int.from_bytes(data[0x14E:0x150],"big"),
    }
    return out

def inspect_save(path: Path) -> dict:
    data=path.read_bytes()
    core=data[:32768]
    tail=data[32768:]
    return {
        "kind":"save","file":path.name,"size":len(data),**hashes(data),
        "raw_sram_bytes":len(core),"host_tail_bytes":len(tail),
        "core_sha256":hashlib.sha256(core).hexdigest(),
        "banks":[{
            "bank":i,
            "nonzero_bytes":sum(x != 0 for x in core[i*8192:(i+1)*8192]),
            "non_ff_bytes":sum(x != 0xFF for x in core[i*8192:(i+1)*8192]),
        } for i in range(4)] if len(core)==32768 else []
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("inputs",nargs="+",type=Path)
    ap.add_argument("-o","--output",type=Path)
    ns=ap.parse_args()
    results=[]
    for path in ns.inputs:
        ext=path.suffix.lower()
        if ext in ROM_EXTS:
            results.append(inspect_rom(path))
        elif ext in SAVE_EXTS:
            results.append(inspect_save(path))
        else:
            raise SystemExit(f"unsupported input: {path}")
    payload={"schema_version":1,"inputs":results}
    text=json.dumps(payload,indent=2,ensure_ascii=False)+"\n"
    if ns.output:
        ns.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
