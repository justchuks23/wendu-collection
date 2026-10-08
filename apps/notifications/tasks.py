from celery import shared_task


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def release_expired_order_reservations(self):
    from apps.orders.services import expire_pending_orders

    return expire_pending_orders()
