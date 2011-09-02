from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils.html import strip_tags
from django.http import HttpResponse, Http404, HttpResponseRedirect
from wootmatch.settings import FACEBOOK_APPLICATION_ID, CANVAS_URL, FACEBOOK_APPLICATION_SECRET_KEY, FACEBOOK_APPLICATION_URL, FACEBOOK_APPLICATION_INITIAL_PERMISSIONS
from fandjango.decorators import facebook_authorization_required
from fandjango.utils import parse_signed_request
from fandjango.models import User
import sys
import json
from wootmatch.fbook.models import Like, Client, Suggestion, FbookUser, Vote
from wootmatch.fbook.forms import *
from urllib import urlencode
import memcache, logging
logger = logging.getLogger()

cache = memcache.Client(['127.0.0.1:11211'])
SUB_QUERY="SELECT uid, name, pic_square FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) and sex = '%s'"
FULL_QUERY="SELECT uid, name, pic_square FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me())"
QUERY2 = "SELECT name FROM user WHERE uid IN (%s)"
SUBJECT = "You have a match on LikeEachOther!"
BODY = "Your match is: %s. Good luck!"

request_variables = {
    'client_id': FACEBOOK_APPLICATION_ID,
    'redirect_uri': FACEBOOK_APPLICATION_URL,
    'scope': ', '.join(FACEBOOK_APPLICATION_INITIAL_PERMISSIONS)
}

urlencoded_request_variables = urlencode(request_variables)
REDIRECT_LINK = "https://graph.facebook.com/oauth/authorize?%s" % urlencoded_request_variables

def get_client(request):
    try:
        client = Client.objects.get(user = request.facebook.user)
        logger.info('Client %s retrieved.', str(client))
    except Client.DoesNotExist:
        client = Client.objects.create(user = request.facebook.user)
        logger.info('Client %s created.', str(client))
    return client

def ensure_allowed(fn):
    def wrapped(request, *args, **kwargs):
            allowed = cache.get('updates_allowed')
            if allowed == '0':
                return render_to_response('updating.html')
            else:
                return fn(request, *args, **kwargs)
    return wrapped
         
@facebook_authorization_required()
@ensure_allowed
def canvas(request):
    client = get_client(request)
    if not request.facebook.user.gender:
        QUERY = FULL_QUERY
    elif request.facebook.user.gender[0]=='m':
        QUERY = SUB_QUERY % 'female'
    else:
        QUERY = SUB_QUERY % 'male'
    authorized = request.facebook.user.authorized    
    #see if there are matches, if so, show ONE MATCH
    likes = client.likez.all().order_by('rank')
    num_likes = client.likez.all().count()
    logger.info('Client likes %s people.', str(num_likes))
    liked_clients = [like.like.uid for like in likes]
    notified = client.notified.all()
    logger.info('Got all notified clients of current Client')
    has_app=[]
    num_like_me = Like.objects.filter(like__uid = client.user.facebook_id).count()
    if likes: #see who has app
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
    return direct_to_template(request, 'sync.html', {'num_like_me':num_like_me, 'CANVAS_URL':CANVAS_URL, 
        'REDIRECT_LINK':REDIRECT_LINK,'first_visit':client.first_visit, 'authorized':authorized,
        'likes_tup':likes_tup, 'email':request.facebook.user.email, 'num_likes':num_likes, 'query':QUERY, 
        'app_id':FACEBOOK_APPLICATION_ID})

@facebook_authorization_required()
@ensure_allowed
def add_person(request):
    if request.method=="POST" and 'add_like_uid' in request.POST and 'add_like_name' in request.POST: 
        client = get_client(request)
        likes = Like.objects.filter(client = client).count()
        if likes > 4:
            return HttpResponse('too_many')
        if client.first_visit:
            client.first_visit = False
            client.save()
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
            Like.objects.create(client=client, like=user, rank=rank)
        # check if liked person has app:
        try:
            Client.objects.get(user__facebook_id = int(uid))
            has_app = 'yes'
        except Client.DoesNotExist:
            has_app = 'no'
        except:
            has_app = 'no'
            logger.error('Check this!', exc_info=sys.exc_info())
        #return a row containing name, rank and app stsatus
        row = """<tr id="%s"><td>%s</td><td></td><td>%s</td><td id="msg$"><a href="#" class="lb" onclick="return showCreateMsg('%s')">create</a></td><td><a href="#tbl1" class="myButton" onclick="return removePerson('%s')">Remove</a></td></tr>""" % (uid,name,has_app,uid,uid)
        return HttpResponse(row)
    else:
        logger.warning('Bad POST Request')
        return HttpResponse('POST Error')

