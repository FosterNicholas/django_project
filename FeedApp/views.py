from django.shortcuts import render, redirect
from .forms import PostForm,ProfileForm, RelationshipForm
from .models import Post, Comment, Like, Profile, Relationship
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.http import Http404


# Create your views here.

# When a URL request matches the pattern we just defined, 
# Django looks for a function called index() in the views.py file. 

def index(request):
    """The home page for Learning Log."""
    return render(request, 'FeedApp/index.html')


# decorator to require that a user must be logged in to access the following function.
@login_required
def profile(request):
    """Display and update user profile."""
    profile = Profile.objects.filter(user=request.user) # do this since user is part of the model already (use filter becaasue it works with exists)
    if not profile.exists(): # see if it exists
        Profile.objects.create(user=request.user) # create a profile if one does not exist
    profile = Profile.objects.get(user=request.user) # get the profile now that we know it

    if request.method != 'POST':
        form = ProfileForm(instance=profile) # pre-fill form with current profile info
    else:
        form = ProfileForm(instance=profile,data=request.POST) # fill form with POST data
        if form.is_valid():
            form.save()
            return redirect('FeedApp:profile') # redirect to profile page after saving
        
    context = {'form': form}
    return render(request, 'FeedApp/profile.html', context)

@login_required
def myfeed(request):
    """Display the user's feed."""
    comment_count_list = []
    like_count_list = []
    posts = Post.objects.filter(username=request.user).order_by('-date_posted') # get posts by the logged-in user w/ most recent first
    for p in posts:
        c_count = Comment.objects.filter(post=p).count() # count comments for each post
        l_count = Like.objects.filter(post=p).count() # count likes for each post
        comment_count_list.append(c_count)
        like_count_list.append(l_count)
    zipped_list = zip(posts, comment_count_list, like_count_list) # combine posts with their comment and like counts

    context = {'posts' :posts, 'zipped_list' :zipped_list}
    return render(request, 'FeedApp/myfeed.html', context)


@login_required
def new_post(request):
    """Create a new post."""
    if request.method != 'POST': # if the request is not a POST, create a blank form
        form = PostForm()
    else:
        form = PostForm(request.POST,request.FILES) # if it is a POST, process it into the database
        if form.is_valid():
            new_post = form.save(commit=False) # create a new post object without saving to the database yet
            new_post.username = request.user # assign username to the logged-in user
            new_post.save()
            return redirect('FeedApp:myfeed')
    
    context = {'form': form}
    return render(request, 'FeedApp/new_post.html', context)

@login_required
def friendsfeed(request):
    """Display friends feed."""
    comment_count_list = []
    like_count_list = []
    friends = Profile.objects.filter(user=request.user).values('friends') # get list of friends for the logged-in user
    posts = Post.objects.filter(username__in=friends).order_by('-date_posted') 
    for p in posts:
        c_count = Comment.objects.filter(post=p).count() # count comments for each post
        l_count = Like.objects.filter(post=p).count() # count likes for each post
        comment_count_list.append(c_count)
        like_count_list.append(l_count)
    zipped_list = zip(posts, comment_count_list, like_count_list) # combine posts with their comment and like counts

    if request.method == 'POST' and request.POST.get("like"):
        post_to_like = request.POST.get("like")
        print(post_to_like)
        like_already_exists = Like.objects.filter(post_id=post_to_like, username=request.user)
        if not like_already_exists.exists():
            Like.objects.create(post_id=post_to_like, username=request.user)
            return redirect('FeedApp:friendsfeed')


    context = {'posts' :posts, 'zipped_list' :zipped_list}
    return render(request, 'FeedApp/friendsfeed.html', context)


@login_required
def comments(request, post_id):
    """Display and add comments to a post."""
    if request.method == 'POST' and request.POST.get("btn1"):
        comment = request.POST.get("comment")
        Comment.objects.create(post_id=post_id,username=request.user,text=comment,date_added=date.today())
    
    comments = Comment.objects.filter(post=post_id)
    post = Post.objects.get(id=post_id)

    context = {'post': post, 'comments': comments}

    return render(request, 'FeedApp/comments.html', context)


@login_required
def friends(request):
    """Display and manage friends."""
    # get the admin_profile and user profile to create the first relationship
    admin_profile = Profile.objects.get(user=1)
    user_profile = Profile.objects.get(user=request.user)

    # to get My Friends
    user_friends = user_profile.friends.all()
    user_friends_profiles = Profile.objects.filter(user__in=user_friends)

    # to get Friend Requests sent
    user_relationships = Relationship.objects.filter(sender=user_profile)
    request_sent_profiles = user_relationships.values('receiver') # collection of receiver profiles


    # to get eligible profiles - exclude the user, their existing friends, and firend requests sent already
    all_profiles = Profile.objects.exclude(user=request.user).exclude(id__in=user_friends_profiles).exclude(id__in=request_sent_profiles)

    # to get friend requests recieved by the user
    request_recieved_profiles = Relationship.objects.filter(receiver=user_profile, status='sent')

    # if this is the first time to access the firend requests page, create the first relationship
    # with the admin of the website
    if not user_relationships.exists():                 # 'filter' works with 'exists()' while 'get' does not
        Relationship.objects.create(sender=user_profile, receiver=admin_profile, status='sent')

    # check to see WHICH submit button was pressed (sending or accepting a friend request)
    # this is to process all send requests
    if request.method == 'POST' and request.POST.get("send_requests"):
        recievers = request.POST.getlist("send_requests")
        for reciever in recievers:
            reciever_profile = Profile.objects.get(id=reciever)
            Relationship.objects.create(sender=user_profile, receiver=reciever_profile, status='sent')
        return redirect('FeedApp:friends')
    
    # this is to process all recieve requests
    if request.method == 'POST' and request.POST.get("recieve_requests"):
        senders = request.POST.getlist("recieve_requests")
        for sender in senders:
            # update the relationship status to 'accepted'
            Relationship.objects.filter(id=sender).update(status='accepted')
            # create a relationship object to access the sender's user id
            # to add to the friends list of the user
            relationship_obj = Relationship.objects.get(id=sender)
            user_profile.friends.add(relationship_obj.sender.user)

            # add the user to the friends list of the sender as well
            relationship_obj.sender.friends.add(request.user)
    
    context = {'user_friends_profiles': user_friends_profiles, 'user_relationships': user_relationships,
               'all_profiles': all_profiles,'request_recieved_profiles': request_recieved_profiles}


    return render(request, 'FeedApp/friends.html', context)