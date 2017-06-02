from __future__ import print_function

from abc import ABCMeta, abstractmethod


class BaseState(object):
    __metaclass__ = ABCMeta
    STATE_CODE = ''

    @abstractmethod
    def update_by_context(self, context):
        pass

    @abstractmethod
    def generate_reply(self, context):
        pass


class InitInsertState(BaseState):
    """Initial Insert state"""
    STATE_CODE = 'INIT_INSERT'

    def update_by_context(self, context):
        context_data = context.get_context()
        report = context.get_report()
        images = context_data.get('images', [])
        report.add_images(images)
        if len(images) > 0:
            del context_data['images']
            context.set_state(ImgUploadedState())

    def generate_reply(self, context):
        return "please upload image to start."


class ImgUploadedState(BaseState):
    """Img Uploaded state"""
    STATE_CODE = 'IMG_UPLOADED'

    def update_by_context(self, context):
        context_data = context.get_context()
        report = context.get_report()
        text = context_data.get('text', '')
        # TODO: add quick reply
        if len(text) > 0:
            del context_data['text']
            report.add_tag(text)
            context.set_state(TagAddedState())

    def generate_reply(self, context):
        return "please add tag"


class TagAddedState(BaseState):
    """Tag Added state
    
    User can add more tag or move to next step
    """
    STATE_CODE = 'TAG_ADDED'

    def update_by_context(self, context):
        context_data = context.get_context()
        report = context.get_report()
        text = context_data.get('text', '')
        # TODO: switch to quick reply
        if text.lower() == 'no':
            del context_data['text']
            context.set_state(ReportUserState())
        elif len(text) > 0:
            del context_data['text']
            report.add_tag(text)

    def generate_reply(self, context):
        return "Add more tag or type 'No' to skip."


class ReportUserState(BaseState):
    """report user state"""
    STATE_CODE = 'REPORT_USER'

    def update_by_context(self, context):
        context_data = context.get_context()
        text = context_data.get('text', '')
        report = context.get_report()
        # TODO: switch to quick reply
        if len(text) > 0:
            del context_data['text']
            report.add_target(text)
            context.set_state(InsertCompleteState())

    def generate_reply(self, context):
        return "Add user's name or type 'No' to skip."


class InsertCompleteState(BaseState):
    """Insert Complete state"""
    STATE_CODE = 'INSERT_COMPTLETE'

    def update_by_context(self, context):
        return

    def generate_reply(self, context):
        return "Insert Completed!"


class InsertCancelState(BaseState):
    """Cancel state"""
    STATE_CODE = 'INSERT_CANCELLED'

    def update_by_context(self, context):
        return

    def generate_reply(self, context):
        return "Insert Cancelled!"


class InsertStateFactory(object):

    STATE_CODE_MAPPING = {
        'INIT_INSERT': InitInsertState,
        'IMG_UPLOADED': ImgUploadedState,
        'TAG_ADDED': TagAddedState,
        'REPORT_USER': ReportUserState,
        'INSERT_COMPTLETE': InsertCompleteState,
        'INSERT_CANCELLED': InsertCancelState,
    }

    @classmethod
    def generate_by_code(cls, state_code):
        return cls.STATE_CODE_MAPPING[state_code]()


class InsertStateContext(object):

    def __init__(self, context_data, report_data):
        self._context_data = context_data
        if 'STATE_CODE' in context_data:
            self.state = InsertStateFactory.generate_by_code(
                context_data['STATE_CODE'])
        else:
            # initialize
            self.state = InitInsertState()
            self._context_data['STATE_CODE'] = self.state.STATE_CODE

        self._report = ReportData()
        self._report.update(report_data)

    def is_completed(self):
        return isinstance(self.state, InsertCompleteState)

    def is_cancelled(self):
        return isinstance(self.state, InsertCancelState)

    def get_context(self):
        return self._context_data

    def get_report(self):
        return self._report

    def receive_context(self, update_dict):
        self._context_data.update(update_dict)
        self.state.update_by_context(self)

    def set_state(self, state):
        self._context_data['STATE_CODE'] = state.STATE_CODE
        self.state = state

    def generate_reply(self):
        return self.state.generate_reply(self.get_context())


class ReportData(object):
    """A dict wrapper for Report record"""

    def __init__(self):
        self._data = {
            'tags': [],
            'images': [],
        }

    def add_user(self, user_id):
        self._data['user_id'] = user_id

    def add_target(self, target):
        self._data['target'] = target

    def add_images(self, images):
        self._data['images'] += images

    def add_tag(self, tag):
        self._data['tags'].append(tag)

    def to_dict(self):
        return self._data

    def update(self, data):
        self._data.update(data)
