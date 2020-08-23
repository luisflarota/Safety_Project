import sqlite3
import pandas as pd
import os
import datetime
import numpy as np
import dateutil
from calendar import monthrange
from dateutil import rrule
from datetime import timedelta


#Setting the files that we will use:
class Carga_Reports:
    def __init__(self, file_hazards, file_incidents, man_hours):
        self.file = file_hazards
        self.file_incidents = pd.read_excel(file_incidents)
        self.manhours = pd.read_excel(man_hours)


class Daily_report(Carga_Reports):
    def __init__(self, file_hazards, file_incidents, man_hours, date, selected_daily = None):
        super().__init__(file_hazards, file_incidents, man_hours)
        self.sel = selected_daily
        self.file_daily = self.file[(self.file.iloc[:,1] == date) & (self.file.iloc[:,5].isin(self.sel.keys()))]
        self.file_daily_columns = self.file_daily.columns.values

    def graphs_daily(self):
        #Pivot table for ORG.UNIT
        self.daily = self.file_daily.groupby(by = self.file_daily_columns[5]).count().reset_index().iloc[:,:2]
        
        merger = pd.DataFrame(self.sel.items(), columns = self.daily.columns.values)
        self.daily = self.daily.merge(merger, on = self.daily.columns.values[0])
        self.daily['Div'] = round(self.daily.iloc[:,1]/ self.daily.iloc[:,2], 2)
        #second part of the daily
        return self.daily
    def data_daily(self):
        pivot = pd.pivot_table(self.file_daily, values = self.file_daily_columns[1], index = [self.file_daily_columns[5], self.file_daily_columns[2]], \
        aggfunc= 'count')
        pivot.columns = ['Amount of Hazards:']
        return pivot
