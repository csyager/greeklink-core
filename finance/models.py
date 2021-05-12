from django.db import models
from core.models import User
from django.utils import timezone
import datetime

# Create your models here.

class Transaction(models.Model):
    """ Represents a request for payment from a group of users.
        For example, could be a request for one semesters dues
    """
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    due_date = models.DateField()
    amount = models.FloatField()

    # restricts amount to 2 decimal places, regardless of what is entered in form
    def save(self, *args, **kwargs):
        self.amount = round(self.amount, 2)
        super(Transaction, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    
class TransactionUserRelation(models.Model):
    """ Represents a relationship between a user and a transaction
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="transaction_user_list")
    amount_paid = models.IntegerField(default=0)


class PaymentEvent(models.Model):
    """ Represents a payment being made either to or from the budget
    """
    description = models.CharField(max_length=50)
    date = models.DateField(default=timezone.now)
    amount = models.FloatField()
    is_cost = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.amount = round(self.amount, 2)
        super(PaymentEvent, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.description

class BudgetLineItem(models.Model):
    """
        Either a cost or revenue, represents a single entry in a budget
        Can be linked to a Transaction
    """
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, blank=True, null=True, related_name="transaction_line_item")
    name = models.CharField(max_length=50)
    is_cost = models.BooleanField()
    description = models.CharField(max_length=500)
    due_date = models.DateField(blank=True, null=True)
    amount = models.FloatField()
    created_date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.transaction is not None and self.pk is None:
            self.name = self.transaction.name
            self.is_cost = False
            self.description = self.transaction.description
            self.due_date = self.transaction.due_date
            self.amount = self.transaction.amount
            super(BudgetLineItem, self).save(*args, **kwargs)
        
        else:
            self.amount = round(self.amount, 2)
            super(BudgetLineItem, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name