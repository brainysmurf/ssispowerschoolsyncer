from ssispowerschoolsyncer.utils import DB


class build_category_tree(DB.DragonNetDBConnection):

    def get_category_tree(self, return_which=None):
        from IPython import embed
        result = self.sql("select * from ssis_categories")
        embed()

              
    
