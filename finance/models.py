from django.db import models
from core.models import User

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