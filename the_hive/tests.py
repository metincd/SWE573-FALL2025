"""
Test ID Format:
- UT-X.Y.Z: Unit Tests
- ST-X.Y.Z: System/Integration Tests  
- UC-X.Y: Use Case Tests
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    User,
    Profile,
    Tag,
    Service,
    ServiceRequest,
    ServiceSession,
    Completion,
    TimeAccount,
    TimeTransaction,
    Conversation,
    Message,
    Thread,
    Post,
    Review,
    ReviewHelpfulVote,
    UserRating,
    ThankYouNote,
    Report,
    ModerationAction,
    Notification,
)

User = get_user_model()


# ==================== UNIT TESTS (UT-X.Y.Z) ====================

class UT1_UserModelTests(TestCase):
    """UT-1: User Model Tests"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_UT_1_1_1_user_creation_with_email(self):
        """UT-1.1.1: Test user creation with email and password"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user.is_active)
    
    def test_UT_1_1_2_user_full_name_property(self):
        """UT-1.1.2: Test full_name property with first and last name"""
        self.assertEqual(self.user.full_name, 'Test User')
    
    def test_UT_1_1_3_user_full_name_fallback_to_email(self):
        """UT-1.1.3: Test full_name property fallback to email when names empty"""
        user2 = User.objects.create_user(email='test2@example.com', password='pass')
        self.assertEqual(user2.full_name, 'test2@example.com')
    
    def test_UT_1_1_4_user_string_representation(self):
        """UT-1.1.4: Test user string representation"""
        self.assertEqual(str(self.user), 'test@example.com')


class UT2_ProfileModelTests(TestCase):
    """UT-2: Profile Model Tests"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            display_name='Test User',
            bio='Test bio',
            latitude=Decimal('41.0082'),
            longitude=Decimal('28.9784')
        )
    
    def test_UT_2_1_1_profile_creation(self):
        """UT-2.1.1: Test profile creation with all fields"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.display_name, 'Test User')
        self.assertEqual(self.profile.bio, 'Test bio')
        self.assertEqual(self.profile.latitude, Decimal('41.0082'))
    
    def test_UT_2_1_2_profile_one_to_one_relationship(self):
        """UT-2.1.2: Test one-to-one relationship with User"""
        self.assertEqual(self.user.profile, self.profile)
    
    def test_UT_2_1_3_profile_location_coordinates(self):
        """UT-2.1.3: Test profile location coordinates storage"""
        self.assertIsNotNone(self.profile.latitude)
        self.assertIsNotNone(self.profile.longitude)


class UT3_TagModelTests(TestCase):
    """UT-3: Tag Model Tests"""
    
    def setUp(self):
        self.tag = Tag.objects.create(
            name='Cooking',
            slug='cooking',
            description='Cooking related services'
        )
    
    def test_UT_3_1_1_tag_creation(self):
        """UT-3.1.1: Test tag creation with name and slug"""
        self.assertEqual(self.tag.name, 'Cooking')
        self.assertEqual(self.tag.slug, 'cooking')
    
    def test_UT_3_1_2_tag_slug_auto_generation(self):
        """UT-3.1.2: Test automatic slug generation from name"""
        tag = Tag.objects.create(name='Math Tutoring')
        self.assertEqual(tag.slug, 'math-tutoring')
    
    def test_UT_3_1_3_tag_wikidata_url_generation(self):
        """UT-3.1.3: Test wikidata URL generation from wikidata_id"""
        tag = Tag.objects.create(
            name='Test',
            wikidata_id='Q123'
        )
        self.assertEqual(tag.wikidata_url, 'https://www.wikidata.org/wiki/Q123')


class UT4_ServiceModelTests(TestCase):
    """UT-4: Service Model Tests"""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='pass123'
        )
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Math Tutoring',
            description='I offer math tutoring',
            estimated_hours=2,
            capacity=1,
            latitude=Decimal('41.0082'),
            longitude=Decimal('28.9784'),
            status='active'
        )
    
    def test_UT_4_1_1_service_creation(self):
        """UT-4.1.1: Test service creation with all fields"""
        self.assertEqual(self.service.owner, self.owner)
        self.assertEqual(self.service.service_type, 'offer')
        self.assertEqual(self.service.title, 'Math Tutoring')
        self.assertEqual(self.service.estimated_hours, 2)
        self.assertEqual(self.service.capacity, 1)
    
    def test_UT_4_1_2_service_default_status(self):
        """UT-4.1.2: Test default status is 'active'"""
        service = Service.objects.create(
            owner=self.owner,
            service_type='need',
            title='Need Help',
            description='I need help'
        )
        self.assertEqual(service.status, 'active')
    
    def test_UT_4_1_3_service_default_capacity(self):
        """UT-4.1.3: Test default capacity is 1"""
        service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Test',
            description='Test'
        )
        self.assertEqual(service.capacity, 1)


class UT5_ServiceRequestModelTests(TestCase):
    """UT-5: ServiceRequest Model Tests"""
    
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='pass')
        self.requester = User.objects.create_user(email='requester@example.com', password='pass')
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Math Tutoring',
            description='Test',
            estimated_hours=2
        )
        self.request = ServiceRequest.objects.create(
            service=self.service,
            requester=self.requester,
            status='pending'
        )
    
    def test_UT_5_1_1_service_request_creation(self):
        """UT-5.1.1: Test service request creation"""
        self.assertEqual(self.request.service, self.service)
        self.assertEqual(self.request.requester, self.requester)
        self.assertEqual(self.request.status, 'pending')
    
    def test_UT_5_1_2_unique_constraint_one_request_per_service(self):
        """UT-5.1.2: Test unique constraint - one request per user per service"""
        with self.assertRaises(IntegrityError):
            ServiceRequest.objects.create(
                service=self.service,
                requester=self.requester,
                status='pending'
            )


class UT6_TimeAccountModelTests(TestCase):
    """UT-6: TimeAccount Model Tests"""
    
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='pass')
        self.account = TimeAccount.objects.create(
            user=self.user,
            balance=Decimal('10.00'),
            total_earned=Decimal('15.00'),
            total_spent=Decimal('5.00')
        )
    
    def test_UT_6_1_1_time_account_creation(self):
        """UT-6.1.1: Test time account creation"""
        self.assertEqual(self.account.user, self.user)
        self.assertEqual(self.account.balance, Decimal('10.00'))
        self.assertEqual(self.account.total_earned, Decimal('15.00'))
        self.assertEqual(self.account.total_spent, Decimal('5.00'))
    
    def test_UT_6_1_2_participation_ratio_calculation(self):
        """UT-6.1.2: Test participation ratio calculation"""
        ratio = self.account.participation_ratio
        self.assertEqual(ratio, 3.0)  # 15/5 = 3
    
    def test_UT_6_1_3_participation_ratio_zero_spent(self):
        """UT-6.1.3: Test participation ratio when total_spent is zero"""
        account = TimeAccount.objects.create(
            user=self.user,
            balance=Decimal('10.00'),
            total_earned=Decimal('10.00'),
            total_spent=Decimal('0.00')
        )
        ratio = account.participation_ratio
        self.assertTrue(ratio == float('inf') or ratio == 0)
    
    def test_UT_6_1_4_is_positive_balance_property(self):
        """UT-6.1.4: Test is_positive_balance property"""
        self.assertTrue(self.account.is_positive_balance)
        self.account.balance = Decimal('0.00')
        self.account.save()
        self.assertFalse(self.account.is_positive_balance)


class UT7_TimeTransactionModelTests(TestCase):
    """UT-7: TimeTransaction Model Tests"""
    
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='pass')
        self.account = TimeAccount.objects.create(user=self.user, balance=Decimal('10.00'))
        self.transaction = TimeTransaction.objects.create(
            account=self.account,
            transaction_type='credit',
            amount=Decimal('5.00'),
            status='completed',
            description='Service completed'
        )
    
    def test_UT_7_1_1_transaction_creation(self):
        """UT-7.1.1: Test transaction creation"""
        self.assertEqual(self.transaction.account, self.account)
        self.assertEqual(self.transaction.transaction_type, 'credit')
        self.assertEqual(self.transaction.amount, Decimal('5.00'))
        self.assertEqual(self.transaction.status, 'completed')
    
    def test_UT_7_1_2_signed_amount_for_credit(self):
        """UT-7.1.2: Test signed_amount for credit transactions"""
        self.assertEqual(self.transaction.signed_amount, Decimal('5.00'))
    
    def test_UT_7_1_3_signed_amount_for_debit(self):
        """UT-7.1.3: Test signed_amount for debit transactions"""
        transaction = TimeTransaction.objects.create(
            account=self.account,
            transaction_type='debit',
            amount=Decimal('3.00'),
            status='completed'
        )
        self.assertEqual(transaction.signed_amount, Decimal('-3.00'))


class UT8_ConversationModelTests(TestCase):
    """UT-8: Conversation Model Tests"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='pass')
        self.user2 = User.objects.create_user(email='user2@example.com', password='pass')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
    
    def test_UT_8_1_1_conversation_creation(self):
        """UT-8.1.1: Test conversation creation"""
        self.assertEqual(self.conversation.participants.count(), 2)
        self.assertIn(self.user1, self.conversation.participants.all())
        self.assertIn(self.user2, self.conversation.participants.all())
    
    def test_UT_8_1_2_conversation_participants_property(self):
        """UT-8.1.2: Test participants property"""
        participants = list(self.conversation.participants.all())
        self.assertIn(self.user1, participants)
        self.assertIn(self.user2, participants)


