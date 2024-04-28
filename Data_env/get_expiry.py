from Data_env.Data_cleaning import data_cleaning
import pandas as pd
import datetime as dt
import holidays
india_holidays = holidays.country_holidays(country="IN")


class get_expiry(data_cleaning):

    def __init__(self,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.dff = self.get_futures_data()
        self.current_backtest_date = self.dff["Timestamp"].iloc[2].date()
        self.india_holidays = holidays.country_holidays(country="IN")
        #self.current_backtest_date = dt.datetime(2019,5,2)--> testing
    def day_of_week(self):

        day_of_week = self.current_backtest_date.weekday()
        return day_of_week

    def current_weekly(self):
        if self.day_of_week() > 3:
            days_to_add = 7 - (self.day_of_week() - 3)
        else:
            days_to_add = (3 - self.day_of_week()) % 7
        target_weekly_exp = self.current_backtest_date + dt.timedelta(days=days_to_add)
        if target_weekly_exp in self.india_holidays:
            print("Thrusday holiday")
            target_weekly_exp = target_weekly_exp -dt.timedelta(days=1)
        target_weekly_exp_formatted = target_weekly_exp.strftime('%d%b').upper()
        return target_weekly_exp_formatted

    def next_weekly(self):
        if self.day_of_week() >= 3:  #If today is Thursday or after
            days_to_add = 7 - (self.day_of_week() - 3)
        else:  # If today is before Thursday
            days_to_add = (3 - self.day_of_week())
        target_next_weekly_exp = self.current_backtest_date + dt.timedelta(days=days_to_add + 7)
        if target_next_weekly_exp in self.india_holidays:
            print("Thrusday holiday")
            target_next_weekly_exp = target_next_weekly_exp -dt.timedelta(days=1)
        target_next_weekly_exp_formatted = target_next_weekly_exp.strftime('%d%b').upper()
        return target_next_weekly_exp_formatted

    def monthly(self):
        next_month = self.current_backtest_date.replace(day=28) + dt.timedelta(days=4)
        last_day_of_month = next_month - dt.timedelta(days=next_month.day)
        current_month = last_day_of_month.month

        while last_day_of_month.weekday() != 3:
            last_day_of_month -= dt.timedelta(days=1)
        third_thursday = last_day_of_month


        if third_thursday.month != current_month:
            while third_thursday.month != current_month:
                third_thursday -= dt.timedelta(days=1)
                third_thursday = third_thursday.strftime('%d%b').upper()
        third_thursday = third_thursday.strftime('%d%b').upper()
        return third_thursday

    def next_monthly(self):
        next_month_start = self.current_backtest_date.replace(day=1) + pd.DateOffset(months=1)
        first_thursday = next_month_start + pd.DateOffset(weekday=3)
        third_thursday = first_thursday + pd.DateOffset(weeks=2)
        third_thursday_formatted = third_thursday.strftime('%d%b').upper()
        return third_thursday_formatted



