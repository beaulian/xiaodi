# xiaodi
重庆大学国创创业组优秀项目-笑递, 部分源代码仅供学习参考

## 版本
这次更新是我结合了工作过程中所学，把代码重构了一遍，使得项目更加pythonic，
因为工程有点大，所以只重构了一部分，但是这部分代码已经充分代表了重构之后的风格

## 更新说明
* 换了数据库mysql，以前用的是mongodb，简单，但是后面发现跨表查询确实是个问题，而且motor不支持ORM
* 去掉了celery，因为感觉就两个定时任务，完全没必要用celery，schedule守护线程可能是个更好更轻量的选择
* 对项目目录做了重大调整，增加了handlers和common，api目录，对程序的职责做了更明确的划分
* IO全部异步化，以前都是只有mongodb是异步客户端，而redis和oss都是同步请求，现在感觉以前很天真
* 对url.py做了重大改变，以前是只有多了一个api，就往url.py里写，弄得后面上百个api很难找到某个
* 功能高度封装，降低代码耦合度，尤其是对异步任务的封装，见xiaodi/common/tasks.py
* 充分利用了python的特性，如对象协议、元类、混入类mixin、列表推导式、生成器
* 对参数的接收采用了flask_restful的reqparse思想，使得代码精简了很多
* 引入了日志
* 引入了sse

## 亮点
* 使用元类避免了重复使用coroutine和asynchronous装饰器
* 使用元类把创建mysql的model的代码精简了很多
* 巧妙地用run_on_executor把mysql的ORM查询异步化
* 对tornado抛出异常的处理
* 对异步任务的封装，对delivery的封装，以及对redis的封装

## 技术架构
tornado + mysql + redis + supervisor

## 总结
python2.7版本的tornado着实有点难用，很容易造成"yield地狱"，
而且python2.7对异步的支持远不及python3，所以推荐不使用tornado，
换成flask_restful这种同步框架或者对异步支持较好的sanic框架
