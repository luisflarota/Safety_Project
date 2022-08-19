#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import datetime
from calendar import monthrange
from textwrap import wrap

import dateutil
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from dateutil import rrule

# Set properties for pictures in the PPT file
FONT = {'family' : 'normal',
        'size'   : 14}
matplotlib.rc('font', **FONT)

class CargaReports:
    """ 
    Load 3 main files for daily (03_AllHazrds), 
    weekly and monthly (the other 2)
    """
    def __init__(self, newhazard=0, file_hazards="03_AllHazards.xlsx", 
                file_incidents="01_Accidents_Fill.xlsx",
                man_hours="02_ManHoursWorked.csv"):
        # Correspond to hazards
        self.file= pd.read_excel(file_hazards).reset_index(drop = True)
        self.file['Event Date'] = pd.to_datetime(self.file['Event Date']).dt.date
        if type(newhazard) == pd.DataFrame:
            print('x')
            newhazard['Event Date'] = pd.to_datetime(newhazard['Event Date'])
            newhazard['Event Creation Date'] = pd.to_datetime(newhazard['Event Creation Date'])
            self.file = pd.concat([self.file, newhazard], ignore_index=True, sort=False)
            self.file['Event Date'] = pd.to_datetime(self.file['Event Date']).dt.date
        # For incidents + accidents
        self.file_incidents = pd.read_excel(file_incidents)
        self.file_incidents['DATE'] = pd.to_datetime(self.file_incidents['DATE'])
        # Man-hours worked
        self.manhours = pd.read_csv(man_hours)
        self.manhours['Date'] = pd.to_datetime(self.manhours['Date'])
        # Some useful constants - injuries classification
        self.recordables = ['FI', 'LTI', 'MTI', 'RWI']
        self.national = ['FI', 'LTI']
        self.all_injuries = ['FI', 'LTI', 'MTI', 'RWI', 'FAI']
        self.lost_time = ['LTI']
        self.fatal = ['FI']
        self.rest = ['RWI']
        self.mti = ['MTI']
        self.fai = ['FAI']

