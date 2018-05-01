class Viaticum(object):
    pass


class Airport(object):

    def __init__(self, iata_code: str, timezone: str = None, viaticum: Viaticum = None) -> None:
        """
        Represents an airport as a 3 letter code
        """
        self.iata_code = iata_code
        self.timezone = timezone
        self.viaticum = viaticum

    def __str__(self):
        return "{}".format(self.iata_code)