"""
Created on 23/06/2016

@author: Xico
"""
from datetime import timedelta

from model.timeClasses import Duration
from model.scheduleClasses import Flight

# TODO : Move all this constants into a configuration file, associated to method set_rules

TRANSOCEANIC = ['MAD', 'CDG', 'MXP', 'FCO', 'LHR', 'AMS', 'SVO', 'BCN', 'MUC', 'FRA', 'NRT', 'ICN', 'PVG', 'PEK']
MINIMUM_BLOCK = Duration(13 * 60)
MINIMUM_DUTY = Duration(15 * 60)
WORKED_DAY = Duration(1 * 60 + 30)

# TABLA 1  Jornada continental
JORNADA_ORDINARIA_VUELO_REGULAR = Duration(7 * 60 + 30)
MAXIMA_IRREBASABLE_VUELO_REGULAR = Duration(10 * 60)
JORNADA_ORDINARIA_SERVICIO_REGULAR = Duration(9 * 60)
MAXIMA_IRREBASABLE_SERVICIO_REGULAR = Duration(12 * 60)

# TABLA 1 Jornada transoceanica
JORNADA_ORDINARIA_VUELO_TRAN = Duration(8 * 60)
MAXIMA_IRREBASABLE_VUELO_TRAN = Duration(13 * 60)
JORNADA_ORDINARIA_SERVICIO_TRAN = Duration(10 * 60)
MAXIMA_IRREBASABLE_SERVICIO_TRAN = Duration(15 * 60)

# TABLA 2 Largo alcance
JORNADA_ORDINARIA_VUELO_LARGO_ALCANCE = Duration(8 * 60)
MAXIMA_ASIGNABLE_VUELO_LARGO_ALCANCE = Duration(13 * 60)
JORNADA_ORDINARIA_SERVICIO_LARGO_ALCANCE = Duration(10 * 60)
MAXIMA_ASIGNABLE_SERVICIO_LARGO_ALCANCE = Duration(15 * 60)

# TABLA 5 Jornada transoceanica especial
JORNADA_ORDINARIA_VUELO_TRANSP = Duration(8 * 60)
MAXIMA_IRREBASABLE_VUELO_TRANSP = Duration(16 * 60)
JORNADA_ORDINARIA_SERVICIO_TRANSP = Duration(10 * 60)
# Nota, la tabla 5 especifica que para efectos de pago, se pagara como tiempo
# de vulo al doble a partir de las 16:00 aunque la maxima asiganble sea 18:00

MAXIMA_IRREBASABLE_SERVICIO_TRANSP = Duration(16 * 60)

# Jornadas mensuales
JORNADA_ORDINARIA_VUELO_MENSUAL = Duration(65 * 60)
JORNADA_ORDINARIA_DH_MENSUAL = Duration(3 * 60)
GARANTIA_HORAS_DE_VUELO_MENSUAL = Duration(15 * 60)

# Otros créditos
RECESO_CONTINENTAL = Duration(12 * 60)
RECESO_TRANS = Duration(48 * 60)
MAX_TURN_TIME = Duration(3 * 60)

# Templates
string_part_template = "{day: >2} {routing!s:20s} {event_names!s:25s} {duty_type:18s} {report:%H:%M} " \
                       "{release:%H:%M}    "
num_part_template = " {daily:3} {block:3} {dh:3} {night:3} {xblock:3} " \
                    "{xduty:3} {maxirre:3} {delay:3} {xturn:3} "
duty_day_credits_template = string_part_template + num_part_template
trip_credits_template = duty_day_credits_template + '{pending_rest:3} '

# TODO : Implement pending credits and template for Line
line_credits_template = 50 * ' ' + "TOTALS" + 27 * ' ' + num_part_template

# Headers
duty_day_credits_header = 'D  RUTA                 SERVICIOS              TIPO DE JORNADA       FIMA  CIERRE    ' \
                          'DUTY  BLK   DH    NOCT  XBLK  XDTY  IRRE  DLAY  PLAT  '
