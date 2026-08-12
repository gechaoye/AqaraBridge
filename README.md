# Aqara Bridge for Home Assistant

基于 Aqara 开放平台，通过云端 API 进行设备控制和消息订阅。

[![version](https://img.shields.io/github/manifest-json/v/princehaku/AqaraBridge3.0?filename=custom_components%2Faqara_bridge%2Fmanifest.json)](https://github.com/princehaku/AqaraBridge3.0/releases/latest) [![stars](https://img.shields.io/github/stars/princehaku/AqaraBridge3.0)](https://github.com/princehaku/AqaraBridge3.0/stargazers) [![issues](https://img.shields.io/github/issues/princehaku/AqaraBridge3.0)](https://github.com/princehaku/AqaraBridge3.0/issues) [![hacs](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)

## 一键添加到HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=princehaku&repository=AqaraBridge3.0&category=integration)

## 需要开发者账号支持

需要注册 Aqara 开放平台开发者账号，具体申请方式和最新平台说明请查看 [Aqara 开放平台文档](https://opendoc.aqara.com/)。

* 提示：如果在安装过程中出现此集成不支持通过UI配置，大概率是因为rocketmq的链接库不存在，当前版本仅自动集成了x86和arm64。
* [V2.1.1]已加入更多架构支持，如果还出现类似问题请复制日志信息提Issue
* 当前支持通过hacs商店进行配置，自定义存储库URL: princehaku/AqaraBridge3.0

重点提示：
* 需要自己申请aqara的开发者账号。
* 申请流程1：在 Aqara 开放平台注册账号，申请通过以后需要选择个人认证，输入姓名和身份证号进行开发者认证。
* 申请流程2：申请通过以后就会有一个DEMO应用，进入项目管理-->详情-->消息推送-->编辑-->选择中国服务、MQ消息推送、消息密钥默认应该只有一个、全订阅-->保存
* 申请流程3：返回概况，Appid&密钥这个点击展开，找到中国服务，记录appId、appkey（需要点击小眼睛）、keyid，然后将这三个参数填写到插件对应的三个值上。
* 消息查看：如果需要确认消息可以将这个插件的日志级别改成info可以查看对应消息情况。

开放平台页面和菜单名称可能会调整，请以官方文档显示为准。设备能否创建实体取决于当前开放平台项目实际返回的资源，并非 Aqara Home 中的所有设备和功能都会通过开放接口提供。

## 当前新增设备支持

| 型号 | 设备 | 当前支持 |
| --- | --- | --- |
| `lumi.switch.acn034` | 集悦妙控屏 S1 Plus | 三路实体开关、面板设置、功率/用电量，以及开放平台返回的无线按键事件 |
| `lumi.switch.acn066` | 妙控场景屏 S100 | 三路实体开关 |
| `aqara.lock.dacn03` | 全自动智能猫眼锁 H100 | 门锁状态、电量，以及室内、指纹、密码、NFC、临时密码等解锁事件 |
| `virtual.ir.default` | Aqara 虚拟红外遥控器 | 查询云端按键并通过 `remote.send_command` 发送命令 |
| `virtual.ir.tv` | Aqara 虚拟电视遥控器 | 查询云端按键并通过 `remote.send_command` 发送命令 |

H100、S1 Plus 和 S100 的实体会根据当前开发者项目返回的开放资源逐项创建。表中列出的是集成已实现的能力，不代表每个账号一定会获得全部实体。

### S1 Plus 实体说明

下列四个 `switch` 是面板自身设置，不是灯路，也不是无线开关：

| 实体后缀 | 功能 | Aqara 资源 |
| --- | --- | --- |
| `screen_saver` | 待机屏保 | `4.46.85` |
| `do_not_disturb` | 勿扰模式 | `4.22.85` |
| `auto_brightness` | 屏幕自动亮度 | `4.14.85` |
| `key_tone` | 按键提示音 | `4.31.85` |

S1 Plus 还会从 `13.21.85` 至 `13.29.85` 检查最多九路无线按键事件，包含三路物理按键和六路可配置屏幕按键。集成只创建开放平台实际返回的端点，单击事件兼容值 `0` 和 `1`。这些按键在 Home Assistant 中是 `event` 实体，用于触发自动化，不是可控制的 `switch`。

Aqara Home 中配置的灯光编组可能会作为其他灯光实体出现，与 S1 Plus 无线按键实体相互独立。

### 虚拟红外遥控器

虚拟红外 `remote` 实体的 `commands` 属性列出 Aqara 云端返回的可用按键名称。可以按名称发送命令，也可以直接使用原始 key ID：

```yaml
action: remote.send_command
target:
  entity_id: remote.example
data:
  command: 电源
```

### 不创建实体的对象

以下对象可能出现在 Aqara 云端设备列表中，但当前不应创建独立实体：

* `app.group.temperature` 是 Aqara Home 内部的温控设备组，不是独立硬件。请使用组内实际温控设备的实体。
* `aqara.swe_rob.stcn01` 是第三方授权同步到 Aqara Home 的石头扫地机器人代理。传统资源接口没有返回可控制资源，现有开放能力也不足以提供完整的开始、暂停、回充等控制，建议使用 Home Assistant 官方 Roborock 集成。

## 常见问题

### Aqara 云端返回 429

`429` 表示请求过多（Too Many Requests）。Aqara 官方文档没有公布固定限流时长、QPS、分钟窗口或明确解除时间。

集成会控制请求间隔；收到 429 后按 2、5、10 秒退避重试，并优先采用响应中的 `Retry-After`。重试后仍受限时，集成会通知 Home Assistant 稍后自动重试配置项。设备位置也会使用批量查询以减少请求数量。

限流期间不要连续手动点击“重新加载”。每次重新加载都会再次执行设备发现，可能继续触发限流。建议等待 Home Assistant 自动重试。

### 实体加载失败或停用后无法重新启用

当前版本已调整实体生命周期和 Home Assistant 新版本兼容性处理：

* 事件实体启动时不再读取瞬时事件资源。
* 初始状态查询失败时，实体会先注册为 `unavailable`，收到后续推送后恢复可用。
* 已存在于实体注册表的实体不会因为一次资源查询波动而消失。
* 配置项重载时会卸载平台、停止 MQ，并清理旧的实体对象和消息分发关系。
* 集成只向实际加入 Home Assistant 的实体分发消息，并使用正确的实体平台域，避免新版本的实体 ID 域警告。

更新到包含上述修复的版本后，建议完整重启一次 Home Assistant，再重新启用此前停用的实体。

## 版本修订
当前版本 V3.0.0，为 AqaraBridge3.0 的首个版本。

V3.0.0
* 项目仓库迁移至 `princehaku/AqaraBridge3.0`，同步更新 HACS、文档和问题反馈地址。
* Aqara 云端授权有效期由 7 天调整为 30 天，并在令牌到期前 3 天自动刷新；刷新失败后 1 小时自动重试。
* 增加并发刷新锁和令牌失效自动刷新重试，避免多个请求同时刷新令牌，并改进云端错误日志。
* 刷新令牌后完整保存新的访问令牌、刷新令牌和有效期；仅在账号、开发者参数或选项变化时重载集成。
* 优化选项配置页，自动回填国家/地区和当前刷新令牌；可直接刷新授权，或清空刷新令牌后使用验证码重新授权。
* 新增 `lumi.sensor_ht.agl001` 温度、湿度和电量传感器支持。
* 兼容 `environment_temperature`、`environment_humidity` 资源及小数形式的温湿度和电量数据。
* 新增 S1 Plus、S100、H100 和 Aqara 虚拟红外遥控器支持；S1 Plus 支持开放平台返回的无线按键事件。
* 改进实体初始加载、停用后重新启用、配置项重载和 Home Assistant 新版本实体域兼容性。
* 增加 Aqara 云端 429 限流退避、`Retry-After` 处理和 Home Assistant 自动重试，并减少设备发现阶段的重复请求。
* 识别 Aqara Home 温控设备组和第三方授权的石头扫地机器人代理，避免将无法控制的云端对象误报为普通设备。

V2.1.2
* 优化初始化向导提示
* 优化设备初始化流程
* 优化人体场景传感器FP2状态管理
* 优化人体存在传感器FP1/FP1E移动事件

- 添加设备：
- 网关类：
- - lumi.gateway.acn008 - 网关 M1S（第二代）
- - lumi.gateway.acn012 - 网关 M3

- 摄像机类：
- - lumi.camera.gwpagl01 - 智能摄像机G3（网关版） - 支持手势等事件

- 开关/插座类：
- - lumi.switch.acn048 - 卡农 智能墙壁开关 Z1（单键版）
- - lumi.switch.acn049 - 卡农 智能墙壁开关 Z1（双键版）
- - lumi.switch.acn054 - 卡农 智能墙壁开关 Z1（三键版）
- - lumi.switch.acn055 - 卡农 智能墙壁开关 Z1（四键版）
- - lumi.switch.acn056 - 卡农 智能墙壁开关 Z1 Pro（单键版）
- - lumi.switch.acn057 - 卡农 智能墙壁开关 Z1 Pro（双键版）
- - lumi.switch.acn058 - 卡农 智能墙壁开关 Z1 Pro（三键版）
- - lumi.switch.acn059 - 卡农 智能墙壁开关 Z1 Pro（四键版）
- - lumi.switch.acn040 - 智能墙壁开关 E1（零火线三键版）
- - lumi.switch.acn041 - 智能墙壁开关 J1（单火线单键版）
- - lumi.switch.acn042 - 智能墙壁开关 J1（单火线双键版）
- - lumi.switch.acn043 - 智能墙壁开关 J1（单火线三键版）
- - lumi.switch.acn044 - 智能墙壁开关 J1（零火线单键版）
- - lumi.switch.acn045 - 智能墙壁开关 J1（零火线双键版）
- - lumi.switch.acn046 - 智能墙壁开关 J1（零火线三键版）
- - lumi.switch.acn062 - 智能墙壁开关 Q1（单键版）
- - lumi.switch.acn063 - 智能墙壁开关 Q1（双键版）
- - lumi.switch.acn065 - 智能墙壁开关 Q1（四键版）
- - lumi.switch.acn047 - 双路控制模块 T2
- - lumi.sensor_switch.v1 - 无线开关
- - lumi.sensor_switch.v2 - 无线开关
- - lumi.sensor_switch.aq2 - 无线开关

- 灯控类：（感谢XaoflySho提交的PR）
- - lumi.dimmer.acn003 - 智能灯带驱动器 T1
- - lumi.dimmer.acn004 - 智能灯带驱动器 T1（120W）
- - lumi.dimmer.acn005 - 智能灯带驱动器 T1（240W）

- 空调温控类：
- - aqara.airrtc.acn02 - 温控伴侣 T1（室内机）
- - lumi.airrtc.pcacn2 - 智能温控器 S3
- - lumi.airrtc.pcacn2_thermostat - 智能温控器 S3
- - lumi.airrtc.agl001 - 智能阀式温控器 E1

- 窗帘类：
- - lumi.curtain.vagl02 - 智能管状电机 T1
- - lumi.curtain.acn002 - 智能卷帘伴侣 E1



V2.1.1
* 修复窗帘位置同步不及时问题
* 修改将被HA弃用的函数
* 完善arm64架构rocketmq支持
* 优化初始化时可能创建无法管理的实体的问题
* 优化冷启动向导相关
* 优化支持不完善的设备弹出大量警告问题
* 按钮button改为event类

- 添加设备：
- 晾衣架类：
- - lumi.airer.acn001 - 智能晾衣机H1
- - lumi.airer.acn02 - Aqara智能晾衣机 Lite

V2.1.0 - 修复大部分错误并添加大量设备
* 重写空调控制器类
* 修复rocketmq启动时阻塞HA初始化问题
* 修复了调用某些HA已废弃/将要废弃常量问题
* 修复light设备类颜色映射错误
* 修复button设备类UI按钮问题
* 修复无线场景开关（六键版）型号错误
* 优化Entities载入流程
* 优化多通道设备初始化流程
* 优化设备和Entity自动命名规则

- 添加设备：
- 网关类：
- - lumi.controller.a4acn1 - 集悦智慧面板 S1 

- 开关/插座类： 
- - lumi.switch.n3acn3 - 智能墙壁开关D1（零火线三键版） 
- - lumi.switch.l3acn3 - 智能墙壁开关D1（单火线三键版） 
- - lumi.ctrl_86plug.aq1 - 墙壁插座（Zigbee版） 
- - lumi.relay.c2acn01 - 双路控制器 

- 灯控类： 
- - lumi.light.cbacn1 - Aqara 智能恒流驱动器 T1-1 
- - lumi.light.cwopcn01 - 吸顶灯MX960（可调色温） 
- - lumi.light.acn007 - 轨道格栅灯 H1（6头） 
- - lumi.light.acn008 - 轨道格栅灯 H1（12头） 
- - lumi.light.acn009 - 轨道泛光灯 H1（30cm） 
- - lumi.light.acn010 - 轨道泛光灯 H1（60cm） 
- - lumi.light.acn011 - 轨道吊线灯 H1 
- - lumi.light.acn012 - 轨道折叠格栅灯 H1（6头） 
- - lumi.light.acn013 - 轨道偏光灯 H1（22cm） 
- - lumi.light.cwjwcn02 - 筒灯（可调色温） 
- - lumi.light.acn004 - Aqara 双色温驱动器 T1 Pro 
- - lumi.light.acn006 - 轨道灯 H1 Pro 
- - lumi.light.acn023 - 射灯 T2（15度） 
- - lumi.light.acn024 - 射灯 T2（24度） 
- - lumi.light.acn025 - 射灯 T2（36度） 
- - lumi.light.acn026 - 筒灯 T2（60度） 
- - lumi.light.acn128 - 筒射灯 T3 
- - lumi.light.acn014 - LED灯泡 T1（可调色温） 
- - lumi.light.acn003 - Aqara 吸顶灯 L1-350 
- - lumi.light.acn015 - Aqara光艺晴空灯 H1 
- - lumi.light.acn032 - 幻彩吸顶灯 T1（40W） 
- - lumi.light.acn132 - 流光溢彩灯带 T1 

- 窗帘类：
- - lumi.curtain.v1 - 智能窗帘电机 (Zigbee开合帘版)
- - umi.curtain.acn007 - Aqara智能窗帘电机 T1
- - lumi.curtain.hagl07 - 智能窗帘电机 C2
- - lumi.curtain.hagl08 - Aqara智能窗帘电机A1
- - lumi.curtain.hagl04 - 智能窗帘电机 B1
- - lumi.curtain.acn015 - Aqara智能窗帘电机 T2
- - lumi.curtain.aq2 - 智能管状电机
- - lumi.curtain.hagl04 - 智能窗帘电机 B1
- - lumi.curtain.acn04 - Aqara智能窗帘电机 C3
- - lumi.curtain.acn003 - 智能窗帘伴侣E1

- 空调/地暖类：
- - lumi.aircondition.acn05 - 空调伴侣 P3
- - lumi.airrtc.vrfegl01 - VRF空调控制器
- - lumi.acpartner.aq1 - 空调伴侣
- - lumi.acpartner.v3 - 空调伴侣（升级版）
- - lumi.ctrl_hvac.es1 - 空调温控器
- - lumi.airrtc.tcpco2ecn01 - 空调温控器（CO2）
- - lumi.acpartner.es1 - 空调伴侣
- - lumi.airrtc.tcpecn01 - 空调温控器
- - lumi.airrtc.tcpecn02 - 空调温控器 S2

- 传感器类：
- - lumi.motion.ac02 - 人体传感器 P1
- - umi.motion.agl02 - 人体传感器 T1
- - lumi.motion.acn001 - 人体传感器 E1
- - lumi.motion.agl001 - 人体场景传感器 FP2
- - lumi.sensor_occupy.agl1 - AI智能存在传感器 FP1E
- - lumi.sensor_natgas.v1 - 天然气报警器
- - lumi.sensor_gas.acn02 - Aqara天然气报警器
- - lumi.airmonitor.acn01 - TVOC空气健康伴侣
- - lumi.sen_ill.agl01 - 光照传感器 T1


V2.0.3
* 修复开发者配置问题，可以使用自己开发者信息。


V2.0.2
* 修复错误保存问题，增加启动依赖，需要在homekit启动正常以后。
* 修复flow的option操作错误，可以重新通过手机号刷新失效token，并修复部分错误提示。
* hass图标已经通过，当前可以正常显示组件图标，以及设备厂商图标。
* 修复其他常规错误。

V2.0.1
* 整体合并到master，原有的配置方式需要使用dev分支，该分支不继续维护。
* 修改flow，将多个网关合并到账号，拆分开发者认证信息允许自行配置自己的开发者AK等。
* 修复大部分组件获取状态异常，以及历史状态修改。
* 感谢[银狼](https://bbs.hassbian.com/?62352)新增部分组件配置：支持无线旋钮H1，H1 12头磁吸格栅灯，无线按钮（升级版）。同时墙壁开关拆分为两部分，其中零火的加入了电量监测，led驱动模块加了电力监测。

V1.0.1
* 修复了大部分组件的问题，增加了无线按键。当前的按键都同时事件订阅刷新时间整体速度还不错，不是轮训机制了。
* 增加房间位置获取。
* 增加按键类开关对应按键名称获取。
* 增加arm64的rocketmq动态链接库，除了X86和arm64其他暂时没处理。
* 增加各类的历史数据获取刷新了最后的trigger_time或者last_update_time。
* 增加button类型，将无线开关从传感器上拆分。
* 配置了大部分常见的网关、无线开关、单火/零火开关、温湿度传感器、智能插座、人体传感器等。
* 增加了部分错误提示，至少不会在配置没任何错误了。

V1.0.0

还有我只支持了大部分我有的设备和类似的组件，如果发现有不支持的懂python的修改：
[custom_components/aqara_bridge/core/aiot_mapping.py](https://github.com/princehaku/AqaraBridge3.0/blob/master/custom_components/aqara_bridge/core/aiot_mapping.py)
