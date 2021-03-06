"""
PyLINQ

LINQ to python, based on http://jslinq.codeplex.com/.

Copyright (C) 2010  Insophia

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
from itertools import tee, chain, imap, ifilter, islice, product

def identity(x):
    return x

def _check(clause):
    if not callable(clause):
        raise TypeError("clause argument must be callable.")

class PyLINQ(object):
    def __init__(self, items):
        self.__items = iter(items)

    def iteritems(self):
        """returns collection as generator"""
        self.__items, ret = tee(self.__items)
        return ret

    def __iter__(self):
        return self.iteritems()

    def items(self):
        """returns collection as list"""
        self.__items, ret = tee(self.__items)
        return list(ret)

    def where(self, clause):
        """return all items in collection for which clause returns true"""
        _check(clause)
        return PyLINQ(ifilter(clause, self.iteritems()))

    def select(self, clause):
        """returns new collection resultant of application of clause
        over each item in input collection"""
        _check(clause)
        return PyLINQ(imap(clause, self.iteritems()))

    def order_by(self, clause, cmp=None, order='asc'):
        """returns new collection ordered by the result of clause over
        each item in input collection"""
        _check(clause)
        ls = sorted(self.iteritems(), key=clause, cmp=cmp, reverse=(order != 'asc'))
        return PyLINQ(ls)

    def count(self, clause=None):
        """returns the count of items in collection"""
        if not clause:
            return sum(1 for _ in self.iteritems())
        _check(clause)
        return sum(1 for _ in ifilter(clause, self.iteritems()))

    def distinct(self, clause):
        """returns new collection mapped from input collection
        by clause, but avoiding duplicates"""
        _check(clause)
        seen = set()
        def _isnew(item):
            try:
                if not item in seen:
                    seen.add(item)
                    return True
                return False
            except:
                raise TypeError("clause should return a hashable item")
        return PyLINQ(ifilter(_isnew, imap(clause, self.iteritems())))

    def any(self, clause):
        """returns True if any element of the collection holds the clause"""
        _check(clause)
        return any(ifilter(clause, self.iteritems()))

    def all(self, clause):
        """returns True if all the elements of the collection holds the
        clause"""
        _check(clause)
        return all(imap(clause, self.iteritems()))

    def reverse(self):
        """returns a reversed collection"""
        return PyLINQ(reversed(self.items()))

    def first(self, clause=None):
        """returns the first element of the collection"""
        if clause:
            return self.where(clause).first()
        for i in self.iteritems():
            return i

    def last(self, clause=None):
        """returns the last element of the collection"""
        if clause:
            return self.where(clause).last()
        ret = None
        for ret in self.iteritems():
            pass
        return ret

    def element_at(self, index):
        """returns the element at position 'index'""" 
        try:
            for i in islice(self.iteritems(), index, None):
                return i
        except ValueError, StopIteration:
            pass
        raise IndexError("index out of range")

    def concat(self, items):
        """append collection to the final"""
        return PyLINQ(chain(self.iteritems(), items))

    def default_if_empty(self, default=None):
        """returns default if collection is empty, else itself"""
        for _ in self.iteritems():
            return self
        return default or []

    def element_at_or_default(self, index, default=None):
        """returns the element at position 'index' or defaultitem in case
        collection hasn't an item in that position."""
        try:
            return self.element_at(index)
        except IndexError:
            return default

    def first_or_default(self, default=None):
        """returns the first element or default"""
        return self.first() or default

    def last_or_default(self, default=None):
        """returns the last element or default"""
        return self.last() or default

    def aggregate(self, clause, start_value=None):
        """returns the aggregated value over the collection folding the
        items. clause is a a function of two arguments cumulatively to
        the items of a sequence, from left to right, so as to reduce
        the sequence to a single value.
        For example, if p=PyLINQ( [1, 2, 3, 4, 5]),
        p.aggregate(lambda x, y: x+y) calculates ((((1+2)+3)+4)+5).
        If initial is present, it is placed before the items
        of the sequence in the calculation, and serves as a default when the
        sequence is empty."""
        # clause arity function should be 2
        _check(clause)
        if start_value is not None:
            return reduce(clause, self.iteritems(), start_value)
        return reduce(clause, self.iteritems())

    def sum(self, clause=None):
        """returns the sum of the elements of the collection
        clause - should returns a numeric value
        """ 
        if clause:
            _check(clause)
            return sum(imap(clause, self.iteritems()))
        return sum(self.iteritems())

    def average(self, clause=None):
        """returns the average of the collection.
        clause - should returns a numeric value
        """
        return self.sum(clause)/self.count()

    def max(self, clause=None):
        """returns the max element of the collection
        clause - should returns a sortable value
        """
        if clause:
            _check(clause)
            current = cmax = None
            for elem in self.iteritems():
                nmax = clause(elem)
                if cmax is None or cmax < nmax:
                    cmax = nmax
                    current = elem
            return current
        return max(self.iteritems())

    def min(self, clause=None):
        """returns the min element of the collection
        clause - should returns a sortable value
        """
        if clause:
            _check(clause)
            current = cmin = None
            for elem in self.iteritems():
                nmin = clause(elem)
                if cmin is None or cmin > nmin:
                    cmin = nmin
                    current = elem
            return current
        return min(self.iteritems())

    def contains(self, item, cmpfun=cmp):
        """returns True if the element is in the collection"""
        _check(cmpfun)
        for elem in self.iteritems():
            if not cmpfun(item, elem):
                return True
        return False

    def intersect(self, items, cmpfun=cmp):
        """returns the intersection of both collections"""
        _check(cmpfun)
        items = (elem1 for elem1, elem2 in product(self.iteritems(), items)
                 if not cmpfun(elem1, elem2))
        return PyLINQ(items)

