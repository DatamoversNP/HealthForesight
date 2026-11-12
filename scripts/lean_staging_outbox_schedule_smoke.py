#!/usr/bin/env python3
"""Lean staging smoke: outbox→Service Bus + schedule claim/cancel/recovery.

Uses staging DATABASE_URL + AZURE_SERVICE_BUS_CONNECTION_STRING only.
Never points at healthforesight-rg / demo DB / demo Redis.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "common" / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from uepi_api.models.scheduling import JobSchedule, JobScheduleOccurrence
from uepi_api.services.execution.outbox import (
    AnalyticalJob,
    JobOutbox,
    OutboxStatus,
    create_job_with_outbox,
)
from uepi_api.services.execution.outbox_relay import drain_pending_outbox
from uepi_api.services.execution.schedule_dispatcher import claim_due_occurrences


def _require_env(*keys: str) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"Missing env: {', '.join(missing)}")


def main() -> None:
    _require_env("DATABASE_URL", "AZURE_SERVICE_BUS_CONNECTION_STRING")
    db_url = os.environ["DATABASE_URL"]
    if "healthforesight-db" in db_url or "healthforesight-rg" in db_url:
        raise SystemExit("Refusing demo DATABASE_URL")
    sb = os.environ["AZURE_SERVICE_BUS_CONNECTION_STRING"]
    if "hfleanstg-bus" not in sb:
        raise SystemExit("Refusing non-staging Service Bus connection string")

    os.environ["ENABLE_ENTERPRISE_SCHEDULER"] = "true"

    engine = create_engine(db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    results = {}

    tenant_id = uuid.uuid4()
    job_id = f"aj_smoke_{uuid.uuid4().hex[:16]}"
    idem = f"idem_smoke_{uuid.uuid4().hex[:16]}"

    with Session() as db:
        create_job_with_outbox(
            db,
            job_id=job_id,
            tenant_id=tenant_id,
            job_type="lean_staging_smoke",
            workload_class="ASYNC_COHORT",
            idempotency_key=idem,
            destination="service_bus",
            payload={
                "job_id": job_id,
                "workload_class": "ASYNC_COHORT",
                "idempotency_key": idem,
                "configuration_digest": "lean-smoke",
                "payload_inline": {"pathway": "PROVENANCE_ONLY"},
            },
            configuration_digest="lean-smoke",
        )
        db.commit()
        drain = drain_pending_outbox(db, limit=20)
        results["outbox_drain"] = drain
        job = db.query(AnalyticalJob).filter(AnalyticalJob.job_id == job_id).one()
        outbox = db.query(JobOutbox).filter(JobOutbox.job_id == job_id).one()
        results["job_status"] = job.status
        results["outbox_status"] = outbox.status
        assert outbox.status == OutboxStatus.PUBLISHED.value, outbox.last_error
        assert job.status == "QUEUED"
        results["outbox_sb"] = "PASS"

    # Receive the message from staging SB to prove dispatch
    from azure.servicebus import ServiceBusClient

    with ServiceBusClient.from_connection_string(sb) as client:
        with client.get_queue_receiver("policy-analytics", max_wait_time=20) as receiver:
            msgs = list(receiver.receive_messages(max_message_count=5, max_wait_time=20))
            matched = []
            for m in msgs:
                raw = b"".join(m.body) if not isinstance(m.body, (bytes, str)) else m.body
                text = raw.decode() if isinstance(raw, (bytes, bytearray)) else str(raw)
                if job_id in text:
                    matched.append(m)
                receiver.complete_message(m)
            assert matched, f"no Service Bus message containing {job_id}; got {len(msgs)} msgs"
            results["sb_receive"] = "PASS"

    # Schedule claim + cancel + recovery
    schedule_id = f"sch_smoke_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with Session() as db:
        sched = JobSchedule(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
            job_type="lean_staging_smoke",
            target_reference="policy:smoke",
            schedule_expression="0 0 * * *",
            timezone="UTC",
            enabled=True,
            trigger_kind="CALENDAR",
            next_due_at=now - timedelta(minutes=1),
            misfire_policy="FIRE_ONCE",
            overlap_policy="SKIP",
            configuration_version="v1",
            workload_class="OBSERVATION",
        )
        db.add(sched)
        db.commit()

        created = claim_due_occurrences(db, now=now, limit=10)
        db.commit()
        assert created, "expected at least one occurrence"
        occ = created[0]
        results["occurrence_status"] = occ.status
        assert occ.status == "SCHEDULED"
        results["schedule_claim"] = "PASS"

        # cancel
        occ.status = "CANCELLED"
        occ.error_message = "lean-smoke-cancel"
        db.commit()
        cancelled = (
            db.query(JobScheduleOccurrence)
            .filter(JobScheduleOccurrence.occurrence_id == occ.occurrence_id)
            .one()
        )
        assert cancelled.status == "CANCELLED"
        results["schedule_cancel"] = "PASS"

        # recovery: re-enable due and claim new occurrence key after next_due bump
        sched = db.query(JobSchedule).filter(JobSchedule.schedule_id == schedule_id).one()
        # claim_due already advanced next_due by 1 day; pull it back for recovery tick
        sched.enabled = True
        sched.next_due_at = now - timedelta(seconds=30)
        db.commit()
        recovered = claim_due_occurrences(db, now=now, limit=10)
        db.commit()
        assert recovered, "expected recovery occurrence"
        assert recovered[0].occurrence_id != occ.occurrence_id
        results["schedule_recovery"] = "PASS"

        # disable schedule to avoid future hot loops
        sched = db.query(JobSchedule).filter(JobSchedule.schedule_id == schedule_id).one()
        sched.enabled = False
        db.commit()

    print("LEAN_STAGING_SMOKE", results)


if __name__ == "__main__":
    main()
