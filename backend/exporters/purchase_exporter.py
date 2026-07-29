"""国内采购合同导出器 (PurchaseExporter)
依据采购合同标准模板（上半部分与下半部分）进行 Excel 内容填充
"""

from typing import Dict, Any
from .base_exporter import BaseExporter
from templates import PURCHASE_TEMPLATE
from templates.config import COMPANY_NAME_CN, COMPANY_ADDRESS, CONTRACT_CLAUSES


class PurchaseExporter(BaseExporter):
    """国内采购合同导出器"""

    def __init__(self):
        super().__init__(PURCHASE_TEMPLATE)

    def export_purchase(self, purchase_data: Dict[str, Any]) -> bytes:
        """导出国内采购合同 Excel 二进制流"""
        return self.export(purchase_data)

    def _fill_dynamic_content(self, ws: Any, data: Dict[str, Any]):
        """填充采购合同动态内容"""
        purchase = data.get("purchase", {})
        supplier = data.get("supplier", {})
        user = data.get("user", {})
        items = data.get("items", [])

        # 1. 头部信息
        ws["A1"] = purchase.get("company_name", COMPANY_NAME_CN)
        ws["A2"] = "采 购 合 同"

        # 2. 合同编号和日期
        po_formula = purchase.get("po_no_formula", "供应商编号 + 维那编号 +采购日期 +序号")
        po_no = purchase.get("po_no", purchase.get("pi_no", ""))
        ws["A3"] = f"合同编号  {po_formula}（{po_no}）"
        ws["H3"] = f"合 同 日 期: {self._format_date(purchase.get('order_date') or purchase.get('created_at'))}"

        # 3. 卖方信息
        ws["B5"] = supplier.get("supplier_name", supplier.get("name", ""))
        ws["B6"] = supplier.get("contact_name", supplier.get("contact", ""))
        ws["B7"] = f"{supplier.get('phone', '')}"
        ws["B8"] = supplier.get("address", "")

        # 4. 买方信息
        buyer_data = data.get("buyer", {})
        ws["H5"] = buyer_data.get("name", COMPANY_NAME_CN)
        ws["H6"] = buyer_data.get("contact", user.get("name", "Jacky"))
        ws["H7"] = buyer_data.get("phone", user.get("phone", "18069766520"))
        ws["H8"] = buyer_data.get("address", COMPANY_ADDRESS)

        # 5. 表头 (12 列)
        headers = [
            "图片",
            "维那型号\n客户编号",
            "工厂型号",
            "产品名称",
            "描述",
            "规格/CM",
            "外包装尺寸",
            "数量",
            "单位",
            "净重/毛重",
            "单价（含税）",
            "总金额（含税）",
        ]
        for col, header in enumerate(headers, 1):
            ws.cell(row=9, column=col, value=header)

        # 6. 产品明细行填充
        row = 10
        total_qty = 0
        total_amount = 0.0

        for item in items:
            qty = item.get("quantity", item.get("qty", 0))
            unit_price = item.get("price_including_tax", item.get("unit_price", 0.0))
            amount = qty * unit_price

            weina_code = item.get("weina_code", item.get("code", ""))
            cust_code = item.get("customer_code", "")
            code_cell_val = f"{weina_code}\n{cust_code}" if cust_code else weina_code

            ws.cell(row=row, column=2, value=code_cell_val)
            ws.cell(row=row, column=3, value=item.get("factory_code", ""))
            ws.cell(row=row, column=4, value=item.get("product_name", item.get("name", "")))
            ws.cell(row=row, column=5, value=item.get("detail_requirement", item.get("description", "")))
            ws.cell(row=row, column=6, value=item.get("specification", item.get("spec", "")))
            ws.cell(row=row, column=7, value=item.get("package_size", item.get("pack_size", "")))
            ws.cell(row=row, column=8, value=qty)
            ws.cell(row=row, column=9, value=item.get("unit", "个"))
            ws.cell(row=row, column=10, value=item.get("nw_gw", f"{item.get('net_weight', '')}/{item.get('gross_weight', '')}"))
            ws.cell(row=row, column=11, value=unit_price)
            ws.cell(row=row, column=12, value=amount)

            total_qty += qty
            total_amount += amount
            row += 1

        # 7. 汇总行
        summary_row = max(row, 10 + len(items))
        ws.cell(row=summary_row, column=1, value="总计")
        ws.cell(row=summary_row, column=8, value=total_qty)
        ws.cell(row=summary_row, column=12, value=total_amount)

        # 8. 约定事项与交货方式
        ws.cell(row=summary_row + 1, column=1, value="产品要求")
        ws.cell(row=summary_row + 1, column=2, value=purchase.get("product_requirement", "无褶皱，清洁无线头，无银光笔笔痕，logo不能倾斜，正确区分青蛙托坐垫跟蝴蝶托坐垫"))

        ws.cell(row=summary_row + 2, column=1, value="包装要求")
        ws.cell(row=summary_row + 2, column=2, value=purchase.get("package_requirement", "300磅五层双瓦纸箱，内加EPE打包方式"))

        ws.cell(row=summary_row + 3, column=1, value="交货日期")
        ws.cell(row=summary_row + 3, column=2, value=self._format_date(purchase.get("delivery_date", "2025/05/18日前")))

        ws.cell(row=summary_row + 4, column=1, value="交货地址")
        ws.cell(row=summary_row + 4, column=2, value=purchase.get("delivery_address", "送到买方指定仓库（卖方负责运输费用）"))

        ws.cell(row=summary_row + 5, column=1, value="供应商收款名称")
        ws.cell(row=summary_row + 5, column=2, value=purchase.get("supplier_bank_name", supplier.get("supplier_name", "")))
        ws.cell(row=summary_row + 5, column=7, value="收货联系人")
        ws.cell(row=summary_row + 5, column=8, value=purchase.get("receiver_contact", user.get("name", "Jacky")))

        ws.cell(row=summary_row + 6, column=1, value="开发行及账号")
        ws.cell(row=summary_row + 6, column=2, value=purchase.get("supplier_bank_account", f"{supplier.get('bank_name', '')} {supplier.get('bank_account', '')}"))
        ws.cell(row=summary_row + 6, column=7, value="联系电话")
        ws.cell(row=summary_row + 6, column=8, value=purchase.get("receiver_phone", user.get("phone", "18857325120")))

        ws.cell(row=summary_row + 7, column=1, value="付款方式")
        ws.cell(row=summary_row + 7, column=2, value=purchase.get("payment_method", "下好订单，卖方确认合同盖章后付预付款；预付款30%，剩余款装货前付清"))

        ws.cell(row=summary_row + 8, column=1, value="备注")
        ws.cell(row=summary_row + 8, column=2, value=purchase.get("remarks", ""))

        # 9. 4 条标准合同条款
        clause_start_row = summary_row + 10
        ws.cell(row=clause_start_row, column=1, value="合同条款：")
        clauses = purchase.get("clauses", CONTRACT_CLAUSES)
        for idx, clause in enumerate(clauses):
            ws.cell(row=clause_start_row + 1 + idx, column=1, value=clause)

        # 10. 底部双框印章落款
        sig_start_row = clause_start_row + 2 + len(clauses)
        ws.cell(row=sig_start_row, column=1, value=f"卖方：{supplier.get('supplier_name', supplier.get('name', ''))}")
        ws.cell(row=sig_start_row, column=7, value=f"买方：{buyer_data.get('name', COMPANY_NAME_CN)}")

        ws.cell(row=sig_start_row + 1, column=1, value="单位名称(公章)：")
        ws.cell(row=sig_start_row + 1, column=7, value="单位名称(公章)：")

        ws.cell(row=sig_start_row + 2, column=1, value=f"单位地址：{supplier.get('address', '')}")
        ws.cell(row=sig_start_row + 2, column=7, value=f"单位地址：{buyer_data.get('address', COMPANY_ADDRESS)}")

        ws.cell(row=sig_start_row + 3, column=1, value=f"联系人：{supplier.get('contact_name', supplier.get('contact', ''))}")
        ws.cell(row=sig_start_row + 3, column=7, value=f"联系人：{buyer_data.get('contact', '李荣军')}")

        ws.cell(row=sig_start_row + 4, column=1, value=f"电话：{supplier.get('phone', '')}")
        ws.cell(row=sig_start_row + 4, column=7, value=f"电话：{buyer_data.get('phone', '0571-86131966')}")

    def _format_date(self, date_value: Any) -> str:
        """格式化日期为 YYYY/MM/DD"""
        if hasattr(date_value, "strftime"):
            return date_value.strftime("%Y/%m/%d")
        return str(date_value) if date_value else ""