from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group

from myjobs.tests.setup import MyJobsBase
from myjobs.tests.factories import UserFactory
from myjobs.tests.test_views import TestClient
from mymessages.models import Message, MessageInfo


class MessageViewTests(MyJobsBase):
    def setUp(self):
        self.user = UserFactory()
        self.message = Message(subject='subject',
                               body='body',
                               message_type='success')
        self.message.save()
        for group in Group.objects.all():
            self.message.group.add(group.pk)
        self.message.save()
        self.messageInfo = MessageInfo(user=self.user,
                                       message=self.message)
        self.messageInfo.save()
        self.client = TestClient()
        self.client.login_user(self.user)

    def test_user_post_mark_message_read(self):
        resp = self.client.post(reverse('read'),
                                data={'name': 'message-'+str(self.message.id)
                                              + '-'+str(self.user.id)},
                                follow=True)
        m = MessageInfo.objects.get(user=self.user, message=self.message)
        self.assertTrue(m.read)
        self.assertTrue(m.read_at)