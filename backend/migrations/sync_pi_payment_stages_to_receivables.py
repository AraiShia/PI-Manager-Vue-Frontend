"""同步历史 PI 付款分期到客户收款记录

将旧接口写入的 pi_payment_stage(status=2) 补建到 ar_customer_payment，
让历史付款能在收款管理页面展示。

可重复执行：脚本会按 pi_id + 金额 + 付款日期检查是否已有对应收款记录。
"""

import os
import sys
from datetime import datetime, time
from decimal import Decimal


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal
from crud.payment import update_pi_payment_status
from models import ArCustomerPayment, PiPaymentStage, PiProformaInvoice
from utils.number_generator import NumberGenerator


def _stage_payment_date(stage: PiPaymentStage) -> datetime:
    paid_date = stage.paid_date or stage.created_at or datetime.utcnow()
    if isinstance(paid_date, datetime):
        return paid_date
    return datetime.combine(paid_date, time.min)


def _amount_equal(left, right) -> bool:
    return Decimal(str(left or 0)).quantize(Decimal("0.0001")) == Decimal(str(right or 0)).quantize(Decimal("0.0001"))


def _payment_exists(db, stage: PiPaymentStage, payment_date: datetime) -> bool:
    existing = db.query(ArCustomerPayment).filter(
        ArCustomerPayment.pi_id == stage.pi_id,
        ArCustomerPayment.payment_date == payment_date,
    ).all()
    return any(
        _amount_equal(payment.actual_amount or payment.amount, stage.amount)
        for payment in existing
    )


def upgrade(dry_run: bool = False) -> dict:
    db = SessionLocal()
    created = 0
    skipped = 0
    missing_pi = 0
    affected_pi_ids = set()

    try:
        stages = db.query(PiPaymentStage).filter(PiPaymentStage.status == 2).order_by(
            PiPaymentStage.pi_id.asc(),
            PiPaymentStage.stage_no.asc(),
            PiPaymentStage.id.asc(),
        ).all()

        for stage in stages:
            pi = db.query(PiProformaInvoice).filter(PiProformaInvoice.id == stage.pi_id).first()
            if not pi:
                missing_pi += 1
                continue

            payment_date = _stage_payment_date(stage)
            if _payment_exists(db, stage, payment_date):
                skipped += 1
                continue

            if dry_run:
                created += 1
                continue

            amount = stage.amount or 0
            db.add(ArCustomerPayment(
                dept_id=pi.dept_id,
                receipt_no=NumberGenerator.generate_receipt_no(db, pi.dept_id),
                pi_id=pi.id,
                customer_id=pi.customer_id,
                amount=amount,
                handling_fee=0,
                actual_amount=amount,
                is_fully_paid=False,
                payment_date=payment_date,
                payment_method="",
                remark=f"由历史付款分期同步，stage_id={stage.id}",
            ))
            created += 1
            affected_pi_ids.add(pi.id)

        if dry_run:
            db.rollback()
        else:
            db.commit()
            for pi_id in affected_pi_ids:
                update_pi_payment_status(db, pi_id)

        result = {
            "created": created,
            "skipped": skipped,
            "missing_pi": missing_pi,
            "total_stages": len(stages),
            "dry_run": dry_run,
        }
        print(result)
        return result
    finally:
        db.close()


if __name__ == "__main__":
    upgrade(dry_run="--dry-run" in sys.argv)
