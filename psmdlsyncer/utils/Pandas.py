"""
Provide a thin wrapper onto Pandas for my particular applications
"""

import pandas as pd
import numpy as np
import unittest
import random

class UnequalColumns(Exception):
    pass

def null():
    """
    Get me a null placeholder value. PS: Are you kidding me?
    """
    return np.nan

class PandasDataFrame:
    """
    A light wrapper around DataFrame, often providing interactions between two different dataframes
    """
    def __init__(self, *args, **kwargs):
        """
        Does not do anything at all
        """
        self.dataframe = pd.DataFrame(*args, **kwargs)

    @staticmethod
    def _we_know_better(source, **kwargs):
        """
        'source' is definitive, but if it doesn't contain keys defined by kwargs,
        then take the 'we know better' approach
        and stick them in there
        """
        for key in kwargs.keys():
            if not key in source:
                source.update( {key:kwargs[key]} )
        return source

    @classmethod
    def from_csv(cls, path, **kwargs):
        """
        Wrapper around read_csv
        Setups up NaN values accordingly, with default delimiters and index columns
        """
        newcls = cls()  # make new 'empty' instance
        newcls.path = path

        kwargs = newcls._we_know_better(kwargs, delimiter='\t', index_col=0)        # Delimiter and index_col should be defined if not already
        newcls.dataframe = pd.read_csv(newcls.path, keep_default_na=False, na_values=[""], **kwargs)
        return newcls

    @classmethod
    def from_dataframe(cls, df):
        newcls = cls()
        newcls.dataframe = df
        return newcls

    @property
    def columns_list(self):
        return list(self.dataframe.columns)

    @property
    def index_values(self):
        return self.dataframe.index.values

    @property
    def unique_index_values(self):
        return set(self.index_values)

    def convert_nas_to_zero(self):
        self.dataframe.fillna(value=0, inplace=True)

    def drop_meaningless(self):
        self.dataframe = self.dataframe.dropna(axis=1, how="all")

    def row_column(self, r, c):
        return self.dataframe.loc[r, c]

    @property
    def routput(self):
        """ random output, useful for informally checking data quickly """
        rand = random.randrange(0, len(self.dataframe.index))
        return self.dataframe[rand:rand+10]

    def derive_new_column(self, from_col, new_col, func):
        """
        Make a new column based on another one
        """
        self.dataframe[new_col] = self.dataframe[from_col].map(func)

    def assign_column(self, column,
                      to=None,
                      from_index=None,
                      from_column=None,
                      by_iterrows=None,
                      by_apply=None):
        """
        Returns the column for assignment

        Does not return anything, because operation is done on a view
        """
        if from_column:
            key = list(from_column.keys())[0]
            func = from_column[key]
            self.dataframe[column] = self.dataframe[key].map(func)
        elif from_index:
            self.dataframe[column] = [from_index(x) for x in self.dataframe.index]
        elif by_iterrows:
            self.dataframe[column] = pd.Series([by_iterrows(index, row) for index, row in self.dataframe.iterrows()], index=self.dataframe.index)
        elif by_apply:
            key = list(by_apply.keys())[0]
            func = by_apply[key]
            self.dataframe[column] = self.dataframe.apply(func)
        else:
            # Can't check for "if to" due to the way pandas handles this assignment,
            #   so make it the default by logic
            # Known issue: If to is a Series, you may end up with nan objects in a column with mostly strings,
            #   which makes future operations a bit of a pain
            #   solve it with subsequent call to PandasDataFrame.set_column_nas after returning
            self.dataframe[column] = to


    def column_matches_string(self, col, match):
        """ returns whole frame that has match string contained within """
        return self.dataframe[self.dataframe[col].str.contains(match)]

    def column_matches_string_subcat(self, col, match, subcat):
        """ returns particular column of frame that has match string contained within """
        return self.dataframe[self.dataframe[col].str.contains(match)][subcat]

    def split_column_text(self, col, sep, index_after_splitting):
        """ returns particular column with its contents split """
        return self.dataframe[col].str.split(sep).str.get(index_after_splitting)

    def slice_column_text(self, col, slice_obj):
        return self.dataframe[col].str.slice(slice_obj)

    def change_index(self, new_index):
        return PandasDataFrame.from_dataframe(self.dataframe.set_index(new_index))

    def set_column_nas(self, column, value=None):
        """ set the column to whatever value, in place operation """
        self.dataframe[column].fillna(value=value, inplace=True)

    def collapse_multiple_values(self, key):
        """ r
        Returns a series of collapsed values in other_key

        TODO: Very slow, figure out how to make it faster
        """
        _list = []
        for item in self.unique_index_values:
            try:
                values = self.dataframe.loc[item, key].values.tolist()
            except AttributeError:
                values = [self.dataframe.loc[item, key]]
            _list.append(",".join(sorted(values)))
        return pd.Series(_list, index=self.unique_index_values)

    #
    # The following methods provide routines for interaction between two dataframes
    #
    def make_matching_matrix(self, other, self_column, other_column, func):
        """
        I call a matching matrix where the cells are some function of the column and rows
        one index, one column
        Takes one column from self and from other, self_column will become the index
        Function gets two arguments, the index and the column value
        """
        index = self.dataframe[self_column].unique()
        columns = set([c for c in other.dataframe[other_column].values if c or not pd.isnull(c)])
        temp_dict = {}
        for c in columns:
            series = [func(i, c) for i in index]
            temp_dict[c] = pd.Series(series, index=[i for i in index])
        return PandasDataFrame(temp_dict)

    def merge_matching_matrix(self, matching_matrix,
                              self_c1, self_c2,
                              new_column,
                              self_c1_callable=None, self_c2_callable=None):
        """
        Use the information from the matching matrix and incorporate it into me
        Callables can be used to mangle the values as needed
        """
        _list = []
        for i in self.dataframe.index:
            c1 = self.row_column(i, self_c1)
            if self_c1_callable:
                c1 = self_c1_callable(c1)
            c2 = self.row_column(i, self_c2)
            if self_c2_callable:
                c2 = self_c2_callable(c2)
            value = matching_matrix.row_column(c1, c2)
            _list.append(value)
        self.dataframe[new_column] = pd.Series(_list, index=range(0, i+1))
            
    def merge_collapsed_multiple_values(self, other, key_to_collapse):
        temp_list = []
        the_index = other.unique_index_values
        for item in the_index:
            try:
                values = self.dataframe.loc[item, key_to_collapse].values
            except AttributeError:
                values = [self.dataframe.loc[item, key_to_collapse]]
            temp_list.append(",".join(sorted(values)))

        new = PandasDataFrame({key_to_collapse:temp_list}, index=the_index)

        self.dataframe = self.dataframe.join(new.dataframe)

    def collapse_foreign_column(self, other,
                                other_key):
        """
        Returns a series of collapsed other_key in other

        Returned series shares index with self, skips any nan
        """
        _list = []
        for _id in self.dataframe.index:
            view = other.dataframe[other.dataframe[other_key]==_id]
            values = view['class'].values
            _list.append(','.join(sorted([v for v in values if v])))
        return pd.Series(_list, index=self.dataframe.index)

    def equal_columns(self, other):
        """ Returns True if columns are exactly the same """
        return self.columns_list == other.columns_list

    @staticmethod
    def is_new(values):
        """ Helper method that returns True if this is a new item, for use with pinpoint_differences result """
        l = list(values)
        return l[2] is None and isinstance(l[3], list)

    @staticmethod
    def is_deleted(values):
        """ Helper method that returns True if this is a deleted item, for use with pinpoint_differences result """
        l = list(values)
        return l[3] is None and isinstance(l[2], list)
        
    def pinpoint_differences(self, other):
        """
        Generates a (new) list of tuples
        that represents the differences between before and after
        (index, column, old_value, new_value)
        New rows are indicated by:
        (index, 'NEW', None, list_of_values)
        Deleted rows are indicated by:
        (index, 'DELETED', list_of_values, None)
        Best practice is to use static methods above to check for new or deleted
        """
        if not self.equal_columns(other):
            raise UnequalColumns("It's assumed that before and after have the same exact columns:\nBefore: {}\n After: {}".format(
                ", ".join(self.columns_list), ", ".join(other.columns_list)
                ))

        # Next two lines drop any columns full of meaningless data,
        # because we don't want to pass on that on to next in line in the chain
        self.drop_meaningless()
        other.drop_meaningless()

        # Next two lines makes any nan a None value, so we can check against itself
        before.convert_nas_to_zero()
        after.convert_nas_to_zero()

        # Determine new items first TODO Figure out a better algorithm for this
        before_indexes = set(before.index_values)
        after_indexes = set(after.index_values)
        for new_one in (after_indexes - before_indexes):
            yield (new_one, "NEW", None, list(after.dataframe.loc[new_one].values))
        
        for index, row in before.dataframe.iterrows():
            for column in range(0, len(row)):
                this_cell = row[column]
                try:
                    that_row = after.dataframe.loc[index]
                except KeyError:
                    # No longer present
                    yield (index, "DELETED", list(before.dataframe.loc[index].values), None)
                    break
                that_cell = that_row[column]
                if this_cell != that_cell:
                    if pd.isnull(this_cell) and pd.isnull(that_cell):
                        # Don't bother yeilding two NaNs, that's meaningless
                        # For some reason NaN's logic makes no sense to me....
                        #TODO include a wrapper for that
                        continue
                    yield (index, before.columns_list[column], this_cell, that_cell)