class Weekly_data(Carga_Reports):
    def __init__(self, file_hazards, file_incidents, man_hours, initial_date, end_date):
        super().__init__(file_hazards, file_incidents, man_hours)
        self.initial_date = datetime.datetime.combine(initial_date, datetime.datetime.min.time())
        self.end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())
        self.init_mma = datetime.datetime.fromisoformat(str(min(self.file_incidents['FECHA'].dt.year)+1)+"-01-01 00:00:00")
    def int_kpi_wtd(self, selected = None):
        return self.file_incidents[(self.file_incidents['CLASIFICACIÓN'].isin(selected)) & (
            self.file_incidents['FECHA'] >= self.initial_date) & (self.file_incidents['FECHA'] <= self.end_date)].shape[0]
    
    
    def int_kpi_mtd(self,selected = None):         
        self.indicator = self.file_incidents[(self.file_incidents['CLASIFICACIÓN'].isin(selected)) & (
            self.file_incidents['FECHA'].dt.month == self.end_date.month) & (self.file_incidents['FECHA'].dt.year == self.end_date.year)].shape[0]
        return self.indicator
 
    def manhoursworkerd_mtd(self, horas = None):
        hor = 'HH ( C )'
        if horas == "todas":
            hor = 'HH (C + NC)'
        self.man_hours_worked = self.manhours[(self.manhours['Fecha'].dt.month == self.end_date.month) & (
            self.manhours['Fecha'].dt.year == self.end_date.year)][hor].sum()
        return self.man_hours_worked

    def kpi_mtd(self, selected = None, horas = None):
        return self.int_kpi_mtd(selected = selected) * 10**6 / self.manhoursworkerd_mtd(horas = horas)

    def int_kpi_ytd(self, selected = None):    
        data = []
        for _ in range(self.end_date.year, min(self.file_incidents['FECHA'].dt.year)-1 , -1):
            self.indicator = self.file_incidents[(self.file_incidents['CLASIFICACIÓN'].isin(selected)) & (
                self.file_incidents['FECHA'].dt.year == _)].shape[0]
            data.append(self.indicator)
        return data

    def manhoursworkerd_ytd(self, horas = None):      
        dato = []
        for _ in range(self.end_date.year, min(self.file_incidents['FECHA'].dt.year)-1 , -1):
            hor = 'HH ( C )'
            if horas == "todas":
                hor = 'HH (C + NC)'
            self.man_hours_worked = self.manhours[self.manhours['Fecha'].dt.year == _][hor].sum()
            dato.append(self.man_hours_worked)    
        return dato
   
    def kpi_ytd(self, selected = None, horas = None):
        return [round(a*10**6/b, 2) for a, b in zip(self.int_kpi_ytd(selected = selected), self.manhoursworkerd_ytd(horas = horas))]

    #Moving average
    def int_kpi_mma(self, selected = None, moving = int()):
        self.initialdate_ = self.end_date + dateutil.relativedelta.relativedelta(months =- moving) - datetime.timedelta(days = self.end_date.day-1)
        self.enddate_= self.initial_date_ + dateutil.relativedelta.relativedelta(months =+ moving) - datetime.timedelta(days = 1)
        self.indicator = self.file_incidents[(self.file_incidents['CLASIFICACIÓN'].isin(selected)) & (self.file_incidents['FECHA'] >= self.initialdate_) & (
            self.file_incidents['FECHA'] < self.enddate_)].shape[0]
        self.man_hours_worked = self.manhours[(self.manhours['Fecha'] >= self.initialdate_) & (self.manhours['Fecha'] <= self.enddate_)]['HH ( C )'].sum()
        return self.indicator*1000000/self.man_hours_worked

    def mma_charts(self, selected = None, moving = int()):
        data_mma = []
        for _ in rrule.rrule(rrule.MONTHLY, dtstart = self.init_mma, until = self.end_date):
            initiator = _ + dateutil.relativedelta.relativedelta(months =- moving)
            finish = _ - datetime.timedelta(days = 1)
            indic = self.file_incidents[(self.file_incidents['CLASIFICACIÓN'].isin(selected)) & (self.file_incidents['FECHA'] >= initiator) & (
            self.file_incidents['FECHA'] <= finish)].shape[0]
            mhw = self.manhours[(self.manhours['Fecha'] >= initiator) & (self.manhours['Fecha'] <= finish)]['HH ( C )'].sum()
            data_mma.append(round(indic*1000000/mhw, 2))
        return data_mma
    
    def names_mma_charts(self, selected = None):
        names_mma = []
        for _ in rrule.rrule(rrule.MONTHLY, dtstart = self.init_mma, until = self.end_date):
            finish = _ - datetime.timedelta(days = 1)  
            names_mma.append(finish.strftime("%b%y"))      
        return names_mma

    def to_dataframe(self, moving = int()):
        self.initial_date_ = self.end_date + dateutil.relativedelta.relativedelta(months =- moving) - datetime.timedelta(days = self.end_date.day-1)
        return self.initial_date_ + dateutil.relativedelta.relativedelta(months =+ moving) - datetime.timedelta(days = 1)
        
    def last_lti_(self, selected = None):
        self.last_lti = self.file_incidents[( self.file_incidents['CLASIFICACIÓN'] == selected) & (self.file_incidents['FECHA'] <= self.end_date)]['FECHA'].sort_values().iloc[-1]
        return self.last_lti
        

    def manhoursworkerd_nolti(self, selected = None):
        self.last_lti = self.file_incidents[( self.file_incidents['CLASIFICACIÓN'] == selected) & (self.file_incidents['FECHA'] <= self.end_date)]['FECHA'].sort_values().iloc[-1]
        self.last_lti_help = monthrange(self.last_lti.year, self.last_lti.month)[1]
        self.end_date_help = monthrange(self.end_date.year, self.end_date.month)[1]

        if self.last_lti == datetime.datetime.today().month and self.last_lti.year == datetime.datetime.today().year:
            return self.manhours[(self.manhours['Fecha'].dt.month == self.last_lti.month) & (self.manhours['Fecha'].dt.year == self.last_lti.year)]['HH ( C )'].sum() * (
                self.end_date.day - self.last_lti.day)/ (self.end_date.day)
        
        elif self.last_lti.month == self.end_date.month and self.last_lti.year == self.end_date.year:
            return self.manhours[(self.manhours['Fecha'].dt.month == self.last_lti.month) & (self.manhours['Fecha'].dt.year == self.last_lti.year)]['HH ( C )'].sum() * (
                self.end_date.day - self.last_lti.day)/ (self.last_lti_help)

        else:
            return self.manhours[(self.manhours['Fecha'] < (self.end_date + dateutil.relativedelta.relativedelta(months =-1))) & (
                self.manhours['Fecha']> self.last_lti) ]['HH ( C )'].sum() + (self.manhours[(self.manhours['Fecha'].dt.month == self.last_lti.month) & (
                    self.manhours['Fecha'].dt.year == self.last_lti.year)]['HH ( C )'].sum() * (self.last_lti_help - self.last_lti.day)/ (self.last_lti_help)) + (
                    self.manhours[(self.manhours['Fecha'].dt.month == self.end_date.month) & (self.manhours['Fecha'].dt.year == self.end_date.year)][
                        'HH ( C )'].sum() * (self.end_date.day)/(self.end_date_help))

    def number_lost_day(self, ya = None):
        if ya:
            return self.file_incidents[(self.file_incidents['FECHA'].dt.year == ya)]['DÍAS PERDIDOS'].sum() + \
                self.file_incidents[(self.file_incidents['FECHA'].dt.year == ya)]['ARRASTRA DÍAS?'].sum()
        return self.file_incidents[(self.file_incidents['FECHA'].dt.year == self.end_date.year)]['DÍAS PERDIDOS'].sum() + \
                self.file_incidents[(self.file_incidents['FECHA'].dt.year == self.end_date.year)]['ARRASTRA DÍAS?'].sum()

    def number_lost_day_national(self, ya = None):
        a = self.file_incidents[(self.file_incidents['FECHA'].dt.month == self.end_date.month) & (self.file_incidents['FECHA'].dt.year == self.end_date.year)]['DÍAS PERDIDOS'].sum() +\
            self.file_incidents[(self.file_incidents['FECHA'].dt.month == self.end_date.month) & (self.file_incidents['FECHA'].dt.year == self.end_date.year)]['ARRASTRA DÍAS?'].sum()
        dato = []
        for _ in range(self.end_date.year, min(self.file_incidents['FECHA'].dt.year)-1 , -1):
            dato.append(self.number_lost_day(ya = _))      
        return [a] + dato

    def national_si_kpi(self):
        return [a*10**6/b for a,b in zip(self.number_lost_day_national(ya = "ok"), [self.manhoursworkerd_mtd(horas = "todas")] + self.manhoursworkerd_ytd(horas = "todas"))]


    def incidents(self):
        return self.file_incidents[(self.file_incidents['FECHA'] >= self.initial_date) & (self.file_incidents['FECHA'] <= self.end_date)][[
            'FECHA', 'AREA', 'EMPRESA', 'DESCRIPCIÓN', 'DAÑO/LESIÓN']]


