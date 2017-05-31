
class FacebookMsgParser(object):
    """parse Facebook Messeage
    """

    @classmethod
    def parse_message_type(cls, msg):
        """parse message type
        """
        if 'delivery' in msg:
            msg_type = 'message_deliveries'
        elif 'read' in msg:
            msg_type = 'message_reads'
        elif 'postback' in msg:
            msg_type = 'postback'
        elif 'optin' in msg:
            msg_type = 'messaging_optins'
        elif 'postback' in msg:
            msg_type = 'postback'
        elif 'message' in msg:
            message = msg['message']
            if message.get('is_echo', False):
                msg_type = 'message_echoes'
            else:
                msg_type = 'message'
        else:
            msg_type = None
        return msg_type
