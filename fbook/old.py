from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from settings import FACEBOOK_APPLICATION_ID, DEFAULT_FROM_EMAIL,FACEBOOK_APPLICATION_SECRET_KEY
from fandjango.decorators import facebook_authorization_required
from fandjango.utils import parse_signed_request
from fandjango.models import User
import sys, requests
from facepy.graph_api import GraphAPI
from urllib import urlretrieve
import json
from likeeachother.fbook.models import Client, FbookUser, Like
from datetime import datetime
from mailer import send_mail
from random import choice
from datetime import datetime, timedelta
import logging
logger = logging.getLogger()


SUB_QUERY="SELECT uid, name, pic_square FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) and sex = '%s'"
QUERY2 = "SELECT name FROM user WHERE uid IN (%s)"
SUBJECT = "You have a match on LikeEachOther!"
BODY = "Your match is: %s. Good luck!"
UPDATES_ALLOWED = True

def get_client(request):
    try:
        client = Client.objects.get(user = request.facebook.user)
        logger.info('Client %s retrieved.', str(client))
    except Client.DoesNotExist:
        client = Client.objects.create(user = request.facebook.user)
        logger.info('Client %s created.', str(client))
    return client

@facebook_authorization_required()
def canvas(request):
    client = get_client(request)
    if request.facebook.user.gender[0]=='m':
        opp_gender = 'female'
    else:
        opp_gender = 'male'
    QUERY = SUB_QUERY % opp_gender
    authorized = request.facebook.user.authorized    
    #see if there are matches, if so, show ONE MATCH
    likes = client.likez.all().order_by('rank')
    num_likes = len(likes)
    #    return HttpResponse(str(num_likes))
    logger.info('Client likes %s people.', str(num_likes))
    liked_clients = [like.like.uid for like in likes]
    notified = client.notified.all()
    logger.info('Got all notified clients of current Client')
    has_app=[]
    if likes: #see who has app and whether there are matches
        for like in likes:
            try:
                c = Client.objects.get(user__facebook_id = like.like.uid)
                logger.info('Got the Client object for Fbookuser with uid: %s', like.like.uid)
                has_app.append(True)
            except Client.DoesNotExist:
                logging.info('Client object does not exist for Fbookuser with uid: %s', like.like.uid)
                has_app.append(False)
            except:
                logging.warning('Unhandled exception when attempting to retrieve Client with uid: %s' % like.like.uid, exc_info=sys.exc_info())
    else:
        logger.info('There are no Likes (Client does not like anyone)')
    likes_tup = zip(likes,has_app)
    return direct_to_template(request, 'sync.html', {'authorized':authorized,'likes_tup':likes_tup, 'email':request.facebook.user.email, 'num_likes':num_likes, 'query':QUERY, 'app_id':FACEBOOK_APPLICATION_ID})

@facebook_authorization_required()
@csrf_exempt
def update_matches(request): # AJAX CALL
    client = get_client(request)
    likes = client.likez.all().order_by('rank')
    matches=[]
    matched_clients=[]
    has_app=[]
    match_strength=[]
    if likes: #see who has app and whether there are matches
        for like in likes:
            try:
                c = Client.objects.get(user__facebook_id = like.like.uid)
                logger.info('Got the Client object for Fbookuser with uid: %s', like.like.uid)
                if c.last_notified and c.less_than_month():
                    logging.info('Liked Client was notified less than one month ago, skipping for match candidate.')
                    continue
                else:
                    logging.info('Liked Client has not been notified for at least 30 days and is eligible for match (but may not be a match.')
                    pass
                try:
                    logger.info('Checking to see if the person Client likes likes the Client back.')
                    l=Like.objects.get(client=c, like__uid = request.facebook.user.facebook_id) 
                    logger.info('Liked Client likes current Client back')
                    #calc like strength:
                    strength = like.rank*like.rank + l.rank*l.rank 
                    match_strength.append(strength)
                    matches.append(c.user.facebook_id)
                    matched_clients.append(c)
                    logger.info('Added Liked Client to matched list.')
                except Like.DoesNotExist:
                    logger.info('Like Client does not like current Client back')
                    pass
            except Client.DoesNotExist:
                logging.info('Client object does not exist for Fbookuser with uid: %s', like.like.uid)
            except:
                logging.warning('Unhandled exception when attempting to retrieve Client with uid: %s' % like.like.uid, exc_info=sys.exc_info())
    else:
        logger.info('There are no Likes (Client does not like anyone)')
    if matches: # get all matches first, then in the order of who is liked, check if person in the matches.
        best_strength = min(match_strength)
        indeces = [i for i, value in enumerate(match_strength) if value == best_strength]
        if len(indeces) > 1:
            index = choice(indeces)    
        else:
            index = indeces[0]
        matched_client = matched_clients[index]
        matched_client.last_notified = datetime.now()
        matched_client.save()
        send_mail(SUBJECT, BODY % str(matched_client), DEFAULT_FROM_EMAIL, [client.user.email])
        send_mail(SUBJECT, BODY % str(client), DEFAULT_FROM_EMAIL, [matched_client.user.email])
        client.notified.add(matched_client)
        client.save() 
        return HttpResponse('You have a match! You were both notified via email!')
    return HttpResponse('No match.')

