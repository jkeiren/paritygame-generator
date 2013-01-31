class Spec(object):
  def mode(self):
    raise NotImplementedError()
  
  def type(self):
    raise NotImplementedError()
  
  def form(self):
    raise NotImplementedError()

class IncludeSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "lmmc"
  
  def __includehelper(self,n):
    if n == 0:
      return "((~q) & (<a>X))"
    else:
      return "(q & <a>(q & (<a>({0}))))".format(self.__includehelper(n-1))
     
  def form(self, n):
    return "((nu X.({0})) ==> (nu Z.mu Y.(((~q) & <a>Z) | (q & <a> (q & <a> Y)))))".format(self.__includehelper(n))
  
class NesterSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "lmmc"
  
  def __nesterpostfix(self, n, i):
    if n == i:
      return "(q_{0} | (<a>(X_{0})))".format(i)
    else:
      return "(q_{0} | (<a>(X_{0} & {1})))".format(i, self.__nesterpostfix(n, i+1))
  
  def __nesterhelper(self, n, i):
    if n < i:
      return self.__nesterpostfix(n, 1)
    elif i % 2 == 0:
      return "(mu X_{0}.{1})".format(i, self.__nesterhelper(n, i+1))
    else: # i % 2 == 1
      return "(nu X_{0}.{1})".format(i, self.__nesterhelper(n, i+1))
  
  def form(self, n):
    return "({0} | ~{0})".format(self.__nesterhelper(n, 1))

class StarNesterSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "pdl"

  def __starnesterprogram(self, i):
    if i == 0:
      return "(tt?^*)"
    else:
      return "(((a^*) . {0} . (b^*))^*)".format(self.__starnesterprogram(i-1))

  def __starnester1(self, n):
    return "((< {0} >q) | ([ {0} ]~q))".format(self.__starnesterprogram(n))
  
  def __starnester2(self, n):
    return "((< {0} >q) | ([ (a | b)^* ]~q))".format(self.__starnesterprogram(n))

  def __starnester3(self, n):
    return "((< (a | b)^* >q) | ([ {0} ]~q))".format(self.__starnesterprogram(n))
  
  def form(self, k, n):
    if k == 1:
      return self.__starnester1(n)
    elif k == 2:
      return self.__starnester2(n)
    elif k == 3:
      return self.__starnester3(n)
    else:
      raise Exception("Starnester not implemented for k == {0}".format(k))

class PetriSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "lmmc"
  
  def __petriwellhelper(self, i, n):
    if i > n:
      return "ff"
    else:
      return "((<t_{0}>(p_{0} & <s_{0}>X)) | {1})".format(i, self.__petriwellhelper(i+1, n))
    
  def __petriwell(self, n):
    return "(nu X.(p & {0}))".format(self.__petriwellhelper(1, n))
    
  def __petrifairhelper(self, j, i, n):
    if j > n:
      return "ff"
    if j == i:
      return self.__petrifairhelper(j+1, i, n)
    else:
      return "(((<t_{0}>Y_{1}) | (<s_{0}>Y_{1})) | {2})".format(j, i, self.__petrifairhelper(j + 1, i, n))

  def __petrifair(self, i, n):
    if i > n:
      return "tt"
    else:
      return "(nu X_{0}. mu Y_{0}.((<t_{0}>X_{0}) | (<s_{0}>Y_{0}) | {1}))".format(i,self.__petrifairhelper(1, i, n))
  
  def __petrihelperpj(self, j, i, n):
    if j > n:
      return "ff"
    elif j == i:
      return self.__petrihelperpj(j+1, i, n)
    else:
      return "(p_{0} | {1})".format(j, self.__petrihelperpj(j+1, i, n))
    
  def __petriexclhelper(self, i, n):
    if i > n:
      return "ff"
    else:
      return "(((<t_{0}>(X & p_{0} & ~p & ~{1})) | (<s_{0}>(X & p & ~{2}))) | {3})".format(i, self.__petrihelperpj(1, i, n), self.__petrihelperpj(1, 0, n), self.__petriexclhelper(i + 1, n))

  def __petriexcl(self, n):
    return "(nu X.{0})".format(self.__petriexclhelper(1, n))

  def __petrinet(self, n):
    return "({0} & {1} & {2})".format(self.__petriwell(n), self.__petrifair(1, n), self.__petriexcl(n))

  def __petrimodelhelper(self, i, n):
    if i > n:
      return "X"
    else:
      return "((p & ~{1}) & <t_{0}>((p_{0} & ~p & ~{2}) & <s_{0}>{3}))".format(i, self.__petrihelperpj(1, 0, n), self.__petrihelperpj(1, i, n), self.__petrimodelhelper(i + 1, n))

  def __petrimodel(self, n):
    return "(nu X.{0})".format(self.__petrimodelhelper(1, n))
  
  def form(self, n):
    return "(({0}) ==> ({1}))".format(self.__petrimodel(n), self.__petrinet(n))

class ParityAndBuechiSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "ltmc"
  
  def __nottheothers(self, i,j):
    if j == 0:
      return "tt"
    elif j == i:
      return self.__nottheothers(i,j-1)
    else:
      return "(~q_{0} & {1})".format(j, self.__nottheothers(i,j-1))

  def __justoneq(self,i,n):
    if i == 0:
      return "ff"
    else:
      return "((q_{0} & {1}) | {2})".format(i, self.__nottheothers(i,n), self.__justoneq(i-1,n))
    
  def __alwaysjustoneq(self,n):
    return "(nu X. ({0} & ()X))".format(self.__justoneq(n,n))

  def __infinitelyoftenq(self,i):
    return "(nu X.(mu Y.(q_{0} | ()Y)) & ()X)".format(i)
  
  def __finitelyoftenq(self, i):
    return "(~({0}))".format(self.__infinitelyoftenq(i))
    
  def __forallgreateroddfinitelyoften(self,n,i):
    assert(i >= 0)
    if i > n:
      return "tt"
    elif i % 2 == 1:
      return "({0} & {1})".format(self.__finitelyoftenq(i), self.__forallgreateroddfinitelyoften(n,i+2))  
    else:
      return self.__forallgreateroddfinitelyoften(n,i+1);

  def __existseveninfpriority(self,n,i):
    assert (i >= 0)
    if i == 0:
      return "ff"
    elif i % 2 == 0:
      return "(({0} & {1}) | {2})".format(self.__infinitelyoftenq(i), self.__forallgreateroddfinitelyoften(n,i+1),self.__existseveninfpriority(n,i-2))
    else:
      return self.__existseveninfpriority(n,i-1)

  def __parityconditionbottom(self,i):
    assert(i >= 0)
    if i == 0:
      return "ff"
    else:
      return "((q_{0} & ()X_{0}) | {1})".format(i, self.__parityconditionbottom(i-1))
    
  def __paritycondition(self,n,i):
    assert(i >= 0)
    if i == 0:
      return self.__parityconditionbottom(n)
    elif i % 2 == 0:
      return "(nu X_{0}.{1})".format(i, self.__paritycondition(n, i - 1))
    else:
      return "(mu X_{0}.{1})".format(i, self.__paritycondition(n, i - 1))
  
  def form(self, n):
    return "(({0}) ==> (({1}) <==> ({2})))".format(self.__alwaysjustoneq(n), self.__paritycondition(n,n), self.__existseveninfpriority(n,n))

class LimitClosureSpec(Spec):
  def __init__(self, ctl):
    self.__ctl = ctl
  
  def mode(self):
    return "validity"
  
  def _phi(self, n):
    return "(G({0}))".format(" | ".join(["(~q_{0})".format(i) for i in range(0,n+1)]))
  
  def _psi(self, n):
    if n == 0:
      return "q_0"
    elif n % 2 == 1:
      return "(q_{0} & ({1} X {2}))".format(n, "E" if self.__ctl else "", self._psi(n-1))
    else:
      return "(q_{0} | ({1} X {2}))".format(n, "E" if self.__ctl else "", self._psi(n-1))

# Here we do not use the limit closure spec above, since that is tailored to
# CTL derived 
class MuCalcLimitClosureSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "mmc"
  
  def form(self, n, phi):
    return "((nu X_{0} . (({1} ==> <> {1}) & []X_{0})) ==> ({1} ==> (nu Y_{0}. ({1} & <>Y_{0}))))".format(n, phi)
  
class CTLLimitClosureSpec(LimitClosureSpec):
  def __init__(self):
    super(CTLLimitClosureSpec, self).__init__(True)
    
  def type(self):
    return "ctl"
  
  def _limitclosure(self, phi):
    return "((A G ({0} ==> (E X {0}))) ==> ({0} ==> (E G {0})))".format(phi)
  
  def form(self, phi):
    return self._limitclosure(phi)  
  
class FLCTLLimitClosureSpec(CTLLimitClosureSpec):
  def form(self, n):
    return self._limitclosure(self._psi(n))

class CTLStarLimitClosureSpec(LimitClosureSpec):
  def __init__(self):
    super(CTLStarLimitClosureSpec, self).__init__(False)
  
  def type(self):
    return "ctlstar"
  
  def _ctlstarlimitclosure(self, phi, psi):
    return "(((A G( (E {1}) ==> (E X (E({0} U {1} ))))) & (E {1})) ==> (E G((E {0}) U (E {1}))))".format(phi,psi)
  
  def form(self, phi, psi):
    return self._ctlstarlimitclosure(phi, psi)
  
