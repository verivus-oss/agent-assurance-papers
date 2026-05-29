import ast,sys,math
from collections import Counter
def find(path,name):
    t=ast.parse(open(path).read())
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name: return n
    return None
CFSET=['If','For','While','Try','ExceptHandler','With','Return','Raise','Break','Continue','Call','BoolOp','Compare','ListComp','Assign']
def hist(fn):
    c=Counter()
    for n in ast.walk(fn):
        t=type(n).__name__
        if t in CFSET: c[t]+=1
    return c
def cos(a,b):
    ks=set(a)|set(b); 
    dot=sum(a[k]*b[k] for k in ks); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0
def skel(stmts,d,out,cap=34):
    for s in stmts:
        if len(out)>=cap: out.append('  '*d+'…'); return out
        if isinstance(s,ast.If):
            out.append('  '*d+'if(·):'); skel(s.body,d+1,out,cap)
            if s.orelse: out.append('  '*d+'else:'); skel(s.orelse,d+1,out,cap)
        elif isinstance(s,(ast.For,ast.AsyncFor)): out.append('  '*d+'for(·):'); skel(s.body,d+1,out,cap)
        elif isinstance(s,ast.While): out.append('  '*d+'while(·):'); skel(s.body,d+1,out,cap)
        elif isinstance(s,ast.Try):
            out.append('  '*d+'try:'); skel(s.body,d+1,out,cap)
            for h in s.handlers: out.append('  '*d+'except:'); skel(h.body,d+1,out,cap)
            if s.orelse: out.append('  '*d+'else:'); skel(s.orelse,d+1,out,cap)
            if s.finalbody: out.append('  '*d+'finally:'); skel(s.finalbody,d+1,out,cap)
        elif isinstance(s,(ast.With,ast.AsyncWith)): out.append('  '*d+'with(·):'); skel(s.body,d+1,out,cap)
        elif isinstance(s,ast.Return): out.append('  '*d+'return ·')
        elif isinstance(s,ast.Raise): out.append('  '*d+'raise')
        elif isinstance(s,(ast.Break,)): out.append('  '*d+'break')
        elif isinstance(s,(ast.Continue,)): out.append('  '*d+'continue')
        elif isinstance(s,(ast.Assign,ast.AugAssign,ast.AnnAssign)): out.append('  '*d+'·=·')
        elif isinstance(s,ast.Expr): out.append('  '*d+'·(·)')
        else: out.append('  '*d+type(s).__name__.lower())
    return out
def report(label,path,name):
    fn=find(path,name)
    if not fn: print(f"## {label}: {name} NOT FOUND in {path}"); return None
    args=fn.args
    nargs=len(args.args)+len(args.kwonlyargs)+(1 if args.vararg else 0)+(1 if args.kwarg else 0)
    h=hist(fn)
    print(f"## {label} — {name}()  [args={nargs}, body-stmts={len(fn.body)}, lines={(fn.end_lineno-fn.lineno+1)}]")
    print("   control-flow histogram:", dict(sorted(h.items(),key=lambda x:-x[1])))
    print("   identifier-blind skeleton:")
    for ln in skel(fn.body,1,[],34): print("   "+ln)
    return h
L="/srv/repos/public/lineage"
V6=f"{L}/_v/chardet-6.0.0/chardet"
V7=f"{L}/_v/chardet-7.0.0/src/chardet"
h6=report("v6 UniversalDetector",f"{V6}/universaldetector.py","feed")
print()
h7=report("v7 orchestrator",f"{V7}/pipeline/orchestrator.py","run_pipeline")
print()
h7c=report("v7 orchestrator",f"{V7}/pipeline/orchestrator.py","_run_pipeline_core")
print("\n=== control-flow histogram cosine (renaming-invariant per-method) ===")
if h6 and h7: print(f"   v6.feed  vs  v7.run_pipeline      : {cos(h6,h7):.3f}")
if h6 and h7c: print(f"   v6.feed  vs  v7._run_pipeline_core: {cos(h6,h7c):.3f}")
