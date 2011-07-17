from mutpy.operators import notmutate


class Simple:
        
    def add(self, x , y):
        return x + y
    
    def addTwo(self, x):
        return self.add(x, 2)

    def addEtc(self, x):
        return x + ' etc.'
    
    def loop(self):
        i = 0

        while i != 100:
            i = i + 1
            
        return i
        
    def lastTwo(self, x):
        return x[-2:]
        
    def emptyString(self):
        return ''
    
    @notmutate
    def equivalent(self, x):
        return x[-1:-1:-1]
    
    def is_odd(self, x):
        if x % 2:
            return True
        return False
        
