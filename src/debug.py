
from aiohttp import web
from aiohttp_session import get_session, new_session
import aiohttp_jinja2
from aiohttp import ClientSession
from bson.objectid import ObjectId

from util import routes, get_user
from backend import users, friends, comments, history, shares, favorites

# TODO: disable debugging code

@routes.get('/debug:populate')
async def debug_populate(request):
    # generate random users with personal data
    async with ClientSession() as session:
        async with session.get('https://randomuser.me/api/?results=100') as response:
            data = await response.json()
            for i, user in enumerate(data['results']):
                password = user['login']['password']
                email = user['email']
                name = user['name']['first'].title() + ' ' + user['name']['last'].title()
                #picture = '/static/img/person%d.jpg' % i 
                picture = user['picture']['large']
                user_id = await users.add(password=password, email=email, name=name, picture=picture)
    # populate usage data for each user
    user_ids = []
    for user in await users.list():
        user_ids.append(user['_id'])
    print(user_ids)

    # get random data to sample from
    with open('data/random/youtube_ids.txt') as fp:
        videos = [line.strip() for line in fp]
    with open('data/random/laurem.txt') as fp:
        paragraphs = [line.strip() for line in fp]
    with open('data/random/queries.txt') as fp:
        queries = [line.strip() for line in fp]
    folder_names = ['Cooking', 'Stuff I like', 'Sailing', 'The teacher asked it', 'Chipmunks', 'To the zoo', 'Home', 'Mum', 'Dad', 'Other', 'Nothing special']

    import random
    for user_id in user_ids:
        folders = []
        for i in range(random.randint(1, 5)):
            name = random.choice(folder_names)
            folders.append(await favorites.add_folder(user_id, name))
        # generate random friend connections
        friend_ids = []
        for num in range(random.randint(1, 8)):
            other_id = random.choice(user_ids)
            if other_id != user_id:
                request = True if random.random() > .5 else False
                await friends.add(user_id, other_id, request)
                if not request:
                    friend_ids.append(other_id)
        print('FRIENDS:', friend_ids)
        # generate random queries
        for num in range(random.randint(1, 15)):
            await history.add(user_id, 'query', random.choice(queries))

        # generate random video history
        for num in range(random.randint(1, 20)):
            video_id = random.choice(videos)
            if random.random() > .5:
                folder_id = random.choice(folders)
                await favorites.add(user_id, folder_id, video_id)
            await history.add(user_id, 'video', video_id)

            # generate random comments
            if random.random() > .3:
                comment_id = await comments.add(user_id, video_id, random.choice(paragraphs))
                comment_item = await comments.get(comment_id)
                # share comment
                for other_id in friend_ids:
                    if random.random() > .5:
                        await shares.add(video_id, comment_id, {'thumbnail': 'https://i.ytimg.com/vi/%s/hqdefault.jpg' % video_id, 'text': comment_item['text']}, user_id, other_id)
    raise web.HTTPFound('/debug:users')

@routes.get('/debug:users')
@aiohttp_jinja2.template('user_list.html')
async def debug_users(request):
    result = []
    for user in await users.list():
        user['href'] = '/debug:login/' + str(user['_id'])
        result.append(user)
    return {'users': result}

@routes.get('/debug:login/{user_id}')
@aiohttp_jinja2.template('login.html')
async def debug_login(request):
    user_id = ObjectId(request.match_info['user_id'])
    user = await users.get(user_id)
    if user is not None:
        session = await new_session(request)
        session['user_id'] = str(user_id)
        await history.add(user_id, 'debug:login')
        raise web.HTTPFound('/')
    else:
        return {'error': 'invalid user_id'}

@routes.get('/debug:clear')
async def debug_clear(request):
    session = await new_session(request)
    if 'user_id' in session:
        del session['user_id']
    import backend
    await backend.clear_all()
    raise web.HTTPFound('/')

@routes.get('/debug:restart')
async def debug_restart(request):
    import os, sys
    os.execvp('python', ['python'] + sys.argv)


