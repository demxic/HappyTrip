import sqlite3
import sys
from datetime import datetime, timedelta

import psycopg2

from model import creditator
# from model.elements import DateTracker
# from model.payment import compensation_dict, PayCheck
# from model.scheduleClasses import Itinerary, Trip, CrewMember
# from rosterReaders.lineCreator import Liner
from model.scheduleClasses import CrewMember, Trip, GroundDuty, DutyDay
from model.timeClasses import DateTracker
from model.txtRoster import RosterReader, Liner


#summaryFile = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\Resumen de horas\\2018\\201805 - resumen de horas.txt"
#summaryFile = "C:\\Users\\Xico\\Desktop\\franco.txt"
# rolFile = "C:\\Users\\demxi\\Google Drive\\Sobrecargo\\roles\\201802.txt"
rolFile = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\Roles\\2018-Roles\\201809.txt"
summaryFile = "C:\\Users\\Xico\\Google Drive\\Sobrecargo\\Resumen de horas\\2018\\201808-resumen de horas.txt"


class Menu:
    """Display a menu and respond to choices when run"""

    def __init__(self):
        self.line = None
        self.choices = {
            "1": self.read_printed_line,
            "2": self.print_line,
            "3": self.credits,
            "4": self.viaticum,
            "5": self.store,
            "6": self.read_flights_summary,
            "7": self.retrieve_duties_from_data_base,
            "8": self.print_components,
            "10": self.quit}

    @staticmethod
    def display_menu():
        print('''
        Orgutrip Menu

        1. Carga tu rol mensual.
        2. Imprime en pantalla tu rol.
        3. Calcula los créditos.
        4. Obtener viáticos.
        5. Almacenar tu rol en la base de datos.
        6. Cargar tu resumen de horas mensuales.
        7. Cargar tiempos por itinerario de la base de datos.
        8. Imprimir cada componente
        10. Quit
        ''')

    def run(self):
        """Display the menu and respond to choices"""
        while True:
            self.display_menu()
            choice = input("¿Qué deseas realizar?: ")
            action = self.choices.get(choice)
            if action:
                action()
            else:
                print("{0} is not a valid choice".format(choice))

    def read_printed_line(self):
        """Let's read the roaster from a given .txt file"""
        print("read_printed_line")
        with open(rolFile) as fp:
            rr = RosterReader(fp)
        crew_member = CrewMember(**rr.crew_stats)
        print("crew_member : ", crew_member)
        print("Carry in within month? ", rr.carry_in)
        print("Roster timeZone ", rr.timeZone)
        print("Roster year and month ", rr.year, rr.month)
        dt = DateTracker(rr.year, rr.month, rr.carry_in)
        print("Date Tracker: ", dt)
        print()
        print("\nCreating a Liner . . . ")
        liner = Liner(dt, rr.roster_days, 'scheduled')
        liner.build_line()
        self.line = liner.line
        self.line.crewMember = crew_member

    def print_line(self):
        """Let's print out the roaster"""
        print(self.line)

    def credits(self):
        cr = creditator.Creditator('SOB', 'SO01', self.line.month)
        print(creditator.line_credits_header)
        for row in self.line.compute_credits(cr):
            print(row)
        print(self.line._credits['template'].format(**self.line._credits))
        mmmm = cr.month_credits(self.line._credits)
        print("""
                        t_ext_vuelo:    {xblock:2}
                        t_ext_servicio: {xduty:2}
                        t_ext_nocturno: {night:2}
                        maxirre:        {maxirre:2}
                        séptimo día     {day7: >5}
                        prima dominical {sunday: >5}
                        """.format(**mmmm))
        # compensations = compensation_dict(691.02 * 30)
        # paycheck = PayCheck(compensations)
        # paycheck.calculate(mmmm)
        # print(paycheck)

    def viaticum(self):
        pass

    def store(self):
        print('Storing data ')
        conn = sqlite3.connect('C:\\Users\\Xico\\Dropbox\\PyCharmProjects\\Orgutrip\\data\\flights.db')
        c = conn.cursor()
        for duty_day in self.line.return_duty_days():
            for event in duty_day.events:
                if event.name == 'X' or event.name == 'RZ':
                    pass
                else:
                    print(event)
                    c.execute("INSERT INTO flights (date, number, origin, begin, destination, duration)"
                              "VALUES (?, ?, ?, ?, ?, ?)", (event.begin.date(),
                                                            event.name,
                                                            event.origin,
                                                            event.begin.strftime("%H%M"),
                                                            event.destination,
                                                            event.duration.minutes))
                    conn.commit()

        print('Reading data :')
        for row in c.execute("SELECT * FROM flights"):
            print(row)
        conn.close()

    def read_flights_summary(self):
        """Let's read month's flights summary from a given .txt file"""
        with open(summaryFile, 'r') as fp:
            content = fp.read()
        rr = RosterReader(content)

        # 1. Create Crew Member
        crew_member = CrewMember(**rr.crew_stats)
        print("Crew Member :", end=" ")
        print(crew_member)
        print("crew_stats : ", rr.crew_stats)
        print("Carry in within month? ", rr.carry_in)
        print("Roster timeZone ", rr.timeZone)
        print("Roster year and month ", rr.year, rr.month)

        dt = DateTracker(rr.year, rr.month, rr.carry_in)
        print("\ndatetracker for ", dt)

        print("\nCreating a Liner")
        liner = Liner(dt, rr.roster_days, 'actual_itinerary', rr.crew_stats['base'])
        liner.build_line()
        self.line = liner.line
        self.line.crew_member = crew_member

    def retrieve_duties_from_data_base(self):
        for duty in self.line.duties:
            if isinstance(duty, Trip):
                duty.update_from_database()
            # if isinstance(duty, DutyDay):
            #     duty.events[0].update_from_database()
        # for duty in self.line.duties:
        #     if isinstance(duty, Trip):
        #         trip = Trip.load_by_id(duty.number, duty.dated)
        #         if trip:
        #             trip.update_with_actual_itineraries(duty)
        #         else:
        #             print("trip #{}/{} not stored in the database ".format(duty.number, duty.dated))
        #     if isinstance(duty, DutyDay):
        #         duty.events[0].update_from_database()

    def print_components(self):
        for duty in self.line:
            if isinstance(duty, Trip):
                for duty_day in duty.duty_days:
                    for turn in duty_day.turns:
                        print(turn)

    def quit(self):
        answer = input("¿Deseas guardar los cambios? S/N").upper()
        if answer[0] == 'S':
            self.line.crew_member.update_to_db()


        print("adiós")
        sys.exit(0)


if __name__ == '__main__':
    Menu().run()