class TestPandas(unittest.TestCase):

    def test_csv_files(self):
        b = PandasDataFrame.from_csv('before.txt', header=None, names=["homeroom","name","emails","entrydate","nationality","delete"])
        a = PandasDataFrame.from_csv('after.txt', header=None, names=["homeroom","fail","emails","entrydate","nationality","delete"])

        with self.assertRaises(UnequalColumns):
            items = list(b.pinpoint_differences(a))

        b = PandasDataFrame.from_csv('before.txt', header=None, names=["homeroom","name","emails","entrydate","nationality","delete"])
        a = PandasDataFrame.from_csv('after.txt', header=None, names=["homeroom","name","emails","entrydate","nationality","delete"])

        items = list(b.pinpoint_differences(a))

        # Note: I've set it up so that nan is "0" in the data
        intended_result = [(99499, 'NEW', None, ['4L', 'Morris, Ji Yun', 'letsmarry@morris329.com,daddymorris@morris329.com', '08/01/2013', 'Morrisey']),
(99999, 'NEW', None, ['8L', 'Morris, Adam', 'mommymorris@morris329.com,daddymorris@morris329.com', '08/01/2013', 'America']),
(31952, 'homeroom', '12E', '11E'),
(43432, 'name', 'Abraham, Nina Marie', 'Abraham, Nina'),
(40453, 'emails', 'aggarwal_ramkishor@cat.com', 'aggarwal_ramkishor@example.com'),
(40452, 'emails', 'aggarwal_ramkishor@cat.com', 'aggarwal_ramkishor@example.com'),
(43612, 'nationality', 'Korea', 'American'),
(41813, 'homeroom', 0, '4JP'),
(13111, 'DELETED', ['9L', 'Kang, Soo Min', 'iloveyou@hanmail.net,dal0702@hanmail.net', '11/16/2008', 'Korea'], None)]

        self.assertEqual(intended_result, items)
        self.assertTrue(b.is_new(intended_result[0]))
        self.assertTrue(b.is_deleted(intended_result[-1]))

if __name__ == "__main__":

    before = PandasDataFrame.from_csv('before.txt', header=None, names=["homeroom","name","emails","entrydate","nationality","delete"])
    after = PandasDataFrame.from_csv('after.txt', header=None, names=["homeroom","name","emails","entrydate","nationality","delete"])

    for item in before.pinpoint_differences(after):
        print(item)

    schedule = PandasDataFrame.from_csv('schedule.txt', header=None, names=["courses","period", "termid", "teacher","studentname", "studentid"], index_col=5)
    after.merge_collapsed_multiple_values(schedule, 'courses')
    print(after.dataframe[:10])

