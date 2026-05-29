import ast,os,math
from collections import Counter
CF=['If','For','While','Try','ExceptHandler','With','Return','Raise','Break','Continue','Call','BoolOp','Compare','ListComp','Assign']
def maxdepth(node,d=0):
    m=d
    for c in ast.iter_child_nodes(node):
        if isinstance(c,(ast.If,ast.For,ast.While,ast.Try,ast.With,ast.AsyncFor,ast.AsyncWith)):
            m=max(m,maxdepth(c,d+1))
        else:
            m=max(m,maxdepth(c,d))
    return m
def feats(fn):
    h=Counter()
    for n in ast.walk(fn):
        t=type(n).__name__
        if t in CF: h[t]+=1
    a=fn.args; arity=len(a.args)+len(a.kwonlyargs)+(1 if a.vararg else 0)+(1 if a.kwarg else 0)
    tot=sum(h.values())
    cyc=1+h['If']+h['For']+h['While']+h['ExceptHandler']+h['BoolOp']
    return dict(h=h,arity=arity,tot=tot,cyc=cyc,depth=maxdepth(fn),
               ret=h['Return'],loop=h['For']+h['While'],br=h['If'])
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
            class V(ast.NodeVisitor):
                def visit_ClassDef(s,n):
                    cls.append(n.name); 
                    for c in n.body: s.visit(c)
                    cls.pop()
                def visit_FunctionDef(s,n): rec(n)
                def visit_AsyncFunctionDef(s,n): rec(n)
            def rec(n):
                fe=feats(n)
                if fe['tot']==0: return
                out.append(dict(name=((cls[-1]+'.') if cls[-1] else '')+n.name,
                                file=os.path.relpath(p,root),**fe))
            V().visit(tree)
    return out
def cos(a,b):
    ks=set(a)|set(b); dot=sum(a[k]*b[k] for k in ks)
    na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0
L="/srv/repos/public/lineage"
v6=collect(f"{L}/_v/chardet-6.0.0/chardet")
v7=collect(f"{L}/_v/chardet-7.0.0/src/chardet")
v6.sort(key=lambda x:-x['cyc'])
N=len(v6); half=v6[:max(1,N//2)]
print(f"v6 impl methods: {N}   v7 impl methods: {len(v7)}   tracing top 50% = {len(half)} methods\n")
def best_match(m):
    # gated: comparable arity (±1) AND comparable size (0.5..2.0x total CF nodes)
    cand=[g for g in v7 if abs(g['arity']-m['arity'])<=1 and m['tot'] and 0.5<=g['tot']/m['tot']<=2.0]
    if not cand: return None,0.0
    g=max(cand,key=lambda g:cos(m['h'],g['h']))
    return g,cos(m['h'],g['h'])
twin=weak=none=0; rows=[]
for i,m in enumerate(half,1):
    g,s=best_match(m)
    if g is None: v='NONE'; none+=1; gn='—'
    elif s>=0.90: v='TWIN'; twin+=1; gn=f"{g['name']} [{g['file']}]"
    else: v='weak'; weak+=1; gn=f"{g['name']} [{g['file']}]"
    rows.append((i,m['name'],m['file'],m['cyc'],m['depth'],m['ret'],v,s,gn))
print(f"VERDICT over top-50% v6 methods (n={len(half)}):")
print(f"  TWIN  (compatible arity+size AND cf-cosine>=0.90): {twin}  ({twin/len(half):.0%})")
print(f"  weak  (compatible candidate, cosine<0.90)        : {weak}  ({weak/len(half):.0%})")
print(f"  NONE  (no v7 method of compatible arity+size)    : {none}  ({none/len(half):.0%})\n")
print(f"{'#':>3} {'v6 method':<34}{'cyc':>4}{'dep':>4}{'ret':>4}  {'verdict':<5}{'cos':>6}  best v7 counterpart")
for (i,nm,fl,cy,dp,rt,v,s,gn) in rows:
    print(f"{i:>3} {nm[:34]:<34}{cy:>4}{dp:>4}{rt:>4}  {v:<5}{s:>6.2f}  {gn[:46]}")

print("\n\n################ STRICT structural gate (shape, not just histogram) ################")
def strict_match(m):
    cand=[g for g in v7 if abs(g['arity']-m['arity'])<=1 and m['tot'] and 0.67<=g['tot']/m['tot']<=1.5
          and abs(g['depth']-m['depth'])<=1 and g['loop']==m['loop'] and abs(g['ret']-m['ret'])<=1]
    if not cand: return None,0.0
    g=max(cand,key=lambda g:cos(m['h'],g['h'])); return g,cos(m['h'],g['h'])
stwin=sweak=snone=0; srows=[]
for i,m in enumerate(half,1):
    g,s=strict_match(m)
    if g is None: v='NONE'; snone+=1; gn='—'
    elif s>=0.95: v='TWIN'; stwin+=1; gn=f"{g['name']} [{g['file']}]"
    else: v='weak'; sweak+=1; gn=f"{g['name']} [{g['file']}]"
    srows.append((i,m['name'],m['cyc'],m['loop'],m['depth'],m['ret'],v,s,gn))
print(f"STRICT twin (arity+size+depth+loop+ret gated, cos>=0.95): {stwin}/{len(half)} = {stwin/len(half):.0%}")
print(f"  weak (gated candidate, cos<0.95): {sweak}   NONE (no shape-compatible v7 method): {snone} ({snone/len(half):.0%})\n")
print(f"{'#':>3} {'v6 method':<34}{'cyc':>4}{'lp':>3}{'dp':>4}{'rt':>4}  {'verdict':<5}{'cos':>6}  best shape-compatible v7")
for (i,nm,cy,lp,dp,rt,v,s,gn) in srows:
    print(f"{i:>3} {nm[:34]:<34}{cy:>4}{lp:>3}{dp:>4}{rt:>4}  {v:<5}{s:>6.2f}  {gn[:44]}")
