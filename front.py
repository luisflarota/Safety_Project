#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import datetime
from calendar import monthrange

import pandas as pd
import streamlit as st

import back_
from utils import *

# Constant variables
SELECTED_DAY = {'COMMUNITY RELATIONS': 10, 'CONCENTRATOR PLANT':118,
                'ENVIRONMENT':6, ' - PROJECT DELIVERY': 18, 
                'LOGISTICS': 23, 'MAINTENANCE': 100,
                'MINE OPERATIONS': 270, 'PLANNING, INVENTORY & WAREHOUSE': 65,
                'SAFETY & HEALTH':7, 'TECHNICAL SERVICES': 37}
MENU = ['Daily Report', 'Weekly Report', 'Monthly Report']
TODAY = datetime.date.today()
# Decrease computational time by fixing loading data

# Loading data is fixed, unless we upload new documents.
# TODO: Save whatever gets uploaded. 
@st.experimental_singleton
def read_files(new_hazards_file='a'):
    """
    Read the source data for daily, weekly and monthly reports.
    Args:
        new_hazards_file (str or dataframe): Help see if there is a new
                            hazard file. This plays with the function
                            decorator in line 25.
    Returns:
        Main (class): Instantiate a class that got multiple objects."""
    Main = back_.CargaReports(new_hazards_file)
    return Main

# TODO: Perhaps apply OOP in the front-end to avoid repeating variables in the 
# weekly and monthly report
def main():
    st.title("Safety KPI Dashboard")
    # Reading hazards, incidents and man-hours worked files
    Main = read_files()
    # Daily, weekly or monthly?
    choice = st.sidebar.selectbox('Report Type', MENU)
    if choice == 'Daily Report': # If daily
        # Create first radio button on the left
        radio_upload = st.sidebar.radio(
            'Do you want to upload new row data?', options=['Yes','No'], index=0
            )
        if radio_upload == 'Yes':
            # Get bytes of newest raw hazard data and the filename
            to_download = create_csv_bytes(Main.file)
            # Download box for newest row hazard data
            st.sidebar.download_button(label='📥 Download newest row hazard data',
                                    data=to_download[0] ,
                                    file_name= to_download[1])
            # Uploader box for newest row hazard data
            new_hazard = st.sidebar.file_uploader(
                'Upload your newest row data:',type='csv')
            if new_hazard:
                df_new_hazard = pd.read_csv(new_hazard)
                # Update hazards file with newest row hazard data
                Main = read_files(new_hazards_file = df_new_hazard)
        # We narrow options for the calendar based on the hazard row data
        min_date_hazard = min(Main.file['Event Date'])+datetime.timedelta(days=1)
        max_date_hazard = max(Main.file['Event Date'])
        # Insert date on calendar
        day_daily = st.sidebar.date_input(
            "Select a day:", value=min_date_hazard, 
            min_value=min_date_hazard, max_value=max_date_hazard)
        go_daily = st.sidebar.checkbox("View Report:")
        if go_daily:
            st.success('People that must be reporting hazards each day:')
            st.dataframe(pd.DataFrame.from_dict(
                SELECTED_DAY, orient ='index',columns = ['#People']))        
            st.success('People that reported hazards on {}'.format(day_daily))
            st.warning('"X" on the chart means that the Org. Unit did not meet the KPI goal')
            try:
                day_current = back_.DailyReport(
                    day_daily, selected_daily= SELECTED_DAY
                    )
                # Get and plot the dynamic chart
                chart_daily = day_current.get_chart_daily()
                st.plotly_chart(chart_daily[0])
                # Get and write details of people that reported on a specific date
                st.success("Details of people reporting on {}". format(day_daily))
                daily_dataframe = day_current.data_daily().reset_index()
                st.write(daily_dataframe)
                # Download a report with (1) static chart and (2) people details
                st.success('Download your daily report:')
                st.download_button(
                    label = 'Download ppt',data = get_ppt_file(
                        date=day_daily, chart = chart_daily[1],
                        org_FAIl =chart_daily[2], data=daily_dataframe
                        ).getvalue(),
                    file_name = 'hazard_report_{}.pptx'.format(str(day_daily))
                    )
            except:
                 st.write('Try to download another file')
