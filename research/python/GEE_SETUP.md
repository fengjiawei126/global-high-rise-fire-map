# Earth Engine unattended setup

本项目使用 Cloud 项目 `graceful-fold-465505-i5`。服务账号邮箱是 `388055120512-compute@developer.gserviceaccount.com`。项目编号 `388055120512` 只用于识别项目，不替代项目 ID。

## 1. Google Cloud 与 Earth Engine

1. 在 Cloud Console 选择 `graceful-fold-465505-i5`。
2. 启用 Earth Engine API。
3. 在 Earth Engine 项目注册页面将该 Cloud 项目注册为符合实际用途的非商业科研或商业项目。
4. 在 IAM 中给运行身份至少授予：
   - Earth Engine Resource Viewer：`roles/earthengine.viewer`；
   - Service Usage Consumer：`roles/serviceusage.serviceUsageConsumer`。
5. 若脚本需要写入 Earth Engine Asset 或发起导出任务，再把 Viewer 提升为 Writer；本项目当前的点位读取与交互计算不主动写 Asset。

## 2. 本地 Windows：JSON 私钥

Google 官方建议仅在无法使用 ADC 的本地环境使用私钥。Cloud Console 中打开服务账号，选择“密钥 → 添加密钥 → 创建新密钥 → JSON”。把下载文件保存到项目目录以外的私密路径。

当前 PowerShell 会话示例：

```powershell
$env:GEE_PROJECT_ID='graceful-fold-465505-i5'
$env:GOOGLE_APPLICATION_CREDENTIALS='D:\private\graceful-fold-service-account.json'
$env:RUN_GEE='1'
.\.venv\Scripts\jupyter-lab
```

不要把 JSON 复制到本项目，不要通过聊天、邮件或 GitHub 发送私钥。如果密钥曾公开，应立即在 Cloud Console 中停用并删除，再创建新密钥。

## 3. Compute Engine、Cloud Run 或其他服务器：ADC

将目标服务账号附加到运行实例，并授予上述 IAM 角色。不要设置 `GOOGLE_APPLICATION_CREDENTIALS`；初始化函数会通过 `google.auth.default()` 获取 ADC。

```powershell
$env:GEE_PROJECT_ID='graceful-fold-465505-i5'
$env:RUN_GEE='1'
.\.venv\Scripts\jupyter-lab
```

## 4. 运行顺序

1. 打开 `notebooks/STEP_2.0_GEE外部数据增强.ipynb`。
2. 确认 `RUN_GEE=1` 后执行全部单元格。
3. 检查 `data/interim/gee_checkpoint_current.csv` 与 `data/processed/case_control_weather.csv`。
4. 执行 STEP 3 生成条件 Logistic 模型与稳健性结果。
5. 执行 STEP 4 重画图件，再重新编译 LaTeX 主文和 SI。

## 5. 当前阻塞诊断

截至 2026-08-31，本机未设置 `GOOGLE_APPLICATION_CREDENTIALS`，未安装 `gcloud`，也没有在 `D:\PersData` 中检测到包含 `service_account` 标识的 JSON。因此当前运行保持 `RUN_GEE=0`，不会伪造气象或 GHSL 结果。

官方依据：

- <https://developers.google.com/earth-engine/guides/service_account>
- <https://developers.google.com/earth-engine/guides/access_control>
- <https://developers.google.com/earth-engine/guides/auth>
