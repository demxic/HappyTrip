"""
Created on 11/04/2015

@author: Xicoténcatl s
"""
import re

roster_data_RE = re.compile(r'''
    (?P<month>\w{3,10})\s+         #Any month from enero to diciembre (or january to december) 
    (?P<year>\d{4})\s+             #4 digit year, v.gr. 2018 
    (?P<header>.+)
    DH:\s+                         #Header ends when DH:  3:45 is found
    (?P<DH>\d{1,2}:\d{1,2}).+      
    DAY.+?DH\s+
    (?P<body>.*)                   #What comes next is the body
    ''', re.VERBOSE | re.DOTALL | re.IGNORECASE)

carryInRE = re.compile(r'''
    (?P<day>\d{2})                 #2 digits at start followed by a - or a whitespace
    (?:\s|-)
    (?P<endDay>\w{2})\s+           #The day when the sequence ends (if any)        v.gr. 07-08
    ''', re.VERBOSE)

first_duty_RE = re.compile(r'''
    (\d{2}-\d{2}\s[A-Z]{1,2}\s)|   #Either a ground duty
    (\d{2}\s[A-Z]{2}\s\d{4}\s)     #Or a trip row
    ''', re.VERBOSE | re.DOTALL)

non_trip_RE = re.compile(r'''
    (?P<day>\d{2})                 #2 digits at start followed by a - 
    -
    (?P<end_day>\d{2})\s+          #The day when the sequence ends (if any)        v.gr. 07-08
    (?P<name>[A-Z]{1,2}|[A-Z]\d)\s+#One or two letters or a letter and a digit
    ''', re.VERBOSE | re.DOTALL)

roster_trip_RE = re.compile(r'''
    (?P<day>\d{2})\s+
    (?P<end_day>[A-Z]{2})\s+
    (?P<name>\d{4})\s+
    (?P<flights>(\w{4,6}\s+\w{3}\s+\d{4}\s+\w{3}\s+\d{4}\s+)+)
    ''', re.VERBOSE | re.DOTALL | re.IGNORECASE)

roster_date_RE = re.compile(r'''
    (?P<month>\w{3,10})\s+         #Any month from enero to diciembre (or january to december) 
    (?P<year>\d{4})\s+             #4 digit year, v.gr. 2018 
    ''', re.VERBOSE)

nameSequenceRE = re.compile(r'''
    (?P<name>\w{1,4})\s+            #one or more alpha numeric chars             v.gr. 5072
    (?P<sequence>.+)                #All remaining data
    ''', re.VERBOSE)

itineraryRE = re.compile(r"""
    Begin\s                          #Begin actual_itinerary word
    (?P<begin>\d{4})\s               #4 digit begin time                                 v.gr.   0300, 1825
    End\s                            #End actual_itinerary word
    (?P<end>\d{4})                   #4 digit end time
    """, re.VERBOSE)

airItineraryRE = re.compile(r"""
    (?P<name>\w{4,6})\s          #An opt 2char airlinecode + 4 digit number + " "    v.gr   AM0001, DH0403, 0170
    (?P<origin>[A-Z]{3})\s         #3 letter origin IATA airport code                  v.gr MEX, SCL, JFK
    (?P<begin>\d{4})\s             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<destination>[A-Z]{3})\s    #3 letter destination IATA airport code             v.gr MEX, SCL, JFK
    (?P<end>\d{4})                 #4 digit end time
    """, re.VERBOSE)

# RegEx que se debe utilizar cuando el rol no contiene Crew Type
crewstats_no_type = re.compile(r"""
    (?P<crew_member_id>\d{6})\s+    #6 digits at start followed by one or more spaces        v.gr. 102711
    (?P<name>(\w{1,12}|(\w{1,11}\s\w{1,11})))\s+           #One or twelve alphanumeric crew member line name        v.gr. XICOTENCATL
    (?P<pos>[A-Z]{3})\s+            #Three letter postion id                                 v.gr. SOB
    (?P<group>\w{4})\s+             #Group for member                                        v.gr. S001
    (?P<base>[A-Z]{3})\s+           #Three letter code for homebase airport                  v.gr. MEX
    (?:\d)\s+                       #Line number, whatever that means                        v.gr. 0
    (?P<seniority>\d{1,4})\s+       #Crewmember's line number                                v.gr. 694
    (Time\sZone:)
    (?P<timeZone>\w).*              #TimeZone for all events                                v.gr. Time
    """, re.VERBOSE | re.IGNORECASE)

# RegEx que se debe utilizar cuando el rol contiene Crew Type
crewstats_with_type = re.compile(r"""
    (?P<crew_member_id>\d{6})\s+    #6 digits at start followed by one or more spaces        v.gr. 102711
    (?P<name>(\w{1,12}|(\w{1,11}\s\w{1,11})))\s+           #One or twelve alphanumeric crew member line name        v.gr. XICOTENCATL
    (?P<pos>[A-Z]{3})\s+            #Three letter postion id                                 v.gr. SOB
    (?P<group>\w{4})\s+             #Group for member                                        v.gr. S001
    (?P<crewType>\w)\s+             #Type, whatever that means                               v.gr. B
    (?P<base>[A-Z]{3})\s+           #Three letter code for homebase airport                  v.gr. MEX
    (?:\d)\s+                       #Line number, whatever that means                        v.gr. 0
    (?P<seniority>\d{1,4})\s+       #Crewmember's line number                                v.gr. 694
    (Time\sZone:)
    (?P<timeZone>\w).*              #TimeZone for all events                                v.gr. Time Zone:B
    """, re.VERBOSE | re.IGNORECASE)

