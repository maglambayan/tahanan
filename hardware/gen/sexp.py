"""Minimal S-expression parser/serializer for KiCad files."""
import re
class Sym(str): pass
_tok=re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')
def parse(s):
    stack=[[]];pos=0;n=len(s)
    while True:
        m=_tok.match(s,pos)
        if not m: break
        pos=m.end()
        if m.group(1): stack.append([])
        elif m.group(2):
            l=stack.pop(); stack[-1].append(l)
        elif m.group(3) is not None: stack[-1].append(m.group(3).replace('\\"','"').replace('\\\\','\\'))
        else: stack[-1].append(Sym(m.group(4)))
    return stack[0][0]
def dump(x,ind=0):
    if isinstance(x,list):
        simple=all(not isinstance(i,list) for i in x)
        if simple: return '('+' '.join(dump(i) for i in x)+')'
        out='('+dump(x[0])
        for i in x[1:]:
            if isinstance(i,list): out+='\n'+'\t'*(ind+1)+dump(i,ind+1)
            else: out+=' '+dump(i)
        return out+'\n'+'\t'*ind+')'
    if isinstance(x,Sym): return str(x)
    if isinstance(x,str): return '"'+x.replace('\\','\\\\').replace('"','\\"')+'"'
    return repr(x)
def find(x,name): return [i for i in x if isinstance(i,list) and i and i[0]==name]
def get(x,name):
    f=find(x,name); return f[0] if f else None
