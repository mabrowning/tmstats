import math
class Welford(object):
    """ Implements Welford's algorithm for computing a running mean
    and standard deviation as described at: 
        http://www.johndcoon.com/standard_deviation.html

    can tane single values or iterables

    Properties:
        mean    - returns the mean
        std     - returns the std
        meanfull- returns the mean and std of the mean

    Usage:
        >>> foo = Welford()
        >>> foo(range(100))
        >>> foo
        <Welford: 49.5 +- 29.0114919759>
        >>> foo([1]*1000)
        >>> foo
        <Welford: 5.40909090909 +- 16.4437417146>
        >>> foo.mean
        5.409090909090906
        >>> foo.std
        16.44374171455467
        >>> foo.meanfull
        (5.409090909090906, 0.4957974674244838)
    """
 
    def __init__(self,lst=None):
        self.n = 0
        self.M1 = 0
        self.M2 = 0
        self.M3 = 0
        self.M4 = 0
        
        self.__call__(lst)
    
    def update(self,x):
        if x is None:
            return
        n1 = self.n
        self.n += 1 
        n = self.n
        delta = x - self.M1
        delta_n = delta / n
        delta_n2 = delta_n * delta_n
        term1 = delta * delta_n * n1
        self.M1 += delta_n
        self.M4 += term1 * delta_n2 * ( n*n - 3*n + 3 ) + 6 * delta_n2 * self.M2
        self.M3 += term1 * delta_n  * (         n - 2 ) - 3 * delta_n  * self.M2
        self.M2 += term1
 
    def consume(self,lst):
        lst = iter(lst)
        for x in lst:
            self.update(x)
    
    def __call__(self,x):
        if hasattr(x,"__iter__"):
            self.consume(x)
        else:
            self.update(x)

    def __add__(a,b):
        new = Welford()
        new.n = a.n + b.n
        delta  = b.M1 - a.M1
        delta2 = delta  * delta
        delta3 = delta2 * delta
        delta4 = delta2 * delta2

        new.M1 = ( a.n * a.M1 + b.n * b.M1 ) / new.n
        new.M2 = a.M2 + b.M2 + delta2 * a.n * b.n / new.n
        new.M3 = a.M3 + b.M3 + delta3 * a.n * b.n * (a.n - b.n)/(new.n*new.n) + \
                    3.0*delta * (a.n*b.M2 - b.n*a.M2) / new.n;
        new.M4 = a.M4 + b.M4 + delta4*a.n*b.n * (a.n*a.n - a.n*b.n + b.n*b.n) / (new.n*new.n*new.n) + \
                    6.0*delta2 * (a.n*a.n*b.M2 + b.n*b.n*a.M2)/(new.n*new.n) + 4.0*delta*(a.n*b.M3 - b.n*a.M3) / new.n;

        return new
            
    @property
    def mean(self):
        return self.M1
    @property
    def meanfull(self):
        return self.mean, self.std/math.sqrt(self.n)
    @property
    def variance(self):
        if self.n==1:
            return 0
        return self.M2/(self.n-1)
    @property
    def std(self):
        return math.sqrt(self.variance)
    @property
    def skewness(self):
        return math.sqrt( float(self.n) ) * self.M3 / ( self.M2 * math.sqrt( self.M2 ) )
    @property
    def kurtosis(self):
        return self.n * self.M4 / (self.M2 * self.M2 ) - 3
    def __repr__(self):
        return "{} +- {}".format(self.mean, self.std)
