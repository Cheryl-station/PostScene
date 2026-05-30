### PostScene ——————  一个强大的工具，基于 Postman 接口自动化场景设计
***

**使用Xmind或者Yaml 设计 postman 自动化场景**

#### 引言 
postman是一个比较轻量级的接口测试工具，在单个接口的测试表现优秀。在批量测试接口方面则提供了Runner Collections这种方式，虽然可以用来做流程测试，但在管理上不是很方便。例如：在postman建立一个collection作为接口文档，然后再建立另外一个collection作为场景测试，接着从接口文档的collection中挑选接口，并复制到场景测试的collection中，而且可能在不同的场景都共用同一个接口，这种方式是听不错的，只是当接口的版本升级之后，需要在场景中找出所有对应的接口进行修改，这样在管理上会比较麻烦。

#### 概念
这个工具根据Xmind或Yaml所写的场景流程，从接口文档的collection中生成一个场景测试的collection，这样即使版本升级，只需要重新生成一次即可，相当方便，同时也提供了一些方便的设参方式和断言。

![输入图片说明](https://images.gitee.com/uploads/images/2020/0517/171141_3a0a3674_5050702.png "屏幕截图.png")


### 能做什么
1.  **管理方便** 。只需要管理接口文档的collection和Xmind/Yaml脚本。
2.  **场景流程更直观** 。在Xmind/Yaml上可以直观的看到整个流程，在细节上也可以看到每个接口的参数定义，以及断言内容。
3.  **代码编写简化** 。在测试行业中，普遍都是代码能力比较差，虽然测试不需要特别强的代码编写能力，postman在Tests界面中也提供了一些快捷片段，但是还是不足够简化，而且也不全面，比如对请求的参数进行签名。
4.  **提供一些快捷的函数**。postman提供的内置函数还是比较少的，比如随机生成32的UUID，md5,获取当前时间，获取前7天，前30天的日期，参数签名等等，这些都需要自己手动写代码。
5.  **无依赖性**。本工具只是一个脚本转换成Postman的脚本工具，即使以后不用，完全可以自己维护Postman的脚本。
6.  **本脚本不支持性能测试**。由于Postman不支持性能测试，star数量达到1000，将开放基于Jmeter的性能测试脚本转换工具的源码。
.......

### 先来看看效果图
![输入图片说明](https://images.gitee.com/uploads/images/2020/0420/111447_678b9ab8_5050702.png "屏幕截图.png")



### 如何上手

使用 `pip` 安装PostScene 

```
pip install -U PostScene
```
#### 命令行调用

```bash
postscene ./src/yaml/demo.yaml ./src/api_document/demo.postman_collection.json -o ./src/scene
```

也可以直接使用模块方式运行：

```bash
python -m post_scene ./src/yaml/demo.yaml ./src/api_document/demo.postman_collection.json -o ./src/scene
```

如果还没有场景脚本，可以先根据 Postman Collection 生成 YAML 模板：

```bash
postscene-template ./src/api_document/demo.postman_collection.json -o ./src/yaml/scene-template.yaml
```

生成后在模板上调整场景顺序、请求参数、断言和变量提取，再执行 `postscene` 转换。

#### 作为 Codex Skill 安装

本仓库包含可发布的 Codex skill 包，路径为 `skills/post-scene`。可以从 GitHub 仓库路径安装：

```bash
python scripts/install-skill-from-github.py \
  --repo Cheryl-station/PostScene \
  --path skills/post-scene
```

安装后重启 Codex，即可通过 `$post-scene` 调用该技能。

#### Python 调用

```python
from post_scene.post_scene import PostScene

yaml_path = './yaml/demo.yaml'  # 脚本文件的路径
xmind_path = './xmind/demo.xmind'  # 脚本文件的路径
api_document_path = './api_document/demo.postman_collection.json'  # postman json data 文件的路径
api_document_url = 'https://www.getpostman.com/collections/马赛克马赛克马赛克马赛克'  # 也可以使用Postman的share link


# 推荐使用 convert。covert 是历史拼写，仍保留兼容。
# PostScene.convert(yaml_path, api_document_path, scene_dirs='./scene')
# PostScene.convert(xmind_path, api_document_path, scene_dirs='./scene')
PostScene.convert(yaml_path, api_document_path, scene_dirs='./scene')
```


#### 例子
***
* 新建一个文件，名字叫什么不重要，但为了迭代开发的考虑，最好还是加上版本号。
> demo-scenev1.0.yaml
* 脚本编写

```yaml
name: demo-scenev1.0                                         #collection 的名字
scene:
   name: 下单流程                                             #collection文件夹的名字
   scene:
     登陆:                                                   #API接口名称
       pre:                                                 #接口请求前脚本
         sign:                                              #参数签名
           secret: 1850e165f1fc19420f2ba3d3a1a5ffe4
         set:                                               #设置变量值
           userName: user
           password: user123
           time: $$times                                    #获取现在的时间
           onceToken: $$uuid32                              #生成32位的uuid
       tests:                                               #请求后脚本
         assert:                                            #请求后断言
           express:
             content: $json.data.code === '1'               #断言返回的json数据的code 是否等于1
             set:                                           #断言成功保存token和uid数据
               token: $json.data.token
               uid: $json.data.uid
     通过餐厅名字搜索餐厅:
       pre:
         sign:
           secret: 1850e165f1fc19420f2ba3d3a1a5ffe4
         set:
           canteenName: 喜茶
       tests:
         assert:
           expect:                                         #断言返回的canteenList的每一个对象的名称都包含喜茶
             content: $json.data.canteenList
             item: $it.name                                 
             include: 喜茶
             set:
               canteenId: $$find(json.data.canteenList, it.canteenName == '喜茶GO').canteenId  #获取喜茶Go的CanteenId
     通过商品名字搜索商品:
       pre:
         sign:
           secret: 1850e165f1fc19420f2ba3d3a1a5ffe4
         ref: canteenId
         set:
           goodsName: 奥利奥千层
       tests:
         assert:
           expect:
             content: $json.data.goodsList
             item: $item.name
             include: 奥利奥千层
             set:
               goodsId: $$find(json.data.goodsList, it.goodsName == '奥利奥千层').goodsId
     加入购物车:
       pre:
         sign:
           secret: 1850e165f1fc19420f2ba3d3a1a5ffe4
         ref: goodsId
         set:
           count: 1
       tests:
         assert:
           express:
             content: $json.code === '1'
             set:
               pocketId: $json.data.pocketId
.......

```
* 脚本转换
1. 使用git或者浏览器下载本项目，再用pycharm打开。

2. 在Postman中选择你已经准备好的api文档collection 然后导出。这里导出为 demo.postman_collection.json

<img src="https://images.gitee.com/uploads/images/2020/0419/205433_ab0d0f7e_5050702.png" width = 50%/>

3. 把导出的文档放入项目中的api_document 脚本放入xmind或yaml

<img src="https://images.gitee.com/uploads/images/2020/0420/111101_b755e5d4_5050702.png" width = 50%/>

4. 使用命令行转换脚本：

```bash
postscene ./src/yaml/demo.yaml ./src/api_document/demo.postman_collection.json -o ./src/scene
```

也可以打开 `src/Index.py`，把脚本路径和接口文档路径改成你的，然后运行。

![输入图片说明](https://images.gitee.com/uploads/images/2020/0420/110449_d637d0a7_5050702.png "屏幕截图.png")

5. 生成的场景文件放在src/scene文件夹中，使用postman的import 把他导入

<img src="https://images.gitee.com/uploads/images/2020/0419/205611_f9bedc10_5050702.png" width = 50%/>

6. 最后可以开始Run collection啦

<img src="https://images.gitee.com/uploads/images/2020/0419/205618_8b34ba14_5050702.png" width = 50%/>

#### 教程
***
>如果你对Postman的Script很熟悉，那以下的内容对你来说绝对是无障碍的。不熟悉也没关系，只要照猫画虎，也能完成脚本的编写，设计这个初衷就是为了降低门槛。教程的讲解都是用yaml来讲解，因为用xmind讲解不是很方便，要截很多图。xmind的话，直接看demo.xmind就好啦。

**学前须知** : 每一个测试用例都由两部分组成 **pre(请求前)** 和 **tests(请求后)** ，pre可以没有，但tests断言一定要有，不然没有意义。每一个测试用例的名称必须和文档中的collection的接口名称一致。这是规范。

### 脚本语法标签

 + **请求前: pre**  
    - [参数设置变量: set](https://gitee.com/tangyajun/PostScene/wikis/%E5%8F%82%E6%95%B0%E8%AE%BE%E7%BD%AE%E5%8F%98%E9%87%8F:%20set?sort_id=2158435)   
    - [参数引用变量: ref](https://gitee.com/tangyajun/PostScene/wikis/%E5%8F%82%E6%95%B0%E5%BC%95%E7%94%A8%E5%8F%98%E9%87%8F:%20ref?sort_id=2158433)      
    - [参数签名: sign](https://gitee.com/tangyajun/PostScene/wikis/%E5%8F%82%E6%95%B0%E7%AD%BE%E5%90%8D:%20sign?sort_id=2158434)      
 + **请求后: tests**  
    - 断言: assert  
        - [状态: status](https://gitee.com/tangyajun/PostScene/wikis/%E7%8A%B6%E6%80%81:%20status?sort_id=2158444)    
        - [是: tobe](https://gitee.com/tangyajun/PostScene/wikis/%E6%98%AF:%20tobe?sort_id=2158441)    
        - [不是: notTobe](https://gitee.com/tangyajun/PostScene/wikis/%E4%B8%8D%E6%98%AF:%20notTobe?sort_id=2158440)    
        - [有: tohave](https://gitee.com/tangyajun/PostScene/wikis/%E6%9C%89:%20tohave?sort_id=2158442)    
        - [没有: notTohave](https://gitee.com/tangyajun/PostScene/wikis/%E6%B2%A1%E6%9C%89:%20notTohave?sort_id=2158443)    
        - [表达式: express](https://gitee.com/tangyajun/PostScene/wikis/%E8%A1%A8%E8%BE%BE%E5%BC%8F:%20express?sort_id=2158445)    
        - [预期: except](https://gitee.com/tangyajun/PostScene/wikis/%E9%A2%84%E6%9C%9F:%20expect?sort_id=2158446)    
    - [条件跳转: next](https://gitee.com/tangyajun/PostScene/wikis/%E6%9D%A1%E4%BB%B6%E8%B7%B3%E8%BD%AC:%20next?sort_id=2158447)  
    - [保存变量: set](https://gitee.com/tangyajun/PostScene/wikis/%E4%BF%9D%E5%AD%98%E5%8F%98%E9%87%8F:%20set?sort_id=2158437)
 + **授权: auth**
    - [bearer](https://gitee.com/tangyajun/PostScene/wikis/bearer?sort_id=2158426)
    - [apikey](https://gitee.com/tangyajun/PostScene/wikis/apikey?sort_id=2158423)
    - [basic](https://gitee.com/tangyajun/PostScene/wikis/basic?sort_id=2158425)
    - [digest](https://gitee.com/tangyajun/PostScene/wikis/digest?sort_id=2158427)
    - [oauth1](https://gitee.com/tangyajun/PostScene/wikis/oauth1?sort_id=2158430)
    - [oauth2](https://gitee.com/tangyajun/PostScene/wikis/oauth2?sort_id=2158431)
    - [hawk](https://gitee.com/tangyajun/PostScene/wikis/hawk?sort_id=2158429)
    - [awsv4](https://gitee.com/tangyajun/PostScene/wikis/awsv4?sort_id=2158424)
    - [edgegrid](https://gitee.com/tangyajun/PostScene/wikis/edgegrid?sort_id=2158428)
 + **快捷函数**  
    - [唯一标识: $uuid32](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [md5加密: $md5](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取列表最后一个: $last](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [查找列表元素: $find](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [反向查找列表元素: $find_last](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取符合的元素: $filter](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取毫秒级时间戳: $timeS](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取秒级时间戳: $times](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取本周开始时间戳: $weekStart](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取本周结束时间戳: $weekEnd](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取上周开始时间戳: $lastWeekStart](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取上周开始时间戳: $lastWeekEnd](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取本月1号时间戳: $monthStart](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取本月结束时间戳: $monthEnd](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取上月1号时间戳: $lastMonthStart](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取上月结束时间戳: $lastMonthEnd](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取前7天时间戳: $last7DaysStart](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [获取前30天时间戳: $last30DaysStart](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    
    - [时间戳转日期格式: $dateFormat](https://gitee.com/tangyajun/PostScene/wikis/%E5%BF%AB%E6%8D%B7%E5%87%BD%E6%95%B0?sort_id=2158438)    

> 写在最后: 目前只提供了这些内置函数，虽然不多但也够用，如果你有什么特别的需要，可以提一个issues    
> 最后，祝你测试愉快 :blush:
****
编码不易，如果你觉得这是一个不错的工具，并且支持我继续努力，那就打赏几块钱给本仙女买杯奶茶吧 :stuck_out_tongue_closed_eyes: 
<img src="https://images.gitee.com/uploads/images/2020/0420/174915_63a25225_5050702.png" width = 30% height = 30% />
