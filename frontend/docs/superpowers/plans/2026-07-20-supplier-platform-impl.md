# 供应商平台分类改造 — 实施计划

> **面向 AI 代理的工作者：** 必需子技能：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 按 1688/微信/线下 分类供应商，后端按平台强校验，线上采购自动建立 supplier_id 关联。

**架构：** 前端 SupplierFormDialog 按平台 Tabs 动态展示字段；后端新增 platform/shop_link/wechat_id/wechat_nickname/is_dropship 五列；采购路由在 CRUD 层完成所有业务校验并抛 ValueError，路由层统一转换为 HTTPException(422)。

**技术栈：** FastAPI + SQLAlchemy + Pydantic + Vue3 + Element Plus + pytest

---

## 文件结构与职责

| 文件 | 职责 |
|------|------|
| `backend/migrations/add_supplier_platform_fields.py` | 新建：sup_supplier + po_purchase_order 双表迁移脚本 |
| `backend/schemas/purchase.py` | 修改：增加 PurchaseCreateOnline（Literal platform 等字段） |
| `backend/models/purchase.py` | 修改：PoPurchaseOrder 新增 platform/shop_link/wechat_id/wechat_nickname/is_dropship |
| `backend/crud/purchase.py` | 修改：create_online_purchase 实现所有业务校验（ValueError），返回 (orders, supplier_id) |
| `backend/routers/purchase.py` | 修改：移除内联校验逻辑，路由仅 try/except ValueError→422；路由入参改为 PurchaseCreateOnline |
| `frontend/src/api/suppliers.ts` | 修改：Supplier/SupplierFormPayload 类型 + 接口函数 |
| `frontend/src/api/purchase.ts` | 修改：PurchaseCreateOnline 类型 + createOnlinePurchase |
| `frontend/src/components/supplier/SupplierFormDialog.vue` | 修改：增加平台 Tabs 动态表单（复用现有组件路径） |
| `frontend/src/components/common/createSupplier.vue` | 修改：适配 SupplierFormDialog |
| `frontend/src/components/order/PurchaseDialog.vue` | 修改：采购提交调用新 API，移除前端 find-or-create |
| `backend/tests/test_supplier_platform.py` | 新建：CRUD 单元测试 |

**已完成（无需再写）：**
- `backend/models/supplier.py` — platform 字段已存在 ✓
- `backend/schemas/supplier.py` — platform 字段已存在 ✓
- `backend/crud/supplier.py` — `_validate_platform_fields` / `_validate_platform_fields_update` / `get_supplier_by_name_and_platform` / `find_or_create_supplier_by_name` → `tuple` 已实现 ✓
- `backend/routers/supplier.py` — find-or-create 路由 + ValueError→422 已实现 ✓
- `backend/tests/test_supplier_platform_api.py` — 接口级测试已实现 ✓

---

## 任务 1：数据库迁移脚本（供应商 + 采购单）

**文件：**
- 创建：`backend/migrations/add_supplier_platform_fields.py`

- [ ] **步骤 1：编写迁移脚本（同时迁移 sup_supplier 和 po_purchase_order）**

```python
"""为 sup_supplier 和 po_purchase_order 增加平台分类字段。

执行：docker compose exec backend python -m migrations.add_supplier_platform_fields
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    with engine.connect() as conn:
        # ── 1. sup_supplier 新增字段 ────────────────────────────────
        for ddl in [
            "ALTER TABLE sup_supplier ADD COLUMN platform VARCHAR(20)",
            "ALTER TABLE sup_supplier ADD COLUMN shop_link VARCHAR(500)",
            "ALTER TABLE sup_supplier ADD COLUMN wechat_id VARCHAR(100)",
            "ALTER TABLE sup_supplier ADD COLUMN wechat_nickname VARCHAR(100)",
        ]:
            try:
                conn.execute(text(ddl))
            except Exception as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

        try:
            conn.execute(text(
                "ALTER TABLE sup_supplier ADD COLUMN is_dropship BOOLEAN NOT NULL DEFAULT 0"
            ))
        except Exception as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

        # ── 2. po_purchase_order 新增字段 ─────────────────────────
        for ddl in [
            "ALTER TABLE po_purchase_order ADD COLUMN platform VARCHAR(20)",
            "ALTER TABLE po_purchase_order ADD COLUMN shop_link VARCHAR(500)",
            "ALTER TABLE po_purchase_order ADD COLUMN wechat_id VARCHAR(100)",
            "ALTER TABLE po_purchase_order ADD COLUMN wechat_nickname VARCHAR(100)",
        ]:
            try:
                conn.execute(text(ddl))
            except Exception as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

        try:
            conn.execute(text(
                "ALTER TABLE po_purchase_order ADD COLUMN is_dropship BOOLEAN NOT NULL DEFAULT 0"
            ))
        except Exception as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

        # ── 3. 检查 sup_supplier 重复数据（创建唯一索引前诊断） ───
        duplicate_rows = conn.execute(text("""
            SELECT dept_id, platform, supplier_name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
            FROM sup_supplier
            WHERE dept_id IS NOT NULL
              AND platform IS NOT NULL
              AND supplier_name IS NOT NULL
              AND supplier_name != ''
            GROUP BY dept_id, platform, supplier_name
            HAVING COUNT(*) > 1
        """)).fetchall()

        if duplicate_rows:
            lines = "\n".join(
                f"  dept_id={r[0]}, platform={r[1]}, supplier_name={r[2]}, "
                f"重复数量={r[3]}, ids={r[4]}"
                for r in duplicate_rows
            )
            raise RuntimeError(
                f"发现 {len(duplicate_rows)} 组重复供应商数据，请先在数据库中合并或删除重复记录后再执行迁移。\n{lines}"
            )

        # ── 4. 创建唯一索引（NULL 不参与约束） ─────────────────────
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX uq_supplier_dept_platform_name "
                "ON sup_supplier(dept_id, platform, supplier_name)"
            ))
        except Exception as exc:
            if "already exists" not in str(exc).lower():
                raise

        conn.commit()
        print("OK: sup_supplier + po_purchase_order platform 字段迁移完成")


if __name__ == "__main__":
    upgrade()
```

