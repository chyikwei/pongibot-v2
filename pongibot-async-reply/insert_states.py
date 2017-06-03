from __future__ import print_function

from abc import ABCMeta, abstractmethod

from reply_utils import QuickReplyGenerator, TemplateGenerator
from ddb_models import ReportTable

class BaseState(object):
    __metaclass__ = ABCMeta
    STATE_CODE = ''

    @abstractmethod
    def update_by_context(self, context):
        pass

    @abstractmethod
    def generate_reply(self, context):
        pass


class InitState(BaseState):
    """Initial state state"""
    STATE_CODE = 'INIT'

    def update_by_context(self, context):
        context_data = context.get_context()
        signal = context_data.pop('signal', '')
        start_timestamp = context_data.pop('start_timestamp', None)
        images = context_data.pop('images', [])
        report = context.get_report()

        if signal == "INSERT_NEW":
            context.set_state(InitInsertState())
        elif signal == "RECENT_REPORT":
            context.set_state(RecentReportState(start_timestamp))
        elif len(images) > 0:
            report.add_images(images)
            context.set_state(ImgUploadedState())

    def generate_reply(self, context):
        preference = context.get_preference()
        qr = QuickReplyGenerator(preference)

        ret = {
            'text': "please select action",
            'quick_replies': qr.generate_initial_menu()
        }
        return ret


class RecentReportState(BaseState):
    """Initial state state"""
    STATE_CODE = 'RECENT_REPORT'
    REPLY_COUNT = 5

    def __init__(self, start_timestamp=None):
        self.start_timestamp = start_timestamp

    def update_by_context(self, context):
        context_data = context.get_context()
        signal = context_data.pop('signal', '')
        start_timestamp = context_data.pop('start_timestamp', None)
        if signal == 'RECENT_REPORT':
            self.start_timestamp = start_timestamp
        else:
            context.set_state(InitState())

    def generate_reply(self, context):
        limit = self.REPLY_COUNT
        user_id = context.user.user_id

        rpt = ReportTable()
        start_time = self.start_timestamp
        # Note: +2 is to make sure next batch has 2+
        # elements
        reports = rpt.load(
            user_id, start_time, limit + 2)
        if len(reports) > 0:
            ret = {
                'template': TemplateGenerator.generate_reports(reports, limit),
            }
        else:
            ret = {
                'text': "No report to display",
            }
        return ret


class InitInsertState(BaseState):
    """Initial Insert state"""
    STATE_CODE = 'INIT_INSERT'

    def update_by_context(self, context):
        context_data = context.get_context()
        report = context.get_report()
        images = context_data.pop('images', [])
        report.add_images(images)
        if len(images) > 0:
            context.set_state(ImgUploadedState())

    def generate_reply(self, context):
        ret = {
            'text': "please upload image to start."
        }
        return ret


class ImgUploadedState(BaseState):
    """Img Uploaded state"""
    STATE_CODE = 'IMG_UPLOADED'

    def update_by_context(self, context):
        context_data = context.get_context()
        report = context.get_report()
        text = context_data.pop('text', '')
        if len(text) > 0:
            report.add_tag(text)
            context.set_state(TagAddedState())

    def generate_reply(self, context):
        preference = context.get_preference()
        qr = QuickReplyGenerator(preference)

        ret = {
            'text': "please add tag",
            "quick_replies": qr.generate_quick_reply_tags()
        }
        return ret


class TagAddedState(BaseState):
    """Tag Added state
    
    User can add more tag or move to next step
    """
    STATE_CODE = 'TAG_ADDED'

    def update_by_context(self, context):
        context_data = context.get_context()
        report = context.get_report()
        text = context_data.pop('text', '')
        signal = context_data.pop('signal', '')
        if signal == 'SKIP':
            context.set_state(ReportUserState())
        elif len(text) > 0:
            report.add_tag(text)

    def generate_reply(self, context):
        preference = context.get_preference()
        qr = QuickReplyGenerator(preference)
        report = context.get_report()
        ret = {
            'text': "Add more tag or skip.",
            "quick_replies": qr.generate_quick_reply_tags(
                report.get_tags(), with_skip=True)
        }
        return ret


class ReportUserState(BaseState):
    """report user state"""

    STATE_CODE = 'REPORT_USER'

    def update_by_context(self, context):
        context_data = context.get_context()
        report = context.get_report()
        text = context_data.pop('text', '')
        signal = context_data.pop('signal', '')
        if signal == 'SKIP':
            context.set_state(InsertCompleteState())
        elif len(text) > 0:
            report.add_target(text)
            context.set_state(InsertCompleteState())

    def generate_reply(self, context):
        preference = context.get_preference()
        qr = QuickReplyGenerator(preference)
        ret = {
            'text': "Add target's name or skip.",
            "quick_replies": qr.generate_quick_reply_targets(with_skip=True)
        }
        return ret


class InsertCompleteState(BaseState):
    """Insert Complete state"""

    STATE_CODE = 'INSERT_COMPTLETE'

    def update_by_context(self, context):
        return

    def generate_reply(self, context):
        ret = {
            'text': "Insert Completed!",
        }
        return ret

class InsertCancelState(BaseState):
    """Cancel state"""

    STATE_CODE = 'INSERT_CANCELLED'

    def update_by_context(self, context):
        return

    def generate_reply(self, context):
        ret = {
            'text': "Insert Cancelled!",
        }
        return ret


class InsertStateFactory(object):

    STATE_CODE_MAPPING = {
        'INIT': InitState,
        'RECENT_REPORT': RecentReportState,
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

    def __init__(self, user, context_data, report_data, preference):
        self.user = user
        self._context_data = context_data
        if 'STATE_CODE' in context_data:
            self.state = InsertStateFactory.generate_by_code(
                context_data['STATE_CODE'])
        else:
            # initialize
            self.state = InitState()
            self._context_data['STATE_CODE'] = self.state.STATE_CODE

        self._report = ReportData()
        self._report.update(report_data)
        self._preference = preference

    def is_completed(self):
        return isinstance(self.state, InsertCompleteState)

    def is_cancelled(self):
        return isinstance(self.state, InsertCancelState)

    def get_context(self):
        return self._context_data

    def get_report(self):
        return self._report

    def get_preference(self):
        return self._preference

    def receive_context(self, update_dict):
        self._context_data.update(update_dict)
        self.state.update_by_context(self)

    def set_state(self, state):
        self._context_data['STATE_CODE'] = state.STATE_CODE
        self.state = state

    def generate_reply(self):
        return self.state.generate_reply(self)


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
        if tag not in self._data['tags']:
            self._data['tags'].append(tag)

    def to_dict(self):
        return self._data

    def update(self, data):
        self._data.update(data)

    def get_tags(self):
        return self._data['tags']