itinerary_RE = re.compile(r"""
    Begin\s                          #Begin actual_itinerary word
    (?P<begin>\d{4})\s               #4 digit begin time                                 v.gr.   0300, 1825
    End\s                            #End actual_itinerary word
    (?P<end>\d{4})                   #4 digit end time
    """, re.VERBOSE)

# https://regex101.com/r/aR5aH9/1
flight_RE = re.compile(r"""
    (?P<date>\w{5})\s+              #Any 5 char alphanumeric number for a date  + " "    v.gr   15FEB, 23MAR, 02JUN
    (?:\d{4})\s+                    #4 digits for RPT time
    (?P<name>\w{4,6})\s+            #4 digits for FLIGHT number
    (?P<origin>[A-Z]{3})\s          #3 letter origin IATA airport code                  v.gr MEX, SCL, JFK
    (?P<begin>\d{4})\s+             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<destination>[A-Z]{3})\s     #3 letter destination IATA airport code             v.gr MEX, SCL, JFK
    (?P<end>\d{4})\s+               #4 digit end time
    (?:\d{4})\s+                    #4 digits for RLS time
    (?:\d{4})\s+                    #4 digits for BLK time
    (?P<equipment>\w{3})            #3 digits for EQ
    """, re.VERBOSE)

twoSpaces_RE = re.compile(r'''
    \s+
    ''', re.VERBOSE)

reserve_RE = re.compile(r"""
    (?P<date>\d{2}[A-Z]{3})\s+       #DD Beginning day and month for the reserve
    (?:\d{4})\s+                    #reserve's report time... to be ignored
    (?P<name>\w{2})\s+              #2 letters/numbers indicate a reserve name
    (?P<origin>[A-Z]{3})\s          #3 letter origin IATA airport code                  v.gr MEX, GDL, TIJ
    (?P<begin>\d{4})\s+             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<destination>[A-Z]{3})\s     #3 letter destination IATA airport code             v.gr MEX, GDL, TIJ
    (?P<end>\d{4})\s+               #4 digit end time
    """, re.VERBOSE | re.DOTALL)

flights_RE = re.compile(r"""
    (?P<name>\w{4,6})\s+            #4 digits for FLIGHT number
    (?P<origin>[A-Z]{3})\s          #3 letter origin IATA airport code                  v.gr MEX, SCL, JFK
    (?P<begin>\d{4})\s+             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<destination>[A-Z]{3})\s     #3 letter destination IATA airport code             v.gr MEX, SCL, JFK
    (?P<end>\d{4})\s+               #4 digit end time
    (?P<blk>\d{4})\s+               #4 digits for RLS or BLK time.  
    (?P<turn>\d{4})\s+              #4 digits for BLK or TURN time.
    (?P<equipment>\w{3})            #3 digits for EQ
    """, re.VERBOSE)

dutyday_RE = re.compile(r'''
    (?P<day>\d{2})                               #DD day for the first flight in the dutyday
    (?P<month>[A-Z]{3})\s+                       #MMM month for the first flight in the dutyday
    (?P<report>\d{4})\s+                         #duty day's first flight report time
    (?P<flights>.*?)                             #All flights data to be further examined
    ((?P<layover_city>[A-Z]{3})\s+               # Layover city      v.gr. GDL
     (?P<layover_duration>\d{2}:\d{2}))?\s+      # Layover duration  v.gr. 23:54
    (?P<bl>\d{4})BL\s+                           #As a named group ---> (?P<bl>\d{4})BL\s+
    (?P<crd> [-\d]{4,5})CRD\s+                          #As a named group ---> (?P<crd>\d{4})CRD\s+
    (?P<tl>\d{4})TL\s+                               #As a named group ---> (?P<tl>\d{4})TL\s+
    (?P<dy>\d{4})DY                                  #As a named group ---> (?P<dy>\d{4})DY
    ''', re.VERBOSE | re.DOTALL)

trip_RE = re.compile(r"""
    \#\s*                           #Ignore the first hashtag and whitespace
    (?P<number>\d{4})\s*             #Next comes the Trip number or TripId
    .*?                             #We don't care for the "CHECK IN AT" legend that follows
    (?P<check_in>\d{2}:\d{2})\s*    #Only for the actual_itinerary check in time
    (?P<dated>\d{2}[A-Z]{3}\d{4})\s*#But we are interested in the trip_match's starting date
    (?P<duty_days>.*?)              #What comes next are all further dutydays to be examined.
    TOTALS\s*                       #And down here come all credits for the trip_match, just in case
    (?P<tl>\d{1,2}:\d{2})TL\s*
    (?P<bl>\d{1,2}:\d{2})BL\s*
    (?P<cr>\d{1,2}:\d{2})CR\s*
    (?P<tafb>\d{1,3}:\d{2})TAFB
    """, re.VERBOSE | re.DOTALL)

# Following re help to elimante footer and headers in the trips file
header_date_RE = re.compile(r"""
    (?P<header_date>\d{1,2}/\d{1,2}/\d{4})\s                                  #header date                                  
""", re.VERBOSE | re.DOTALL)

header_link_RE = re.compile(r"""
    (?P<header_link>http://crew.am.jepphost.com/amx/portal/)\s                    #header link
""", re.VERBOSE | re.DOTALL)

footer_link_RE = re.compile(r"""
    (?P<footer_link>crew.am.jepphost.com/amx/portal/)\s
""", re.VERBOSE | re.DOTALL)

footer_paging_RE = re.compile(r"""
    (?P<footer_paging>\d{1,3}/\d{1,3})\s                                #Paging       v.gr.   4/430
""", re.VERBOSE | re.DOTALL)

simple_trip_RE = re.compile(r"""
    \#\s
    (?P<number>\d{4})\s*    
    .*?
    (?P<dated>\d{2}[A-Z]{3}\d{4})\s*
    """, re.VERBOSE | re.DOTALL)