class DailyReport(CargaReports):
    """
    Nested DailyReport class to get fixed information from CargaReports
    Args:
        Date (datetime.date)             : It is selected in a streamlit date inputbox 
                                        - frontend
        selected_daily (dict, org.unit:#): How org. unit should be reporting
    """
    def __init__(self, date, selected_daily = None):
        super().__init__(newhazard=0,file_hazards="03_AllHazards.xlsx", 
                file_incidents="01_Accidents_Fill.xlsx",
                man_hours="02_ManHoursWorked.csv")
        self.date_daily = date
        self.date_dailybefore = self.date_daily - datetime.timedelta(days = 1)
        self.sel = selected_daily
        self.file_daily = self.file[
            (self.file.iloc[:,1] == self.date_daily)
            &(self.file.iloc[:,5].isin(self.sel.keys()))
            ]
        self.file_daily_columns = self.file_daily.columns.values
        self.file_before = self.file[
            (self.file.iloc[:,1] == self.date_dailybefore)
            &(self.file.iloc[:,5].isin(self.sel.keys()))
            ]
        self.file_before_columns = self.file_before.columns.values
        self.before, self.current = self.join_dailys()

    def get_chart_daily(self):
        """
        Get the first dynamic and static chart of people reporting vs should be reporting.
        Returns:
            fig (plotly)        : Dynamic chart of people ...
            fig_plt (plt)       : Static chart of people ...
            goal_FAIl (list)    : Org. Units that did not meet the goal for a specific
                                chosen date.
         """
        fig = go.Figure(go.Bar(
            x = self.before.iloc[:,0], y = self.before.iloc[:,1], yaxis = 'y1', 
            marker_color = "#AAF0D1",name = 'People: '+
            str(self.date_daily- datetime.timedelta(days = 1))
            ))
        fig.add_trace(go.Bar(
            x = self.current.iloc[:,0], y = self.current.iloc[:,1], yaxis = 'y1', 
            marker_color = "#50BFE6",name = 'People: '+str(self.date_daily)
            ))
        #Plotly
        fig.add_trace(go.Scatter(
            x = self.current.iloc[:,0], y = self.current.iloc[:,3], mode = 'markers+text',
            showlegend = True, marker = dict(color = "#50BFE6", size = 20, 
            line = dict(color = '#FFFFFF', width = 3)), 
            text = list(map(txt,self.current.iloc[:,3])), 
            textfont = dict(color = "#800000", size = 32),
            yaxis = 'y2', name = "Ratio "+str(self.date_daily)
            ))
        fig.update_layout(
            barmode = 'stack', yaxis = go.layout.YAxis(), 
            yaxis2 = go.layout.YAxis(side = 'right', overlaying = 'y'), 
            legend = dict(
                orientation = 'h', yanchor = 'bottom', xanchor = 'right', y = 1.1, x = 1
                ),
            xaxis_title = '<b>Organizational Units</b>',
            yaxis_title = '<b>#People Reporting Hazards</b>',
            yaxis2_title = '<b>Hazard Ratio (#Reported/# Must Report)</b>',
            legend_title = 'Dates:'
            )
        #matplotlib side
        fig_plt, ax_plt = plt.subplots(figsize=(15,6))
        ax_twin = ax_plt.twinx()
        ax_plt.bar(
            self.before.iloc[:,0],self.before.iloc[:,1],color="#AAF0D1", 
            label='People: '+str(self.date_daily- datetime.timedelta(days = 1))
            )
        ax_plt.bar(
            self.current.iloc[:,0],self.current.iloc[:,1], 
            bottom = self.before.iloc[:,1], color="#50BFE6", 
            label='People: '+str(self.date_daily)
            )
        ax_twin.scatter(
            self.current.iloc[:,0],self.current.iloc[:,3], c="#50BFE6",s=110, 
            label='Ratio: '+str(self.date_daily), edgecolors='w', linewidth=2.5
            )
        goal_FAIl = []
        for row in range(self.current.shape[0]):
            if self.current.iloc[row,3]<1:
                ax_twin.annotate(
                    'X', xy=(self.current.iloc[row,0],self.current.iloc[row,3]),
                    color='red', size=20)
                goal_FAIl.append(self.current.iloc[row,0])
        labels_x = ['\n'.join(wrap(lab, 8)) for lab in self.before.iloc[:,0]]
        ax_plt.set_xticklabels(labels_x)
        ax_plt.set_ylabel('#People Reporting Hazards')
        ax_twin.set_ylabel('Hazard Ratio (#Reported/#Reporting)')
        ax_plt.legend(loc='upper left',bbox_to_anchor=(0.6, 1.30))
        ax_twin.add_artist(ax_twin.legend(loc='upper left',bbox_to_anchor=(0, 1.19)))
        ax_twin.set_xlabel('Organizational Units')
        ax_plt.set_xlabel('Organizational Units')
        plt.tight_layout()
        return fig, fig_plt, sorted(goal_FAIl)

    def merge_daily(self, file_daily, file_daily_columns):
        """
        Create a pivot table to get the daily chart
        Args:
            file_daily (dataframe)      : Hazards file
            file_daily_columns (list)   : It comes from the org. unit. that must be on a 
                                        daily report
        Returns:
            daily (dataframe): Pivot table containing org. unit and people reporting in
                                each one.
        """
        #Pivot table for ORG.UNIT
        daily = file_daily.groupby(
            by = file_daily_columns[5]
            ).count().reset_index().iloc[:,:2]
        merger = pd.DataFrame(self.sel.items(), columns = daily.columns.values)
        daily = daily.merge(merger, on = daily.columns.values[0])
        daily['Div'] = round(daily.iloc[:,1]/ daily.iloc[:,2], 2)
        #second part of the daily
        return daily

    def join_dailys(self):
        """
        Returns:
            data_bef, self.current: two dataframes, one for current date and
                the oner for one day before.
        """
        self.current =  self.merge_daily(self.file_daily, self.file_daily_columns)
        data_bef =  self.merge_daily(self.file_before, self.file_before_columns)
        example_dict = {'ORGANIZATIONAL UNIT':0, 'Event ID_x':0, 'Event ID_y':0,'Div':0}
        org_units_bef = list(data_bef['ORGANIZATIONAL UNIT'])
        org_units_current = list(self.current['ORGANIZATIONAL UNIT'])
        lefts = [x for x in org_units_bef if x not in org_units_current
            ] + [x for x in org_units_current if x not in org_units_bef]
        for left in lefts:
            if left not in org_units_bef:
                example_dict['ORGANIZATIONAL UNIT'] = left
                data_bef = data_bef.append(example_dict, ignore_index=True)
            if left not in org_units_current:
                example_dict['ORGANIZATIONAL UNIT'] = left
                self.current = self.current.append(example_dict, ignore_index=True)
        data_bef = data_bef.sort_values(by='ORGANIZATIONAL UNIT')
        self.current = self.current.sort_values(by='ORGANIZATIONAL UNIT')
        return data_bef, self.current

    def data_daily(self):
        pivot = pd.pivot_table(
            self.file_daily, values = self.file_daily_columns[1], 
            index = [self.file_daily_columns[5], self.file_daily_columns[2]],
            aggfunc= 'count')
        pivot.columns = ['#R.']
        return pivot
        
