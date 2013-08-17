from Model import DatabaseObject

teacher_notices_samples = [
    (2036, 1281, 'Judy', 'Chen', '', 'Date to Publish', '1355400000'), (2036, 1281, 'Judy', 'Chen', '', 'School Section', 'All Secondary ##secstunot_all##'), (2036, 1281, 'Judy', 'Chen', '', 'Times to Repeat', None),
    (2039, 38, 'Michael', 'Hawkes', '', 'Times to Repeat', '1'), (2039, 38, 'Michael', 'Hawkes', '', 'School Section', 'All Secondary ##secstunot_all##'), (2039, 38, 'Michael', 'Hawkes', '', 'Full Content', "<p><strong>Gardening Club</strong>: Why does Santa have 3 gardens? So he can ho-ho-ho.</p>\r\n<p>Happy Holidays from Farmer's Son, Wylie, and Hawkes</p>"), (2039, 38, 'Michael', 'Hawkes', '', 'Attached Content', ''), (2039, 38, 'Michael', 'Hawkes', '', 'Date to Publish', '1355486400'),
    (2042, 1040, 'Ingrid', 'Morton', '', 'Date to Publish', '1355400000'), (2042, 1040, 'Ingrid', 'Morton', '', 'School Section', 'High School only##secstunot_hs##'), (2042, 1040, 'Ingrid', 'Morton', '', 'Times to Repeat', None), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>Try this out for size</p>'), (2042, 1040, 'Ingrid', 'Morton', '', 'Full Content', '<p>TOEIC class</p>\r\n<p>If you have signed up for the TOEIC class starting after Christmas please come and see Mrs. Morton in BN111 this morning.</p>'), (2042, 1040, 'Ingrid', 'Morton', '', 'Attached Content', ''), (2043, 1040, 'Ingrid', 'Morton', '', 'Date to Publish', '1355486400'),
    (2043, 1040, 'Ingrid', 'Morton', '', 'School Section', 'High School only##secstunot_hs##'), (2043, 1040, 'Ingrid', 'Morton', '', 'Times to Repeat', None),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2043, 1040, 'Ingrid', 'Morton', '', 'Full Content', ''),
    (2043, 1040, 'Ingrid', 'Morton', '', 'Attached Content', ''),
    (2044, 1040, 'Ingrid', 'Morton', '', 'Date to Publish', '1355486400'), (2044, 1040, 'Ingrid', 'Morton', '', 'School Section', 'All Secondary ##secstunot_all##'), (2044, 1040, 'Ingrid', 'Morton', '', 'Times to Repeat', None), (2044, 1040, 'Ingrid', 'Morton', '', 'Full Content', '<p>English Plus</p>\r\n<p>The classes are starting on Tuesday January 8th. You need to sign up today!</p>'),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2044, 1040, 'Ingrid', 'Morton', '', 'Attached Content', ''),
    (2045, 1281, 'Judy', 'Chen', '', 'Date to Publish', '1355486400'), (2045, 1281, 'Judy', 'Chen', '', 'School Section', 'High School only##secstunot_hs##'), (2045, 1281, 'Judy', 'Chen', '', 'Times to Repeat', None), (2045, 1281, 'Judy', 'Chen', '', 'Full Content', '<p>Hope you all enjoyed your candy canes. Happy Christmas!</p>'), (2045, 1281, 'Judy', 'Chen', '', 'Attached Content', ''),
    (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', ''), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', 'Tuesday (8th Jan)'), (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'All Secondary'), (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>This is another one.</p>'),
    (22049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (22049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', 'Tuesday (8th Jan)'), (22049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>This is one without a subject!.</p>'),
    (222049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (222049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', 'Tuesday (8th Jan)'),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', ''),
    (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', 'Monday (7th Jan)'), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'Whole School'), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>Tomorrow, this is going to <strong>rock</strong>!</p>'),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', ''), (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'Secondary'),
    (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', '<p>No attachments</p>'),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>Middle school is the best, right?</p>'),
    (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', ''),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', ''),
    (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', ''), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'Secondary'),
    (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', ''), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'Whole School'), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>test test</p>'), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', '')]

teacher_notices_tag_samples = ["Whole School", "Secondary", "Elementary"]


student_notices_samples = [
    (2036, 1281, 'Judy', 'Chen', '', 'Date to Publish', '1355400000'), (2036, 1281, 'Judy', 'Chen', '', 'School Section', 'All Secondary ##secstunot_all##'), (2036, 1281, 'Judy', 'Chen', '', 'Times to Repeat', None),
    (2039, 38, 'Michael', 'Hawkes', '', 'Times to Repeat', '1'), (2039, 38, 'Michael', 'Hawkes', '', 'School Section', 'All Secondary ##secstunot_all##'), (2039, 38, 'Michael', 'Hawkes', '', 'Full Content', "<p><strong>Gardening Club</strong>: Why does Santa have 3 gardens? So he can ho-ho-ho.</p>\r\n<p>Happy Holidays from Farmer's Son, Wylie, and Hawkes</p>"), (2039, 38, 'Michael', 'Hawkes', '', 'Attached Content', ''), (2039, 38, 'Michael', 'Hawkes', '', 'Date to Publish', '1355486400'),
    (2042, 1040, 'Ingrid', 'Morton', '', 'Date to Publish', '1355400000'), (2042, 1040, 'Ingrid', 'Morton', '', 'School Section', 'High School only##secstunot_hs##'), (2042, 1040, 'Ingrid', 'Morton', '', 'Times to Repeat', None), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>Try this out for size</p>'), (2042, 1040, 'Ingrid', 'Morton', '', 'Full Content', '<p>TOEIC class</p>\r\n<p>If you have signed up for the TOEIC class starting after Christmas please come and see Mrs. Morton in BN111 this morning.</p>'), (2042, 1040, 'Ingrid', 'Morton', '', 'Attached Content', ''), (2043, 1040, 'Ingrid', 'Morton', '', 'Date to Publish', '1355486400'),
    (2043, 1040, 'Ingrid', 'Morton', '', 'School Section', 'High School only##secstunot_hs##'), (2043, 1040, 'Ingrid', 'Morton', '', 'Times to Repeat', None),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2043, 1040, 'Ingrid', 'Morton', '', 'Full Content', ''),
    (2043, 1040, 'Ingrid', 'Morton', '', 'Attached Content', ''),
    (2044, 1040, 'Ingrid', 'Morton', '', 'Date to Publish', '1355486400'), (2044, 1040, 'Ingrid', 'Morton', '', 'School Section', 'All Secondary ##secstunot_all##'), (2044, 1040, 'Ingrid', 'Morton', '', 'Times to Repeat', None), (2044, 1040, 'Ingrid', 'Morton', '', 'Full Content', '<p>English Plus</p>\r\n<p>The classes are starting on Tuesday January 8th. You need to sign up today!</p>'),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2044, 1040, 'Ingrid', 'Morton', '', 'Attached Content', ''),
    (2045, 1281, 'Judy', 'Chen', '', 'Date to Publish', '1355486400'), (2045, 1281, 'Judy', 'Chen', '', 'School Section', 'High School only##secstunot_hs##'), (2045, 1281, 'Judy', 'Chen', '', 'Times to Repeat', None), (2045, 1281, 'Judy', 'Chen', '', 'Full Content', '<p>Hope you all enjoyed your candy canes. Happy Christmas!</p>'), (2045, 1281, 'Judy', 'Chen', '', 'Attached Content', ''),
    (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', ''), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', 'Tuesday (8th Jan)'), (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'All Secondary'), (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>This is another one.</p>'), (22049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (22049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', 'Tuesday (8th Jan)'), (22049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>This is one without a subject!.</p>'),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Date to Publish', None), (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Times to Repeat', None),
    (2049, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', ''),
    (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', 'Monday (7th Jan)'), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'All Secondary'), (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>Tomorrow, this is going to <strong>rock</strong>!</p>'),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', ''), (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'Middle School only'),
    (2048, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', '<p>No attachments</p>'),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>Middle school is the best, right?</p>'),
    (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', ''),
    (2051, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', ''),
    (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Start Date', 'Tomorrow (4th Jan)'), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', ''), (2050, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'High School only'),
    (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'End Date', ''), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'School Section', 'All Secondary'), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Full Content', '<p>test test</p>'), (2046, 2, 'DragonNet', 'Admin', 'Mr Morris', 'Attached Content', '')]

student_notices_tag_samples = ["All Secondary", "High School only", "Middle School only"]

class StudentNoticeSamples:
    """
    Depreciated
    """
    def __init__(self):
        super().__init__()
        self.add( DatabaseObject(user_first_name='Adam', user_last_name="Morris",
                                 user_id=100,
                                 full_content='hello',
                                 start_date='Blah (3rd Jan)',
                                 end_date='Blah (5th Jan)',
                                 school_section='All Secondary',
                                 attachment=''
            ))
        self.add( DatabaseObject(user_first_name='Yuri', user_last_name='Kim',
                                 user_id = 1000,
                                 full_content='Hello my man',
                                 start_date='Blah dfd (4th Jan)',
                                 end_date='',
                                 school_section='Middle School',
                                 attachment=''
            ))
        self.add( DatabaseObject(user_first_name='Mr', user_last_name='Sir',
                                 user_id = 32,
                                 full_content='Wow',
                                 start_date='Sometime (2nd Jan)',
                                 end_date='Friday (4th Jan)',
                                 school_section='High School',
                                 attachment=''
            ))
        self.add( DatabaseObject(user_first_name='Someone', user_last_name='else',
                                 user_id = 392,
                                 full_content='I should be higher than Mr Sir',
                                 start_date='Sometime (4th Jan)',
                                 end_date='',
                                 school_section='High School',
                                 attachment=''
            ))
        self.add( DatabaseObject(user_first_name='Someone', user_last_name='else',
                                 user_id = 32,
                                 full_content='I should be lower than Mr Sir',
                                 start_date='Sometime (2nd Jan)',
                                 end_date='Friday (4th Jan)',
                                 school_section='High School',
                                 attachment=''
            ))
        self.add( DatabaseObject(user_first_name='Mr', user_last_name='Sir',
                                 user_id = 32,
                                 full_content='This should be on top!',
                                 start_date='Sometime (4th Jan)',
                                 end_date='Friday (4th Jan)',
                                 school_section='All Secondary',
                                 attachment=''
            ))
        self.add( DatabaseObject(user_first_name='Anonymous', user_last_name="Nobody",
                                 user_id = 1442,
                                 full_content='Heaven help me!',
                                 start_date='Sometime (2nd Jan)',
                                 end_date='Friday (4th Jan)',
                                 school_section='All Secondary',
                                 attachment=''
            ))
