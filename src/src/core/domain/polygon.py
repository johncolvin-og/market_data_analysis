
class Polygon:

    class Leg:
        # ex: +(SIH1-SIU1) +(SIU1-SIZ1) +SIZ1 -SIH1
        # +HGN1 -HGM1 +(HGM1-HGN1)
        def __init__(self,leg_str):
            self.is_future = leg_str[1] != '('
            self.leg_qty = 1
            self.leg_str = leg_str
            if(self.leg_str[1] == '-'):
                self.leg_qty = -1

        def n_contracts(self):
            if (self.is_future):
                return 1
            else:
                return 2

    def __init__(self,poly_str):
        self.str = poly_str
        self.legs = []
        toks = poly_str.split(' ')
        for t in toks:
            self.legs.append(Polygon.Leg(t))

    def has_future(self):
        for l in self.legs:
            if l.is_future:
                return True
        return False

    def n_legs(self):
        return len(self.legs)

    def n_contracts(self):
        rv = 0
        for l in self.legs:
            rv += l.n_contracts()
        return rv       

