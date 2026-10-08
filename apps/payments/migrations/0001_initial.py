import django.db.models.deletion
from django.db import migrations,models

class Migration(migrations.Migration):
    initial=True
    dependencies=[("orders","0001_initial")]
    operations=[
      migrations.CreateModel(name="Payment",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("provider",models.CharField(choices=[("paystack","Paystack"),("flutterwave","Flutterwave")],max_length=16)),("reference",models.CharField(max_length=64,unique=True)),("amount_minor",models.PositiveBigIntegerField()),("currency",models.CharField(default="NGN",max_length=3)),("status",models.CharField(choices=[("pending","Pending"),("succeeded","Succeeded"),("failed","Failed"),("refund_required","Refund required")],default="pending",max_length=24)),("checkout_url",models.URLField(blank=True,max_length=600)),("provider_transaction_id",models.CharField(blank=True,max_length=80)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),("order",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="payments",to="orders.order"))],options={"ordering":["-created_at"]}),
      migrations.CreateModel(name="WebhookEvent",fields=[("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),("provider",models.CharField(choices=[("paystack","Paystack"),("flutterwave","Flutterwave")],max_length=16)),("event_key",models.CharField(max_length=180)),("event_type",models.CharField(blank=True,max_length=80)),("received_at",models.DateTimeField(auto_now_add=True)),("processed_at",models.DateTimeField(blank=True,null=True)),("payment",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="webhook_events",to="payments.payment"))]),
      migrations.AddConstraint(model_name="webhookevent",constraint=models.UniqueConstraint(fields=("provider","event_key"),name="unique_provider_webhook_event")),
    ]
