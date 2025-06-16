<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-deltaforce-simulator
</div>

# 介绍
- nonebot平台的三角洲行动鼠鼠偷吃模拟器（开容器模拟器）
- 本项目思路源于[该网站](https://www.acgice.com/sjz/v/mnq_ss)的思路，物品信息图片资源json来源于[该项目](https://github.com/UyNewNas/astrbot_plugin_deltaforce)的整理，图片资源文件来源于三角洲官网。
- 本插件为受群友之托开发的插件，作者不是三角洲玩家，因此插件各容器的白、绿、蓝、紫、金、红物品爆率，以及可能摸到的物品类别均由AI根据网上的资料整理生成生成
- 支持添加修改自定义容器，支持修改容器内各品质物品爆率、容器大小以及可能摸出的物品数量范围和种类



# 插件效果
<img src="demo1.jpg" width="40%">
<img src="demo2.jpg" width="40%">


# 安装
* 手动安装
  ```
  git clone https://github.com/Alpaca4610/nonebot_plugin_deltaforce_simulator.git
  ```

  下载完成后在bot项目的pyproject.toml文件手动添加插件：

  ```
  plugin_dirs = ["xxxxxx","xxxxxx",......,"下载完成的插件路径/nonebot-plugin-deltaforce-simulator]
  ```
<!-- * 使用 pip
  ```
  pip install nonebot-plugin-random-reply
  ``` -->

# 修改容器配置文
修改[容器配置json文件container_configs.json](nonebot_plugin_deltaforce_simulator/container_configs.json)，实现自定义容器以及爆率，示例如下：

```
"small_safe": {
        "grid_size": 3, // 容器大小, N x N
        "allow_types": ["collection","armor"],  //该容器能开出的物品类型，按需填入，armor为护甲，bag为背包，chest为胸挂，collection为收集品，helmet为头盔
        "grade_weights": {"1": 15, "2": 20, "3": 25, "4": 20, "5": 15, "6": 5},  // 该容器内各品质物品的爆率，1~6，数字越大越稀有，分别对应白、绿、蓝、紫、金、红
        "min_items": 1,  // 该容器内物品数量范围最小值（至少会开到多少个物品）
        "max_items": 2,  // 该容器内物品数量范围，最大值（最多会开到多少个物品）
        "name": "小保险箱",  // 容器名称
        "icon": "resource/xbxx.png",  // 容器图标图片的相对路径，图片可以从三角洲官网获取
        "rarity": 3  // 容器稀有度，1~5，数字越大越稀有
    },
```
然后在.env文件中添加自定义的json文件的绝对路径：
```
deltaforce_sim_config = "xxxxxxx"
```

# 使用方法
- 发送“开始跑刀”开始，如有命令前缀需要添加
- 跑刀结果出来后，发送“还要吃”继续开容器，不需要添加命令前缀
- 跑刀结果出来后，发送其他任意信息撤离
