from Data_env.Data_cleaning import data_cleaning
import pandas as pd
import datetime as dt
import holidays
india_holidays = holidays.country_holidays(country="IN")


class get_expiry(data_cleaning):

    def __init__(self,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.dff = self.get_futures_data()
        self.backtest_dates = []
        if not self.dff.empty:
            self.current_backtest_date = self.dff["Timestamp"].dt.date.min()
            self.current_backtest_date_max = self.dff["Timestamp"].dt.date.max()
        else:
            self.current_backtest_date = None
            self.current_backtest_date_max = None
        if self.current_backtest_date and self.current_backtest_date_max:
            for curr_date in range((self.current_backtest_date_max - self.current_backtest_date).days + 1):
                self.backtest_dates.append(self.current_backtest_date + dt.timedelta(days=curr_date))

        self.india_holidays = holidays.country_holidays(country="IN")


    def current_weekly(self):
        target_weekly_exp_formatted =[]
        for day_of_week in self.backtest_dates:
            if day_of_week.weekday() > 3:
                days_to_add = 7 - (day_of_week.weekday() - 3)
            else:
                days_to_add = (3 - day_of_week.weekday()) % 7
            target_weekly_exp = day_of_week+ dt.timedelta(days=days_to_add)
            if target_weekly_exp in self.india_holidays:
                print("Thrusday holiday")
                target_weekly_exp = target_weekly_exp -dt.timedelta(days=1)
            target_weekly_exp_formatted.append(target_weekly_exp.strftime('%d%b').upper())

        return list(set(target_weekly_exp_formatted))

    def monthly(self):
        monthly_exp_formatted = []

        for date in self.backtest_dates:
            next_month = date.replace(day=28) + dt.timedelta(days=4)
            last_day_of_month = next_month - dt.timedelta(days=next_month.day)
            current_month = last_day_of_month.month

            while last_day_of_month.weekday() != 3:
                last_day_of_month -= dt.timedelta(days=1)

            monthly_exp = last_day_of_month.strftime('%d%b').upper()
            monthly_exp_formatted.append(monthly_exp)


        return list(set(monthly_exp_formatted))






