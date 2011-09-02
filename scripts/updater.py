import logging
import memcache
import sys
import time
from datetime import datetime, timedelta

from django.core.management import setup_environ
sys.path.append('/srv/www')
sys.path.append('/srv/www/wootmatch')
from django.db.models import Q
from django.conf import settings
setup_environ(settings)

from wootmatch.fbook.models import Client, Like, MatchStat
from mailer import send_mail

logger = logging.getLogger()
cache = memcache.Client(['127.0.0.1:11211'])
SUBJECT = "You have a match on LikeEachOther!"
BODY = "Your match is: %s. Good luck!"
BODY2 = "Your match is: %s. \nYour match %s says: %s"

def global_update():
    cache.set('updates_allowed','0')
    #time.sleep(5*15)
    latest = datetime.now() - timedelta(days=30)
    clients = Client.objects.filter(Q(last_notified__lt = latest) | Q(last_notified = None))
    count = Client.objects.filter(Q(last_notified__lt = latest) | Q(last_notified = None)).count()
    logger.info('Got %s eligible clients.' % count)
    matches=[]
    for client in clients:
        #check for matches
        logger.info('Checking Client: %s' % str(Client))
        for like in client.likez.all():
            try:
                cl = Client.objects.get(user__facebook_id = like.like.uid) #XXX check this
                logger.info('liked person is a Client')
            except Client.DoesNotExist:
                logger.info('liked person is not a Client, going to next liked person.')
                continue
            try:
                l = Like.objects.get(client=cl, like__uid = client.user.facebook_id)
                logger.info('liked person likes back!')
            except Like.DoesNotExist: #person doesn't liek back
                logger.info('likes person does not like back, going to next liked person')
                continue
            #person likes client back
            #calculate strength
            strength = like.rank * like.rank + l.rank * l.rank 
            logger.info('strength is %s' % strength)
            if cl.user.facebook_id < client.user.facebook_id:
                if (cl,client,strength) in matches: #check for duplicates
                    logger.info('duplicate, moving to next liked person')
                    continue
                else:
                    logger.info('added this match to matches list.')
                    matches.append((cl,client,strength)) 
            else:
                if (client,cl,strength) in matches: #check for duplicates
                    logger.info('duplicate, moving to next liked person')
                    continue
                else:
                    matches.append((client,cl,strength))
                    logger.info('added this match to matches list.')
    matches.sort(key=lambda tup: tup[2])
    stat = MatchStat(num_matches = len(matches))
    stat.save()
    #all possible matches are sorted by strength
    emailed_ids= [] #list of uids that were mailed.
    logger.info('Matches are sorted and there are %s matches.' % len(matches))
    for match in matches:
        #if either person in the match is in the emailed matches list, continue
        client1 = match[0]
        client2 = match[1]
        if client1.user.facebook_id in emailed_ids or client2.user.facebook_id in emailed_ids:
            logger.info('skipping because this person already was sent a match.') 
            continue
        else:#else send email to both in the match
            like=Like.objects.get(client=client1, like__uid = client2.user.facebook_id)
            if like.msg:
                body = BODY2 % (str(client1), str(client1), like.msg)
            else:
                body = BODY % str(client1)
            send_mail(SUBJECT, body, settings.DEFAULT_FROM_EMAIL, [client2.user.email])
            logger.info('Sent mail to Q.')
            like2=Like.objects.get(client=client2, like__uid = client1.user.facebook_id)
            if like2.msg:
                body = BODY2 % (str(client2), str(client2), like2.msg)
            else:
                body = BODY % str(client2)
            send_mail(SUBJECT, body, settings.DEFAULT_FROM_EMAIL, [client1.user.email])
            logger.info('sent mail to Q.')
            now = datetime.now()
            client1.last_notified = now
            client2.last_notified = now
            client2.save()
            client1.notified.add(client2)
            client1.save()
            logger.info('client.notified updated for both.')
            emailed_ids.append(match[0].user.facebook_id)
            logger.info('added client id to emailed_ids list.')
            emailed_ids.append(match[1].user.facebook_id)
            logger.info('added client id to emailed_ids list.')
    cache.set('updates_allowed','1')

if __name__ == '__main__':
    global_update() 