- [ ] **步骤 2：验证脚本语法**

```bash
py -c "import ast; ast.parse(open('d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend/migrations/add_supplier_platform_fields.py').read())"
```
预期：无输出（语法正确）

- [ ] **步骤 3：Commit**

```bash
git add backend/migrations/add_supplier_platform_fields.py
git commit -m "feat: add supplier platform migration script"
```

---

## 任务 2：采购 Schema 与 ORM Model

**文件：**
- 修改：`backend/schemas/purchase.py`
- 修改：`backend/models/purchase.py`

- [ ] **步骤 1：在 PurchaseCreateOnline 中新增 platform 及平台字段**

在 `backend/schemas/purchase.py` 的 `PurchaseOrderCreate` 之后插入：

```python
class PurchaseCreateOnline(BaseModel):
    """线上采购（1688/微信）请求体，包含平台分类字段"""
    dept_id: str
    pi_id: int
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    platform: Literal['1688', 'wechat', 'offline']   # 必填
    items: List[PurchaseOrderItemCreate]
    link: Optional[str] = None
    contact_wechat: Optional[str] = None
    screenshot: Optional[str] = None
    remark: Optional[str] = None
    # 新增平台字段
    shop_link: Optional[str] = None
    wechat_id: Optional[str] = None
    wechat_nickname: Optional[str] = None
    is_dropship: Optional[bool] = None
    # 线下联系人
    supplier_contact: Optional[str] = None
    supplier_phone: Optional[str] = None
```

- [ ] **步骤 2：在 PoPurchaseOrder ORM Model 中新增平台字段**

在 `backend/models/purchase.py` 的 `PoPurchaseOrder` 类（`__tablename__ = "po_purchase_order"`）中添加：

```python
# 平台分类字段（2026-07-20 新增）
platform = Column(String(20), nullable=True)
shop_link = Column(String(500), nullable=True)
wechat_id = Column(String(100), nullable=True)
wechat_nickname = Column(String(100), nullable=True)
is_dropship = Column(Boolean, default=False, nullable=False, server_default='0')
```

- [ ] **步骤 3：验证语法**

```bash
py -c "import ast; [ast.parse(open(f).read()) for f in [r'd:\TraeProjects\PI Manager\worktrees\frontend-repo\backend\schemas\purchase.py', r'd:\TraeProjects\PI Manager\worktrees\frontend-repo\backend\models\purchase.py']]; print('OK')"
```
预期：OK

- [ ] **步骤 4：Commit**

```bash
git add backend/schemas/purchase.py backend/models/purchase.py
git commit -m "feat: add platform fields to PurchaseCreateOnline schema and PurchaseOrder model"
```

---

## 任务 3：CRUD 层 — create_online_purchase 实现

**文件：**
- 修改：`backend/crud/purchase.py`

**说明：** 当前 `routers/purchase.py` 中的业务校验层（dept/platform/null）是写在路由里的。现在需要将 `create_online_purchase` 函数实现在 `crud/purchase.py` 中，完整实现所有校验并抛 ValueError。路由层只保留 try/except 转换为 HTTPException。

