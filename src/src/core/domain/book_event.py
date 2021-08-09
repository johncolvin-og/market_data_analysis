
class BookEvent:
    def __init__(self,r):
        self.ok = r['ok']
        self.sec = r['contract']
        self.change = r['change']
        self.side = r['order_side']
        self.price = r['price']
        self.qty = r['qty']
    def to_string(self):
        return (str(self.sec) + '/' +
                str(self.change) + '/' +
                str(self.side) + '/' +
                str(self.price) + '/' +
                str(self.qty))
    
    def __str__(self):
        return self.to_string()