@facebook_authorization_required()
def canvas_2(request):
    client = get_client(request)
    if request.facebook.user.gender[0]=='m':
        opp_gender = 'female'
    else:
        opp_gender = 'male'
    QUERY = SUB_QUERY % opp_gender
    authorized = request.facebook.user.authorized    
    #see if there are matches, if so, show ONE MATCH
    likes = client.likez.all().order_by('rank')
    num_likes = len(likes)
    #    return HttpResponse(str(num_likes))
    logger.info('Client likes %s people.', str(num_likes))
    logger.info('Got all Likes for client ordered by rank.')
    liked_clients = [like.like.uid for like in likes]
    notified = client.notified.all()
    logger.info('Got all notified clients of current Client')
    matches=[]
    matched_clients=[]
    has_app=[]
    match_strength=[]
    if likes: #see who has app and whether there are matches
        for like in likes:
            try:
                c = Client.objects.get(user__facebook_id = like.like.uid)
                logger.info('Got the Client object for Fbookuser with uid: %s', like.like.uid)
                has_app.append(True)
                if c.last_notified and c.less_than_month():
                    logging.info('Liked Client was notified less than one month ago, skipping for match candidate.')
                    continue
                else:
                    logging.info('Liked Client has not been notified for at least 30 days and is eligible for match (but may not be a match.')
                    pass
                try:
                    logger.info('Checking to see if the person Client likes likes the Client back.')
                    l=Like.objects.get(client=c, like__uid = request.facebook.user.facebook_id) 
                    logger.info('Liked Client likes current Client back')
                    #calc like strength:
                    strength = like.rank*like.rank + l.rank*l.rank 
                    match_strength.append(strength)
                    matches.append(c.user.facebook_id)
                    matched_clients.append(c)
                    logger.info('Added Liked Client to matched list.')
                except Like.DoesNotExist:
                    logger.info('Like Client does not like current Client back')
                    pass
            except Client.DoesNotExist:
                logging.info('Client object does not exist for Fbookuser with uid: %s', like.like.uid)
                has_app.append(False)
            except:
                logging.warning('Unhandled exception when attempting to retrieve Client with uid: %s' % like.like.uid, exc_info=sys.exc_info())
    else:
        logger.info('There are no Likes (Client does not like anyone)')
    if matches: # get all matches first, then in the order of who is liked, check if person in the matches.
        best_strength = min(match_strength)
        indeces = [i for i, value in enumerate(match_strength) if value == best_strength]
        if len(indeces) > 1:
            index = choice(indeces)    
        else:
            index = indeces[0]
        matched_client = matched_clients[index]
        send_mail(SUBJECT, BODY % str(matched_client), DEFAULT_FROM_EMAIL, [client.user.email])
        send_mail(SUBJECT, BODY % str(client), DEFAULT_FROM_EMAIL, [matched_client.user.email])
        client.notified.add(matched_client)
        client.save() 
    likes_tup = zip(likes,has_app)
    return direct_to_template(request, 'sync.html', {'authorized':authorized,'likes_tup':likes_tup, 'email':request.facebook.user.email, 'num_likes':num_likes, 'query':QUERY, 'app_id':FACEBOOK_APPLICATION_ID})