- [ ] **步骤 1：在 crud/purchase.py 末尾添加 create_online_purchase 函数**

```python
def create_online_purchase(db: Session, payload: PurchaseCreateOnline) -> tuple[list, int | None]:
    """线上采购自动 find-or-create，返回 (purchase_orders, supplier_id)

    返回 supplier_id 用于写入采购单（若 supplier_name 传入但 supplier_id 未传入，则为新创建或已存在的供应商 ID）。

    业务校验（唯一事实来源）：
    - supplier_id 与 supplier_name 均缺失/空白 → ValueError
    - supplier_id 关联时：供应商不存在 / dept_id 不一致 / platform=NULL / platform 不一致 → ValueError
    """
    # 1. supplier_name 空白校验
    has_supplier_name = bool(payload.supplier_name and str(payload.supplier_name).strip())
    if not payload.supplier_id and not has_supplier_name:
        raise ValueError('supplier_id 或 supplier_name（非空）至少填写一个')

    supplier_id = payload.supplier_id

    # 2. supplier_id 关联时校验
    if supplier_id:
        from models import SupSupplier
        supplier = db.query(SupSupplier).filter(SupSupplier.id == supplier_id).first()
        if not supplier:
            raise ValueError('供应商不存在')
        # 2.1 部门一致性
        if supplier.dept_id != payload.dept_id:
            raise ValueError(
                f'所选供应商部门为 {supplier.dept_id}，与本次采购部门 {payload.dept_id} 不一致，'
                '请选择本部门供应商或通过"新建供应商"创建'
            )
        # 2.2 platform=NULL 禁止用于线上采购
        if supplier.platform is None:
            raise ValueError(
                f'所选供应商（{supplier.supplier_name}）尚未分配平台，无法关联到线上采购。'
                '请先在"供应商管理"中为该供应商设置平台类型。'
            )
        # 2.3 平台一致性
        if supplier.platform != payload.platform:
            raise ValueError(
                f'所选供应商平台为 {supplier.platform}，与本次采购平台 {payload.platform} 不一致，'
                '请重新选择或使用"新建供应商"流程'
            )
        # 一致则直接使用 supplier_id，无需 find-or-create
        return ([], supplier_id)

    # 3. 无 supplier_id 但有 supplier_name → find-or-create
    if has_supplier_name:
        from crud.supplier import find_or_create_supplier_by_name
        result = find_or_create_supplier_by_name(
            db,
            supplier_name=str(payload.supplier_name).strip(),
            platform=payload.platform,
            dept_id=payload.dept_id,
            shop_link=payload.shop_link,
            wechat_id=payload.wechat_id,
            wechat_nickname=payload.wechat_nickname,
            is_dropship=payload.is_dropship,
            contact_person=payload.supplier_contact,
            phone=payload.supplier_phone,
        )
        if result is None:
            raise ValueError('创建供应商失败')
        supplier_obj, _ = result
        supplier_id = supplier_obj.id

    return ([], supplier_id)
```

- [ ] **步骤 2：验证语法**

```bash
py -c "import ast; ast.parse(open(r'd:\TraeProjects\PI Manager\worktrees\frontend-repo\backend\crud\purchase.py').read()); print('OK')"
```
预期：OK

- [ ] **步骤 3：Commit**

```bash
git add backend/crud/purchase.py
git commit -m "feat: implement create_online_purchase in crud layer with full validation"
```

---

## 任务 4：采购路由改造

**文件：**
- 修改：`backend/routers/purchase.py`

**关键约束：** 路由入参必须改为 `PurchaseCreateOnline`（已包含 platform/supplier_name/shop_link 等全部字段），不能再用旧的 `PurchaseOrderCreate`。同时删除当前路由中手写的"业务校验层"内联代码块（`# ── 业务校验层 ──` 到 `if supplier_id:` 段），校验职责全部由 CRUD 层承接。

- [ ] **步骤 1：修改 create_1688_purchase_api（路由入参改 PurchaseCreateOnline，删除内联校验）**

