#!/usr/bin/env python3
"""Pilot geometric crosswalk (not a catalogue of available download files).

Requires pyproj and shapely. JGD2011 horizontal coordinates only; all sheet edges
and mesh edges are densified. CSV relationships, geographic GeoJSON and coverage
QA are written; original sheet bounds are supplied by the plugin's tested core.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from forest_map_sheet_generator.core.grid import sheet_from_code
from pyproj import Transformer
from shapely.geometry import Polygon, box, mapping
from shapely.ops import unary_union

FACTORS = {1: (1.5, 1), 2: (12, 8), 3: (120, 80)}


def mesh_code(level, i, j):
    n = {1: 1, 2: 8, 3: 80}[level]
    p, q = i // n, j // n
    if not 0 <= p <= 99 or not 0 <= q <= 99:
        raise ValueError('Mesh is outside the supported regional code domain')
    code = f'{p:02d}{q:02d}'
    if level >= 2:
        sub = 1 if level == 2 else 10
        code += f'{i % n // sub}{j % n // sub}'
    if level == 3:
        code += f'{i % 10}{j % 10}'
    return code


def mesh_bounds(level, i, j):
    a, b = FACTORS[level]
    return 100 + j/b, i/a, 100+(j+1)/b, (i+1)/a


def ring(e0,n0,e1,n1,nx,ny):
    # Shared mesh edges use identical coordinates (no gaps between neighbours).
    points = [(e0+(e1-e0)*k/nx,n0) for k in range(nx)]
    points += [(e1,n0+(n1-n0)*k/ny) for k in range(ny)]
    points += [(e1-(e1-e0)*k/nx,n1) for k in range(nx)]
    points += [(e0,n1-(n1-n0)*k/ny) for k in range(ny)]
    return points + [points[0]]


def calculate(code, level, step):
    if step <= 0 or not math.isfinite(step):
        raise ValueError('Densification step must be positive and finite')
    sheet = sheet_from_code(code)
    crs = f'EPSG:{6668+sheet.zone}'
    to_geo = Transformer.from_crs(crs, 'EPSG:6668', always_xy=True)
    to_plane = Transformer.from_crs('EPSG:6668', crs, always_xy=True)
    footprint = box(sheet.e_min,sheet.n_min,sheet.e_max,sheet.n_max)
    planar_ring = ring(sheet.e_min,sheet.n_min,sheet.e_max,sheet.n_max,
                       math.ceil(sheet.width/step),math.ceil(sheet.height/step))
    geo_ring = [to_geo.transform(*p) for p in planar_ring]
    xs,ys = zip(*geo_ring)
    a,b = FACTORS[level]
    rows, intersections, features = [], [], []
    # One-cell padding protects the candidate envelope of curved boundaries.
    for i in range(math.floor(min(ys)*a)-1,math.floor(max(ys)*a)+2):
        for j in range(math.floor((min(xs)-100)*b)-1,math.floor((max(xs)-100)*b)+2):
            bounds = mesh_bounds(level,i,j)
            e0,n0,e1,n1 = bounds
            nx = max(1,math.ceil((e1-e0)*111320/step))
            ny = max(1,math.ceil((n1-n0)*111320/step))
            geographic_ring = ring(*bounds,nx,ny)
            polygon = Polygon([to_plane.transform(*p) for p in geographic_ring])
            if not polygon.is_valid: raise ValueError('Invalid transformed mesh')
            intersection = footprint.intersection(polygon)
            area = intersection.area
            if area <= 0: continue
            mc = mesh_code(level,i,j)
            rows.append({'sheet_code':code,'grid_type':sheet.grid_type,'zone':sheet.zone,
                'sheet_crs':crs,'mesh_code':mc,'mesh_level':level,'mesh_crs':'EPSG:6668',
                'overlap_area_m2':area,'sheet_coverage_ratio':area/footprint.area,
                'mesh_coverage_ratio':area/polygon.area,'relation':'positive_area',
                'densify_step_m':step,'availability':'unverified'})
            intersections.append(intersection)
            features.append({'type':'Feature','properties':{'mesh_code':mc,'mesh_level':level,'sheet_code':code},
                             'geometry':mapping(Polygon(geographic_ring))})
    union = unary_union(intersections)
    gap = footprint.difference(union).area
    qa = {'sheet_code':code,'mesh_level':level,'mesh_count':len(rows),
          'sheet_area_m2':footprint.area,'sum_overlap_m2':sum(r['overlap_area_m2'] for r in rows),
          'uncovered_m2':gap,'sum_error_m2':abs(sum(r['overlap_area_m2'] for r in rows)-footprint.area)}
    if gap > 0.01 or qa['sum_error_m2'] > 0.01:
        raise ValueError(f'Coverage QA failed: {qa}')
    sheet_feature = {'type':'Feature','properties':{'sheet_code':code,'kind':'sheet','crs_source':crs},
                     'geometry':mapping(Polygon(geo_ring))}
    return rows,qa,[sheet_feature]+features


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codes',nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--step',type=float,default=100)
    args=parser.parse_args()
    # Never overwrite a user's earlier pilot output.
    args.output.mkdir(parents=True,exist_ok=False)
    all_rows, all_qa, features = [], [], []
    for code in args.codes:
        per_level={}
        for level in (1,2,3):
            rows,qa,fs=calculate(code,level,args.step)
            finer,fqa,ffs=calculate(code,level,args.step/2)
            by_code={r['mesh_code']:r for r in finer}
            if {r['mesh_code'] for r in rows} != set(by_code):
                raise ValueError(f'Unstable candidate set: {code} level{level}')
            qa['stable_candidate_set']=True
            qa['max_overlap_change_m2']=max(abs(r['overlap_area_m2']-by_code[r['mesh_code']]['overlap_area_m2']) for r in rows)
            # Save the finer calculation, report both numerical QA records.
            qa['finer_coverage']=fqa
            per_level[level]={r['mesh_code'] for r in finer}
            all_rows.extend(finer);all_qa.append(qa);features.extend(ffs if level == 1 else ffs[1:])
        for level,digits in ((1,4),(2,6)):
            if per_level[level] != {m[:digits] for m in per_level[3]}:
                raise ValueError(f'Parent aggregation differs: {code} level{level}')
    with (args.output/'sheet_mesh_crosswalk.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(all_rows[0]));w.writeheader();w.writerows(all_rows)
    (args.output/'coverage_qa.json').write_text(json.dumps(all_qa,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'preview.geojson').write_text(json.dumps({'type':'FeatureCollection','crs':{'type':'name','properties':{'name':'urn:ogc:def:crs:EPSG::6668'}},'features':features},ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'pairs':len(all_rows),'sheets':len(args.codes),'qa_passed':True,'availability':'unverified'}))


if __name__=='__main__': main()
