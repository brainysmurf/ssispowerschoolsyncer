from psmdlsyncer.mod.database.DatabaseActivityExtender import UpdateField
import datetime
from psmdlsyncer.utils.Dates import date_to_database_timestamp, tomorrow, day_after_tomorrow, today, custom_strftime

class RelativeDateFieldUpdater(UpdateField):

    def update_menu_relative_dates(self,
                                   forward_days=7,
                                   skip=['Saturday', 'Sunday']):
        d = self.first()
        forward_delta = datetime.timedelta(days=forward_days)
        menu = []
        every_seven_days = [i * 7 for i in range(1, 100)]

        for day in range(forward_delta.days):
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
        return custom_strftime( "{S} %b %Y", d )

if __name__ == "__main__":

    t = RelativeDateFieldUpdater('Teacher Notices Database', 'Start Date')
    u = RelativeDateFieldUpdater('Teacher Notices Database', 'End Date')
    t.first = lambda : tomorrow()
    u.first = lambda : day_after_tomorrow()
    t.update_menu_relative_dates()
    u.update_menu_relative_dates()