class FLCTLStarLimitClosureSpec(CTLStarLimitClosureSpec):
  def __init__(self):
    super(FLCTLStarLimitClosureSpec, self).__init__()
    
  def form(self, n):
    return self._ctlstarlimitclosure(self._phi(n), self._psi(n))
  
class CTLStarSimpleLimitClosureSpec(CTLStarLimitClosureSpec):
  def __init__(self):
    super(CTLStarSimpleLimitClosureSpec, self).__init__()
    
  def form(self, phi):
    return self._ctlstarlimitclosure("tt", phi)

class FLCTLStarSimpleLimitClosureSpec(CTLStarSimpleLimitClosureSpec):
  def __init__(self):
    super(FLCTLStarSimpleLimitClosureSpec, self).__init__()
    
  def form(self, n):
    return self._ctlstarlimitclosure("tt", self._phi(n))
  
class DemriKillerFormulaSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "mmc"
  
  def form(self, n):
    if n == 0:
      return "p"
    else:
      return MuCalcLimitClosureSpec().form(n, self.form(n-1))

class FairSchedulerSpec(Spec):
  def mode(self):
    return "validity"
  
  def type(self):
    return "ctlstar"

  def __alwayseventuallynextevent(self,i,n):
    return "(A G(q_{0} ==> (E X (F q_{1}))))".format(i, (i+1) % n)

  def __alwayseventuallynextevents(self,i,n):
    if i == 0:
      return self.__alwayseventuallynextevent(0,n)
    else:
      return "({0} & {1})".format(self.__alwayseventuallynextevent(i,n), self.__alwayseventuallynextevents(i-1,n))
    
  def __infinitelyoftenevents(self,i):
    if i == 0:
      return "(G F q_0)"
    else:
      return "((G F q_{0}) & {1})".format(i, self.__infinitelyoftenevents(i-1))
  
  def form(self, n):
    return "((q_0 & {0}) ==> (E {1}))".format(self.__alwayseventuallynextevents(n-1,n), self.__infinitelyoftenevents(n-1))

class BinaryCounterSpec(Spec):
  def mode(self):
    return "satisfiability"
  
  def _bincounterauxcon(self,n):
    if n == 0:
      return "(~c_0)"
    else:
      return "({0} & ~c_{1})".format(self._bincounterauxcon(n - 1), n)

class LTMucalcBinaryCounterSpec(BinaryCounterSpec):
  def type(self):
    return "ltmc"
  
  def __ltmcbincounteraux(self,n):
    if n == 0:
      return "(c_0 <==> (()~c_0))"
    else:
      return "(((()c_{0}) <==> ((c_{0} & ~c_{1} & ()c_{1}) | (~c_{0} & c_{1} & ()~c_{1}))) & {2})".format(n, n-1, self.__ltmcbincounteraux(n-1))
              
  def form(self, n):
    return "((nu X.(({0}) & ()X)) & {1})".format(self.__ltmcbincounteraux(n-1), self._bincounterauxcon(n-1))
    
class CTLStarBinaryCounterSpec(BinaryCounterSpec):
  def type(self):
    return "ctlstar"
  
  def __ctlstarbincounteraux(self,n):
    if n == 0:
      return "(c_0 <==> (X ~c_0))"
    else:
      return "(((X c_{0}) <==> ((c_{0} & ~c_{1} & X c_{1}) | (~c_{0} & c_{1} & X ~c_{1}))) & {2})".format(n, n-1, self.__ctlstarbincounteraux(n-1))

  def form(self, n):
    return "(E ((G({0})) & {1}))".format(self.__ctlstarbincounteraux(n-1),self._bincounterauxcon(n-1))
    
class PDLBinaryCounterSpec(BinaryCounterSpec):
  def type(self):
    return "pdl"
  
  def __pdlbincounteraux(self,n):
    if n == 0:
      return "((c_0 ==> ([a]~c_0)) & ((~c_0) ==> ([a]c_0)))"
    else:
      return "((((~c_{1}) | (<a>c_{1})) ==> ((c_{0} ==> ([a]c_{0})) & ((~c_{0}) ==> ([a]~c_{0})))) & ((c_{1} & (<a>~c_{1})) ==> ((c_{0} ==> ([a]~c_{0})) & ((~c_{0}) ==> ([a]c_{0})))) & {2})".format(n, n-1,self.__pdlbincounteraux(n-1)) 

  def form(self, n):
    return "(([a^*]((<a>tt) & {0})) & {1})".format(self.__pdlbincounteraux(n-1),self._bincounterauxcon(n-1))