# TODO: We can use OOP to avoid repetition for weekly and monthly at the front-end
    if choice == 'Weekly Report':
        initial_date = st.sidebar.date_input(
            "From:", TODAY-datetime.timedelta(days = 7),
            min_value=min(Main.manhours['Date'])
            )
        end_date = st.sidebar.date_input(
            "To:", max_value=TODAY,
            help='Choose up to 14 days from the initial date'
            )
        # Making sure that initial is neither  (1) beyond  today or the end date 
        # and the difference between the init. and the end. is less than 7 days. 
        if initial_date > TODAY or initial_date >= end_date or (
            end_date-initial_date)>datetime.timedelta(days = 7
            ):
            st.sidebar.error("Change dates")
        else:
            go_weekly = st.sidebar.checkbox("View Report:")
            if go_weekly:
                st.header(("Weekly Report from {} to {}").format(
                    initial_date, end_date)
                    )
                weekly = back_.WeeklyData(initial_date, end_date)
                info_week = weekly.convey_weekly(weekly = 1)
                #First dataframe
                st.subheader("1. OSHA monitoring indicators")
                st.dataframe(info_week[0].style.format("{:,.2f}"))
                st.dataframe(info_week[1].style.format("{:,.2f}"))
                #Third part
                st.subheader("2. National monitoring indicators")
                st.dataframe(info_week[2].style.format("{:.2f}"))
                #Fourth Part
                st.subheader("3. Injuries and illnesses")
                st.dataframe(info_week[3].style.format("{:.0f}"))
                #fifth part
                st.subheader("4. Incidents and accidents that occurred in the week")
                st.write(info_week[4])
                #sixth part
                st.subheader("5. Mining safety performance")
                st.success("#Accidents and ratios since 2018")
                st.plotly_chart(info_week[5])
                #Seventh part
                st.success("Yearly and TRIFR - 3Month rolling average since 2018")
                if len(info_week[7])>0:
                    st.plotly_chart(info_week[6])
                else:
                    st.warning('Plotting after 2019')


    if choice == 'Monthly Report':
        year_now = datetime.datetime.today().year
        month_now = datetime.datetime.today().month
        year = st.sidebar.selectbox("Year: ", range(2018, year_now+1))
        # Return dict with month:number
        dict_months = return_dict_months()
        # If year is "this" year, months should be narrowed 
        month_options = monthoptions(year, year_now, month_now)
        month = st.sidebar.selectbox("Month: ", month_options)
        start =  datetime.datetime.strptime(
            str(year)+"-"
            +str(dict_months[month])
            +"-01 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        end = datetime.datetime.strptime(
            str(year)+"-"
            +str(dict_months[month])+ "-" 
            + str(monthrange(year, dict_months[month])[1])+
            " 00:00:00", "%Y-%m-%d %H:%M:%S"
            )
        go_monthly = st.sidebar.checkbox("View Report: ")
        if go_monthly:
            st.header(("Report of {}").format(start.strftime("%B-%Y")))
            monthly_rep = back_.WeeklyData(start, end)
            info_month = monthly_rep.convey_weekly()
            #First dataframe
            st.subheader("1. OSHA monitoring indicators")
            st.dataframe(info_month[0].style.format("{:,.2f}"))
            st.dataframe(info_month[1].style.format("{:,.2f}"))
            #Third part
            st.subheader("2. National monitoring indicators")
            st.dataframe(info_month[2].style.format("{:.2f}"))
            #Fourth Part
            st.subheader("3. Injuries and illnesses")
            st.dataframe(info_month[3].style.format("{:.0f}"))
            #fifth part
            st.subheader("4. Incidents and accidents that occurred in the week")
            st.write(info_month[4])
            #sixth part
            st.subheader("5. Mining safety performance")
            st.success("#Accidents and ratios since 2018")
            st.plotly_chart(info_month[5])
            #Seventh part
            st.success("Yearly and TRIFR - 3Month rolling average since 2018")
            if len(info_month[7])>0:
                st.plotly_chart(info_month[6])
            else:
                st.warning('Plotting after 2019')

if __name__ == '__main__':
    main()