trip_credits_header = duty_day_credits_header + 'RECE  '
line_credits_header = trip_credits_header + 'DESC FERI'


def get_rules_for(position, group):
    pass


class ConsecutiveDays(object):
    """Keeps track of how many consecutive days have been worked"""

    def __init__(self, starting_date, frequency):
        self.frequency = frequency
        self.last_counted_date = starting_date
        self.count = 0
        self.dates = []

    def calculate(self, duty):
        if duty.report.date() != self.last_counted_date + timedelta(days=1):
            self.count = 0
        for date in duty.get_elapsed_dates():
            self.count += 1
            if self.count == self.frequency:
                self.count = 0
                self.dates.append(date)
        self.last_counted_date = duty.release.date()


class Creditator(object):
    def __init__(self, position: str = None, group: str = None, month_scope=None) -> None:
        """According to the position and group, creditator should load the corresponding
        rules to build credit objects
        """
        self.position = position
        self.group = group
        self.rules = None
        self.set_rules()
        self.month_scope = month_scope

    def set_rules(self):
        pass

    @staticmethod
    def calculate_pending_rest(rest):
        # TODO : Implement pending_rest for all other duty_day types
        pending_rest = RECESO_CONTINENTAL - rest
        return pending_rest

    @staticmethod
    def credits_from_duty_day(duty_day):
        """
        Returns
        """
        # 1. Init our _credits
        duty_day._credits = CreditsDict()
        duty_day._credits.update({'day': duty_day.begin.day,
                                  'routing': FormattedList([duty_day.origin]),
                                  'report': duty_day.report,
                                  'release': duty_day.release,
                                  'duty_type': 'regular',
                                  'event_names': FormattedList(['']),
                                  'daily': duty_day.duration,
                                  'block': Duration(0),
                                  'dh': Duration(0),
                                  'night': Duration(0),
                                  'xduty': Duration(0),
                                  'xblock': Duration(0),
                                  'maxirre': Duration(0),
                                  'delay': duty_day.delay,
                                  'pending_rest': Duration(0),
                                  'xturn': Duration(0),
                                  'sunday': 0})

        # 2. Calculate night, event_names and routing
        for event in duty_day.events:
            event.compute_credits()
            #DH flights don't account for night time
            if isinstance(event, Flight) and not event.dh:
                duty_day._credits['night'] += Creditator.calculate_night_time(event)
            duty_day._credits['block'] += event._credits['block']
            duty_day._credits['dh'] += event._credits['dh']
            duty_day._credits['event_names'].append(event.name)
            duty_day._credits['routing'].append(event.route.destination)
        duty_day._credits['total'] = duty_day._credits['block'] + duty_day._credits['dh']

        # 3. Calculate xturn:
        for turn in duty_day.turns:
            duty_day._credits['xturn'] += (turn - MAX_TURN_TIME)

        # 4. Classify duty
        Creditator.duty_day_classifier(duty_day)

        if duty_day._credits['duty_type'] == 'regular':
            duty_day._credits['xblock'] = duty_day._credits['block'] - JORNADA_ORDINARIA_VUELO_REGULAR
            duty_day._credits['xduty'] = duty_day._credits['daily'] - JORNADA_ORDINARIA_SERVICIO_REGULAR
            duty_day._credits['maxirre'] = duty_day._credits['daily'] - MAXIMA_IRREBASABLE_SERVICIO_REGULAR
        elif duty_day._credits['duty_type'] == 'transoceanic':
            duty_day._credits['xblock'] = duty_day._credits['block'] - JORNADA_ORDINARIA_VUELO_TRAN
            duty_day._credits['xduty'] = duty_day._credits['daily'] - JORNADA_ORDINARIA_SERVICIO_TRAN
            duty_day._credits['maxirre'] = duty_day._credits['daily'] - MAXIMA_IRREBASABLE_SERVICIO_TRAN
        elif duty_day._credits['duty_type'] == 'special trans':
            duty_day._credits['xblock'] = duty_day._credits['block'] - JORNADA_ORDINARIA_VUELO_TRANSP
            duty_day._credits['xduty'] = duty_day._credits['daily'] - JORNADA_ORDINARIA_SERVICIO_TRANSP
            duty_day._credits['maxirre'] = duty_day._credits['daily'] - MAXIMA_IRREBASABLE_SERVICIO_TRANSP
            # If there is a maxirre, normal xduty time ends where maxirre starts
        elif duty_day._credits['duty_type'] == 'long haul':
            duty_day._credits['xblock'] = duty_day._credits['block'] - JORNADA_ORDINARIA_VUELO_LARGO_ALCANCE
            duty_day._credits['xduty'] = duty_day._credits['daily'] - JORNADA_ORDINARIA_SERVICIO_LARGO_ALCANCE
            duty_day._credits['maxirre'] = duty_day._credits['daily'] - MAXIMA_ASIGNABLE_SERVICIO_LARGO_ALCANCE
            # If there is a maxirre, normal xduty time ends where maxirre starts
            if duty_day._credits['maxirre'] > Duration(0):
                duty_day._credits['xduty'] = Duration(5 * 60)

        # 5. If there is a maxirre, normal xduty time ends where maxirre starts
        if duty_day._credits['maxirre'] > Duration(0):
            duty_day._credits['xduty'] = Duration(5 * 60)

        # 6. How many sundays?
        duty_day._credits['sunday'] = duty_day.how_many_sundays()
        duty_day_release_time = Duration(duty_day.release.hour * 60 + duty_day.release.minute)
        duty_day_ending_weekday = duty_day.release.isoweekday()
        is_a_worked_day = duty_day_release_time > WORKED_DAY
        if duty_day_ending_weekday == 7 and not is_a_worked_day:
            duty_day._credits['sunday'] -= 1

        # 7. Assign the needed template to print credits
        duty_day._credits['header'] = duty_day_credits_header
        duty_day._credits['template'] = duty_day_credits_template


    def credits_from_trip(self, trip):
        """Returns a list of all duty_day_credits_dict within the trip_match"""

        credits_list = []
        trip._credits = CreditsDict()
        # 1 Add all credits to find totals
        trip._credits['block'] = Duration(0)
        trip._credits['dh'] = Duration(0)
        trip._credits['daily'] = Duration(0)
        trip._credits['night'] = Duration(0)
        trip._credits['xblock'] = Duration(0)
        trip._credits['xduty'] = Duration(0)
        trip._credits['maxirre'] = Duration(0)
        trip._credits['delay'] = Duration(0)
        trip._credits['pending_rest'] = Duration(0)
        trip._credits['xturn'] = Duration(0)
        trip._credits['sunday'] = 0
        for duty_day in trip.duty_days:
            if duty_day.begin.month == self.month_scope:
                duty_day.compute_credits(self)
                trip._credits['block'] += duty_day._credits['block']
                trip._credits['dh'] += duty_day._credits['dh']
                trip._credits['daily'] += duty_day._credits['daily']
                trip._credits['night'] += duty_day._credits['night']
                trip._credits['xblock'] += duty_day._credits['xblock']
                trip._credits['xduty'] += duty_day._credits['xduty']
                trip._credits['maxirre'] += duty_day._credits['maxirre']
                trip._credits['delay'] += duty_day._credits['delay']
                trip._credits['xturn'] += duty_day._credits['xturn']
                trip._credits['sunday'] += duty_day._credits['sunday']
                credits_list.append(duty_day._credits)

        # 2. Calculate pending_rest between each duty day
        for rest, duty_day in zip(trip.rests, trip.duty_days):
            if (duty_day.begin.month == self.month_scope) and rest < Duration(12 * 60):
                tempo = Creditator.calculate_pending_rest(rest)
                duty_day._credits['pending_rest'] = tempo
                trip._credits['pending_rest'] += duty_day._credits['pending_rest']

        # 3. How many sundays?
        trip._credits['sunday'] = trip.how_many_sundays()
        trip_release_time = Duration(duty_day.release.hour * 60 + duty_day.release.minute)
        trip_ending_weekday = duty_day.release.isoweekday()
        is_a_worked_day = trip_release_time > WORKED_DAY
        if trip_ending_weekday == 7 and not is_a_worked_day:
            trip._credits['sunday'] -= 1

        # 4 Assign the needed template to print credits
        trip._credits['header'] = trip_credits_header
        trip._credits['template'] = trip_credits_template

        return credits_list

    def credits_from_line(self, line):
        """Returns a credits_list with all credits for given line"""

        # 1. Calculate pending credits for line DESC 7DAT HDAY
        line._credits.update({'day': '',
                              'routing': 'TOTALS',
                              'report': '',
                              'release': '',
                              'duty_type': '',
                              'event_names': '',
                              'daily': Duration(0),
                              'block': Duration(0),
                              'dh': Duration(0),
                              'night': Duration(0),
                              'xduty': Duration(0),
                              'xblock': Duration(0),
                              'maxirre': Duration(0),
                              'delay': Duration(0),
                              'pending_rest': Duration(0),
                              'xturn': Duration(0),
                              'sunday': 0,
                              '7day': 0})

        # 2 Add all credits to find totals
        line_credits_list = []
        consecutive_days = ConsecutiveDays(line.duties[0].report.date(), 7)
        for duty in line.duties:
            credit_list = duty.compute_credits(self)
            if credit_list:
                line_credits_list.extend(credit_list)
                line._credits['block'] += duty._credits['block']
                line._credits['dh'] += duty._credits['dh']
                line._credits['daily'] += duty._credits['daily']
                line._credits['night'] += duty._credits['night']
                line._credits['xblock'] += duty._credits['xblock']
                line._credits['xduty'] += duty._credits['xduty']
                line._credits['maxirre'] += duty._credits['maxirre']
                line._credits['delay'] += duty._credits['delay']
                line._credits['pending_rest'] += duty._credits['pending_rest']
                line._credits['xturn'] += duty._credits['xturn']
                line._credits['sunday'] += duty._credits['sunday']
                consecutive_days.calculate(duty)

        # 3 How many 7day do we have?
        days7 = consecutive_days.dates
        line._credits['7day'] += len(days7)

        # 4 Assign the needed template to print credits
        line._credits['header'] = line_credits_header
        line._credits['template'] = line_credits_template

        return line_credits_list

    @staticmethod
    def calculate_night_time(event):
        """
        Returns the nighttime flown in a given event, value is returned in seconds
        """

        BEGIN = event.begin.hour * 60 + event.begin.minute
        END = event.end.hour * 60 + event.end.minute
        NIGHTTIME_BEGIN = 22 * 60
        NIGHTTIME_END = 5 * 60
        MIDNIGHT = 24 * 60
        morninginter = [0, NIGHTTIME_END]
        nightinter = [NIGHTTIME_BEGIN, MIDNIGHT]

        if BEGIN > END:  # Event starts and ends in different days
            total = Creditator.overlapping(nightinter, [BEGIN, MIDNIGHT]) + Creditator.overlapping(morninginter,
                                                                                                   [0, END])
        else:  # Event starts and ends in same day
            total = Creditator.overlapping(morninginter, [BEGIN, END]) + Creditator.overlapping(nightinter,
                                                                                                [BEGIN, END])

        return Duration(total)

    @staticmethod
    # TODO : Probably this should be integrated into all ScheduleClasses as ScheduledClass.overlapping(00:30, 05:00)
    def overlapping(a, b):
        """
        returns the total overlapping time of periods a and b
        """
        return max(0, min(a[1], b[1]) - max(a[0], b[0]))

    @staticmethod
    def has_early_morning_time(event):
        """
        Returns true if event.overlaps(00:59, 04:59)
        """

        BEGIN = event.begin.hour * 60 + event.begin.minute
        END = event.end.hour * 60 + event.end.minute
        EARLY_MORNING_BEGIN = 59
        EARLY_MORNING_END = 4 * 60 + 59

        return (EARLY_MORNING_BEGIN < BEGIN < EARLY_MORNING_END) or (EARLY_MORNING_BEGIN < END < EARLY_MORNING_END)

    @staticmethod
    def duty_day_classifier(duty_day):
        """Given a DutyDay, this classifier will insert the following tags:
           - regular : any continental flight under 10:00 duty time. It is the default value
           - transoceanic : MAD, CDG, MXP, FCO, LHR, AMS, SVO, BCN, MUC, FRA, NRT, ICN, PVG, PEK
           - special transoceanic :
                                    a) MUST be transoceanic
                                    b) scheduled block time > 13:00 hrs
                                    c) scheduled duty time  > 15:00 hrs
           - long haul : Any flight with
                                    a) #of legs <= 2
                                    b) AND at least one leg > 4:30 hrs
                                    c) AND
                                        - OR    BLK > 10:00
                                        - OR    DUTY > 12:00
                                        - OR    DUTY > 09:30 AND  DUTY.OVERLAPS(00:59, 04:59) inclusive
           """
        # TODO : I don't like the way this looks
        if set([airport.iata_code for airport in duty_day._credits['routing']]).intersection(TRANSOCEANIC):
            duty_day._credits['duty_type'] = 'transoceanic'
            if (duty_day._credits['total']) > MINIMUM_BLOCK or duty_day._credits['daily'] > MINIMUM_DUTY:
                duty_day._credits['duty_type'] = 'special trans'
        elif len(duty_day.events) <= 2:
            for event in duty_day.events:
                if event.duration > Duration(4 * 60 + 30):
                    if duty_day._credits['block'] > Duration(10 * 60) or \
                                    duty_day._credits['daily'] > Duration(12 * 60) or \
                            (duty_day._credits['daily'] > Duration(9 * 60 + 30) and
                                 Creditator.has_early_morning_time(duty_day)):
                        duty_day._credits['duty_type'] = 'long haul'
                    break

    @staticmethod
    def month_credits(credits_dict):
        payable_credits = {}
        block = GARANTIA_HORAS_DE_VUELO_MENSUAL if credits_dict['block'] < GARANTIA_HORAS_DE_VUELO_MENSUAL \
            else credits_dict['block']
        dh = credits_dict['dh']
        # dh = credits_dict['dh'] - JORNADA_ORDINARIA_DH_MENSUAL

        # payable_credits['xblock'] = block + \
        #                             dh + \
        #                             credits_dict['xblock'] + \
        #                             credits_dict['pending_rest'] + \
        #                             credits_dict['xturn'] + \
        #                             credits_dict['delay'] - \
        #                             JORNADA_ORDINARIA_VUELO_MENSUAL
        payable_credits['xblock'] = block + \
                                    dh + \
                                    credits_dict['xblock'] + \
                                    credits_dict['pending_rest'] + \
                                    credits_dict['xturn'] - \
                                    JORNADA_ORDINARIA_VUELO_MENSUAL
        payable_credits['xduty'] = credits_dict['xduty']
        payable_credits['night'] = credits_dict['night']
        payable_credits['maxirre'] = credits_dict['maxirre']
        payable_credits['sunday'] = credits_dict['sunday']
        payable_credits['day7'] = credits_dict['7day']


        return payable_credits


class FormattedList(list):
    """List containing all cities traveled chronologically in a given Duty Day"""

    def __str__(self):
        #formatted = '/'.join(str(self))
        formatted = ''
        for element in self:
            formatted = formatted + str(element) + '/'
        return formatted


class CreditsDict(dict):
    """I need to add str representation and return a part of key-values as a list"""

    def __str__(self):
        """Use the class variable template"""
        return self['template'].format(**self)
