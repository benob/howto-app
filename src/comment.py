from aiohttp import web
from datetime import datetime
import aiohttp_jinja2

from util import routes, login_required, get_user, to_objectid

from backend import comments, friends, videos, shares

# GET /comment/{video_id} => form to write and share a comment
@routes.get('/comment/{video_id}') 
@login_required
@aiohttp_jinja2.template('comment.html')
async def write_comment(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    video = await videos.get(video_id)
    friend_items = await friends.list(user['_id'], populate=True)
    return {'video': video, 'friends': friend_items}

#POST /comment/{video_id} (text) => add root comment to video
@routes.post('/comment/{video_id}')
@login_required
async def post_comment(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    data = await request.post()
    if 'text' in data:
        comment_id = await comments.add(user['_id'], video_id, data['text'])
        for key, other_id in data.items():
            if key == 'friend':
                print('adding', other_id)
                await shares.add(video_id, comment_id, {'thumbnail': 'https://i.ytimg.com/vi/%s/hqdefault.jpg' % video_id, 'text': data['text']}, user['_id'], to_objectid(other_id))
        raise web.HTTPFound('/watch/' + video_id + '#' + str(comment_id))
    else:
        raise web.HTTPBadRequest()

@routes.get('/comments')
@login_required
@aiohttp_jinja2.template('comments.html')
async def show_comments(request):
    user = await get_user(request)
    comment_items = await comments.list(user['_id'], populate=True)
    return {'comments': comment_items, 'show_video': True}