class HugeModelsSpec(Spec):
  """Specification that is satisfiable in huge models only"""
  
  def type(self):
    return "ctlstar"
  
  def mode(self):
    return "satisfiability"
  
  def __allbitsnochange(self,n):
    if n == 0:
      return "(c_0 <==> (X c_0))"
    else:
      return "((c_{0} <==> (X c_{0})) & {1})".format(n, self.__allbitsnochange(n-1))

  def __hugemodelsskeleton(self,n):
    return "(z & (A G ((z ==> ((E X z) & (E X ~z))) & (~z ==> (A X ~z)))) & (A G A ((X ~z) ==> ((e <==> (X e)) & (f <==> (X f)) & (c <==> (X c)) & {0}))))".format(self.__allbitsnochange(n))

  def __null(self,n):
    if n == 0:
      return "(~c_0)"
    else:
      return "((~c_{0}) & {1})".format(n, self.__null(n-1))

  def __full(self,n):
    if n == 0:
      return "(c_0)"
    else:
      return "(c_{0} & {1})".format(n, self.__full(n-1))

  def __increasecounter1(self,n):
    if n == 0:
      return "tt"
    else:
      return "(((X c_{0}) <==> (c_{0} <==> (c_{1} ==> (X c_{1})))) & {2})".format(n, n-1, self.__increasecounter1(n-1))

  def __hugemodelscounter1(self,n):
    return "({0} & (A G A( (X z) ==> ((c_0 <==> (X ~c_0)) & {1}))))".format(self.__null(n), self.__increasecounter1(n))

  def __hugemodelsflip(self,n):
    return "(A G A( (X (z & ~{0})) ==> ( ({1} ==> f) & (~{1} ==> ((~f ==> (X ~f)) & (f ==> (c <==> (X f))))))))".format(self.__full(n), self.__null(n))

  def __hugemodelseven(self, n):
    return "(e & (A G A( (X z) ==> (( (~{0}) ==> (e <==> (X e))) & ({0} ==> (e <==> (X ~e)))))))".format(self.__full(n))

  def __pathselaux(self,n):
    if n < 0:
      return "tt"
    else:
      return "((c_{0} ==> (F A G c_{0})) & (~c_{0} ==> (F A G ~c_{0})) & {1})".format(n, self.__pathselaux(n-1))
 
  def __pathselector(self,n):
    return "((X z) & ((~{0}) ==> ~(F(z & e & {0}) & F(z & ~e & {0}))) & ({0} ==> ~(F(z & e & {1}) & F(z & ~e & {1}))) & {2})".format(self.__null(n), self.__full(n), self.__pathselaux(n))

  def __hugemodelscounter2(self,n):
    return "(~c & A((G z) ==> ((~c) U (c & {0}))) & A G A( {1} ==> ((f ==> ((c ==> (F A G ~c)) & ((~c) ==> (F A G c)))) & ((~f) ==> ((c ==> F A G c) & ((~c) ==> (F A G ~c)))))))".format(self.__null(n), self.__pathselector(n))

  def form(self, n):
    return "{0} & {1} & {2} & {3} & {4}".format(self.__hugemodelsskeleton(n-1),
                                                self.__hugemodelscounter1(n-1),
                                                self.__hugemodelsflip(n-1),
                                                self.__hugemodelseven(n-1),
                                                self.__hugemodelscounter2(n-1))
  
__SPECS = {
    'Include': IncludeSpec(),
    'Nester': NesterSpec(),
    'StarNester': StarNesterSpec(),
    'Petri': PetriSpec(),
    'ParityAndBuechi': ParityAndBuechiSpec(),
    'MuCalcLimitClosure': MuCalcLimitClosureSpec(),
    'CTLLimitClosure': CTLLimitClosureSpec(),
    'CTLStarLimitClosure': CTLStarLimitClosureSpec(),
    'CTLStarSimpleLimitClosure': CTLStarSimpleLimitClosureSpec(),
    'FLCTLLimitClosure': FLCTLLimitClosureSpec(),
    'FLCTLStarLimitClosure': FLCTLStarLimitClosureSpec(),
    'FLCTLStarSimpleLimitClosure': FLCTLStarSimpleLimitClosureSpec(),
    'DemriKillerFormula': DemriKillerFormulaSpec(),
    'FairScheduler': FairSchedulerSpec(),
    'LTMucalcBinaryCounter': LTMucalcBinaryCounterSpec(),
    'CTLStarBinaryCounter': CTLStarBinaryCounterSpec(),
    'PDLBinaryCounter': PDLBinaryCounterSpec(),
    'HugeModels': HugeModelsSpec()
  }

def get(name):
  return __SPECS[name]