@facebook_authorization_required()
@ensure_allowed
def remove_person(request):
    if request.method == 'POST' and 'remove' in request.POST:
        client = get_client(request)
        uid = request.POST.get('remove') # should be a string
        try:
            l = Like.objects.get(client=client, like__uid=int(uid))
            l.delete()
            msg = 'ok'
        except Like.DoesNotExist:
            msg = 'Like Does Not Exist'
    else:
            logger.warning('Bad POST request')
            msg = 'error'
    return HttpResponse(msg)

@facebook_authorization_required()
@ensure_allowed
def update_rank(request):
    if request.method == 'POST' and 'rank_order' in request.POST:
        ranks = request.POST.get('rank_order').split('.')[0:-1]
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
@ensure_allowed
def delete_account(request):
    if request.method == "POST":
        client = get_client(request)
        client.delete()
        return HttpResponseRedirect(reverse('canvas'))
    else:
        raise Http404

@facebook_authorization_required()
@ensure_allowed
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
    else:
        raise Http404

@facebook_authorization_required()
@ensure_allowed
def request_features(request):
    client = get_client(request)
    if request.method == "POST":
        form = SuggestionForm(request.POST)
        if form.is_valid():
            Suggestion.objects.create(title = form.cleaned_data['title'],suggestion=form.cleaned_data['suggestion'],client=client)
            return HttpResponseRedirect(reverse('request_features'))
    else:
        form = SuggestionForm()
    suggestions = Suggestion.objects.filter(status=1).order_by('-votes')
    return direct_to_template(request, 'comments.html', {'suggestions':suggestions, 'form':form})

@facebook_authorization_required()
@ensure_allowed
def upvote(request):
    if request.method == "POST":
        #VOTE_LIMIT = 10
        client = get_client(request)
        #vote_count = Vote.objects.filter(client=client).count()
        #if vote_count >= VOTE_LIMIT:
        #    return HttpResponse('too_many')
        #find out the suggestion
        suggestion = Suggestion.objects.get(pk=int(request.POST.get('pk')))
        #check if client voted on this already
        try:
            Vote.objects.get(suggestion = suggestion, client = client)
            return HttpResponse('already_voted')
        except Vote.DoesNotExist:
            suggestion.votes += 1
            suggestion.save()
            Vote.objects.create(suggestion = suggestion, client = client)
        except:
            logger.error('Exception in Upvote view. CHECK THIS', exc_info=sys.exc_info())
        return HttpResponse('ok')
    else:
        raise Http404

@facebook_authorization_required()
@ensure_allowed
def create_msg(request):
    if request.method == 'POST' and 'msg' in request.POST:
        msg = strip_tags(request.POST.get('msg'))
        likeuid = request.POST.get('likeuid')
        client = get_client(request)
        try:
            like = Like.objects.get(client=client, like__uid = int(likeuid))
        except Like.DoesNotExist: 
            raise Http404
        like.msg = msg
        like.save()
        return HttpResponse('ok')
    else:
        raise Http404

@facebook_authorization_required()
@ensure_allowed
def get_msg(request):
    if request.method == 'POST' and 'likeuid' in request.POST: 
        client = get_client(request)
        try:
            like = Like.objects.get(client=client, like__uid = int(request.POST.get('likeuid')))
        except Like.DoesNotExist:
            raise Http404
        return HttpResponse(like.msg)        
    else:
        raise Http404


def test(request):
    if request.method == "POST":
        return HttpResponse('k')
    else:
        return direct_to_template(request, 'test.html')       