@facebook_authorization_required()
@csrf_exempt
def add_person(request):
    global_matching_check()
    if request.method=="POST" and 'add_like_uid' in request.POST and 'add_like_name' in request.POST: #and 'rank' in request.POST:
        client = get_client(request)
        uid=request.POST.get('add_like_uid')
        rank_str = request.POST.get('rank')
        name = request.POST.get('add_like_name')
        if uid == '' or uid == 'undefined':
            return HttpResponse('uid error')
        try:
            rank = int(rank_str)
        except:
            return HttpResponse('rank error')
        try:
            user = FbookUser.objects.get(uid = uid)
        except FbookUser.DoesNotExist:
            user = FbookUser.objects.create(uid = uid, name = name)
        try: #check if that person is already liked by the current client
            l=Like.objects.get(client=client, like=user)
            # no django users yet...request.user.message_set.create(message = 'You already like that person')
            return HttpResponse('you already like that person')
        except Like.DoesNotExist:
            Like.objects.create(client=client, like=user, rank=rank)#int(request.POST.get('rank')))
        # check if liked person has app:
        try:
            Client.objects.get(user__facebook_id = int(uid))
            has_app = 'yes'
        except Client.DoesNotExist:
            has_app = 'no'
        except:
            has_app = 'no'
            logger.error('Check this!', exc_info=sys.exc_info())
        #return HttpResponse('ok')
        #return a row containing name, rank and app stsatus
        row = """<tr id="%s"><td>%s</td><td></td><td>%s</td><td><a href="#tbl1" class="myButton" onclick="return removePerson('%s')">Remove</a></td></tr>""" % (uid,name,has_app,uid)
        return HttpResponse(row)
    else:
        logger.warning('Bad POST Request')
        return HttpResponse('POST Error')

def global_matching_check():
    if UPDATES_ALLOWED:
        pass
    else:
        return direct_to_template(request, '', {})

@facebook_authorization_required()
@csrf_exempt
def remove_person(request):
    global_matching_check()
    if request.method == 'POST' and 'remove' in request.POST:
        uid = request.POST.get('remove') # should be a string
        try:
            l = Like.objects.get(like__uid=int(uid))
            l.delete()
            msg = 'ok'
        except Like.DoesNotExist:
            msg = 'Like Does Not Exist'
    else:
            logger.warning('Bad POST request')
            msg = 'error'
    return HttpResponse(msg)

    
@facebook_authorization_required()
@csrf_exempt
def update_rank(request):
    global_matching_check()
    if request.method == 'POST' and 'rank_order' in request.POST:
        ranks = request.POST.get('rank_order').split('.')[0:-1]
        #return HttpResponse(ranks)
        for i, uid in enumerate(ranks):
            try:
                l=Like.objects.get(like__uid=int(uid))
            except:
                raise Http404
            l.rank = i+1
            l.save() 
        return HttpResponse('ok')
    else:
        logger.warning('Bad POST request')
        return HttpResponse('error')

def global_update():
    UPDATES_ALLOWED = False
    all_clients=Client.objects.all()
    latest = datetime.now() - timedelta(days=30)
    clients = Client.objects.filter(last_notified__lte = latest)
    matches=[]
    for client in clients:
        #check for matches
        for like in client.likez.all():
            try:
                cl = Client.objects.get(user__facebook_id = like.like.uid) #XXX check this
            except Client.DoesNotExist:
                continue
            try:
                l = Like.objects.get(client=cl, like__uid = client.user.facebook_id)
            except Like.DoesNotExist: #person doesn't liek back
                continue
            #person likes client back
            #calculate strength
            strength = like.rank*like.rank + l.rank*l.rank 
            if cl.user.facebook_id < client.user.facebook_id:
                if (cl,client,strength) in matches: #check for duplicates
                    continue
                else:
                    matches.append((cl,client,strength)) 
            else:
                if (client,cl,strength) in matches: #check for duplicates
                    continue
                else:
                    matches.append((client,cl,strength))
    matches.sort(key=lambda tup: tup[2])
    #all possible matches are sorted by strength
    emailed_ids= [] #list of uids that were mailed.
    for match in matches:
        #if either person in the match is in the emailed matches list, continue
        client1 = match[0]
        client2 = match[1]
        if client1.user.facebook_id in emailed_matches or client2.user.facebook_id in emailed_matches:
            continue
        else:#else send email to both in the match
            send_mail(SUBJECT, BODY % str(client1), DEFAULT_FROM_EMAIL, [client2.user.email])
            send_mail(SUBJECT, BODY % str(client2), DEFAULT_FROM_EMAIL, [client1.user.email])
            client1.notified.add(client2)
            client1.save()
            emailed_ids.append(match[0].user.facebook_id)
            emailed_ids.append(match[1].user.facebook_id)
    UPDATES_ALLOWED = True

