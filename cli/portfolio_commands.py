portfolio_commands = """wp --path=/var/www/portfolios blog create --slug='{0.slug}' --title='{0.firstname} {0.homeroom}' --email='{0.teacher_email}'
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option update blogdescription "My Learning"
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} user set-role {0.student_email} author
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} user update {0.student_email} --first_name='{0.firstname}' --last_name='{0.lastname}' --display_name='{0.firstname}'
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post create --user={0.teacher_email} --post_title='Portfolio blog post instructions' --post_status=publish first_post.txt 
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post delete 2 --force
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post delete 1 --force
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} theme activate twentytwelve
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} theme mod set header_textcolor 515151
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} theme mod set header_image http://portfolios.ssis-suzhou.net/template/wp-content/uploads/sites/3/2016/08/cropped-image6149.png
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} theme mod set header_image_data '{{"attachment_id":12,"url":"http:\/\/portfolios.ssis-suzhou.net\/template\/wp-content\/uploads\/sites\/3\/2016\/08\/cropped-image6149.png","thumbnail_url":"http:\/\/portfolios.ssis-suzhou.net\/template\/wp-content\/uploads\/sites\/3\/2016\/08\/cropped-image6149.png", "height":215,"width":825}}'
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} theme mod set background_color ffffff
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} term delete category 1
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} term create category Homeroom
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} term create category Art
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} term create category Music
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} term create category PE
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post term remove 3 category Uncategorized
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post term add 3 category Homeroom
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post term add 3 category Art
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post term add 3 category Music
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} post term add 3 category PE
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} widget deactivate search-2
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} widget move categories-2 --position=1
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} widget deactivate meta-2
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} widget deactivate archives-2
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} widget add tag_cloud sidebar-1 2 --title='Post tags' --taxonomy='post_tag'
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} plugin activate subscribe2
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} widget add s2_form_widget sidebar-1 5 --title='Subscribe to my blog!' --div=search --size=20
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set akismet_strictness 1
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set comment_moderation 1
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set comment_whitelist 0
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set moderation_notify 0
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set comments_notify 0
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set default_category 2
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set category_base category
wp --path=/var/www/portfolios --url=http://portfolios.ssis-suzhou.net/{0.slug} option set tag_base '/tag'
"""