from django.db import models
from fandjango.models import User

class Client(models.Model):
    user = models.ForeignKey(User)
    #interests = models.ManyToManyField('self', through='Interest', symmetrical=False, related_name='interest_in')
    likes = models.CharField(max_length=100, blank=True)
    last_update = models.DateTimeField(null=True, blank=True)
    notified = models.ManyToManyField('self', blank=True, symmetrical=True, related_name='notify')
    last_notified = models.DateTimeField(blank=True)
    first_visit = models.BooleanField(default=True)
    votes = models.IntegerField(max_length=3, default=0)
    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    def less_than_month(self):
        delta = datetime.datetime.now() - self.last_notified
        if delta.days < 30:
            return True
        else:
            return False

class FbookUser(models.Model):
    uid = models.BigIntegerField()
    name = models.CharField(max_length=50)
    def __unicode__(self):
        return self.name

class Like(models.Model):
    client = models.ForeignKey(Client, related_name='likez') 
    like = models.ForeignKey(FbookUser)
    rank = models.IntegerField(max_length=2)
    msg = models.CharField(max_length=500, blank = True)

    def __unicode__(self):
        return '%s likes %s' % (self.client, self.like.name)

STATUS_CHOICES = (
    (1,'Under Consideration'),
    (2,'In Progress'),
    (3,'Completed'),
    (4,'Rejected'),
)


class Suggestion(models.Model):
    client = models.ForeignKey(Client)
    title = models.CharField(max_length=100)
    suggestion = models.CharField(max_length=400)
    votes = models.IntegerField(max_length=4, default=0)
    status = models.IntegerField(max_length=1, choices = STATUS_CHOICES, default = 1)
    dev_comment = models.TextField()

    def __unicode__(self):
        return self.title

class Vote(models.Model):
    suggestion = models.ForeignKey(Suggestion)
    client = models.ForeignKey(Client)
    def __unicode__(self):
        return "%s for '%s'" % (str(self.client), str(self.suggestion))

class MatchStat(models.Model):
    num_matches = models.IntegerField(max_length=7)
    date = models.DateTimeField(auto_now_add=True)


#every client should be able to vote on     
#XXX User selects friends he/she is interested in (if possible) and submits form, the "interest" relationship is formed between that user and the other user (if possible..). Backend checks to see if that person is registered and if the person is, checks to see if the interest is mutual. 

#XXX Use rselects friends from list of ppl who hav app he/she is interested in. (harder to gain traction...). 


# Create your models here.
