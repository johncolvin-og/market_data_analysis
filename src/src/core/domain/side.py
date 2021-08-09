from enum import Enum

def foreach(fn):
    fn('Buy')
    fn('Sell')

class Side(Enum):
    Buy = 0
    Sell = 1

    @staticmethod
    def foreach(fn):
        fn(Side.Buy)
        fn(Side.Sell)

    def mkt_name(self):
        if self == Side.Buy:
            return 'bid'
        if self == Side.Sell:
            return 'ask'
        return 'unknown'

    @staticmethod
    def from_mkt_name(name):
        if name.lower() == 'bid':
            return Side.Buy
        if name.lower() == 'ask':
            return Side.Sell
        return Side.Sell
        
    def other_side(self):
        if self == Side.Buy:
            return Side.Sell
        if self == Side.Sell:
            return Side.Buy
#         print(f'Wtf {self.value} != {Side.Buy}')
        return None