def deauthorize_application(request):
    """
    When a user deauthorizes an application, Facebook sends a HTTP POST request to the application's
    "deauthorization callback" URL. This view picks up on requests of this sort and marks the corresponding
    users as unauthorized.
    """
    logger.info("attempting to deauthorize app for user")
    data = parse_signed_request(request.POST['signed_request'], FACEBOOK_APPLICATION_SECRET_KEY)

    user = User.objects.get(facebook_id=data['user_id'])
    user.authorized = False
    user.save()
    logger.info("user deauthorized app.")
    client = Client.objects.get(user=user) 
    client.delete()
    logging.info('deleted client')
    return HttpResponse()

@facebook_authorization_required()
def delete_account(request):
    if request.method == "POST":
        client = get_client(request)
        client.delete()
    return direct_to_template(request, 'deleted_account.html')

@facebook_authorization_required()
def canvas2(request):
    message=''
    try:
        client = Client.objects.get(user = request.facebook.user)
    except Client.DoesNotExist:
        client = Client.objects.create(user = request.facebook.user)
    token=request.facebook.user.graph.oauth_token
    if request.facebook.user.gender[0]=='m':
        opp_gender = 'female'
    else:
        opp_gender = 'male'
    QUERY = SUB_QUERY % opp_gender 
    max=False
    likes=''
    if client.likes:
        likes=client.likes[0:-1]
        if len(likes.split(','))>4:
            max = True
    if request.method=="POST" and 'intz' in request.POST:
        if max:
            message="You already like the maximum number of people"
        else:
            x=request.POST.get('intz')        
            if x == '':
                message = 'must have valid value'
            elif x== 'undefined':
                message = 'please retry'
            elif x in client.likes:
                message='you already like that person'
            else:
                client.likes += x+','
                client.save()
                likes=client.likes[0:-1]
    return direct_to_template(request, 'main.html',{'email':request.facebook.user.email, 'last_update':client.last_update,'message':message, 'max':max, 'likeslist':likes, 'token':token, 'app_id':FACEBOOK_APPLICATION_ID, 'query':QUERY})

@facebook_authorization_required()
def change_email(request):
    """docstring for change_email"""
    if request.method == "POST":
        try:
            new_email = request.POST.get('email') 
        except:
            return HttpResponse('no email was set')
        request.facebook.user.email = new_email
        request.facebook.user.save()
        return HttpResponseRedirect(reverse('canvas'))

@facebook_authorization_required()
@csrf_exempt
def update_matches_orig(request):
    #get useres likes, for each like ,check if that persons likes have users id in it.
    try:
        client=Client.objects.get(user = request.facebook.user)
    except:
        return HttpResponse('you are not a client!')
    likes=client.likes[0:-1].split(',')
    matches=[]
    has_app=[]
    notified = client.notified.all()
    for person in likes:
        try:
            other = Client.objects.get(user__facebook_id = person)
            has_app.append(person)
            if str(request.facebook.user.facebook_id) in other.likes.split(','):
                matches.append(person)
                if other not in notified:
                    send_mail(SUBJECT, BODY % other, DEFAULT_FROM_EMAIL, [other.user.email, client.user.email])
                    client.notified.add(other)
        except Client.DoesNotExist:
            pass
    client.last_update=datetime.now()
    client.save()
    return HttpResponse(json.dumps({'matches':matches, 'has_app':has_app}), mimetype='application/javascript')
  
@facebook_authorization_required()
def remove(request):
    if request.method=="POST" and 'remove' in request.POST:
#        return HttpResponse(request.POST.get('remove'))
        try:
            client = Client.objects.get(user = request.facebook.user)
        except Client.DoesNotExist:
            return HttpResponse('uh oh')
        fbookid = request.POST.get('remove')
        client.likes = client.likes.replace(fbookid+',','')
        client.save()
        return HttpResponseRedirect(reverse('canvas'))
    else:
        return HttpResponse('uh oh')

def privacy(request):
    return render_to_response('privacy.html')

def tos(request):
    return render_to_response('tos.html')

"""logging.info('There are matches for Client.')
        for cl in liked_clients:#integer uid
            #XXX ALSO CHECK THE TOP RANKED CLIENTS MATCHES!!!
            if cl in matches: # and cl not in notified:
                first_matched_client = matched_clients[matches.index(cl)]
                if first_matched_client not in notified:
                    send_mail(SUBJECT, BODY % str(first_matched_client), DEFAULT_FROM_EMAIL, [client.user.email])
                    send_mail(SUBJECT, BODY % str(client), DEFAULT_FROM_EMAIL, [first_matched_client.user.email])
                    client.notified.add(first_matched_client)
                    client.save()
                    break"""

