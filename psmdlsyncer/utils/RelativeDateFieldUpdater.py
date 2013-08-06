from ssispowerschoolsyncer.utils.DB import UpdateField
import datetime
from ssispowerschoolsyncer.utils.Dates import date_to_database_timestamp, today, custom_strftime

class RelativeDateFieldUpdater(UpdateField):

    def update_menu_relative_dates(self,
                                   forward_days=7,
                                   skip=['Saturday', 'Sunday']):
        d = self.first()
        forward_delta = datetime.timedelta(days=forward_days)
        menu = []
        every_seven_days = [i * 7 for i in range(1, 100)]

        for day in range(1, forward_delta.days+1):  # 1..7 by default
            iter_date = d + datetime.timedelta(days=day)
            day_of_week = iter_date.strftime('%A')

            if not day_of_week in skip:
                dictionary = {'day_of_week':day_of_week, 'date':self.format_date(iter_date)}
                menu.append( self.output().format(**dictionary) )

        self.update_menu(menu)

    def first(self):
        """
        Return the first date to start with, default is today
        """
        return today()
        
    def output(self):
        return "{day_of_week} ({date})"

    def tomorrow_text(self):
        return "Tomorrow"

    def next_text(self):
        return "next "

    def format_date(self, d):
        return custom_strftime( "{S} %b", d )
    

if __name__ == "__main__":

    t = RelativeDateFieldUpdater('Testing testing', 'Changeme')

    t.update_menu_relative_dates(forward_delta=datetime.timedelta(days=20))
