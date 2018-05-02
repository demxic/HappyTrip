from datetime import timedelta


class Duration(object):

    def __init__(self, minutes: int):
        """value should be a timedelta or minutes (int)"""
        # TODO : IMPLEMENT __format__ method
        if minutes < 0:
            minutes = 0
        self.minutes = int(minutes)

    @classmethod
    def from_timedelta(cls, value):
        minutes = value.total_seconds() / 60
        return cls(minutes)

    def as_timedelta(self):
        return timedelta(minutes=self.minutes)

    def no_trailing_zero(self):
        """Prints as HH:MM v.gr. 7:30 instead of 07:30"""
        if self.minutes == 0:
            hm = 4 * ''
        else:
            hours, minutes = divmod(self.minutes, 60)
            hm = "{0}:{1:0>2d}".format(hours, minutes)

        return hm

    def __str__(self):
        """Prints as HHMM v.gr. 1230"""
        if self.minutes == 0:
            hm = 4 * ''
        else:
            hours, minutes = divmod(self.minutes, 60)
            hm = "{0:0>2d}{1:0>2d}".format(hours, minutes)

        return hm

    def __repr__(self):
        """Prints as HHH:MM v.gr. 123:30"""
        if self.minutes == 0:
            hm = '00:00'
        else:
            hours, minutes = divmod(self.minutes, 60)
            hm = "{0:0>2d}:{1:0>2d}".format(hours, minutes)

        return hm

    def __add__(self, other):
        return Duration(self.minutes + other.minutes)

    def __radd__(self, other):
        """Because sum(x) always starts adding a 0, Duration takes this into account in this method"""
        other = Duration(other)
        return Duration(self.minutes + other.minutes)

    def __sub__(self, other):
        return Duration(self.minutes - other.minutes)

    def __rsub__(self, other):
        return Duration(self.minutes - other.minutes)

    def __mul__(self, other):
        return self.minutes / 60 * other

    def __rmul__(self, other):
        return self.__mul__(other)

    def __lt__(self, other):
        return self.minutes < other.minutes

    # def __format__(self, fmt='0'):
    #     """Depending on fmt value, a Duration can be printed as follow:
    #     fmt = 0  :   HHMM          4 chars no signs                                v.gr. 0132, 0025, 0000
    #     fmt = 1  :   HHMM          4 chars no sings or blank if self.minutes = 0   v.gr. 0132, 0025,'   '
    #     fmt = 2  : HHH:MM          6 chars with colon in between                   v.gr  01:32, 00:25, 00:00, 132:45
    #     fmt = 3  :  HH:MM          5 chars colon in between and blank for min =0   v.gr  01:32, 00:25, '    '
    #     Any other value defaults to fmt == 0
    #     """
    #
    #     if fmt == '1':
    #         return str(self)
    #     elif fmt == '2':
    #         return repr(self)
    #     elif fmt == '3':
    #         prov = repr(self)
    #         if self.minutes == 0:
    #             return '     '
    #         else:
    #             return repr(self)
    #     else:
    #         if self.minutes == 0:
    #             return '0000'
    #         else:
    #             return self.__str__()