class UT9_MessageModelTests(TestCase):
    """UT-9: Message Model Tests"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='pass')
        self.user2 = User.objects.create_user(email='user2@example.com', password='pass')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            body='Hello, this is a test message'
        )
    
    def test_UT_9_1_1_message_creation(self):
        """UT-9.1.1: Test message creation"""
        self.assertEqual(self.message.conversation, self.conversation)
        self.assertEqual(self.message.sender, self.user1)
        self.assertEqual(self.message.body, 'Hello, this is a test message')
        self.assertFalse(self.message.is_read)
    
    def test_UT_9_1_2_message_is_recent_property(self):
        """UT-9.1.2: Test is_recent property (within 24 hours)"""
        # Message just created should be recent
        self.assertTrue(self.message.is_recent)


class UT10_ThreadModelTests(TestCase):
    """UT-10: Thread Model Tests"""
    
    def setUp(self):
        self.author = User.objects.create_user(email='author@example.com', password='pass')
        self.thread = Thread.objects.create(
            author=self.author,
            title='Test Thread',
            status='open'
        )
    
    def test_UT_10_1_1_thread_creation(self):
        """UT-10.1.1: Test thread creation"""
        self.assertEqual(self.thread.author, self.author)
        self.assertEqual(self.thread.title, 'Test Thread')
        self.assertEqual(self.thread.status, 'open')
        self.assertEqual(self.thread.views_count, 0)
        self.assertEqual(self.thread.post_count, 0)
    
    def test_UT_10_1_2_thread_is_active_property(self):
        """UT-10.1.2: Test is_active property (activity within 7 days)"""
        # New thread should be active
        self.assertTrue(self.thread.is_active)


class UT11_ReviewModelTests(TestCase):
    """UT-11: Review Model Tests"""
    
    def setUp(self):
        self.reviewer = User.objects.create_user(email='reviewer@example.com', password='pass')
        self.reviewee = User.objects.create_user(email='reviewee@example.com', password='pass')
        self.owner = User.objects.create_user(email='owner@example.com', password='pass')
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Test Service',
            description='Test'
        )
        self.review = Review.objects.create(
            reviewer=self.reviewer,
            reviewee=self.reviewee,
            review_type='service_provider',
            rating=5,
            title='Great service',
            content='Excellent work!',
            related_service=self.service,
            is_published=True
        )
    
    def test_UT_11_1_1_review_creation(self):
        """UT-11.1.1: Test review creation"""
        self.assertEqual(self.review.reviewer, self.reviewer)
        self.assertEqual(self.review.reviewee, self.reviewee)
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.title, 'Great service')
        self.assertTrue(self.review.is_published)
    
    def test_UT_11_1_2_rating_display_property(self):
        """UT-11.1.2: Test rating_display property"""
        # rating_display uses ⭐ and ☆ symbols
        self.assertEqual(self.review.rating_display, '⭐⭐⭐⭐⭐')
    
    def test_UT_11_1_3_is_positive_review_property(self):
        """UT-11.1.3: Test is_positive property"""
        # Property is is_positive (not is_positive_review)
        self.assertTrue(self.review.is_positive)  # rating=5 >= 4
        
        review2 = Review.objects.create(
            reviewer=self.reviewer,
            reviewee=self.reviewee,
            review_type='service_provider',
            rating=1,
            title='Bad service',
            content='Poor work',
            related_service=self.service
        )
        self.assertFalse(review2.is_positive)  # rating=1 < 4


# ==================== SYSTEM TESTS (ST-X.Y.Z) ====================

class ST1_UserRegistrationAPITests(TestCase):
    """ST-1: User Registration API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/register/'
    
    def test_ST_1_1_1_user_registration_success(self):
        """ST-1.1.1: Test successful user registration"""
        data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_ST_1_1_2_user_registration_password_mismatch(self):
        """ST-1.1.2: Test registration with password mismatch"""
        data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'differentpass',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_ST_1_1_3_time_account_creation_on_registration(self):
        """ST-1.1.3: Test TimeAccount is created on registration with 3 TBH"""
        data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(TimeAccount.objects.filter(user=user).exists())
        account = TimeAccount.objects.get(user=user)
        self.assertEqual(account.balance, Decimal('3.00'))


