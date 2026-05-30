import ast,os,math,sys
# Generalized per-method renaming-invariant trace.
# Descriptor + gates are IDENTICAL to per_method_trace_cov.py (the v6/v7 run);
# only the implementation-package paths and labels are now arguments.
#
# usage: per_method_trace_cov_generic.py <A_pkg> <B_pkg> <A_label> <B_label> <cov> <fwd|rev>
#   fwd = A->B (A is the chronologically-earlier / source side)
#   rev = B->A
A_PKG=sys.argv[1]; B_PKG=sys.argv[2]
A_LBL=sys.argv[3]; B_LBL=sys.argv[4]
COV=float(sys.argv[5]) if len(sys.argv)>5 else 0.8
DIR=sys.argv[6] if len(sys.argv)>6 else 'fwd'
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
from collections import Counter
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
A=collect(A_PKG); B=collect(B_PKG)
src,dst,sl,dl=(A,B,A_LBL,B_LBL) if DIR=='fwd' else (B,A,B_LBL,A_LBL)
src=sorted(src,key=lambda x:-x['cyc']); N=len(src); k=max(1,round(N*COV)); cov=src[:k]
print(f"[{DIR}: {sl}->{dl}]  {sl} methods={N}  {dl} methods={len(dst)}  coverage {COV:.0%} -> {k} mapped\n")
def strict(m):
    c=[g for g in dst if abs(g['arity']-m['arity'])<=1 and m['tot'] and 0.67<=g['tot']/m['tot']<=1.5
       and abs(g['depth']-m['depth'])<=1 and g['loop']==m['loop'] and abs(g['ret']-m['ret'])<=1]
    if not c: return None,0.0
    g=max(c,key=lambda g:cos(m['h'],g['h'])); return g,cos(m['h'],g['h'])
def naive(m):
    c=[g for g in dst if abs(g['arity']-m['arity'])<=1 and m['tot'] and 0.5<=g['tot']/m['tot']<=2.0]
    return max((cos(m['h'],g['h']) for g in c),default=0.0)
nt=sum(1 for m in cov if naive(m)>=0.90)
bands={'load-bearing cyc>=8':[0,0,0],'substantive 5-7':[0,0,0],'minor 3-4':[0,0,0],'trivial <=2':[0,0,0]}
bn=lambda c:'load-bearing cyc>=8' if c>=8 else 'substantive 5-7' if c>=5 else 'minor 3-4' if c>=3 else 'trivial <=2'
st=0; lb=[]
for m in cov:
    g,s=strict(m); b=bn(m['cyc'])
    if g is None: bands[b][2]+=1; v='NONE'; gn='—'
    elif s>=0.95: bands[b][0]+=1; st+=1; v='TWIN'; gn=f"{g['name']} [{g['file']}]"
    else: bands[b][1]+=1; v='weak'; gn=f"{g['name']} [{g['file']}]"
    if m['cyc']>=8: lb.append((m['name'],m['cyc'],v,s,gn))
print(f"NAIVE twin (cf-cos>=0.90): {nt}/{k} = {nt/k:.0%}")
print(f"STRICT twin (shape-gated): {st}/{k} = {st/k:.0%}\n")
print("STRICT by band [TWIN/weak/NONE]:")
for b,(t,w,n) in bands.items():
    tot=t+w+n
    if tot: print(f"  {b:<22}: {t:>3}/{w:>3}/{n:>3}  (n={tot}, twin={t/tot:.0%})")
print(f"\nload-bearing {sl} methods (cyc>=8) and their best {dl} structural match:")
for nm,cy,v,s,gn in lb:
    print(f"  {nm[:36]:<36} cyc={cy:>2}  {v:<5} {s:>5.2f}  {gn[:40]}")