```python
@router.post("/1688")
def create_1688_purchase_api(purchase_data: PurchaseCreateOnline, db: Session = Depends(get_db)):
    """2026-07-20：1688 线上采购

    路由层仅负责：
    1. 接收 PurchaseCreateOnline 校验后的数据（Pydantic 自动拦截缺失字段）
    2. 调用 CRUD 层完成所有业务校验并捕获 ValueError → HTTPException(422)
    所有业务校验逻辑在 crud.purchase.create_online_purchase 中完成。
    """
    # 兼容 dict 与 pydantic（未来统一后可移除）
    if hasattr(purchase_data, "model_dump"):
        data = purchase_data.model_dump()
    elif hasattr(purchase_data, "dict"):
        data = purchase_data.dict()
    else:
        data = dict(purchase_data)

    # CRUD 层完成所有业务校验（supplier_id/name 均缺失 / dept 不一致 / platform 不一致 / platform=NULL）
    try:
        _, supplier_id = create_online_purchase(db, purchase_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 1) 1688 采购明细（直接从 data 字典提取，保持原有逻辑不变）
    created_records: list = []
    src_items = data.get("items") or []
    if src_items:
        batch_items = []
        for it in src_items:
            batch_items.append(Po1688PurchaseItem(
                product_id=it.get("product_id"),
                supplier_name=it.get("supplier_name") or data.get("supplier_name"),
                product_url=it.get("link") or it.get("product_url"),
                product_remark=it.get("remark"),
                color=it.get("color"),
                invoice_type=it.get("invoice_type"),
                labeling_fee=it.get("labeling_fee"),
                shipping_fee=it.get("shipping_fee"),
                shipping_method=it.get("shipping_method"),
                carton_count=it.get("carton_count"),
                freight=it.get("freight"),
                unit_price=it.get("unit_price"),
                tax_fee=it.get("tax_fee"),
                payment_method=it.get("payment_method"),
                gross_weight=it.get("gross_weight"),
            ))
        batch = Po1688PurchaseBatchCreate(
            dept_id=data.get("dept_id"),
            po_id=data.get("po_id"),
            pi_id=data.get("pi_id"),
            screenshot=data.get("screenshot"),
            remark=data.get("remark"),
            items=batch_items,
        )
        try:
            created_records = create_1688_purchase_batch(db, batch)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # 2) 按 supplier_id 分组生成采购单（使用 PurchaseCreateOnline）
    try:
        purchase_orders = create_grouped_purchase_orders(db, purchase_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "success": True,
        "purchase_orders": purchase_orders,
        "records": created_records,
    }
```

- [ ] **步骤 2：删除 routers/purchase.py 中的内联业务校验块**

找到并删除 `create_1688_purchase_api` 函数内从 `# ── 业务校验层 ──` 注释开始到 `if supplier_id:` 块结束的所有代码（前次实施时手动写入的 dept/platform 校验逻辑）。这些职责已全部移入 CRUD 层，保留会造成重复校验。

- [ ] **步骤 3：验证语法**

```bash
py -c "import ast; ast.parse(open(r'd:\TraeProjects\PI Manager\worktrees\frontend-repo\backend\routers\purchase.py').read()); print('OK')"
```
预期：OK

- [ ] **步骤 4：Commit**

```bash
git add backend/routers/purchase.py
git commit -m "refactor: change purchase route to use PurchaseCreateOnline, remove inline validation"
```

---

## 任务 5：前端 — SupplierFormDialog 平台 Tabs 表单

**文件：**
- 修改：`frontend/src/components/supplier/SupplierFormDialog.vue`（**改造现有组件，非新建**；该路径已有组件，不要在 `common/` 下重复创建）

- [ ] **步骤 1：改造 frontend/src/components/supplier/SupplierFormDialog.vue（覆盖现有文件）**

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="560px"
    :close-on-click-modal="false"
    :before-close="requestClose"
  >
    <!-- 平台 Tabs：新建或历史数据（platform=NULL）时可切换 -->
    <el-tabs v-if="!hasPlatform" v-model="currentPlatform" class="platform-tabs">
      <el-tab-pane label="1688" name="1688" />
      <el-tab-pane label="微信" name="wechat" />
      <el-tab-pane label="线下" name="offline" />
    </el-tabs>

    <!-- 已有 platform 的供应商，Tabs 锁定为该值 -->
    <div v-else class="platform-locked">
      <el-tag type="info">{{ platformLabelMap[currentPlatform] }}</el-tag>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="supplier-form">
      <!-- 供应商名称（各平台通用） -->
      <el-form-item label="供应商名称" prop="supplier_name">
        <el-input v-model="form.supplier_name" placeholder="请输入供应商名称" />
      </el-form-item>

      <!-- 1688 专属字段 -->
      <template v-if="currentPlatform === '1688'">
        <el-form-item label="店铺链接" prop="shop_link">
          <el-input v-model="form.shop_link" placeholder="https://shop.1688.com/..." />
        </el-form-item>
        <el-form-item label="微信号">
          <el-input v-model="form.wechat_id" placeholder="选填" />
        </el-form-item>
      </template>

      <!-- 微信专属字段 -->
      <template v-if="currentPlatform === 'wechat'">
        <el-form-item label="微信昵称">
          <el-input v-model="form.wechat_nickname" placeholder="选填" />
        </el-form-item>
        <el-form-item label="支持代发">
          <el-switch v-model="form.is_dropship" />
        </el-form-item>
      </template>

      <!-- 通用字段（各平台共享） -->
      <el-form-item label="联系人">
        <el-input v-model="form.contact_person" placeholder="选填" />
      </el-form-item>
      <el-form-item label="电话">
        <el-input v-model="form.phone" placeholder="选填" />
      </el-form-item>
      <el-form-item label="省份">
        <el-select v-model="form.province" placeholder="请选择省份" clearable filterable allow-create>
          <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
        </el-select>
      </el-form-item>
      <el-form-item label="城市" v-if="form.province">
        <el-select v-model="form.city" placeholder="请选择城市" clearable filterable allow-create>
          <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="requestClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { suppliersApi } from '@/api/suppliers'