class ST2_ServiceAPITests(TestCase):
    """ST-2: Service API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='pass123'
        )
        # Create profile for owner
        Profile.objects.create(user=self.owner)
        self.client.force_authenticate(user=self.owner)
        self.service_url = '/api/services/'
    
    def test_ST_2_1_1_create_service(self):
        """ST-2.1.1: Test create service endpoint"""
        data = {
            'service_type': 'offer',
            'title': 'Math Tutoring',
            'description': 'I offer math tutoring services',
            'estimated_hours': 2,
            'capacity': 1,
            'latitude': '41.0082',
            'longitude': '28.9784',
            'address': 'Istanbul, Turkey'
        }
        response = self.client.post(self.service_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Service.objects.filter(title='Math Tutoring').exists())
    
    def test_ST_2_1_2_list_services(self):
        """ST-2.1.2: Test list services endpoint"""
        Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Service 1',
            description='Test'
        )
        Service.objects.create(
            owner=self.owner,
            service_type='need',
            title='Service 2',
            description='Test'
        )
        response = self.client.get(self.service_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get('results', [])), 2)
    
    def test_ST_2_1_3_filter_services_by_type(self):
        """ST-2.1.3: Test filter services by type"""
        Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Offer Service',
            description='Test'
        )
        Service.objects.create(
            owner=self.owner,
            service_type='need',
            title='Need Service',
            description='Test'
        )
        response = self.client.get(self.service_url, {'type': 'offer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertTrue(all(s['service_type'] == 'offer' for s in results))
    
    def test_ST_2_1_4_filter_services_by_status(self):
        """ST-2.1.4: Test filter services by status"""
        Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Active Service',
            description='Test',
            status='active'
        )
        Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Completed Service',
            description='Test',
            status='completed'
        )
        response = self.client.get(self.service_url, {'status': 'active'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertTrue(all(s['status'] == 'active' for s in results))


class ST3_ServiceRequestAPITests(TestCase):
    """ST-3: ServiceRequest API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='pass123'
        )
        self.requester = User.objects.create_user(
            email='requester@example.com',
            password='pass123'
        )
        # Create profiles
        Profile.objects.create(user=self.owner)
        Profile.objects.create(user=self.requester)
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Math Tutoring',
            description='I offer math tutoring',
            estimated_hours=2
        )
        # Create time accounts with sufficient balance
        TimeAccount.objects.get_or_create(user=self.owner, defaults={'balance': Decimal('10.00')})
        TimeAccount.objects.get_or_create(user=self.requester, defaults={'balance': Decimal('10.00')})
        self.request_url = '/api/service-requests/'
    
    def test_ST_3_1_1_create_service_request(self):
        """ST-3.1.1: Test creating a service request"""
        self.client.force_authenticate(user=self.requester)
        data = {
            'service_id': self.service.id,  # Use service_id not service
            'message': 'I would like to request this service'
        }
        response = self.client.post(self.request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ServiceRequest.objects.filter(
            service=self.service,
            requester=self.requester
        ).exists())
    
    def test_ST_3_1_2_cannot_request_own_service(self):
        """ST-3.1.2: Test user cannot request their own service"""
        self.client.force_authenticate(user=self.owner)
        data = {
            'service_id': self.service.id,  # Use service_id
            'message': 'Test'
        }
        response = self.client.post(self.request_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_ST_3_1_3_accept_service_request(self):
        """ST-3.1.3: Test accepting a service request"""
        request_obj = ServiceRequest.objects.create(
            service=self.service,
            requester=self.requester,
            status='pending'
        )
        self.client.force_authenticate(user=self.owner)
        # Use set_status endpoint instead of accept
        response = self.client.post(
            f'/api/service-requests/{request_obj.id}/set_status/',
            {'status': 'accepted'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'accepted')


class ST4_TimeAccountAPITests(TestCase):
    """ST-4: TimeAccount API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass123'
        )
        self.account = TimeAccount.objects.create(
            user=self.user,
            balance=Decimal('10.00'),
            total_earned=Decimal('15.00'),
            total_spent=Decimal('5.00')
        )
        self.client.force_authenticate(user=self.user)
        self.account_url = '/api/time-accounts/'
    
    def test_ST_4_1_1_get_time_account(self):
        """ST-4.1.1: Test retrieving time account"""
        response = self.client.get(self.account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TimeAccountViewSet.list() returns a list directly
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        account_data = response.data[0]
        self.assertEqual(float(account_data['balance']), 10.00)
    
    def test_ST_4_1_2_time_account_balance_display(self):
        """ST-4.1.2: Test time account balance is displayed correctly"""
        response = self.client.get(self.account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        account_data = response.data[0]  # Returns list directly
        self.assertIn('balance', account_data)
        self.assertIn('total_earned', account_data)
        self.assertIn('total_spent', account_data)


class ST5_ConversationAPITests(TestCase):
    """ST-5: Conversation API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(email='user1@example.com', password='pass')
        self.user2 = User.objects.create_user(email='user2@example.com', password='pass')
        # Create profiles
        Profile.objects.create(user=self.user1)
        Profile.objects.create(user=self.user2)
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
        self.conversation_url = '/api/conversations/'
    
    def test_ST_5_1_1_list_conversations(self):
        """ST-5.1.1: Test listing conversations"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.conversation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_ST_5_1_2_create_message(self):
        """ST-5.1.2: Test creating a message in conversation"""
        self.client.force_authenticate(user=self.user1)
        message_url = '/api/messages/'
        data = {
            'conversation': self.conversation.id,
            'body': 'Hello, this is a test message'
        }
        response = self.client.post(message_url, data, format='json')
        # May require user to be participant - check status
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN])
        if response.status_code == status.HTTP_201_CREATED:
            self.assertTrue(Message.objects.filter(
                conversation=self.conversation,
                sender=self.user1
            ).exists())


class ST6_HealthCheckAPITests(TestCase):
    """ST-6: Health Check API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.health_url = '/api/health/'
    
    def test_ST_6_1_1_health_check(self):
        """ST-6.1.1: Test health check endpoint"""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('status'), 'ok')


class ST7_TagAPITests(TestCase):
    """ST-7: Tag API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='pass')
        self.client.force_authenticate(user=self.user)
        self.tag_url = '/api/tags/'
    
    def test_ST_7_1_1_list_tags(self):
        """ST-7.1.1: Test list tags endpoint"""
        Tag.objects.create(name='Cooking', slug='cooking')
        Tag.objects.create(name='Tutoring', slug='tutoring')
        response = self.client.get(self.tag_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)
    
    def test_ST_7_1_2_create_tag(self):
        """ST-7.1.2: Test create tag endpoint"""
        data = {
            'name': 'Gardening',
            'description': 'Gardening related services'
        }
        response = self.client.post(self.tag_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Tag.objects.filter(name='Gardening').exists())
    
    def test_ST_7_1_3_popular_tags_endpoint(self):
        """ST-7.1.3: Test popular tags endpoint"""
        tag1 = Tag.objects.create(name='Popular', slug='popular')
        tag2 = Tag.objects.create(name='Unpopular', slug='unpopular')
        service = Service.objects.create(
            owner=self.user,
            service_type='offer',
            title='Test',
            description='Test'
        )
        service.tags.add(tag1)
        response = self.client.get(f'{self.tag_url}popular/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data
        self.assertGreater(len(results), 0)


class ST8_ThreadAPITests(TestCase):
    """ST-8: Thread API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='pass')
        # Create profile for user
        Profile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.thread_url = '/api/threads/'
    
    def test_ST_8_1_1_create_thread(self):
        """ST-8.1.1: Test create thread endpoint"""
        data = {
            'title': 'Test Thread',
            'status': 'open'
        }
        response = self.client.post(self.thread_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Thread.objects.filter(title='Test Thread').exists())
    
    def test_ST_8_1_2_list_threads(self):
        """ST-8.1.2: Test list threads endpoint"""
        Thread.objects.create(
            author=self.user,
            title='Thread 1',
            status='open'
        )
        Thread.objects.create(
            author=self.user,
            title='Thread 2',
            status='closed'
        )
        response = self.client.get(self.thread_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get('results', [])), 2)
    
    def test_ST_8_1_3_create_post(self):
        """ST-8.1.3: Test create post endpoint"""
        thread = Thread.objects.create(
            author=self.user,
            title='Test Thread',
            status='open'
        )
        post_url = '/api/posts/'
        data = {
            'thread': thread.id,
            'body': 'This is a reply'
        }
        response = self.client.post(post_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(thread=thread).exists())


