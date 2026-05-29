import ast,os,math
from collections import Counter
# CONTROL 2 — null / unrelated-codebase baseline.
# Question: how surprising is the OBSERVED load-bearing strict-twin rate?
# Match each source package's load-bearing methods (cyc>=8) against (a) the REAL
# destination and (b) several UNRELATED Python stdlib packages (a no-relationship
# null). Identical descriptor + strict gate + cos>=0.95 as the main trace.
# If real v5->v6 (13/15) >> null and real v6->v7 / v6->csn (0/14) ~= null, then
# HIGH is a genuine signal while ~0 is just the no-relationship baseline (one-sided).
# Pure ast; deterministic; the only "randomness" is the fixed unrelated-pkg panel.
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
    if os.path.isfile(root):
        walks=[(os.path.dirname(root),[],[os.path.basename(root)])]
    else:
        walks=os.walk(root)
    for dp,_,fs in walks:
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
                out.append(dict(name=((cls[-1]+'.') if cls[-1] else '')+n.name,**fe))
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
def twins(lb,dst,thr=0.95):
    n=0
    for m in lb:
        c=[g for g in dst if abs(g['arity']-m['arity'])<=1 and m['tot'] and 0.67<=g['tot']/m['tot']<=1.5
           and abs(g['depth']-m['depth'])<=1 and g['loop']==m['loop'] and abs(g['ret']-m['ret'])<=1]
        if c and max(cos(m['h'],g['h']) for g in c)>=thr: n+=1
    return n
L="/srv/repos/public/lineage/_v"; S="/usr/lib64/python3.13"
PKG={'v5':f"{L}/chardet-5.0.0/chardet",'v6':f"{L}/chardet-6.0.0/chardet",
     'v7':f"{L}/chardet-7.0.0/src/chardet",'csn':f"{L}/csn-3.4.7/src/charset_normalizer"}
NULLS=['argparse.py','json','http','asyncio','logging','email','xml','statistics.py','fractions.py','difflib.py']
M={k:collect(v) for k,v in PKG.items()}
NM={n:collect(f"{S}/{n}") for n in NULLS}
def lb(pkg): return [m for m in M[pkg] if m['cyc']>=8]
REAL=[('v5','v6'),('v6','v7'),('v6','csn')]
print("Unrelated-Python null panel (stdlib), load-bearing cyc>=8, strict gate, cos>=0.95.\n")
for sl,dl in REAL:
    src=lb(sl); n=len(src)
    r=twins(src,M[dl])
    nullrates=[twins(src,NM[nm]) for nm in NULLS]
    mean=sum(nullrates)/len(nullrates)
    mx=max(nullrates)
    print(f"=== {sl} load-bearing methods (n={n}) ===")
    print(f"  REAL  {sl}->{dl:<4}: {r}/{n} = {r/n*100:.0f}%")
    print(f"  NULL  {sl}->unrelated stdlib (n={len(NULLS)} pkgs): mean {mean:.2f}/{n} = {mean/n*100:.0f}%, max {mx}/{n} = {mx/n*100:.0f}%")
    print(f"        per-null twins: "+", ".join(f"{nm}:{nr}" for nm,nr in zip(NULLS,nullrates)))
    print()