import { getProvinces, getCities } from '@/api/suppliers'

const props = defineProps<{
  modelValue: boolean
  supplier: Supplier | null
  defaultPlatform?: '1688' | 'wechat' | 'offline'
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  'success': [supplier: Supplier]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const hasPlatform = computed(() => !!props.supplier?.platform)
const currentPlatform = ref<'1688' | 'wechat' | 'offline'>(
  (props.supplier?.platform as any) || props.defaultPlatform || 'offline'
)

const platformLabelMap: Record<string, string> = {
  '1688': '1688 平台',
  'wechat': '微信平台',
  'offline': '线下供应商',
}

const formRef = ref<FormInstance>()
const saving = ref(false)

const form = ref({
  supplier_name: '',
  shop_link: '',
  wechat_id: '',
  wechat_nickname: '',
  is_dropship: false,
  contact_person: '',
  phone: '',
  province: '',
  city: '',
})

// 加载已有供应商数据到表单
watch(() => props.supplier, (s) => {
  if (s) {
    form.value = {
      supplier_name: s.supplier_name || '',
      shop_link: s.shop_link || '',
      wechat_id: s.wechat_id || '',
      wechat_nickname: s.wechat_nickname || '',
      is_dropship: s.is_dropship || false,
      contact_person: (s as any).contact_person || '',
      phone: (s as any).phone || '',
      province: (s as any).province || '',
      city: (s as any).city || '',
    }
  } else {
    form.value = { supplier_name: '', shop_link: '', wechat_id: '', wechat_nickname: '', is_dropship: false, contact_person: '', phone: '', province: '', city: '' }
    currentPlatform.value = props.defaultPlatform || 'offline'
  }
}, { immediate: true })

const rules: FormRules = {
  supplier_name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  shop_link: [{
    validator: (_r, value, callback) => {
      if (currentPlatform.value === '1688' && !value?.trim()) {
        callback(new Error('1688 供应商必须填写店铺链接'))
      } else {
        callback()
      }
    },
    trigger: 'blur',
  }],
}

const provinces = ref<string[]>([])
const cities = ref<string[]>([])
getProvinces().then((data) => { provinces.value = data })

watch(() => form.value.province, (p) => {
  if (p) {
    getCities(p).then((data) => { cities.value = data })
  } else {
    cities.value = []
    form.value.city = ''
  }
})

async function save() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload: any = {
      supplier_name: form.value.supplier_name,
      province: form.value.province || null,
      city: form.value.city || null,
      contact_person: form.value.contact_person || null,
      phone: form.value.phone || null,
      platform: currentPlatform.value,
    }
    if (currentPlatform.value === '1688') {
      payload.shop_link = form.value.shop_link || null
      payload.wechat_id = form.value.wechat_id || null
    } else if (currentPlatform.value === 'wechat') {
      payload.wechat_id = form.value.supplier_name  // 微信号即名称
      payload.wechat_nickname = form.value.wechat_nickname || null
      payload.is_dropship = form.value.is_dropship
    }
    const res = props.supplier
      ? await suppliersApi.update(props.supplier.id, payload)
      : await suppliersApi.create(payload)
    ElMessage.success(props.supplier ? '供应商已更新' : '供应商已创建')
    emit('success', res.data)
    visible.value = false
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

function requestClose() {
  visible.value = false
}
</script>

<style scoped>
.platform-tabs { margin-bottom: 16px; }
.platform-locked { margin-bottom: 16px; }
.supplier-form { margin-top: 8px; }
</style>
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/components/supplier/SupplierFormDialog.vue
git commit -m "feat: add SupplierFormDialog with platform tabs (1688/wechat/offline)"
```

---

## 任务 6：前端 — Supplier 类型与 API 改造

**文件：**
- 修改：`frontend/src/api/suppliers.ts`

- [ ] **步骤 1：更新 suppliers.ts 类型与 API 函数**

在 `frontend/src/api/suppliers.ts` 中替换或追加：

```typescript
export interface Supplier {
  id: number
  supplier_code: string
  supplier_name: string
  dept_id: string
  region?: string | null
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  status: number
  created_at: string
  // 平台分类字段（2026-07-20 新增）
  platform?: '1688' | 'wechat' | 'offline' | null
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}

export interface SupplierFormPayload {
  supplier_name: string
  province?: string | null
  city?: string | null
  city_code?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  platform?: '1688' | 'wechat' | 'offline'
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
}

export interface FindOrCreateSupplierResponse {
  id: number
  supplier_name: string
  supplier_code?: string
  created: boolean  // true=新建，false=复用已有
}

export const suppliersApi = {
  create(payload: SupplierFormPayload) {
    return client.post('/api/suppliers/', payload)
  },
  update(id: number, payload: SupplierFormPayload) {
    return client.put(`/api/suppliers/${id}`, payload)
  },
  delete(id: number) {
    return client.delete(`/api/suppliers/${id}`)
  },
  findOrCreate(payload: SupplierFormPayload & { platform: '1688' | 'wechat' | 'offline' }): Promise<{ data: FindOrCreateSupplierResponse }> {
    return client.post('/api/suppliers/find-or-create', payload)
  },
  list(params?: { skip?: number; limit?: number; keyword?: string }) {
    return client.get('/api/suppliers/', { params })
  },
  getProvinces() {
    return client.get('/api/suppliers/provinces').then((r) => r.data as string[])
  },
  getCities(province: string) {
    return client.get(`/api/suppliers/cities/${province}`).then((r) => r.data as string[])
  },
}
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/api/suppliers.ts
git commit -m "feat: add platform fields to Supplier type and suppliers API"
```

---

## 任务 6b：前端 — Purchase API 类型改造

**文件：**
- 修改：`frontend/src/api/purchase.ts`

- [ ] **步骤 1：在 purchase.ts 末尾追加 PurchaseCreateOnline 类型和 createOnlinePurchase 函数**

```typescript
/** 线上采购（1688/微信）请求体，对应后端 PurchaseCreateOnline */
export interface PurchaseCreateOnline {
  dept_id: string
  pi_id: number
  supplier_id?: number | null
  supplier_name?: string | null
  platform: '1688' | 'wechat' | 'offline'
  items: PurchaseItem[]
  link?: string | null
  contact_wechat?: string | null
  screenshot?: string | null
  remark?: string | null
  // 平台字段
  shop_link?: string | null
  wechat_id?: string | null
  wechat_nickname?: string | null
  is_dropship?: boolean | null
  // 联系人
  supplier_contact?: string | null
  supplier_phone?: string | null
}

/** 后端 /api/purchase-orders/1688 响应 */
export interface CreateOnlinePurchaseResponse {
  success: boolean
  purchase_orders: any[]
  records: any[]
}

/** 调用线上采购接口 */
export async function createOnlinePurchase(payload: PurchaseCreateOnline): Promise<CreateOnlinePurchaseResponse> {
  const res = await client.post('/api/purchase-orders/1688', payload)
  return res.data
}
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/api/purchase.ts
git commit -m "feat: add PurchaseCreateOnline type and createOnlinePurchase to purchase API"
```

---

## 任务 7b：后端 — 确认 FindOrCreateSupplierResponse 的 created 透传

**文件：**
- 确认：`backend/routers/supplier.py` 中 `find_or_create_supplier_api` 的返回值

`FindOrCreateSupplierResponse` 已包含 `created: bool` 字段，`find_or_create_supplier_by_name` 返回 `tuple[SupSupplier, bool]`，路由层已实现解包 `new_supplier, created = result` 并透传到响应。本步骤仅确认这三者对齐，无需额外代码。

- [ ] **步骤 1：确认响应链**

读取 `backend/routers/supplier.py` 中 `find_or_create_supplier_api` 函数，确认：
1. `result = find_or_create_supplier_by_name(...)` 接收 tuple
2. `new_supplier, created = result` 解包
3. `FindOrCreateSupplierResponse(..., created=created)` 如实传递

若已对齐则无需修改；若未对齐，修正解包逻辑。

- [ ] **步骤 2：Commit（如有修改）**

```bash
git add backend/routers/supplier.py
git commit -m "fix: ensure created flag is correctly propagated in find-or-create response"
```

---

## 任务 7：前端 — PurchaseDialog 改造（移除前端 find-or-create）

**文件：**
- 修改：`frontend/src/components/order/PurchaseDialog.vue`（或对应文件路径）

**说明：** 采购提交时不再在前端手动调用 find-or-create，直接传 `supplier_name` + `platform` + `shop_link` 等字段，由后端在 `create_online_purchase` 中自动建立 supplier_id 关联。

- [ ] **步骤 1：在 PurchaseDialog 的提交函数中适配新 API**

在 PurchaseDialog.vue 的提交函数中，找到 1688/微信分支，将：

```typescript
// 旧逻辑：前端手动 find-or-create
const supplierRes = await suppliersApi.findOrCreate({ ... })
payload.supplier_id = supplierRes.data.id
await purchaseApi.createOnlinePurchase(payload)
```

替换为：

```typescript
// 新逻辑：直接传 platform + supplier_name，后端自动 find-or-create
await purchaseApi.createOnlinePurchase({
  ...payload,
  platform: platform.value,        // '1688' | 'wechat'
  supplier_name: supplierName.value, // 1688 店铺名 或 微信昵称
  shop_link: linkUrl.value || null,
  wechat_id: wechatId.value || null,
  wechat_nickname: wechatNickname.value || null,
  is_dropship: dropshipEnabled.value || false,
  supplier_contact: contactPerson.value || null,
  supplier_phone: supplierPhone.value || null,
})
```

- [ ] **步骤 2：Commit**

```bash
git add frontend/src/components/order/PurchaseDialog.vue
git commit -m "refactor: remove frontend find-or-create, delegate to backend create_online_purchase"
```

---

## 任务 8：CRUD 单元测试

**文件：**
- 新建：`backend/tests/test_supplier_platform.py`

- [ ] **步骤 1：编写 CRUD 单元测试**

```python
"""供应商平台分类 — CRUD 单元测试（ValueError 语义）

CRUD 层是唯一业务校验层：platform 校验 / shop_link 必填 / find-or-create 语义 等
均通过 pytest.raises(ValueError) 验证。
路由层测试见 test_supplier_platform_api.py（断言 HTTP 422）。
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from models import SupSupplier
from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from crud.supplier import (
    create_supplier, update_supplier,
    find_or_create_supplier_by_name,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def insert_supplier(db, request):
    def _insert(supplier_name: str, platform: str | None = None, **kwargs):
        s = SupSupplier(
            supplier_name=supplier_name,
            dept_id=kwargs.get("dept_id", "S"),
            supplier_code=f"SP{kwargs.get('seq', 1):03d}",
            platform=platform,
            shop_link=kwargs.get("shop_link"),
            wechat_id=kwargs.get("wechat_id"),
            wechat_nickname=kwargs.get("wechat_nickname"),
            is_dropship=kwargs.get("is_dropship", False),
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s
    return _insert


# --- create_supplier 平台校验 ---

def test_create_1688_requires_shop_link(db):
    payload = SupplierCreate(supplier_name="1688店", platform="1688")
    with pytest.raises(ValueError, match="店铺链接"):
        create_supplier(db, payload)


def test_create_1688_with_shop_link_ok(db):
    payload = SupplierCreate(supplier_name="1688店", platform="1688", shop_link="https://shop.1688.com")
    s = create_supplier(db, payload)
    assert s.platform == "1688"
    assert s.shop_link == "https://shop.1688.com"


def test_create_wechat_ok_without_shop_link(db):
    payload = SupplierCreate(supplier_name="wx123", platform="wechat")
    s = create_supplier(db, payload)
    assert s.platform == "wechat"
    assert s.shop_link is None


def test_response_includes_platform_fields(db):
    payload = SupplierCreate(supplier_name="wx123", platform="wechat", wechat_nickname="昵称")
    s = create_supplier(db, payload)
    r = SupplierResponse.model_validate(s)
    assert r.platform == "wechat"
    assert r.wechat_nickname == "昵称"


# --- find_or_create 返回值语义 ---

def test_find_or_create_creates_new(db):
    supplier, created = find_or_create_supplier_by_name(
        db, "1688店A", platform="1688", shop_link="https://shop.1688.com"
    )
    assert created is True
    assert supplier.platform == "1688"


def test_find_or_create_hits_existing(db, insert_supplier):
    s1 = insert_supplier("1688店B", platform="1688")
    supplier, created = find_or_create_supplier_by_name(
        db, "1688店B", platform="1688", shop_link="https://new.1688.com"
    )
    assert created is False
    assert supplier.id == s1.id
    assert supplier.shop_link == "https://new.1688.com"  # 已补齐


def test_find_or_create_raises_when_1688_no_shop_link(db, insert_supplier):
    insert_supplier("1688店C", platform="1688", shop_link=None)
    with pytest.raises(ValueError, match="店铺链接"):
        find_or_create_supplier_by_name(db, "1688店C", platform="1688")


def test_find_or_create_raises_on_invalid_platform(db):
    with pytest.raises(ValueError, match="无效"):
        find_or_create_supplier_by_name(db, "任意店", platform="taobao")


# --- update_supplier 平台锁定 ---

def test_update_blocked_when_changing_existing_platform(db, insert_supplier):
    s = insert_supplier("1688店D", platform="1688", shop_link="https://x.com")
    update = SupplierUpdate(platform="wechat")
    with pytest.raises(ValueError, match="不可修改"):
        update_supplier(db, s.id, update)


def test_update_allows_first_time_platform_set(db, insert_supplier):
    s = insert_supplier("历史店", platform=None)
    update = SupplierUpdate(platform="offline")
    result = update_supplier(db, s.id, update)
    assert result.platform == "offline"


# --- 采购单 CRUD 业务校验 ---

def test_purchase_rejects_missing_supplier_id_and_name(db):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import create_online_purchase
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="1688",
        supplier_id=None, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="supplier_id.*supplier_name"):
        create_online_purchase(db, payload)


def test_purchase_rejects_null_platform_supplier(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import create_online_purchase
    s = insert_supplier("历史店", platform=None, seq=1)
    payload = PurchaseCreateOnline(
        dept_id="S", pi_id=1, platform="1688",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="尚未分配平台"):
        create_online_purchase(db, payload)


def test_purchase_rejects_wrong_dept(db, insert_supplier):
    from schemas.purchase import PurchaseCreateOnline
    from crud.purchase import create_online_purchase
    s = insert_supplier("A部门店", platform="1688", dept_id="A", seq=1)
    payload = PurchaseCreateOnline(
        dept_id="B", pi_id=1, platform="1688",
        supplier_id=s.id, supplier_name=None, items=[]
    )
    with pytest.raises(ValueError, match="部门.*不一致"):
        create_online_purchase(db, payload)
```

- [ ] **步骤 2：运行测试验证**

```bash
cd d:/TraeProjects/PI Manager/worktrees/frontend-repo/backend
py -m pytest tests/test_supplier_platform.py -v --tb=short 2>&1 | head -n 80
```
预期：所有用例 PASS（或 FAILED 带清晰错误信息）

- [ ] **步骤 3：Commit**

```bash
git add backend/tests/test_supplier_platform.py
git commit -m "test: add CRUD unit tests for supplier platform validation"
```

---

## 自检清单

1. **覆盖度**：所有 spec 章节有对应任务
   - [x] 数据库迁移（sup_supplier + po_purchase_order） → 任务 1
   - [x] PurchaseCreateOnline schema + PoPurchaseOrder model → 任务 2
   - [x] create_online_purchase CRUD 业务校验 → 任务 3
   - [x] 路由入参改 PurchaseCreateOnline + 移除内联校验块 → 任务 4
   - [x] SupplierFormDialog 改造（复用现有路径） → 任务 5
   - [x] 前端 suppliers.ts 类型 → 任务 6
   - [x] 前端 purchase.ts 类型（新增 PurchaseCreateOnline + createOnlinePurchase） → 任务 6b
   - [x] PurchaseDialog 调用改造 → 任务 7
   - [x] created 响应链确认 → 任务 7b
   - [x] CRUD 单元测试 → 任务 8
   - [x] 接口级测试（已有）→ test_supplier_platform_api.py

2. **占位符扫描**：无 "TODO" / "待定" / "后续实现" 等占位符

3. **P0 问题已修正**：
   - [x] 迁移脚本包含 po_purchase_order 五列
   - [x] 路由入参使用 PurchaseCreateOnline（非旧 PurchaseOrderCreate）
   - [x] SupplierFormDialog 改造现有组件（非在 common/ 新建）
   - [x] purchase.ts 新增 PurchaseCreateOnline 类型

4. **P1 问题已修正**：
   - [x] SupplierFormDialog 校验：`const valid = await formRef.value?.validate().catch(() => false)`
   - [x] created 响应链：路由解包透传，已有确认步骤（任务 7b）
   - [x] 测试文件名：`test_supplier_platform.py`（非 pattern）

5. **类型一致性**：
   - `PurchaseCreateOnline.platform` 为 `Literal['1688', 'wechat', 'offline']`
   - `find_or_create_supplier_by_name` 返回 `tuple[SupSupplier, bool]`
   - `create_online_purchase` 返回 `tuple[list, int | None]`
   - 前端 `SupplierFormPayload.platform` 为 `'1688' | 'wechat' | 'offline'`
   - 前端 `PurchaseCreateOnline.platform` 为 `'1688' | 'wechat' | 'offline'`
