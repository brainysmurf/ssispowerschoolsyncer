from psmdlsyncer.Teacher import Teacher
from utils.Pandas import PandasDataFrame

here = """ xuehong@ssis-suzhou.net
 peggykoh@ssis-suzhou.net
 shareegrant@ssis-suzhou.net
 wilmakersten@ssis-suzhou.net
 gracegao@ssis-suzhou.net
 parkseoyoung@ssis-suzhou.net
 michellemi@ssis-suzhou.net
 catherinewhiter@ssis-suzhou.net
 gregstewart@ssis-suzhou.net
 liyan@ssis-suzhou.net
 karenturner@ssis-suzhou.net
 yanlili@cn.ibm.com
 guoyueru@ssis-suzhou.net
 dorishu@ssis-suzhou.net
 keonseungyang@ssis-suzhou.net
 garypost@ssis-suzhou.net
 qinfang@ssis-suzhou.net
 henrywong@ssis-suzhou.net
 shunkagaya@ssis-suzhou.net
 richardkent@ssis-suzhou.net
 zhengyijuan@ssis-suzhou.net
 susanshuford@ssis-suzhou.net
 carolinhofmann@ssis-suzhou.net
 sunchunyan@ssis-suzhou.net
 libbyince@ssis-suzhou.net
 dexterphillips@ssis-suzhou.net
 douglasglenn@ssis-suzhou.net
 leanneharvey@ssis-suzhou.net
 tapritter@yahoo.com
 wendychoo@ssis-suzhou.net
 hyuksangson@ssis-suzhou.net
 sakanyan@gmail.com
 zhoujinhua@ssis-suzhou.net
 nicholaslittle@ssis-suzhou.net
 juileshen@ssis-suzhou.net
 raysull20@bigpond.com
 shireenblakeway@ssis-suzhou.net
 bishakha.raha@gmail.com
 dottifrisinger@ssis-suzhou.net
 kesaianaisara@ssis-suzhou.net
 liuyunlu@ssis-suzhou.net
 rebeccaruan@ssis-suzhou.net
 paulskadsen@ssis-suzhou.net
 susanfullerton@ssis-suzhou.net
 noone@ssis-suzhou.net
 maggiezhai@ssis-suzhou.net
 ya pingkong@ssis-suzhou.net
 tangying@ssis-suzhou.net
 meng yuanli@ssis-suzhou.net
 graceqin@ssis-suzhou.net
 angelsu@ssis-suzhou.net
 chun yansun@ssis-suzhou.net
 yu fengwang@ssis-suzhou.net
 hongxue@ssis-suzhou.net
 li yeyan@ssis-suzhou.net
 susanyou@ssis-suzhou.net
 amywu@ssis-suzhou.net
 lili@ssis-suzhou.net
 pettyzhang@ssis-suzhou.net
 parkseoyoung@ssis-suzhou.net
 virginia@ssis-suzhou.net
 craigfullerton@ssis-suzhou.net
 yuanxulan@ssis-suzhou.net
 liangshuang@ssis-suzhou.net
 brendalyons@ssis-suzhou.net
 luhuifen@ssis-suzhou.net
 limengyuan@ssis-suzhou.net
 bevanjames@example.com
 yangpg21@ssis-suzhou.net
 testing@example.com
 ruthywang@ssis-suzhou.net
 noone@nowhere.org
 wangyufeng@ssis-suzhou.net
 zhouting@ssis-suzhou.net
 matthewmarshall@ssis-suzhou.net
 heidimesser@ssis-suzhou.net
 susieliu@ssis-suzhou.net
 test@example.org
 andrewwarren@ssis-suzhou.net
 stevenharvey@ssis-suzhou.net
 DJohnson@biss.com.cn
 ninazhu@ssis-suzhou.net
 lisaliu@ssis-suzhou.net
 mavisli@ssis-suzhou.net
 ccchen@ssis-suzhou.net
 carolinema@ssis-suzhou.net
 ashleyyao@ssis-suzhou.net
 tracyzhang@ssis-suzhou.net
 mypcoordinator@student.ssis-suzhou.net
 judyxu@ssis-suzhou.net
 tammytang@ssis-suzhou.net
 caroldu@ssis-suzhou.net
 gracetian@ssis-suzhou.net
 dursleychiu@ssis-suzhou.net
 wangwei@ssis-suzhou.net
 donglijia@ssis-suzhou.net
 conniepedraza@ssis-suzhou.net
 wanglimin@ssis-suzhou.net
 zhangmingde@ssis-suzhou.net
 sherryxue@ssis-suzhou.net
 mojianming@ssis-suzhou.net
 dannyzhang@ssis-suzhou.net
 cynthiashen@ssis-suzhou.net
 rebeccawang@ssis-suzhou.net
 leanneliang@ssis-suzhou.net
 jenniferlively@ssis-suzhou.net
 audreyji@ssis-suzhou.net
 gohtienjin@ssis-suzhou.net
 angelsun@ssis-suzhou.net
 venusjin@ssis-suzhou.net
 davidng@ssis-suzhou.net
 liuwenzhu@ssis-suzhou.net
 kimjin@ssis-suzhou.net
 lilyfang@ssis-suzhou.net
 paulinikoroi@ssis-suzhou.net
 youxiaoyan@ssis-suzhou.net
 cindyye@ssis-suzhou.net
 yanghuihui@ssis-suzhou.net
 meganlin@ssis-suzhou.net
 cherrycheng@ssis-suzhou.net
 warrenmessy@ssis-suzhou.net
 valderdagmar@ssis-suzhou.net
 hollywilliams@ssis-suzhou.net
 michellechang@ssis-suzhou.net
 sarahyu@ssis-suzhou.net
 philomenachan@ssis-suzhou.net
 annefowles@ssis-suzhou.net
 giselafrische@ssis-suzhou.net
 selainawai@ssis-suzhou.net
 cathyhuang@ssis-suzhou.net
 yanliye@ssis-suzhou.net
 yuanxulan@ssis-suzhou.net
 bonniexu@ssis-suzhou.net
 niamhprice@ssis-suzhou.net
 renrynne@ssis-suzhou.net
 kimgilbertson@ssis-suzhou.net
 lindseymessing@ssis-suzhou.net
 christinama@ssis-suzhou.net
 cliffpackman@ssis-suzhou.net
 wangyufeng@ssis-suzhou.net
 tracylu@ssis-suzhou.net
 annahuang@ssis-suzhou.net
 yeonjukim19@student.ssis-suzhou.net
 anitawu@ssis-suzhou.net
 anthonyiacobucci@ssis-suzhou.net
 linaliu@ssis-suzhou.net
 richardlamontebird@ssis-suzhou.net
 christinateu@ssis-suzhou.net
 yuzijing@ssis-suzhou.net
 idasabinelindved17@student.ssis-suzhou.net
 veronicazhou@ssis-suzhou.net
 marktreichel@ssis-suzhou.net
 dominicthomas@ssis-suzhou.net
 nanparker@ssis-suzhou.net
 idontknow@anyone.com
 miaolingling@ssis-suzhou.net
 ivyhou@ssis-suzhou.net
 mohamadrafiandiansya18@student.ssis-suzhou.net
 barbaraschindler@ssis-suzhou.net
 cherryzhao@ssis-suzhou.net
 amandadeng@ssis-suzhou.net
 gabrielekullas@ssis-suzhou.net
 iainfitzgerald@ssis-suzhou.net
 jiwoncheong15@student.ssis-suzhou.net
 bobbiepenrose@ssis-suzhou.net
 christamplin.ntis@yahoo.com
 sashaauyang@ssis-suzhou.net
 stacymurray@ssis-suzhou.net
 andreaseelbach@ssis-suzhou.net
 peterfowles@ssis-suzhou.net
 yingtang@ssis-suzhou.net
 jixiaoli@ssis-suzhou.net
 tinagibson@ssis-suzhou.net
 elisahu@ssis-suzhou.net
 leepreston@ssis-suzhou.net
 jasonhe@ssis-suzhou.net
 yurikim@ssis-suzhou.net
 scottturner@ssis-suzhou.net
 ambertang@ssis-suzhou.net
 aparent@student.ssis-suzhou.net
 kinnerishah@ssis-suzhou.net
 charlespollard@ssis-suzhou.net
 thaimmalariosa@ssis-suzhou.net
 michellewu@ssis-suzhou.net
 hyuksangson@ssis-suzhou.net
 yuanxulan@ssis-suzhou.net
 janezeng@ssis-suzhou.net
 suescott@ssis-suzhou.net
 xuhelen@ssis-suzhou.net
 vivianhan@ssis-suzhou.net
 thom.w.jones@gmail.com
 michaelasimpson@ssis-suzhou.net
 jiechen@ssis-suzhou.net
 rebecca louiseclentworth@ssis-suzhou.net
 crystalhuang@ssis-suzhou.net
 susancheng@ssis-suzhou.net
 shirleynegrette@ssis-suzhou.net
 cathyhuang@ssis-suzhou.net
 andreaphillips@ssis-suzhou.net
 laraskadsen@ssis-suzhou.net
 nancymeng@ssis-suzhou.net
 deidratineo@ssis-suzhou.net
 noelsouthall@ssis-suzhou.net
 jungchengwu15@student.ssis-suzhou.net
 meilynfreeman.ncis@gmail.com
 dianagabrielaballinc19@student.ssis-suzhou.net
 neilmarshallinns@ssis-suzhou.net
 donitabell@ssis-suzhou.net
 davidshepherd.ncis@gmail.com
 joannelee@ssis-suzhou.net
 chiang_marian@yahoo.com
 jfox@samsung.com
 yintina2002@hotmail.com
 lorrainebrockbank@ssis-suzhou.net
 ronniefrisinger@ssis-suzhou.net
 mitchellhyde@ssis-suzhou.net
 kimjacobson@ssis-suzhou.net
 fionaxu@ssis-suzhou.net
 barbarashu@ssis-suzhou.net
 root@localhost
 grahammorton@ssis-suzhou.net
 cheowerlim@ssis-suzhou.net
 eileenhurley@ssis-suzhou.net
 sallywatters@ssis-suzhou.net
 julieshen@ssis-suzhou.net
 erinnicolls@ssis-suzhou.net
 tatjanasabo@ssis-suzhou.net
 melodiegreene@ssis-suzhou.net
 zhengyawang@ssis-suzhou.net
 cassandrahoover@ssis-suzhou.net
 julianmandersjones@ssis-suzhou.net
 benjaminwylie@ssis-suzhou.net
 katalynhu@ssis-suzhou.net
 leeannesmith@ssis-suzhou.net
 andrewsierman@ssis-suzhou.net
 yukixu@ssis-suzhou.net
 donpreston@ssis-suzhou.net
 lindazhu@ssis-suzhou.net
 deanwatters@ssis-suzhou.net
 geoffreyderry@ssis-suzhou.net
 krisdaly@ssis-suzhou.net
 davidrynne@ssis-suzhou.net
 lauralynnstefureak@ssis-suzhou.net
 susanferguson@ssis-suzhou.net
 ingridmorton@ssis-suzhou.net
 joannerodriguez@ssis-suzhou.net
 liamoshea@ssis-suzhou.net
 chrisfowler@ssis-suzhou.net
 lukexi@ssis-suzhou.net
 kateholmes@ssis-suzhou.net
 florayu@ssis-suzhou.net
 brettnugent@ssis-suzhou.net
 richardjackson.ntis@yahoo.com
 iainfitzgerald@ssis-suzhou.net
 Teresahou@ssis-suzhou.net
 michaelhawkes@ssis-suzhou.net
 johnpryke@ssis-suzhou.net
 jaybrownrigg@ssis-suzhou.net
 ianmfowler@ssis-suzhou.net
 darkosabo@ssis-suzhou.net
 charlespollard@ssis-suzhou.net
 lilyjin@ssis-suzhou.net
 peterguyan@ssis-suzhou.net
 warrenmassey@ssis-suzhou.net
 gracema@ssis-suzhou.net
 brentclark@ssis-suzhou.net
 suhaiyan@ssis-suzhou.net
 zoulinhua@ssis-suzhou.net
 timbell@ssis-suzhou.net
 kungjueihsu14@student.ssis-suzhou.net
 annhsu16@student.ssis-suzhou.net
 reneerehfeldt@ssis-suzhou.net
 siobhanwestbrook@ssis-suzhou.net
 peterlundin@ssis-suzhou.net
 wilhelmvalderrama@ssis-suzhou.net
 KimHyunAe@ssis-suzhou.net"""

from psmdlsyncer.settings import config
import numpy as np

full_path = lambda _file: config['DIRECTORIES'].get('path_to_powerschool_dump') + '/' + _file
staff = PandasDataFrame.from_csv(full_path('ssis_dist_staffinfo_v3.0'),
                                 header=None,
                                 names=["powerschoolID",
                                        "first_name", "email", "middle_name", "last_name",
                                        "preferred_name", "title", "staff_status", "status", "delete"],
                                 index_col=False,
                                 dtype={'powerschoolID':np.object})

staff.set_column_nas('email', 'none@example.com')

staff.change_index('email')

from collections import defaultdict
result = defaultdict(list)

for teacher in here.split('\n'):
    teacher_email = teacher.strip()
    try: 
        idnumber = staff.dataframe.loc[teacher_email, 'powerschoolID']
    except KeyError:
        continue
    if isinstance(idnumber, str):
        result[teacher_email] = idnumber
    else:
        for value in idnumber.values:
            result[teacher_email] = value

dnet = ModifyDNet

print('username,idnumber')
for item in result:
    this = result[item]
    if 'x' in this:
        continue
    print(item[:item.index('@')].lower() + ',' + this)
