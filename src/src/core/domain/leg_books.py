
class LegBooks:

    def __init__(self, books):
        self.leg_books = []
        for l_bk in books:
            self.leg_books.append(l_bk)

    def append_leg_book(self, l_bk):
        self.leg_books.append(l_bk)

    def to_string(self, n_levels):
        rv = ''
        for l_bk in self.leg_books:
            rv += l_bk.to_string(n_levels) + ' | '
        return rv
    
    def __str__(self):
        return self.to_string(len(self.leg_books))

    @staticmethod
    def get_leg_books(r, n_legs = 4):
        """Appends the leg books into one string"""
        l_books = LegBooks([])
        for l_idx in range(1, n_legs):
            col_b = f'book_{l_idx}_bid_bk'
            col_a = f'book_{l_idx}_ask_bk'
            l_books.append_leg_book(Book(BookSide(r[col_b]),BookSide(r[col_a])))
        return l_books

