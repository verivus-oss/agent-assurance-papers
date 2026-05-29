import ast,os,math,sys
from collections import Counter
# CONTROL 1 — gate/cyclomatic threshold sweep.
# Reuses the IDENTICAL descriptor + strict shape-candidate gate as
# per_method_trace_cov_generic.py; varies only (a) the load-bearing cyclomatic
# floor and (b) the cosine twin-threshold, to test whether the cyc>=8 / cos>=0.95
# choices are load-bearing for the 87/71% vs 0/0% split. Pure ast; no RNG.
CF=['If','For','While','Try','ExceptHandler','With','Return','Raise','Break','Continue','Call','BoolOp','Compare','ListComp','Assign']
def maxdepth(n,d=0):
    m=d
    for c in ast.iter_child_nodes(n):
        m=max(m,maxdepth(c,d+1) if isinstance(c,(ast.If,ast.For,ast.While,ast.Try,ast.With,ast.AsyncFor,ast.AsyncWith)) else maxdepth(c,d))
    return m
def feats(fn):
    h=Counter()
    for n in ast.walk(fn):
        t=type(n).__name__
        if t in CF: h[t]+=1
    a=fn.args; arity=len(a.args)+len(a.kwonlyargs)+(1 if a.vararg else 0)+(1 if a.kwarg else 0)
    return dict(h=h,arity=arity,tot=sum(h.values()),cyc=1+h['If']+h['For']+h['While']+h['ExceptHandler']+h['BoolOp'],
               depth=maxdepth(fn),ret=h['Return'],loop=h['For']+h['While'])
def collect(root):
    out=[]
    for dp,_,fs in os.walk(root):
        if 'test' in dp.lower(): continue
        for f in fs:
            if not f.endswith('.py'): continue
            p=os.path.join(dp,f)
            try: tree=ast.parse(open(p,encoding='utf-8',errors='ignore').read())
            except: continue
            cls=[None]
            def rec(n):
                fe=feats(n)
                if fe['tot']==0: return
                out.append(dict(name=((cls[-1]+'.') if cls[-1] else '')+n.name,file=os.path.relpath(p,root),**fe))
            class V(ast.NodeVisitor):
                def visit_ClassDef(s,n):
                    cls.append(n.name); [s.visit(c) for c in n.body]; cls.pop()
                def visit_FunctionDef(s,n): rec(n)
                def visit_AsyncFunctionDef(s,n): rec(n)
            V().visit(tree)
    return out
def cos(a,b):
    ks=set(a)|set(b); dot=sum(a[k]*b[k] for k in ks)
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0
def best_strict_cos(m,dst):
    c=[g for g in dst if abs(g['arity']-m['arity'])<=1 and m['tot'] and 0.67<=g['tot']/m['tot']<=1.5
       and abs(g['depth']-m['depth'])<=1 and g['loop']==m['loop'] and abs(g['ret']-m['ret'])<=1]
    if not c: return 0.0
    return max(cos(m['h'],g['h']) for g in c)
L="/srv/repos/public/lineage/_v"
PKG={'v5':f"{L}/chardet-5.0.0/chardet",'v6':f"{L}/chardet-6.0.0/chardet",
     'v7':f"{L}/chardet-7.0.0/src/chardet",'csn':f"{L}/csn-3.4.7/src/charset_normalizer"}
M={k:collect(v) for k,v in PKG.items()}
CYC_FLOORS=[6,7,8,9,10]; COS_THR=[0.90,0.93,0.95,0.97]
PAIRS=[('v5','v6'),('v6','v5'),('v6','v7'),('v7','v6'),('v6','csn'),('csn','v6')]
for sl,dl in PAIRS:
    src,dst=M[sl],M[dl]
    print(f"\n=== {sl}->{dl}  load-bearing strict-twin rate (rows=cyc floor, cols=cos threshold) ===")
    print("cyc\\cos   "+ "".join(f"{c:>10.2f}" for c in COS_THR))
    for cf in CYC_FLOORS:
        lb=[m for m in src if m['cyc']>=cf]; n=len(lb)
        bc=[best_strict_cos(m,dst) for m in lb]
        cells=[]
        for ct in COS_THR:
            tw=sum(1 for b in bc if b>=ct)
            cells.append(f"{tw}/{n}={tw/n*100:.0f}%" if n else "n=0")
        print(f"cyc>={cf} (n={n:>2}) "+ "".join(f"{x:>10}" for x in cells))
