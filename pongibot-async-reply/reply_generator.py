from __future__ import print_function


USER_STATES = [
    'init',
    'img_uploaded',
    'img_tagged',
    'tag_completed',
]

USER_ACTION = [
    'upload_img',
    'type_text',
    #'quick_reply',
    #'confirm_tag',
    #'confirm_complete'
]


class UserState(object):

    def __init__(self, user):
        self.user = user

    def current_state(self):
        user_data = self.user.current_data
        if not user_data:
            self.user.get_or_create()
            user_data = self.user.current_data
        return user_data.get('user_state', 'init')

    def next_state(self, action, action_data):
        state = self.current_state()
        print("state: {}".format(state))

        next_state = None
        update_data = {}
        if state in ['init', 'done']:
            if action == 'upload_img' and len(action_data['images']) > 0:
                update_data['images'] = action_data['images']
                next_state = 'img_uploaded'
            else:
                next_state = 'init'

        elif state == 'img_uploaded':
            if action == 'type_text':
                update_data['tags'] = [action_data['text']]
                next_state = 'img_tagged'

        elif state == 'img_tagged':
            if action == 'type_text':
                if action_data['text'].lower() == 'no':
                    next_state = 'done'
                else:
                    update_data['tags'] = [action_data['text']]
                    next_state = 'img_tagged'
        # default is no change
        if next_state is None:
            next_state = state
        return next_state, update_data


class ReplyGenerator(object):

    def __init__(self, user):
        self.user = user
        self.user_state = UserState(user)

    def next_step(self, action, action_data):
        next_state, update_data = self.user_state.next_state(action, action_data)
        update_data['user_state'] = next_state

        if next_state == 'init':
            reply_msg = 'Please upload imamge to start.'
        elif next_state == 'img_uploaded':
            reply_msg = 'image uploaded. please add tags.'
        elif next_state == 'img_tagged':
            reply_msg = "add more tags? or Type 'No' to complete"
        elif next_state == 'done':
            reply_msg = "Done. report genearated!"
        return reply_msg, update_data
