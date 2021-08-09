

class BookSide: 

    class BLevel:        
        def __init__(self, f, s):
            self.p = f 
            self.q = s

    def __init__(self, bk_side_txt):
        self.bk_side = []
        if(bk_side_txt == 'nan'):
            return
        levels = bk_side_txt.split(' ')
        for l in levels:
            pq = l.split('/')            
            self.bk_side.append(BookSide.BLevel(int(pq[0]),int(pq[1])))

    def to_string(self, n_levels):
        i = 0
        rv = ''
        for pq in self.bk_side:
            if i<n_levels:
               rv += str(pq.p) + '/' + str(pq.q) + ' '
            i += 1
        return rv