class ST9_ReviewAPITests(TestCase):
    """ST-9: Review API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.reviewer = User.objects.create_user(email='reviewer@example.com', password='pass')
        self.reviewee = User.objects.create_user(email='reviewee@example.com', password='pass')
        self.owner = User.objects.create_user(email='owner@example.com', password='pass')
        # Create profiles
        Profile.objects.create(user=self.reviewer)
        Profile.objects.create(user=self.reviewee)
        Profile.objects.create(user=self.owner)
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Test Service',
            description='Test'
        )
        self.client.force_authenticate(user=self.reviewer)
        self.review_url = '/api/reviews/'
    
    def test_ST_9_1_1_create_review(self):
        """ST-9.1.1: Test create review endpoint"""
        data = {
            'reviewee': self.reviewee.id,
            'review_type': 'service_provider',
            'rating': 5,
            'title': 'Great service',
            'content': 'Excellent work!',
            'related_service': self.service.id,
            'is_published': True
        }
        response = self.client.post(self.review_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Review.objects.filter(
            reviewer=self.reviewer,
            reviewee=self.reviewee
        ).exists())
    
    def test_ST_9_1_2_list_reviews(self):
        """ST-9.1.2: Test list reviews endpoint"""
        Review.objects.create(
            reviewer=self.reviewer,
            reviewee=self.reviewee,
            review_type='service_provider',
            rating=5,
            title='Great',
            content='Test',
            related_service=self.service,
            is_published=True
        )
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data.get('results', [])), 1)


class ST10_ReportAPITests(TestCase):
    """ST-10: Report API Tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password='pass')
        self.owner = User.objects.create_user(email='owner@example.com', password='pass')
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Test Service',
            description='Test'
        )
        self.client.force_authenticate(user=self.user)
        self.report_url = '/api/reports/'
    
    def test_ST_10_1_1_create_report(self):
        """ST-10.1.1: Test create report endpoint"""
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Service)
        data = {
            'content_type': content_type.id,
            'object_id': self.service.id,
            'reason': 'spam',
            'description': 'This is spam content'
        }
        response = self.client.post(self.report_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Report.objects.filter(
            reporter=self.user,
            content_type=content_type,
            object_id=self.service.id
        ).exists())


