from utils.DB import UpdateField
import datetime
from utils.Dates import date_to_database_timestamp, today, custom_strftime

class RelativeDateFieldUpdater(UpdateField):

    def update_menu_relative_dates(self,
                                   forward_days=7,
                                   skip=['Saturday', 'Sunday']):
        d = today()
        forward_delta = datetime.timedelta(days=forward_days)
        menu = []
        for day in range(1, forward_delta.days+1):  # 1..7 by default
            print(day)
            iter_date = d + datetime.timedelta(days=day)
            day_of_week = iter_date.strftime('%A')
            if not day_of_week in skip:
                if day == 1:
                    day_of_week = "Tomorrow"
                if day in range(7,14):
                    if day == 7:
                        menu.append('------')
                    day_of_week = "Next " + day_of_week
                elif day in range(14,21):
                    if day == 14:
                        menu.append('------')
                    day_of_week = "Next next " + day_of_week

                menu.append( "{} ({})".format(day_of_week, self.format_date(iter_date)) )
                print(menu)

        self.update_menu(menu)


    def format_date(self, d):
        return custom_strftime( "{S} %b", d )
    

if __name__ == "__main__":

    t = RelativeDateFieldUpdater('Testing testing', 'Changeme')

    t.update_menu_relative_dates(forward_delta=datetime.timedelta(days=20))