class WeeklyData(CargaReports):
    """ 
    This class will inherit of CargaReports' objects for "simplicity". 
    Inheritance is called in the super init
    """
    def __init__(self, initial_date, end_date):
        super().__init__(self, file_hazards="03_AllHazards.xlsx", 
                file_incidents="01_Accidents_Fill.xlsx",
                man_hours="02_ManHoursWorked.csv")
        self.initial_date = datetime.datetime.combine(
            initial_date, datetime.datetime.min.time()
            )
        self.end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())
        self.init_mma = datetime.datetime.fromisoformat(
            str(min(self.file_incidents['DATE'].dt.year)+1)+"-01-01 00:00:00"
            )
    # The following get indicator based on selected one for weekly and monthly report
    def int_kpi_wtd(self, selected = None):
        """
        Args:
            selected (list): This is the group of injuries for the kpi
        Returns:
            ... (dataframe): Get the accidents corresponding to the <selected>
                            argument and between the dates chosen by the user - this 
                            case is weekly
        """
        return self.file_incidents[
            (self.file_incidents['CLASSIFICATION'].isin(selected)) 
            & (self.file_incidents['DATE'] >= self.initial_date) 
            & (self.file_incidents['DATE'] <= self.end_date)
            ].shape[0]
    
    def int_kpi_mtd(self,selected = None):
        """
        Args:
            selected (list): This is the group of injuries for the kpi
        Returns:
            ... (dataframe): Get the accidents corresponding to the <selected>
                            argument and for the month chosen by the user.
        """       
        self.indicator = self.file_incidents[
            (self.file_incidents['CLASSIFICATION'].isin(selected)) 
            & (self.file_incidents['DATE'].dt.month == self.end_date.month) 
            & (self.file_incidents['DATE'].dt.year == self.end_date.year)
            ].shape[0]
        return self.indicator
 
    def manhoursworkerd_mtd(self, horas = None):
        """
        Args:
            horas (str): Either controlled or uncontrolled man-hours worked
        Returns:
            self.man_hours_worked (dataframe): Man-hours worked for the selected month
        """
        hor = 'MHW ( C )'
        if horas == "todas":
            hor = 'MHW (C + NC)'
        self.man_hours_worked = self.manhours[
            (self.manhours['Date'].dt.month == self.end_date.month) 
            & (self.manhours['Date'].dt.year == self.end_date.year)
            ][hor].sum()
        return self.man_hours_worked

    def kpi_mtd(self, selected = None, horas = None):
        """
        Args:
            selected (list): Injuries selected to be reported in a KPI
            horas (str): Either controlled or uncontrolled man-hours worked
        Returns:
            indicator (float): monthly indicator based on selected injuries and hours
                                (args).
        """
        indicator = self.int_kpi_mtd(
            selected = selected
            )* 10**6 / self.manhoursworkerd_mtd(horas = horas) #getting mtd iondicator
        if indicator != indicator:
            indicator = 0
        return indicator

    def int_kpi_ytd(self, selected = None):
        """
        Args:
            selected (list): Injuries selected to be reported in a KPI
        Returns:
            data (list): group of indicators based on selected injuries 
                        and for each year until the last year of the user's
                        selected date.
        """
        data = []
        for _ in range(self.end_date.year, min(self.file_incidents['DATE'].dt.year)-1 , -1):
            self.indicator = self.file_incidents[
                (self.file_incidents['CLASSIFICATION'].isin(selected)) 
                & (self.file_incidents['DATE'].dt.year == _)
                ].shape[0]
            data.append(self.indicator)
        return data

    def manhoursworkerd_ytd(self, horas = None):
        """
        Args:
            horas (str): Either controlled or uncontrolled man-hours worked
        Returns:
            dato (list): Yearly man-hours worked until the year of the selected day.
        """   
        dato = []
        for _ in range(self.end_date.year, min(self.file_incidents['DATE'].dt.year)-1 , -1):
            hor = 'MHW ( C )'
            if horas == "todas":
                hor = 'MHW (C + NC)'
            self.man_hours_worked = self.manhours[
                self.manhours['Date'].dt.year == _
                ][hor].sum()
            dato.append(self.man_hours_worked)    
        return dato
   
    def kpi_ytd(self, selected = None, horas = None):
        """
        Args:
            selected (list): Injuries selected to be reported in a KPI
            horas (str): Either controlled or uncontrolled man-hours worked
        Returns:
            indicator (float): indicator based on selected injuries and hours - for the year.
        """
        return [round(a*10**6/b, 2) if b!=0 else 0 for a, b in zip(
            self.int_kpi_ytd(selected = selected), self.manhoursworkerd_ytd(horas = horas)
            )]

    #Moving average
    def int_kpi_mma(self, selected = None, moving = int()):
        """
        Args:
            selected (list): Injuries selected to be reported in a KPI
            moving (int): number of months for the rolling average. The int() functions
                        makes sure that the input is a integer.
        Returns:
            indicator (float): indicator based on selected injuries and hours - for the
                            rolling average.
        """
        self.initialdate_ = self.end_date + dateutil.relativedelta.relativedelta(
            months =- moving
            ) - datetime.timedelta(days = self.end_date.day-1)
        self.enddate_= self.initial_date_ + dateutil.relativedelta.relativedelta(
            months =+ moving
            ) - datetime.timedelta(days = 1)
        self.indicator = self.file_incidents[
            (self.file_incidents['CLASSIFICATION'].isin(selected)) 
            & (self.file_incidents['DATE'] >= self.initialdate_) 
            & (self.file_incidents['DATE'] < self.enddate_)
            ].shape[0]
        self.man_hours_worked = self.manhours[
            (self.manhours['Date'] >= self.initialdate_)
             & (self.manhours['Date'] <= self.enddate_)
             ]['MHW ( C )'].sum()
        indicator = self.indicator*1000000/self.man_hours_worked
        if indicator != indicator:
            indicator = 0
        return indicator

    def mma_charts(self, selected = None, moving = int()):
        """
        Args:
            selected (list): This is the group of injuries for the kpi.
            moving (int): number of months for the rolling average. The int() functions
                        makes sure that the input is a integer.
        Returns:
            data_mma (list): Get the indicator for each month's rolling average. For
                            instance, if moving =3 and date is August 2022, it will 
                            calculate the indicator for June, July and Aug.
        """      
        data_mma = []
        for _ in rrule.rrule(rrule.MONTHLY, dtstart = self.init_mma, until = self.end_date):
            initiator = _ + dateutil.relativedelta.relativedelta(months =- moving)
            finish = _ - datetime.timedelta(days = 1)
            indic = self.file_incidents[
                (self.file_incidents['CLASSIFICATION'].isin(selected)) 
                & (self.file_incidents['DATE'] >= initiator) 
                & (self.file_incidents['DATE'] <= finish)
                ].shape[0]
            mhw = self.manhours[
                (self.manhours['Date'] >= initiator) 
                & (self.manhours['Date'] <= finish)
                ]['MHW ( C )'].sum()
            data_mma.append(round(indic*1000000/mhw, 2))
        return data_mma
    
    def names_mma_charts(self):
        """
        Returns:
            names_mma (list): Get the name for each month's rolling average, i.e., 
                                Jun2022, July2022 and so on.
        """  
        names_mma = []
        for _ in rrule.rrule(rrule.MONTHLY, dtstart = self.init_mma, until = self.end_date):
            finish = _ - datetime.timedelta(days = 1)  
            names_mma.append(finish.strftime("%b%y"))      
        return names_mma

    def to_dataframe(self, moving = int()):
        """
        Args:
            moving (int): number of months for the rolling average. The int() functions
                        makes sure that the input is a integer.
        Returns:
            ... (datetime): Correspong to the previous month and date of the selected date
        """   
        self.initial_date_ = self.end_date + dateutil.relativedelta.relativedelta(
            months =- moving
            ) - datetime.timedelta(days = self.end_date.day-1)
        return self.initial_date_ + dateutil.relativedelta.relativedelta(
            months =+ moving
            ) - datetime.timedelta(days = 1)
        
    def last_lti_(self, selected = None):
        """
        Args:
            selected (list): This is the group of injuries for the kpi
        Returns:
            self.last_lti (str): The last lost time injury when compared to the
                                user's selected date.
        """   
        try:
            self.last_lti = self.file_incidents[
                (self.file_incidents['CLASSIFICATION'] == selected) 
                & (self.file_incidents['DATE'] <= self.end_date)
                ]['DATE'].sort_values().iloc[-1]
        except:
            self.last_lti = min(self.manhours['Date'])
        return self.last_lti

    def convey_weekly(self, weekly=0):
        """
        Args:
            weekly (int): This will trigger if the report is either weekly or monthly.
                            0 if not, otherwise yes.
        Returns:
        TODO: Get better variables' names
            first_part (dataframe)  : OSHA Monitoring Indicators. 
            second_part (dataframe) : Second table after the one above - starting with TRIFR
                                    12 MMA...
            third_part (dataframe)  : National Monitoring Indicators.
            fourth_part (dataframe) : Injuries and Illnesses Table.
            fifth_part (dataframe)  : Detailed information of accidents in the week/month.
            fig (plotly)            : Mining Safety Performance chart.
            fig2 (plt)              : Rolling average charts.
            mov_12 (dataframe)      : In case the date is 2018, the mov_12 will be used to 
                                    print a message that the user should select another date.
        """   
        if weekly:
            name_first_up = [
            self.end_date.strftime("%b-%Y (Up to {})".format(
                self.end_date.strftime("%b"+str(self.end_date.day))
                ))]
        else:
            name_first_up = [self.end_date.strftime("%B-%Y")]
    
        lista = name_first_up + [
                    _ for _ in range(self.end_date.year, 
                    min(self.file_incidents['DATE'].dt.year)-1 , -1)
                    ]
        #OSHA MONITORING - first table
        first_part = pd.DataFrame(columns = lista)
        first_part.loc['All Injuries Frequency Rate (AIFR)'] = [
            self.kpi_mtd(selected = self.all_injuries)
            ] + self.kpi_ytd(selected= self.all_injuries)
        first_part.loc['Total Recordable Injuries Frequency Rate (TRIFR)'] = [
            self.kpi_mtd(selected = self.recordables)
            ] + self.kpi_ytd(selected= self.recordables)
        first_part.loc['Lost Time Injuries Frequency Rate (LTIFR)'] = [
            self.kpi_mtd(selected = self.lost_time)
            ] + self.kpi_ytd(selected= self.lost_time)
        # Second part of first table
        last_lti = self.last_lti_(selected = 'LTI')
        if last_lti == min(self.manhours['Date']):
            last_lti = 'Did not happen yet'
        second_part = pd.DataFrame(columns = ["Values"], index = [
            "TRIFR 12MMA (Up to {})".format(self.to_dataframe(moving=12).strftime("%d%b%Y")),
            "Man-hours worked without LTI (Last one on {})".format(
                last_lti
                ), "Lost Days (Year-to-date)"
                ])
        second_part.iloc[:,0] = [
            self.int_kpi_mma(selected = self.recordables, moving = 12), 
            self.manhoursworkerd_nolti(), self.number_lost_day()]

        # NATIONAL monitoring indicators - third table
        third_part = pd.DataFrame(columns = lista)
            #index = [, 'Severity Index (SI)','Accidentability Index (AI)']
        third_part.loc['Frequency Index (FI)'] = [
            self.kpi_mtd(selected = self.national , horas = "todas")
            ] + self.kpi_ytd(selected = self.national , horas = "todas")
        third_part.loc['Severity Index (SI)'] = self.national_si_kpi()
        third_part = third_part.fillna(0)
        third_part.loc['Accidentability Index (AI)'] = third_part.loc[
            'Frequency Index (FI)'
            ] * third_part.loc['Severity Index (SI)'] / 1000

        # Injuries and Illnesses - fourth table
        fourth_part = pd.DataFrame(columns = [
            self.initial_date.strftime("%b-%d") + " to " + self.end_date.strftime("%b-%d")
            ]+ lista)
        fourth_part.loc['A. Fatalities'] = [
            self.int_kpi_wtd(selected = self.fatal)
            ] + [
                self.int_kpi_mtd(selected = self.fatal)
                ] + self.int_kpi_ytd(selected = self.fatal)
        fourth_part.loc['B. Lost Time Inj.'] = [
            self.int_kpi_wtd(selected = self.lost_time)
            ] + [self.int_kpi_mtd(selected = self.lost_time)] + self.int_kpi_ytd(
                selected = self.lost_time
                )
        fourth_part.loc['C. Rest. Work Inj.'] = [
            self.int_kpi_wtd(selected = self.rest)
            ] + [
                self.int_kpi_mtd(selected = self.rest)
                ] + self.int_kpi_ytd(selected = self.rest)
        fourth_part.loc['D. Medic. Tre. Inj.'] = [
            self.int_kpi_wtd(selected = self.mti)
            ] + [
                self.int_kpi_mtd(selected = self.mti)
                ] + self.int_kpi_ytd(selected = self.mti)
        fourth_part.loc['E. Recordable Injuries'] = fourth_part.sum(axis = 0) 
        fourth_part.loc["F. First Aid Inj."] = [
            self.int_kpi_wtd(selected = self.fai)
            ] + [
                self.int_kpi_mtd(selected = self.fai)
                ] + self.int_kpi_ytd(selected = self.fai)
        fourth_part.loc["G. Total Injuries:"] = fourth_part.loc[
            ['E. Recordable Injuries', "F. First Aid Inj."]
            ].sum(axis = 0) 
        if weekly == 0:
            fourth_part.drop(
                self.initial_date.strftime("%b-%d") + 
                " to " + self.end_date.strftime("%b-%d"),
                 axis=1, inplace=True)
        # Incidents table: Fifth part
        if len(self.incidents()) <= 0:
            fifth_part = "Nice, we did not have incidents!!"
        else:
            fifth_part = self.incidents()

        #TRIFR, AIFR CHART: Sixth part
        cols_c = fourth_part.columns.to_list()[::-1][:-1]
        index_c = [
            "A. Fatalities", "B. Lost Time Inj.","C. self.rest. Work Inj.",
            "D. Medic. Tre. Inj.","F. First Aid Inj."
            ]
        up = pd.DataFrame(fourth_part, columns = cols_c, index = index_c)
        low = pd.DataFrame(first_part, index = [
            'Total Recordable Injuries Frequency Rate (TRIFR)',
             'Lost Time Injuries Frequency Rate (LTIFR)',
              'All Injuries Frequency Rate (AIFR)'
              ], columns = cols_c)
        last = pd.concat([up, low])
        last.index = ['FI', 'LTI', 'RWI', 'MTI', 'FAI', 'TRIFR', 'LTIFR', 'AIFR']
        last = last.T
        fig = go.Figure()
        color1 = ['#800000', '#3366ff', '#ff9933', '#00ff00', '#ffff00']
        color2 = ['#003300','#ff00ff' ]
        for column, color in zip(last.columns[:5], color1):
            fig.add_trace(
                go.Bar(
                    x = [str(x) for x in last.index], 
                    y = last[column], 
                    marker_color = color,
                    name = column, yaxis = 'y1'
                    )
                )
        for column, color in zip(last.columns[[5,7]], color2):
            x_axis = [str(x) for x in last.index]
            y_axis = [round(elem, 2) for elem in last[column]]
            fig.add_trace(
                go.Scatter(
                    x = x_axis, y = y_axis, marker_color=color,
                    name = column, yaxis = 'y2', mode = 'lines+markers+text'
                    )
                )#, text = text, textfont = dict(color = color)))
            
        fig.update_layout(barmode = 'stack', xaxis = {
            'type' : 'category'
            }, yaxis = go.layout.YAxis(), yaxis2 = go.layout.YAxis(
                side = 'right', overlaying = 'y1'
                ), legend = dict(orientation = 'h', x=0,y=-0.2),
            xaxis_title='Date', yaxis_title='# Accidents',
            yaxis2_title='Ratio (AIFR or TRIFR)')
        
        x_axis = self.names_mma_charts()
        fig2 = go.Figure()
        mov_12 =  self.mma_charts(selected = self.recordables, moving =12)
        fig2.add_trace(
            go.Scatter(
                x = x_axis, y = mov_12, 
                mode = 'lines+markers', name = 'TRIFR-12MMA', marker_color = '#000000'
                )
            )
        fig2.add_trace(
            go.Scatter(
                x = x_axis, y = self.mma_charts(selected = self.recordables, moving =3), 
                mode = 'lines+markers', name = 'TRIFR-3MMA', marker_color = '#c4bcbc'
                )
            )
        fig2.update_layout(
            legend = dict(orientation = 'h', x=0,y=-0.2),xaxis_title='Date', 
            yaxis_title='Ratio'
            )
        return [first_part, second_part, third_part, fourth_part, fifth_part, fig, fig2, mov_12]
    
    def manhoursworkerd_nolti(self):
        """
        Returns:
            ... (dataframe): Hours worked after last lost time injury.
        """
        self.last_lti_help = monthrange(self.last_lti.year, self.last_lti.month)[1]
        self.end_date_help = monthrange(self.end_date.year, self.end_date.month)[1]

        if self.last_lti == datetime.datetime.today().month and \
            self.last_lti.year == datetime.datetime.today().year:
            return self.manhours[
                (self.manhours['Date'].dt.month == self.last_lti.month) 
                & (self.manhours['Date'].dt.year == self.last_lti.year)
                ]['MHW ( C )'].sum() * (
                self.end_date.day - self.last_lti.day
                )/ (self.end_date.day)
        
        elif self.last_lti.month == self.end_date.month and\
             self.last_lti.year == self.end_date.year:
            return self.manhours[
                (self.manhours['Date'].dt.month == self.last_lti.month)
                & (self.manhours['Date'].dt.year == self.last_lti.year)
                ]['MHW ( C )'].sum() * (
                self.end_date.day - self.last_lti.day
                )/ (self.last_lti_help)

        else:
            return self.manhours[
                (self.manhours['Date'] < 
                (self.end_date + dateutil.relativedelta.relativedelta(months =-1))) 
                & (self.manhours['Date']> self.last_lti)
                ]['MHW ( C )'].sum() + (
                    self.manhours[
                        (self.manhours['Date'].dt.month == self.last_lti.month) 
                    & (self.manhours['Date'].dt.year == self.last_lti.year)
                    ]['MHW ( C )'].sum() *
                     (self.last_lti_help - self.last_lti.day)/(self.last_lti_help)
                     ) + (
                    self.manhours[(self.manhours['Date'].dt.month == self.end_date.month) 
                    & (self.manhours['Date'].dt.year == self.end_date.year)][
                        'MHW ( C )'].sum() * (self.end_date.day)/(self.end_date_help)
                        )

    def number_lost_day(self, ya = None):
        """
        Args:
            ya (int): If first year it will be none, otherwise if will return second
                    statement
        Returns:
            ... (dataframe): This will be the number of days lost because of lost time
                            injuries
         """
        if ya:
            return self.file_incidents[
                (self.file_incidents['DATE'].dt.year == ya)
                ]['LOST DAYS FROM LOST TIME INJURY'].sum() +self.file_incidents[
                    (self.file_incidents['DATE'].dt.year == ya)
                    ]['LOST DAYS FROM PREVIOUS LOST TIME INJURIES'].sum()
        return self.file_incidents[
            (self.file_incidents['DATE'].dt.year == self.end_date.year)
            ]['LOST DAYS FROM LOST TIME INJURY'].sum() +self.file_incidents[
                (self.file_incidents['DATE'].dt.year == self.end_date.year)
                ]['LOST DAYS FROM PREVIOUS LOST TIME INJURIES'].sum()

    # This function will be apply same as the previous one.
    def number_lost_day_national(self):
        a = self.file_incidents[
            (self.file_incidents['DATE'].dt.month == self.end_date.month) 
            & (self.file_incidents['DATE'].dt.year == self.end_date.year)
            ]['LOST DAYS FROM LOST TIME INJURY'].sum()+self.file_incidents[
                (self.file_incidents['DATE'].dt.month == self.end_date.month) 
                & (self.file_incidents['DATE'].dt.year == self.end_date.year)
                ]['LOST DAYS FROM PREVIOUS LOST TIME INJURIES'].sum()
        dato = []
        for _ in range(self.end_date.year, min(self.file_incidents['DATE'].dt.year)-1 , -1):
            dato.append(self.number_lost_day(ya = _))      
        return [a] + dato

    # Refer to national kpi_ytd line 316.
    def national_si_kpi(self):
        return [
            a*10**6/b for a,b in zip(self.number_lost_day_national(), 
            [
                self.manhoursworkerd_mtd(horas = "todas")
                ] + self.manhoursworkerd_ytd(horas = "todas"))]

    def incidents(self):
        """
        Returns:
            data_return (dataframe): Detailed table of accidents ocurring between the
                                    user's selected date inputs.
        """
        data_return = self.file_incidents[
            (self.file_incidents['DATE'] >= self.initial_date) 
            & (self.file_incidents['DATE'] <= self.end_date)
            ][['DATE', 'ORGANIZATIONAL UNIT', 'COMPANY NAME', 'DESCRIPTION', 'INJURY']]
        if data_return.shape[0] == 0:
            return "Nice! We did not have incidents."
        else:
            return data_return

def txt(valor):
    """Help map the hazard indicator
    Args:
        valor(int): Hazard KPI - #reported/#supposed to be reporting
    """
    if valor < 1:
        return "x"
    else:
        return ""