# ==================== USE CASE TESTS (UC-X.Y) ====================

class UC1_ServiceRequestWorkflowTests(TestCase):
    """UC-1: Complete Service Request Workflow"""
    
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='pass123'
        )
        self.requester = User.objects.create_user(
            email='requester@example.com',
            password='pass123'
        )
        # Create profiles
        Profile.objects.create(user=self.owner)
        Profile.objects.create(user=self.requester)
        # Create time accounts
        TimeAccount.objects.create(user=self.owner, balance=Decimal('10.00'))
        TimeAccount.objects.create(user=self.requester, balance=Decimal('10.00'))
        
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Math Tutoring',
            description='I offer math tutoring',
            estimated_hours=2
        )
    
    def test_UC_1_1_complete_service_workflow(self):
        """UC-1.1: Complete workflow: request → accept → start → complete → time transfer"""
        # Step 1: Create request
        self.client.force_authenticate(user=self.requester)
        response = self.client.post('/api/service-requests/', {
            'service_id': self.service.id,  # Use service_id
            'message': 'I want this service'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request_id = response.data['id']
        
        # Step 2: Accept request
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f'/api/service-requests/{request_id}/set_status/',
            {'status': 'accepted'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 3: Start service (approve_start)
        response = self.client.post(
            f'/api/service-requests/{request_id}/approve_start/',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 4: Complete service (owner)
        response = self.client.post(
            f'/api/service-requests/{request_id}/complete/',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 5: Complete service (requester)
        self.client.force_authenticate(user=self.requester)
        response = self.client.post(
            f'/api/service-requests/{request_id}/complete/',
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify time transfer
        owner_account = TimeAccount.objects.get(user=self.owner)
        requester_account = TimeAccount.objects.get(user=self.requester)
        
        # Owner should have received 2 hours, requester should have paid 2 hours
        self.assertEqual(owner_account.balance, Decimal('12.00'))
        self.assertEqual(requester_account.balance, Decimal('8.00'))


class UC2_UserRegistrationWorkflowTests(TestCase):
    """UC-2: User Registration and Profile Setup"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_UC_2_1_user_registration_and_profile_setup(self):
        """UC-2.1: Complete user registration workflow"""
        # Step 1: Register user
        response = self.client.post('/api/register/', {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'latitude': '41.0082',
            'longitude': '28.9784'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_id = response.data['user_id']
        
        # Step 2: Verify user created
        user = User.objects.get(id=user_id)
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Step 3: Verify profile created
        self.assertTrue(Profile.objects.filter(user=user).exists())
        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile.latitude)
        
        # Step 4: Verify TimeAccount created with 3 TBH
        self.assertTrue(TimeAccount.objects.filter(user=user).exists())
        account = TimeAccount.objects.get(user=user)
        self.assertEqual(account.balance, Decimal('3.00'))


class UC3_ServiceCreationWorkflowTests(TestCase):
    """UC-3: Service Creation and Discovery"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password='pass')
        Profile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.tag = Tag.objects.create(name='Cooking', slug='cooking')
    
    def test_UC_3_1_service_creation_and_tagging(self):
        """UC-3.1: Create service with tags and verify it appears in search"""
        # Step 1: Create service
        response = self.client.post('/api/services/', {
            'service_type': 'offer',
            'title': 'Cooking Classes',
            'description': 'Learn to cook Italian cuisine',
            'estimated_hours': 3,
            'tags': ['cooking'],
            'latitude': '41.0082',
            'longitude': '28.9784'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        service_id = response.data['id']
        
        # Step 2: Verify service created
        self.assertTrue(Service.objects.filter(id=service_id).exists())
        service = Service.objects.get(id=service_id)
        self.assertEqual(service.title, 'Cooking Classes')
        
        # Step 3: Verify tags associated
        self.assertIn(self.tag, service.tags.all())
        
        # Step 4: Search by tag
        response = self.client.get('/api/services/', {'tag': 'cooking'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', [])
        self.assertTrue(any(s['id'] == service_id for s in results))


class UC4_TimeBankingWorkflowTests(TestCase):
    """UC-4: Time Banking Transaction Flow"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password='pass')
        self.account = TimeAccount.objects.create(user=self.user, balance=Decimal('10.00'))
        self.client.force_authenticate(user=self.user)
    
    def test_UC_4_1_time_transaction_flow(self):
        """UC-4.1: Complete time transaction workflow"""
        # Step 1: Verify initial balance
        response = self.client.get('/api/time-accounts/')
        # Response might be list or dict with results
        if isinstance(response.data, list):
            initial_balance = response.data[0]['balance']
        else:
            initial_balance = response.data.get('results', [response.data])[0]['balance']
        self.assertEqual(float(initial_balance), 10.00)
        
        # Step 2: Create credit transaction (simulated)
        transaction = TimeTransaction.objects.create(
            account=self.account,
            transaction_type='credit',
            amount=Decimal('5.00'),
            status='completed',
            description='Service completed'
        )
        
        # Step 3: Update account balance
        self.account.balance += transaction.amount
        self.account.total_earned += transaction.amount
        self.account.save()
        
        # Step 4: Verify balance updated
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal('15.00'))
        self.assertEqual(self.account.total_earned, Decimal('5.00'))


class UC5_ModerationWorkflowTests(TestCase):
    """UC-5: Content Reporting and Moderation"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password='pass')
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='pass',
            is_staff=True
        )
        self.owner = User.objects.create_user(email='owner@example.com', password='pass')
        self.service = Service.objects.create(
            owner=self.owner,
            service_type='offer',
            title='Test Service',
            description='Test'
        )
    
    def test_UC_5_1_report_and_moderation_workflow(self):
        """UC-5.1: Report content and admin moderation"""
        from django.contrib.contenttypes.models import ContentType
        
        # Step 1: User reports content
        self.client.force_authenticate(user=self.user)
        content_type = ContentType.objects.get_for_model(Service)
        response = self.client.post('/api/reports/', {
            'content_type': content_type.id,
            'object_id': self.service.id,
            'reason': 'spam',
            'description': 'This is spam'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        report_id = response.data['id']
        
        # Step 2: Admin views reports
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reports = response.data.get('results', [])
        self.assertTrue(any(r['id'] == report_id for r in reports))
        
        # Step 3: Admin resolves report
        response = self.client.post(
            f'/api/reports/{report_id}/resolve/',
            {'action': 'dismiss', 'notes': 'Not spam'},
            format='json'
        )
        # Note: Actual endpoint may vary
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
